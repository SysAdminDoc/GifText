# GifText v1.2.1

## What
Full-featured animated GIF text editor for meme creation. Add multiple text labels that track moving subjects with keyframe animation, onion skinning, undo/redo, project save/load, presets, and multi-format export.

## Stack
- Python, PyQt6 (GUI), Pillow (GIF I/O + export rendering), OpenCV (opencv-python-headless)
- Single file: `GifText.py`
- `_bootstrap()` auto-installs deps (PyQt6, Pillow, opencv-python-headless)

## Run
```
python GifText.py
```

## Version History
- **v1.2.1** - UI color refinement (GitHub Dark palette #0d1117), toolbar reorganized into primary/utility rows, selection card panel, workspaceMeta/workspaceHint labels, reduced border-radius (14px)
- **v1.2.0** - Deep dark UI overhaul (AMOLED-level #060913 base), layer visibility toggles, helper refactors (_reset_document_state, _schedule_snapshot, _ensure_keyframe, _resolve_export_target, _set_layer_controls_enabled), improved project file handling (relative paths, UTF-8), export improvements (PNG sequence status, filter-based extension), UndoManager.clear(), OpenCV dependency added
- **v1.1.0** - Drag-resize handle, recent files menu, undo-on-drag-end, resize cursor feedback, README
- **v1.0.0** - Major feature release (16 features from competitive research)
- **v0.2.0** - On-canvas text selection, drag tracking, mousewheel frame stepping
- **v0.1.0** - Initial commit

## Architecture
- **TextLayer** - text element with keyframes, timing (frame_in/out, fade_in/out), visibility toggle, serializable
- **TextKeyframe** - per-frame properties (position, font, color, etc.), serializable to/from dict, interpolation support
- **UndoManager** - JSON snapshot-based undo/redo stack (50 levels), clear() method
- **GifCanvas** - QWidget: onion skin, zoom/pan, drag/drop, click-to-select, drag-to-move, drag-to-resize, visibility_changed signal
- **LayerTimeline** - visual timeline with colored layer bars, keyframe diamonds, playhead
- **GifTextApp (QMainWindow)** - main window, property panel, transport controls, export, project save/load, recent files
- Export: GIF (RGB), WebP (RGBA, quality 85), PNG sequence

## Key Design Decisions
- Drag-resize detected via _check_resize_handle() measuring distance from bottom-right of text bounding box
- drag_ended signal triggers undo snapshot (not every mousemove)
- _schedule_snapshot() with 280ms delay for batching rapid property changes
- Recent files stored in ~/.giftext_recent.json (max 10)
- Project file (.giftext) stores absolute + relative GIF path with multi-candidate fallback
- Deep dark theme: #060913 base, #0d1321 panels, #1b2437 borders, gradient accent buttons
- Layer visibility ON/OFF toggle per layer in the layer list

## Gotchas
- GIF format has no alpha - GIF export converts RGBA->RGB
- WebP export preserves alpha
- Font path matching is Windows-specific (C:/Windows/Fonts/)
- Pillow rounded_rectangle used for bg_box in export (requires Pillow 8.2+)
- QPlainTextEdit textChanged has no args (unlike QLineEdit)
- QPointF.toPoint() needed for menu positioning
- MSVC raw string literal 16380 char limit if ever porting to C++
- OpenCV added for future motion tracking features; currently imported but core tracking not yet wired
