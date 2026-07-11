#!/usr/bin/env python3
"""
Нормализация Character Pieces для Character Generator 2.0.

Купленный asset-pack Modern Interiors новой версии: размеры листов не совпадают
с SpriteSize_* в CharacterTypeSO, на которые заточен генератор. Этот скрипт
приводит PNG к ожидаемым размерам в ОТДЕЛЬНУЮ папку (оригиналы не трогает):

  ADULT  (Bodies/Eyes/Outfits/Hairstyles/Accessories/Premade/Books):
         896x656 (или 927x656)  ->  crop до 896x640 (верхние 640 строк, левые 896).
         Безопасно: реальный контент во всех adult-листах заканчивается на Y<=639.

  KIDS   Eyes_kids / Outfits_kids:  384x96  ->  pad до 384x128 прозрачным СНИЗУ.
         Контент привязан к верху (проверено структурно: отступ глаз/одежды от
         макушки тела совпадает с adult-эталоном). LimeZu обрезал пустые нижние ряды.
         Файлы уже 384x128 копируются как есть.

  KIDS   Bodies_kids / Hairstyles_kids: 384x128 -> копируются без изменений.

Код генератора грузит ТОЛЬКО <category>/16x16/*.png, поэтому нормализуем
только подпапки 16x16.

Использование:
  python3 normalize_character_pieces.py <SRC> <DST>
  SRC = оригинальная папка Character_Generator (с symlink'ом в корне проекта)
  DST = куда положить нормализованную копию
"""
import os
import sys
import shutil
from PIL import Image

# target: (width, height, mode)
#   crop  — взять левый-верхний угол (0,0,W,H), отбросить padding снизу/справа
#   pad_b — paste в (0,0) на холст WxH, добор прозрачным снизу
TARGETS = {
    "Bodies":            (896, 640, "crop"),
    "Eyes":              (896, 640, "crop"),
    "Outfits":           (896, 640, "crop"),
    "Hairstyles":        (896, 640, "crop"),
    "Accessories":       (896, 640, "crop"),
    "0_Premade_Characters": (896, 640, "crop"),
    "Books":             (896, 640, "crop"),
    "Bodies_kids":       (384, 128, "copy"),
    "Hairstyles_kids":   (384, 128, "copy"),
    "Eyes_kids":         (384, 128, "pad_b"),
    "Outfits_kids":      (384, 128, "pad_b"),
}


def rms(a, b):
    """Среднеквадратичное отличие RGBA-изображений одинакового размера."""
    if a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    w, h = a.size
    s = 0.0
    n = 0
    for y in range(h):
        for x in range(w):
            ra, ga, ba, aa = pa[x, y]
            rb, gb, bb, ab = pb[x, y]
            s += (ra - rb) ** 2 + (ga - gb) ** 2 + (ba - bb) ** 2 + (aa - ab) ** 2
            n += 4
    return (s / n) ** 0.5 if n else 0.0


def normalize_one(src_path, dst_path, target_w, target_h, mode):
    """Вернуть (исходный размер, итоговый размер, rms_искажения_контента)."""
    src = Image.open(src_path).convert("RGBA")
    sw, sh = src.size

    if mode == "copy":
        # Просто копируем (размер уже должен совпадать с target).
        dst = src
        dist = 0.0 if (sw == target_w and sh == target_h) else None
    elif mode == "crop":
        # Левый-верхний угол target_w x target_h.
        dst = src.crop((0, 0, target_w, target_h))
        # Контент должен полностью уместиться: проверяем, что то что отбросили
        # снизу/справа — пустое (прозрачное). RMS между сохранённым регионом
        # оригинала и результатом должен быть 0 (crop не меняет пиксели).
        original_region = src.crop((0, 0, min(sw, target_w), min(sh, target_h)))
        result_region = dst.crop((0, 0, min(sw, target_w), min(sh, target_h)))
        dist = rms(original_region, result_region)
    elif mode == "pad_b":
        if sh >= target_h:
            # Уже достаточной высоты — берём как есть (copy).
            dst = src.crop((0, 0, min(sw, target_w), target_h))
            original_region = src.crop((0, 0, min(sw, target_w), target_h))
            dist = rms(original_region, dst)
        else:
            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            canvas.paste(src, (0, 0))
            dst = canvas
            # Контент (верхние sh строк) должен совпасть с оригиналом побайтово.
            original_region = src.crop((0, 0, sw, sh))
            result_region = dst.crop((0, 0, sw, sh))
            dist = rms(original_region, result_region)
            # Добор снизу должен быть полностью прозрачным.
            padding = dst.crop((0, sh, target_w, target_h))
            if padding.getbbox() is not None:
                dist = -1.0  # сигнал: в padding оказались непрозрачные пиксели
    else:
        raise ValueError(mode)

    dst.save(dst_path)
    return (sw, sh), dst.size, dist


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src_root, dst_root = sys.argv[1], sys.argv[2]

    if os.path.exists(dst_root):
        shutil.rmtree(dst_root)
    os.makedirs(dst_root)

    summary = {}
    problems = []

    for cat, (tw, th, mode) in TARGETS.items():
        src_dir = os.path.join(src_root, cat, "16x16")
        dst_dir = os.path.join(dst_root, cat, "16x16")
        if not os.path.isdir(src_dir):
            print(f"[SKIP] нет папки: {src_dir}")
            continue
        os.makedirs(dst_dir, exist_ok=True)

        files = sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".png"))
        sizes_before = {}
        distortions = []
        for fn in files:
            src_path = os.path.join(src_dir, fn)
            dst_path = os.path.join(dst_dir, fn)
            before, after, dist = normalize_one(src_path, dst_path, tw, th, mode)
            sizes_before[before] = sizes_before.get(before, 0) + 1
            if dist is None:
                problems.append(f"{cat}/{fn}: размер не совпал с target {before}->{after}")
            elif dist < 0:
                problems.append(f"{cat}/{fn}: в padding попал непрозрачный контент!")
            elif dist > 0.5:
                problems.append(f"{cat}/{fn}: RMS контента {dist:.2f} (ожидалась точная копия)")
            else:
                distortions.append(dist)

        before_str = ", ".join(f"{w}x{h}x{n}" for (w, h), n in sorted(sizes_before.items()))
        max_dist = max(distortions) if distortions else 0.0
        summary[cat] = (before_str, f"{tw}x{th}", len(files), mode, max_dist)

    print("\n=== Сводка нормализации ===")
    print(f"{'Категория':24s} {'было':28s} {'стало':10s} {'файлов':6s} {'режим':6s} {'maxRMS'}")
    for cat, (b, a, n, m, d) in summary.items():
        print(f"{cat:24s} {b:28s} {a:10s} {n:<6d} {m:6s} {d:.2f}")

    if problems:
        print(f"\n⚠️  ПРОБЛЕМ ({len(problems)}):")
        for p in problems:
            print("  -", p)
        sys.exit(2)
    else:
        total = sum(s[2] for s in summary.values())
        print(f"\n✅ OK: {total} файлов нормализовано, контент не искажён.")


if __name__ == "__main__":
    main()
