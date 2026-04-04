# GifText v1.0.0

## What
Full-featured animated GIF text editor for meme creation. Add multiple text labels that track moving subjects with keyframe animation, onion skinning, undo/redo, project save/load, presets, and multi-format export.

## Stack
- Python, PyQt6 (GUI), Pillow (GIF I/O + export rendering)
- Single file: `GifText.py`
- `_bootstrap()` auto-installs deps

## Run
```
python GifText.py
```

## Features Added in v1.0.0
- Undo/Redo (Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y) with snapshot history
- Onion skinning (ghost previous frame)
- Multi-line text input (QPlainTextEdit)
- Layer timing: start/end frames + fade in/out
- Layer timeline bars showing colored ranges + keyframe diamonds + playhead
- Meme presets (Classic, Modern, Subtitle, Bold Impact, Neon)
- Background box option (subtitle-style semi-transparent BG)
- Copy keyframe to range (10 frames)
- Duplicate layer (right-click context menu)
- Playback speed control (0.25x-4x)
- Zoom/pan canvas (Ctrl+wheel zoom, middle-click pan)
- Drag & drop GIF onto canvas
- Project save/load (.giftext JSON)
- Recent files tracking
- WebP + PNG sequence export
- Ctrl+S save project shortcut

## Architecture
- **TextLayer** - text element with keyframes, timing (frame_in/out, fade_in/out), serializable
- **TextKeyframe** - per-frame properties, serializable to/from dict
- **UndoManager** - JSON snapshot-based undo/redo stack (50 levels)
- **GifCanvas** - QWidget: onion skin, zoom/pan, drag/drop, click-to-select, drag-to-move
- **LayerTimeline** - visual timeline with colored layer bars, keyframe diamonds, playhead
- **LayerWidget** - layer list item with context menu (duplicate)
- Export: GIF (RGB), WebP (RGBA, quality 85), PNG sequence

## Key Design Decisions
- Onion skin draws previous frame at 30% opacity with blue tint
- Layer timing: frame_out=-1 means "last frame"
- Fade in/out multiplies with keyframe opacity
- Presets set both layer properties AND current keyframe properties
- Copy KF copies current keyframe props to next 10 frames
- Project file (.giftext) stores absolute GIF path with fallback to relative
- Zoom via Ctrl+wheel, pan via middle-click drag, reset via button
- Undo snapshots on: add/delete layer, set/delete keyframe, color change, preset apply

## Gotchas
- GIF format has no alpha - GIF export converts RGBA->RGB
- WebP export preserves alpha
- Font path matching is Windows-specific (C:/Windows/Fonts/)
- Pillow rounded_rectangle used for bg_box in export (requires Pillow 8.2+)
- QPlainTextEdit textChanged has no args (unlike QLineEdit)
