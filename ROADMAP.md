# ROADMAP

Backlog for GifText. Stays focused on the "label moving subjects in a GIF" niche that nothing
else handles cleanly on desktop.

## Planned Features

### Text rendering
- **Gradient fill** + **rainbow animation** on the text color channel.
- **Emoji rendering** via the OS emoji font with color support.
- **Rich text per-line** - different size/color/weight within one text block.
- **Curved / arc text** path option.

### Canvas
- **Multi-layer stickers / emoji / shapes** alongside text layers with the same keyframe engine.
- **Mask layer** - drawable alpha mask that clips text to a subject shape.
- **Crop / rotate source GIF** non-destructively at export.

### Export
- **Palette quality slider** (gif.js-style dither options).

### Workflow
- **Project template library** - save a multi-layer setup as a template, apply to a new GIF.
- **Recent projects with thumbnails**.


## Competitive Research

- **Ezgif "Add text" tool** - single-frame or globally-fixed text; no tracking. GifText's
  keyframes are already the differentiator; keep pushing on that axis.
- **Kapwing / Giphy Caption** - polished but server-side and watermarked on free tier. GifText
  is the local-only alternative.
- **After Effects** - overkill for GIF-labeling; GifText stays the one-purpose fast option.
- **ScreenToGif (C#, Windows)** - excellent frame-editor; worth borrowing its frame-level
  operations (delete, duplicate, reverse range) which GifText currently lacks.
- **Motion Canvas / Rive** - code-based animation; useful as a reference for the keyframe curve
  editor.

## Nice-to-Haves

- **Auto-suggest label position** - detect subjects via BlazeFace/MediaPipe and propose where to
  anchor a label.
- **Plugin SDK** (Python entry points) for custom effect layers.

## Open-Source Research (Round 2)

### Related OSS Projects
- **animeme (OfirKP)** - https://github.com/OfirKP/animeme - Closest peer: Python GIF-meme editor with keyframes for text position + font size, linear interpolation, JSON template save/load, CLI `generate_meme.py`.
- **Gifcurry** - https://github.com/lettier/gifcurry - Haskell; GUI+CLI with font/size/color/position/outline/rotation + per-text timing. Mature text overlay model.
- **Kapi** - https://github.com/jeremyckahn/kapi - Pure keyframe animation API for canvas; useful library model if you refactor animation engine.
- **rekapi** - https://github.com/jeremyckahn/rekapi - Kapi's successor; full tween engine with easing functions and actor-based timeline.
- **ScreenToGif** - https://github.com/NickeManarin/ScreenToGif - C#/WPF per-frame text edit; different UX paradigm (no interpolation) but strong frame-list ergonomics.
- **gif-meme-generator / impactful JS libs** - https://github.com/topics/gif-maker - small one-off meme scripts worth skimming.
- **gif.js** - https://github.com/jnordberg/gif.js - Encoder if you want a web-export path in the future.

### Features to Borrow
- JSON template save/load from `animeme` - extend: export `.gmtext` templates to share online, import via drag-drop.

### Patterns & Architectures Worth Studying
- **Actor + timeline model** (`rekapi`): text = actor; keyframes = state at time t; engine tweens.
- **Dirty-rect repaint**: only re-rasterize the text area on keyframe change, not the whole GIF.






