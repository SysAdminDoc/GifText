# GifText v0.2.0

## What
Animated GIF text editor for meme creation. Add multiple text labels that track moving subjects across frames with keyframe animation.

## Stack
- Python, PyQt6 (GUI), Pillow (GIF I/O + export rendering)
- Single file: `GifText.py`
- `_bootstrap()` auto-installs deps

## Run
```
python GifText.py
```

## Architecture
- **TextLayer** - text element with keyframe list, color-coded accent for identification
- **TextKeyframe** - per-frame properties (position, size, opacity, color, outline, rotation)
- **GifCanvas** - QWidget with QPainter rendering, click-to-select, drag-to-move, mousewheel frame stepping
- **KeyframeBar** - clickable timeline with keyframe diamonds
- Smooth ease-in-out (smoothstep) interpolation between keyframes
- Export renders text via Pillow ImageDraw with stroke_width support

## Key Design Decisions
- Positions stored as 0..1 relative coords (resolution independent)
- On-canvas click-to-select: hit tests each visible layer, selects nearest
- Dragging auto-creates keyframe at current frame
- Each layer gets a unique accent color + tag label visible on canvas
- Selected layer shows dashed bounding box with corner handles
- Mousewheel on canvas steps frames (core workflow for tracking subjects)
- Pillow export uses stroke_width for outlines with manual offset fallback

## Workflow (sinking boat meme example)
1. Load GIF
2. Add 3 text layers, type each boy's name
3. Frame 1: drag each name above each boy
4. Mousewheel to advance ~10 frames, drag names to follow movement
5. Repeat until end - interpolation fills gaps smoothly
6. Export

## Gotchas
- GIF format has no alpha - export converts RGBA->RGB
- Font path matching is Windows-specific (C:/Windows/Fonts/)
- Hit testing uses approximate character-width estimation, not pixel-perfect
