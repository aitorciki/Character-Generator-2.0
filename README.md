# Character Generator 2.0 — macOS build

<p align="center">
  <img src="https://github.com/Legendaryswordsman2/Character-Generator-2.0/assets/87250196/150acf80-6c30-424c-b8e7-050adccb200a" alt="Character Generator 2.0 Logo" />
</p>

A native **macOS (Apple Silicon)** build of [Character Generator 2.0](https://legendaryswordsman2.itch.io/character-generator) by **Legendaryswordsman2**, fixed to work with the current version of the paid **Modern Interiors** asset pack by **LimeZu**.

The upstream project only ships Windows/Linux builds on itch.io. This fork adds:

1. A **normalization script** that adapts the *current* Modern Interiors spritesheets (whose dimensions changed in a newer version) to what the generator expects — restoring correct character previews and animation frames.
2. A **path-resolution fix** (based on [PR #3](https://github.com/Legendaryswordsman2/Character-Generator-2.0/pull/3) by JohanJimenex) so the built `.app` finds `Character Pieces` next to itself — i.e. it launches with a normal double-click, no terminal required.

---

## ⚠️ Read this first — licensing

This project depends on **paid / proprietary** assets and libraries. By using it you accept the following:

| Component | License | What you may do |
|---|---|---|
| **Character Generator 2.0** source (this repo) | **GNU GPL v3** (upstream) | Fork, modify, distribute — derivative works must also be GPL v3 with source available |
| **Modern Interiors** spritesheets | **© LimeZu — paid**, [buy on itch.io](https://limezu.itch.io/moderninteriors) | **Never redistribute.** Every user must buy their own copy |
| **Odin Inspector** | **© Sirenix — paid** | Used for development only (`Editor`-only assemblies). **Not included in the built app.** Anyone *building from source* needs their own Odin license |
| **LootLocker** SDK | proprietary | The upstream `apiKey` was **removed** in this fork — cloud features (leaderboards/cloud saves) are disabled |

**This fork does not contain, and never will contain, the paid Modern Interiors spritesheets.** You must obtain them yourself.

---

## Quick start (end users)

You want the running app, not the source.

### 1. Download the macOS build
From the [**latest release**](../../releases/latest), pick the build for **your Mac's architecture** and unzip it:
- **`Character-Generator-2.0-AppleSilicon.zip`** — for M-series chips (M1/M2/M3/…). You get `Character-Generator-2.0.app`.
- **`Character-Generator-2.0-Intel.zip`** — for Intel Macs. You get `Character-Generator-2.0_intel.app` (also runs on Apple Silicon via Rosetta, but use the native build if you can).

Not sure which? Apple menu → **About This Mac** shows "Apple M-series" (use Apple Silicon) or an Intel chip name (use Intel).

> The app is **unsigned**. On first launch macOS Gatekeeper will block it. Right-click → **Open** → confirm, or run once in Terminal:
> ```bash
> xattr -dr com.apple.quarantine /path/to/Character-Generator-2.0.app
> ```

### 2. Buy Modern Interiors
Purchase [Modern Interiors](https://limezu.itch.io/moderninteriors) by LimeZu. From the archive, locate `2_Characters/Character_Generator/` — this is your raw `Character Pieces` source.

### 3. Normalize the spritesheets
The current asset pack version has different dimensions than the generator expects, which breaks character previews and animations. Normalize once with the included script:

```bash
# Python 3.9+ required
pip install Pillow            # or: pip install -r tools/requirements.txt
python3 tools/normalize_character_pieces.py \
    "/path/to/Character_Generator" \
    "/path/to/Character_Generator_normalized"
```

This produces a `Character_Generator_normalized/` folder (originals are untouched) where every sheet matches the size the generator expects (`896×640` for adults, `384×128` for kids). The script verifies pixel-for-pixel that **no content is lost** (RMS = 0).

### 4. Put `Character Pieces` next to the app
Rename the normalized folder to **`Character Pieces`** (with a space) and place it **in the same folder as** `Character-Generator-2.0.app`:

```
My Folder/
├── Character-Generator-2.0.app
└── Character Pieces/        ← the normalized folder
    ├── Bodies/16x16/...
    ├── Eyes/16x16/...
    └── ...
```

Now **double-click the `.app`**. It will find `Character Pieces` next to itself and load. Done.

> Where are saved characters stored? In `~/Library/Application Support/com.Gray-Matter-Studios.Character-Generator-2.0/Saved Characters/` (Unity derives this path from the app's bundle id; standard macOS app data location — survives app reinstall, not transferred to another Mac automatically). In Finder: **Go → Go to Folder (⇧⌘G)**, paste the path.
>
> After saving you may see **"(Offline) Can't load personal/global stats"** — this is expected and harmless: online leaderboards are disabled in this fork, and the character PNG is already written to the folder above.

---

## Building from source (developers)

You only need this if you want to modify the project or build for Intel/Universal macOS yourself.

### Requirements
- **Unity Hub** + **Unity 2022.3.14f1** (exact version — matches `ProjectSettings/ProjectVersion.txt`)
- A valid **Odin Inspector** license (Sirenix) — the project uses Odin attributes; the Editor assemblies are not committed as functional without a license
- **Modern Interiors** purchased (see above), normalized via the script
- Python 3.9+ with Pillow (only for the normalization step)

### Steps
1. Clone this repo.
2. In the project root, create a symlink (or copy) so `Character Pieces` points at your **normalized** folder:
   ```bash
   ln -s "/abs/path/to/Character_Generator_normalized" "Character Pieces"
   ```
3. Open the project in Unity 2022.3.14f1, let it import fully.
4. **File → Build Settings** → Platform `PC, Mac & Linux Standalone`, Target `macOS`, Architecture `ARM64` (or Universal).
5. **Build** to an empty folder. `Assets/Editor/CharacterPiecesPostBuild.cs` will auto-copy `Character Pieces` next to the built `.app` and into its `StreamingAssets`.
6. Launch the produced `.app`.

> A fresh checkout has an **empty** `LootLockerConfig.asset` (the upstream API key was removed). Cloud features won't work until you enter your own key in Unity → LootLocker settings.

---

## The problem this fork solves

Legendaryswordsman2 built the generator against an **older** version of Modern Interiors. LimeZu later changed the spritesheet dimensions:

| Category | Generator expects | Current asset pack | Difference |
|---|---|---|---|
| Adult (Bodies/Eyes/Outfits/Hair/Accessories) | `896×640` | `896×656` / `927×656` | empty padding (bottom + right) |
| Child `Eyes_kids` / `Outfits_kids` | `384×128` | `384×96` | missing 32px (content is top-aligned) |

This caused a chain of bugs: sprites rejected by the size check → `IndexOutOfRangeException` in `SpriteManager.CombineTwoTextures` (layers of different sizes) → shifted content → broken animation sub-sprite rects (head at the bottom, "random tiles" while walking, missing child outfits).

**Fix:** normalize the assets to the expected sizes (script), rather than patching the runtime code. This keeps the generator's code at the upstream original and fixes *everything at once*. Verified with RMS comparison: **no content is lost**.

Full background is in [`HANDOFF.md`](HANDOFF.md).

---

## Changes vs upstream

This fork is upstream `Main` plus:

- `tools/normalize_character_pieces.py` + `tools/requirements.txt` — asset normalization.
- `Assets/Create Character Menu/Scripts/CharacterPieceDatabase.cs` — `TryResolveCharacterPiecesDirectory()` (searches cwd, `Assets`, `StreamingAssets`, `persistentDataPath`, and locations near the `.app` bundle). Based on PR #3, extended to also look *next to* the `.app`.
- `Assets/Create Character Menu/Scripts/CharacterPieceGrabber.cs` — uses `TryResolveCharacterPiecesDirectory` instead of `Directory.GetCurrentDirectory()` only.
- `Assets/Editor/CharacterPiecesPostBuild.cs` — auto-copies `Character Pieces` into the build (from PR #3, unchanged).
- `Assets/Plugins/aarch64/discord_game_sdk.dylib.meta` — disables the duplicate Discord plugin (the `.bundle` remains the active macOS plugin). Resolves import errors.
- `Assets/LootLockerSDK/Resources/Config/LootLockerConfig.asset` — upstream API key/token **removed**.
- `README.md`, `HANDOFF.md`.

---

## Credits

- **Character Generator 2.0** — [Legendaryswordsman2](https://github.com/Legendaryswordsman2) (GPL v3)
- **Modern Interiors** sprites — [LimeZu](https://limezu.itch.io) (paid, not included)
- macOS path-resolution & PostBuild — [JohanJimenex (PR #3)](https://github.com/Legendaryswordsman2/Character-Generator-2.0/pull/3)

## Known limitations

- Two architecture-specific builds (Apple Silicon + Intel). No single Universal binary — see *Quick start* for which to download. Build Universal yourself if you want one fat `.app`.
- **Unsigned** app — Gatekeeper warning on first launch (see Quick start).
- **LootLocker disabled** — leaderboards/cloud saves off unless you set your own key. The "(Offline) can't load stats" note after saving is expected; local saving is unaffected.
- Normalization is tuned to the asset-pack dimensions described above; if a future LimeZu update changes dimensions again, re-run the script (rules are in `TARGETS` inside it).

---

# Using the generator (original guide by Legendaryswordsman2)

## The Character Generator 2.0 was created to aid in the process of creating characters from Modern Interiors. It's a remake of the orignal Character Generator which had several flaws which this new Character Generator fixes.

## Guide

### –Familiarize yourself–
#### At the top of the screen are dropdowns. Each dropdown allows you to modify a different part of the character (Body, Eyes, Outfit, Etc). In the middle of the screen is the character preview where you can view your character as you're making it.

### -Tabs-
#### At the bottom of the screen are 4 tabs, each tab serves a different purpose in helping you create your character. To the sides are two buttons, the right side button allows you to save your character to your computer. The left side button is an info menu showing various information about the Character Generaator 2.0.

### -Animation Tab-
#### This is the default tab. This tab allows you to change the animation playing in the character preview. 10 animations are available to choose such as idle, walk, sit, etc. Click on any animation to start playing it on repeat.

### -Randomize Tab-
#### To the right of the window is a set of toggles. You can use these to set which parts of the character you want to be randomized. To the left of the window is a button labeled "Randomize", clicking it will randomize all parts of the character that have been toggled on.

### -History Tab-
#### This tab contains a list of the last 30 character modifications and saved characters. The default view shows your previous character edits. Every time you change any piece of your character it will be logged here. Clicking on any previous character will revert your character to that version.

#### At the bottom of the tab  you can change the view mode, the "Modifications" mode is the default mode which was previously explained. The "Saved" mode shows your last 30 saved characters.

### -Character Tab-
#### To the left of the character tab you can select the character type, the default is adult. The second option is a child. Children contain all the same character pieces an adult has except accessories.

#### To the right of the tab is the "Try Character" button. Clicking this button will transport you to a simulated world where you can test out how your character looks and feels.

### -Save Character-
#### To the right of the tabs is a button labeled "Save". Clicking this button opens a popup allowing you to save your character as a png file on your computer. Simply input the name you want for your character, it's size and optionally select which part of the spritesheet to save. You can save the entire spritesheet or only a particular animation, then click save.

#### Once saved, you'll be shown statistics about how many characters have been created and a button will be shown which when clicked will show where your character was saved.

### -Hotkeys-
#### Various hotkeys are available to make use of the Character Generator 2.0 easier. Hotkeys include the following:

#### - Open Save Popup: 'S'
#### - Open Info Popup: 'I'
#### - Randomize Character: 'R'
#### - Transfer to Try Character Scene: 'C'

### -Adding Character Pieces-
#### More character pieces are included in Modern Exteriors, to add them to the Character Generator first locate the installation directy of the Character Generator
#### (Defaults to Program Files (x86)).

#### From within that folder locate the "Character Pieces" folder which contains every character piece split into it's own folder. Simply go to the folder with the same type piece you want to add and drag and drop your new character piece into that folder. Note a 16x16 #### version is neccesary for it to be loaded when the tool is launched. Additional character pieces must be the same size as every other file in the same folder otherwise the file won't be loaded.

### –Need More Help?--
#### If you’re still confused about something or need clarification feel free to join the official LimeZu Community Server and ask me (@LegendarySwordsman2) any questions you may have. https://discord.com/invite/2wB3RuAESb
