# GifText v1.1.0

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

## v1.1.0 Changes
- Functional drag-resize handle (bottom-right corner handle resizes font on canvas)
- Recent files dropdown menu
- Undo snapshot on drag end (not every mousemove)
- Resize handle cursor feedback (SizeFDiagCursor on hover)
- README.md for GitHub

## Architecture
- **TextLayer** - text element with keyframes, timing (frame_in/out, fade_in/out), serializable
- **TextKeyframe** - per-frame properties, serializable to/from dict
- **UndoManager** - JSON snapshot-based undo/redo stack (50 levels)
- **GifCanvas** - QWidget: onion skin, zoom/pan, drag/drop, click-to-select, drag-to-move, drag-to-resize
- **LayerTimeline** - visual timeline with colored layer bars, keyframe diamonds, playhead
- Export: GIF (RGB), WebP (RGBA, quality 85), PNG sequence

## Key Design Decisions
- Drag-resize detected via _check_resize_handle() measuring distance from bottom-right of text bounding box
- drag_ended signal triggers undo snapshot (not every mousemove)
- Recent files stored in ~/.giftext_recent.json (max 10)
- Project file (.giftext) stores absolute GIF path with fallback to relative

## Gotchas
- GIF format has no alpha - GIF export converts RGBA->RGB
- WebP export preserves alpha
- Font path matching is Windows-specific (C:/Windows/Fonts/)
- Pillow rounded_rectangle used for bg_box in export (requires Pillow 8.2+)
- QPlainTextEdit textChanged has no args (unlike QLineEdit)
- QPointF.toPoint() needed for menu positioning
