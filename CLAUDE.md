# GifText v0.1.0

## What
Animated GIF text editor for meme creation. Add text with keyframe-based animation (position, size, opacity, color, rotation) smoothly interpolated across frames.

## Stack
- Python, PyQt6 (GUI), Pillow (GIF I/O + export rendering)
- Single file: `GifText.py`
- `_bootstrap()` auto-installs deps

## Run
```
python GifText.py
```

## Architecture
- **TextLayer** - text element with keyframe list
- **TextKeyframe** - per-frame properties (position, size, opacity, color, outline, rotation)
- **GifCanvas** - QLabel-based canvas with QPainter rendering, drag-to-position
- **KeyframeBar** - visual timeline showing keyframe diamonds
- Smooth ease-in-out interpolation between keyframes
- Export renders text via Pillow ImageDraw onto each PIL frame

## Key Decisions
- Positions stored as 0..1 relative coords (resolution independent)
- Dragging on canvas auto-creates keyframe at current frame
- QPainterPath used for outline text (stroke + fill technique)
- Font lookup tries Windows font paths, falls back to Impact then default

## Gotchas
- Pillow GIF export uses RGB (no alpha in GIF format)
- Font path matching is best-effort on Windows (truetype filename conventions vary)
- Outline rendering in export uses brute-force offset drawing (no stroke_width in older Pillow)
