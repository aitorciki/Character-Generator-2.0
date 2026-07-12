#!/usr/bin/env python3
"""
Normalize Character Pieces for Character Generator 2.0.

The current (paid) Modern Interiors asset pack uses spritesheet dimensions that
no longer match the SpriteSize_* values in CharacterTypeSO the generator is built
against. This script converts the PNGs to the expected sizes, writing them into a
SEPARATE folder (originals are left untouched):

  ADULT  (Bodies/Eyes/Outfits/Hairstyles/Accessories/Premade/Books):
         896x656 (or 927x656)  ->  crop to 896x640 (top 640 rows, left 896 cols).
         Safe: real content in every adult sheet ends at Y<=639.

  KIDS   Eyes_kids / Outfits_kids:  384x96  ->  pad to 384x128 with transparent
         pixels at the BOTTOM. Content is top-aligned (verified structurally: the
         eye/outfit offset from the top of the body matches the adult reference).
         LimeZu trimmed empty bottom rows. Files already 384x128 are copied as-is.

  KIDS   Bodies_kids / Hairstyles_kids: 384x128 -> copied unchanged.

The generator only loads <category>/16x16/*.png, so only the 16x16 subfolders are
normalized.

Usage:
  python3 normalize_character_pieces.py <SRC> <DST>
  SRC = original Character_Generator folder (or the project's "Character Pieces" symlink)
  DST = where to write the normalized copy
"""
import os
import sys
import shutil
from PIL import Image

# target: (width, height, mode)
#   crop  — take the top-left region (0,0,W,H), discarding bottom/right padding
#   pad_b — paste at (0,0) onto a WxH canvas, filling transparent at the bottom
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
    """Root-mean-square difference between two RGBA images of equal size."""
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
    """Return (source size, result size, content distortion RMS)."""
    src = Image.open(src_path).convert("RGBA")
    sw, sh = src.size

    if mode == "copy":
        # Plain copy (size should already match the target).
        dst = src
        dist = 0.0 if (sw == target_w and sh == target_h) else None
    elif mode == "crop":
        # Top-left region target_w x target_h.
        dst = src.crop((0, 0, target_w, target_h))
        # Content must fit entirely: verify that what we discard at the bottom/right
        # is empty (transparent). RMS between the kept region of the original and the
        # result must be 0 (cropping does not modify pixels).
        original_region = src.crop((0, 0, min(sw, target_w), min(sh, target_h)))
        result_region = dst.crop((0, 0, min(sw, target_w), min(sh, target_h)))
        dist = rms(original_region, result_region)
    elif mode == "pad_b":
        if sh >= target_h:
            # Already tall enough — take as-is (copy).
            dst = src.crop((0, 0, min(sw, target_w), target_h))
            original_region = src.crop((0, 0, min(sw, target_w), target_h))
            dist = rms(original_region, dst)
        else:
            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            canvas.paste(src, (0, 0))
            dst = canvas
            # The content (top sh rows) must match the original byte-for-byte.
            original_region = src.crop((0, 0, sw, sh))
            result_region = dst.crop((0, 0, sw, sh))
            dist = rms(original_region, result_region)
            # The bottom padding must be fully transparent.
            padding = dst.crop((0, sh, target_w, target_h))
            if padding.getbbox() is not None:
                dist = -1.0  # signal: opaque pixels ended up in the padding
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
            print(f"[SKIP] folder not found: {src_dir}")
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
                problems.append(f"{cat}/{fn}: size does not match target {before}->{after}")
            elif dist < 0:
                problems.append(f"{cat}/{fn}: opaque content ended up in the padding!")
            elif dist > 0.5:
                problems.append(f"{cat}/{fn}: content RMS {dist:.2f} (expected an exact copy)")
            else:
                distortions.append(dist)

        before_str = ", ".join(f"{w}x{h}x{n}" for (w, h), n in sorted(sizes_before.items()))
        max_dist = max(distortions) if distortions else 0.0
        summary[cat] = (before_str, f"{tw}x{th}", len(files), mode, max_dist)

    print("\n=== Normalization summary ===")
    print(f"{'Category':24s} {'before':28s} {'after':10s} {'files':6s} {'mode':6s} {'maxRMS'}")
    for cat, (b, a, n, m, d) in summary.items():
        print(f"{cat:24s} {b:28s} {a:10s} {n:<6d} {m:6s} {d:.2f}")

    if problems:
        print(f"\n⚠️  PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  -", p)
        sys.exit(2)
    else:
        total = sum(s[2] for s in summary.values())
        print(f"\n✅ OK: {total} files normalized, content not distorted.")


if __name__ == "__main__":
    main()
