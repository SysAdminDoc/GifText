# ROADMAP

Backlog for GifText. Stays focused on the "label moving subjects in a GIF" niche that nothing
else handles cleanly on desktop.

## Planned Features

### Animation
- **Motion tracking** — OpenCV-based point tracker (KCF/CSRT) that auto-generates keyframes as
  the chosen subject moves; user just clicks the subject once.
- **Path-based animation** — draw a bezier path, text follows it over N frames.
- **Bounce / wiggle / shake presets** — procedural jitter for emphasis text.
- **Ease curve editor** — per-keyframe Bezier curve picker, not just fixed ease-in-out.
- **Stagger multi-line text** — animate letters / words sequentially in.

### Text rendering
- **Outline + shadow + stroke layers** separately, each with its own color/opacity.
- **Gradient fill** + **rainbow animation** on the text color channel.
- **Font import** — load any TTF/OTF from disk; font picker with search.
- **Emoji rendering** via the OS emoji font with color support.
- **Rich text per-line** — different size/color/weight within one text block.
- **Curved / arc text** path option.

### Canvas
- **Multi-layer stickers / emoji / shapes** alongside text layers with the same keyframe engine.
- **Mask layer** — drawable alpha mask that clips text to a subject shape.
- **Crop / rotate source GIF** non-destructively at export.
- **Trim range** — cut start/end frames before labeling.
- **Resize source** for smaller output files.

### Export
- **Animated WebP + APNG** in addition to GIF and PNG sequence.
- **MP4 / WebM** export via PyAV so users can post to platforms that don't accept GIF.
- **Size-target export** — iteratively re-encode until output ≤ N MB.
- **Per-frame delay override** on export.
- **Palette quality slider** (gif.js-style dither options).

### Workflow
- **Import GifStudio project file** (sibling browser app) and reverse — unify the keyframe model
  across both apps.
- **Project template library** — save a multi-layer setup as a template, apply to a new GIF.
- **Recent projects with thumbnails**.
- **Autosave to IDB-like local cache** every N seconds.
- **Session recovery** on crash.

### Distribution
- **PyInstaller single-file exe** with `multiprocessing.freeze_support()` guard (PyQt6 + Pillow
  can pull in multiprocessing) and a runtime hook per the global CLAUDE.md pattern.
- **macOS `.app`** via py2app, notarized.
- **Linux AppImage**.
- **CI/CD build workflow** (GH Actions) targeting Windows/macOS/Linux.

## Competitive Research

- **Ezgif "Add text" tool** — single-frame or globally-fixed text; no tracking. GifText's
  keyframes are already the differentiator; keep pushing on that axis.
- **Kapwing / Giphy Caption** — polished but server-side and watermarked on free tier. GifText
  is the local-only alternative.
- **After Effects** — overkill for GIF-labeling; GifText stays the one-purpose fast option.
- **ScreenToGif (C#, Windows)** — excellent frame-editor; worth borrowing its frame-level
  operations (delete, duplicate, reverse range) which GifText currently lacks.
- **Motion Canvas / Rive** — code-based animation; out of scope but useful as a reference for the
  keyframe curve editor.

## Nice-to-Haves

- **Auto-suggest label position** — detect subjects via BlazeFace/MediaPipe and propose where to
  anchor a label.
- **Speech-to-text auto-subtitle** via Whisper (small model) on the GIF's audio if source video
  file is supplied alongside.
- **Share-to-imgur / giphy** button with user-supplied API token.
- **Cloud sync of projects** (opt-in, user-owned S3 bucket).
- **Plugin SDK** (Python entry points) for custom effect layers.
- **Command-line mode** — headless render from a project file, for batch labeling pipelines.

## Open-Source Research (Round 2)

### Related OSS Projects
- **animeme (OfirKP)** — https://github.com/OfirKP/animeme — Closest peer: Python GIF-meme editor with keyframes for text position + font size, linear interpolation, JSON template save/load, CLI `generate_meme.py`.
- **Gifcurry** — https://github.com/lettier/gifcurry — Haskell; GUI+CLI with font/size/color/position/outline/rotation + per-text timing. Mature text overlay model.
- **Kapi** — https://github.com/jeremyckahn/kapi — Pure keyframe animation API for canvas; useful library model if you refactor animation engine.
- **rekapi** — https://github.com/jeremyckahn/rekapi — Kapi's successor; full tween engine with easing functions and actor-based timeline.
- **ScreenToGif** — https://github.com/NickeManarin/ScreenToGif — C#/WPF per-frame text edit; different UX paradigm (no interpolation) but strong frame-list ergonomics.
- **gif-meme-generator / impactful JS libs** — https://github.com/topics/gif-maker — small one-off meme scripts worth skimming.
- **gif.js** — https://github.com/jnordberg/gif.js — Encoder if you want a web-export path in the future.

### Features to Borrow
- JSON template save/load from `animeme` — already present but extend: export `.gmtext` templates to share online, import via drag-drop.
- Keyframe interpolation of font size + rotation + color (`animeme` position-only + `rekapi`) — expand beyond position; opacity fade for meme transitions.
- Easing curves (`rekapi`) — ease-in/out/back/bounce; current linear only is limiting.
- Subtitle import `.srt`/`.vtt` (`Gifcurry`) — auto-generate timed text tracks from caption files.
- CLI rendering (`animeme generate_meme.py`) — headless `python gif_text.py --template=x.json --text="HELLO" --out=out.gif`.
- Font outline + drop-shadow (`Gifcurry`) — "Impact white on black stroke" is 90% of memes; preset button.
- Multi-text-layer timeline (each text its own track) — `ScreenToGif` frame-list + per-layer enable/disable.

### Patterns & Architectures Worth Studying
- **Actor + timeline model** (`rekapi`): text = actor; keyframes = state at time t; engine tweens. Cleaner than per-frame dict lookup; supports easing + pause/resume.
- **Dirty-rect repaint**: only re-rasterize the text area on keyframe change, not the whole GIF. Matters once you have 5+ text layers on 200-frame GIFs.
- **Bezier timing functions** (cubic-bezier) like CSS — store 4 control points, evaluate per-frame. Tiny code, huge UX gain vs linear.
- **Template versioning**: animeme's JSON is flat; add `{"schema_version": 2, ...}` now so future fields (opacity, rotation, outline) don't break old templates.
