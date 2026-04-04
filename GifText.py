"""
GifText v1.0.0 - Animated GIF Text Editor
Full-featured meme text animator with keyframe animation, onion skinning,
undo/redo, project save/load, drag-resize, text presets, and more.
"""

import sys
import os
import math
import copy
import json
import time

def _bootstrap():
    import subprocess
    required = {"PyQt6": "PyQt6", "PIL": "Pillow"}
    for mod, pkg in required.items():
        try:
            __import__(mod)
        except ImportError:
            for cmd in [
                [sys.executable, "-m", "pip", "install", pkg],
                [sys.executable, "-m", "pip", "install", "--user", pkg],
                [sys.executable, "-m", "pip", "install", "--break-system-packages", pkg],
            ]:
                try:
                    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except Exception:
                    continue

_bootstrap()

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox, QComboBox,
    QColorDialog, QFileDialog, QFrame, QSplitter, QCheckBox,
    QFontComboBox, QGroupBox, QGridLayout, QSizePolicy, QScrollArea,
    QPlainTextEdit, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, QSize, QMimeData
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPainter, QFont, QPen, QBrush,
    QFontMetrics, QPainterPath, QCursor, QWheelEvent, QAction
)
from PIL import Image, ImageDraw, ImageFont
import io

VERSION = "1.0.0"

LAYER_COLORS = [
    "#89b4fa", "#a6e3a1", "#f9e2af", "#f38ba8", "#cba6f7",
    "#fab387", "#94e2d5", "#f5c2e7", "#74c7ec", "#b4befe",
]

MEME_PRESETS = {
    "Classic Meme": {"font": "Impact", "bold": True, "upper": True, "color": "#ffffff",
                     "outline_color": "#000000", "outline_width": 4, "shadow": False, "size": 52, "bg_box": False},
    "Modern Clean": {"font": "Montserrat", "bold": True, "upper": False, "color": "#ffffff",
                     "outline_color": "#000000", "outline_width": 0, "shadow": True, "size": 36, "bg_box": False},
    "Subtitle": {"font": "Arial", "bold": True, "upper": False, "color": "#ffffff",
                 "outline_color": "#000000", "outline_width": 0, "shadow": False, "size": 28, "bg_box": True},
    "Bold Impact": {"font": "Impact", "bold": True, "upper": True, "color": "#f9e2af",
                    "outline_color": "#1e1e2e", "outline_width": 5, "shadow": True, "size": 60, "bg_box": False},
    "Neon": {"font": "Arial", "bold": True, "upper": False, "color": "#89b4fa",
             "outline_color": "#cba6f7", "outline_width": 3, "shadow": True, "size": 40, "bg_box": False},
}

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e; color: #cdd6f4;
    font-family: "Segoe UI", sans-serif; font-size: 13px;
}
QPushButton {
    background-color: #313244; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 6px;
    padding: 5px 12px; font-weight: 500;
}
QPushButton:hover { background-color: #45475a; border-color: #89b4fa; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { background-color: #1e1e2e; color: #585b70; border-color: #313244; }
QPushButton#accent { background-color: #89b4fa; color: #1e1e2e; font-weight: 600; }
QPushButton#accent:hover { background-color: #74c7ec; }
QPushButton#accent:disabled { background-color: #45475a; color: #585b70; }
QPushButton#danger { background-color: #f38ba8; color: #1e1e2e; }
QPushButton#danger:hover { background-color: #eba0ac; }
QPushButton#keyframeSet { background-color: #a6e3a1; color: #1e1e2e; font-weight: 600; }
QPushButton#keyframeSet:hover { background-color: #94e2d5; }
QPushButton#keyframeDel { background-color: #f38ba8; color: #1e1e2e; }
QPushButton#preset { background-color: #45475a; color: #cdd6f4; border-radius: 4px; padding: 3px 8px; font-size: 11px; }
QPushButton#preset:hover { background-color: #585b70; border-color: #89b4fa; }
QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox {
    background-color: #313244; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px;
    selection-background-color: #585b70;
}
QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #89b4fa; }
QPlainTextEdit { font-size: 14px; font-weight: 600; }
QSlider::groove:horizontal { height: 6px; background: #313244; border-radius: 3px; }
QSlider::handle:horizontal { background: #89b4fa; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }
QSlider::sub-page:horizontal { background: #585b70; border-radius: 3px; }
QGroupBox {
    border: 1px solid #45475a; border-radius: 6px;
    margin-top: 12px; padding-top: 14px; font-weight: 600; color: #89b4fa;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QScrollArea { border: none; background: transparent; }
QLabel#frameLabel { font-size: 15px; font-weight: 700; color: #f9e2af; min-width: 110px; }
QFrame#timeline { background-color: #181825; border-top: 1px solid #45475a; }
QStatusBar { background-color: #181825; color: #a6adc8; font-size: 12px; }
QCheckBox { spacing: 6px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #45475a; background: #313244; }
QCheckBox::indicator:checked { background: #89b4fa; border-color: #89b4fa; }
QSplitter::handle { background: #313244; width: 2px; }
QMenu { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px; }
QMenu::item { padding: 4px 20px; border-radius: 3px; }
QMenu::item:selected { background-color: #45475a; }
"""


# ============================================================================
#  Data Models
# ============================================================================

class TextKeyframe:
    __slots__ = ('frame', 'x', 'y', 'font_size', 'opacity',
                 'color', 'outline_color', 'outline_width', 'rotation')

    def __init__(self, frame=0, x=0.5, y=0.5, font_size=48, opacity=1.0,
                 color="#ffffff", outline_color="#000000", outline_width=3,
                 rotation=0.0):
        self.frame = frame
        self.x = x
        self.y = y
        self.font_size = font_size
        self.opacity = opacity
        self.color = color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.rotation = rotation

    def copy(self):
        return TextKeyframe(
            self.frame, self.x, self.y, self.font_size, self.opacity,
            self.color, self.outline_color, self.outline_width, self.rotation
        )

    def to_dict(self):
        return {s: getattr(self, s) for s in self.__slots__}

    @staticmethod
    def from_dict(d):
        return TextKeyframe(**{k: d[k] for k in TextKeyframe.__slots__ if k in d})


class TextLayer:
    _counter = 0

    def __init__(self, text="TEXT"):
        TextLayer._counter += 1
        self.id = TextLayer._counter
        self.text = text
        self.font_family = "Impact"
        self.bold = True
        self.italic = False
        self.alignment = "center"
        self.keyframes: list[TextKeyframe] = [TextKeyframe()]
        self.visible = True
        self.shadow = False
        self.uppercase = True
        self.bg_box = False
        self.accent = LAYER_COLORS[(self.id - 1) % len(LAYER_COLORS)]
        self.frame_in = 0
        self.frame_out = -1  # -1 = last frame
        self.fade_in = 0     # frames to fade in
        self.fade_out = 0    # frames to fade out

    def is_visible_at(self, frame: int, total_frames: int) -> bool:
        if not self.visible:
            return False
        out = self.frame_out if self.frame_out >= 0 else total_frames - 1
        return self.frame_in <= frame <= out

    def get_fade_opacity(self, frame: int, total_frames: int) -> float:
        out = self.frame_out if self.frame_out >= 0 else total_frames - 1
        fade = 1.0
        if self.fade_in > 0 and frame < self.frame_in + self.fade_in:
            fade = min(fade, (frame - self.frame_in) / self.fade_in)
        if self.fade_out > 0 and frame > out - self.fade_out:
            fade = min(fade, (out - frame) / self.fade_out)
        return max(0.0, min(1.0, fade))

    def get_interpolated(self, frame: int) -> TextKeyframe:
        if not self.keyframes:
            return TextKeyframe(frame)
        if len(self.keyframes) == 1:
            kf = self.keyframes[0].copy()
            kf.frame = frame
            return kf

        sorted_kfs = sorted(self.keyframes, key=lambda k: k.frame)
        if frame <= sorted_kfs[0].frame:
            kf = sorted_kfs[0].copy(); kf.frame = frame; return kf
        if frame >= sorted_kfs[-1].frame:
            kf = sorted_kfs[-1].copy(); kf.frame = frame; return kf

        for i in range(len(sorted_kfs) - 1):
            if sorted_kfs[i].frame <= frame <= sorted_kfs[i + 1].frame:
                k1, k2 = sorted_kfs[i], sorted_kfs[i + 1]
                span = k2.frame - k1.frame
                if span == 0:
                    return k1.copy()
                t = (frame - k1.frame) / span
                t = t * t * (3 - 2 * t)
                return self._lerp(k1, k2, t, frame)
        return sorted_kfs[-1].copy()

    def _lerp(self, k1, k2, t, frame):
        def mix(a, b): return a + (b - a) * t
        def mix_color(c1, c2):
            a, b = QColor(c1), QColor(c2)
            return QColor(int(mix(a.red(), b.red())), int(mix(a.green(), b.green())),
                          int(mix(a.blue(), b.blue()))).name()
        kf = TextKeyframe(frame=frame)
        kf.x = mix(k1.x, k2.x); kf.y = mix(k1.y, k2.y)
        kf.font_size = int(mix(k1.font_size, k2.font_size))
        kf.opacity = mix(k1.opacity, k2.opacity)
        kf.outline_width = int(mix(k1.outline_width, k2.outline_width))
        kf.rotation = mix(k1.rotation, k2.rotation)
        kf.color = mix_color(k1.color, k2.color)
        kf.outline_color = mix_color(k1.outline_color, k2.outline_color)
        return kf

    def get_keyframe_at(self, frame):
        for kf in self.keyframes:
            if kf.frame == frame:
                return kf
        return None

    def set_keyframe(self, kf):
        for i, ex in enumerate(self.keyframes):
            if ex.frame == kf.frame:
                self.keyframes[i] = kf; return
        self.keyframes.append(kf)

    def remove_keyframe(self, frame):
        self.keyframes = [k for k in self.keyframes if k.frame != frame]
        if not self.keyframes:
            self.keyframes = [TextKeyframe()]

    def hit_test(self, rx, ry, frame, scale_factor=1.0):
        kf = self.get_interpolated(frame)
        char_w = (kf.font_size * 0.6 * max(len(l) for l in self.text.split('\n'))) * scale_factor
        char_h = kf.font_size * 1.2 * len(self.text.split('\n')) * scale_factor
        dx, dy = abs(rx - kf.x), abs(ry - kf.y)
        if dx < char_w / 2 + 0.03 and dy < char_h / 2 + 0.03:
            return math.sqrt(dx * dx + dy * dy)
        return None

    def to_dict(self):
        return {
            "text": self.text, "font_family": self.font_family,
            "bold": self.bold, "italic": self.italic, "alignment": self.alignment,
            "visible": self.visible, "shadow": self.shadow, "uppercase": self.uppercase,
            "bg_box": self.bg_box, "frame_in": self.frame_in, "frame_out": self.frame_out,
            "fade_in": self.fade_in, "fade_out": self.fade_out,
            "keyframes": [kf.to_dict() for kf in self.keyframes],
        }

    @staticmethod
    def from_dict(d):
        layer = TextLayer.__new__(TextLayer)
        TextLayer._counter += 1
        layer.id = TextLayer._counter
        layer.text = d.get("text", "TEXT")
        layer.font_family = d.get("font_family", "Impact")
        layer.bold = d.get("bold", True)
        layer.italic = d.get("italic", False)
        layer.alignment = d.get("alignment", "center")
        layer.visible = d.get("visible", True)
        layer.shadow = d.get("shadow", False)
        layer.uppercase = d.get("uppercase", True)
        layer.bg_box = d.get("bg_box", False)
        layer.frame_in = d.get("frame_in", 0)
        layer.frame_out = d.get("frame_out", -1)
        layer.fade_in = d.get("fade_in", 0)
        layer.fade_out = d.get("fade_out", 0)
        layer.accent = LAYER_COLORS[(layer.id - 1) % len(LAYER_COLORS)]
        layer.keyframes = [TextKeyframe.from_dict(k) for k in d.get("keyframes", [{"frame": 0}])]
        return layer


# ============================================================================
#  Undo System
# ============================================================================

class UndoManager:
    def __init__(self, max_history=50):
        self._history: list[str] = []
        self._index = -1
        self._max = max_history

    def snapshot(self, layers: list[TextLayer]):
        state = json.dumps([l.to_dict() for l in layers])
        # Discard redo history
        self._history = self._history[:self._index + 1]
        self._history.append(state)
        if len(self._history) > self._max:
            self._history.pop(0)
        self._index = len(self._history) - 1

    def undo(self) -> list[TextLayer] | None:
        if self._index <= 0:
            return None
        self._index -= 1
        return self._restore()

    def redo(self) -> list[TextLayer] | None:
        if self._index >= len(self._history) - 1:
            return None
        self._index += 1
        return self._restore()

    def _restore(self) -> list[TextLayer]:
        data = json.loads(self._history[self._index])
        TextLayer._counter = 0
        return [TextLayer.from_dict(d) for d in data]

    @property
    def can_undo(self): return self._index > 0
    @property
    def can_redo(self): return self._index < len(self._history) - 1


# ============================================================================
#  Canvas
# ============================================================================

class GifCanvas(QWidget):
    text_moved = pyqtSignal(float, float)
    text_clicked = pyqtSignal(int)
    frame_step = pyqtSignal(int)
    canvas_clicked = pyqtSignal(float, float)
    resize_delta = pyqtSignal(float)  # drag-resize: delta in relative units
    zoom_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAcceptDrops(True)

        self._base_pixmap: QPixmap | None = None
        self._prev_pixmap: QPixmap | None = None  # onion skin
        self._layers: list[TextLayer] = []
        self._selected_id = -1
        self._current_frame = 0
        self._total_frames = 1
        self._gif_rect = QRectF()
        self._dragging = False
        self._resizing = False
        self._hovering_id = -1
        self._rendered = QPixmap()
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._panning = False
        self._pan_start = QPointF()
        self._pan_offset_start = (0.0, 0.0)
        self.onion_skin = False
        self.onion_opacity = 0.3

    def set_frame(self, pixmap, prev_pixmap, layers, frame, selected_id, total_frames):
        self._base_pixmap = pixmap
        self._prev_pixmap = prev_pixmap
        self._layers = layers
        self._current_frame = frame
        self._selected_id = selected_id
        self._total_frames = total_frames
        self._render()
        self.update()

    def paintEvent(self, event):
        if self._rendered.isNull():
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("#11111b"))
            p.setPen(QColor("#585b70"))
            p.setFont(QFont("Segoe UI", 14))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Load a GIF or drop one here")
            p.end()
            return
        p = QPainter(self)
        p.drawPixmap(0, 0, self._rendered)
        p.end()

    def _render(self):
        if not self._base_pixmap:
            return
        cw, ch = self.width(), self.height()
        pw, ph = self._base_pixmap.width(), self._base_pixmap.height()
        base_scale = min(cw / pw, ch / ph, 3.0)
        scale = base_scale * self._zoom
        sw, sh = int(pw * scale), int(ph * scale)
        ox = int((cw - sw) / 2 + self._pan_x)
        oy = int((ch - sh) / 2 + self._pan_y)
        self._gif_rect = QRectF(ox, oy, sw, sh)

        result = QPixmap(cw, ch)
        result.fill(QColor("#11111b"))
        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Checkerboard
        cs = 10
        clip_r = QRectF(max(0, ox), max(0, oy), min(sw, cw - max(0, ox)), min(sh, ch - max(0, oy)))
        for cy in range(int(clip_r.top()), int(clip_r.bottom()), cs):
            for cx in range(int(clip_r.left()), int(clip_r.right()), cs):
                g = ((cx - ox) // cs + (cy - oy) // cs) % 2
                p.fillRect(cx, cy, cs, cs, QColor("#2a2a3a") if g else QColor("#232336"))

        # Onion skin (previous frame)
        if self.onion_skin and self._prev_pixmap and self._current_frame > 0:
            p.setOpacity(self.onion_opacity)
            p.drawPixmap(ox, oy, sw, sh, self._prev_pixmap)
            p.setOpacity(1.0)
            # Tint overlay
            p.fillRect(QRectF(ox, oy, sw, sh), QColor(137, 180, 250, 30))

        # Current frame
        p.drawPixmap(ox, oy, sw, sh, self._base_pixmap)

        # Text layers
        for layer in self._layers:
            if not layer.is_visible_at(self._current_frame, self._total_frames):
                continue
            kf = layer.get_interpolated(self._current_frame)
            sel = layer.id == self._selected_id
            hov = layer.id == self._hovering_id
            fade = layer.get_fade_opacity(self._current_frame, self._total_frames)
            self._draw_text_layer(p, layer, kf, ox, oy, sw, sh, scale, sel, hov, fade)

        # Zoom indicator
        if self._zoom != 1.0:
            p.setPen(QColor("#585b70"))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(8, ch - 8, f"{self._zoom:.1f}x")

        p.end()
        self._rendered = result

    def _draw_text_layer(self, p, layer, kf, ox, oy, sw, sh, scale, selected, hover, fade_mult):
        text = layer.text.upper() if layer.uppercase else layer.text
        if not text:
            return

        font = QFont(layer.font_family, max(4, int(kf.font_size * scale)))
        font.setBold(layer.bold)
        font.setItalic(layer.italic)
        tx = ox + kf.x * sw
        ty = oy + kf.y * sh

        p.save()
        p.translate(tx, ty)
        if kf.rotation != 0:
            p.rotate(kf.rotation)

        effective_opacity = kf.opacity * fade_mult
        p.setOpacity(effective_opacity)

        fm = QFontMetrics(font)
        lines = text.split('\n')
        total_h = fm.height() * len(lines)
        y_start = -total_h / 2
        max_w = max(fm.horizontalAdvance(l) for l in lines) if lines else 0
        bbox = QRectF(-max_w / 2 - 8, y_start - 8, max_w + 16, total_h + 16)

        # Background box (subtitle style)
        if layer.bg_box:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, int(160 * effective_opacity)))
            p.drawRoundedRect(bbox, 4, 4)

        # Selection indicator
        if selected or hover:
            p.setOpacity(1.0)
            accent = QColor(layer.accent)
            if selected:
                pen = QPen(accent, 2, Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(bbox, 4, 4)
                # Resize handle (bottom-right)
                hr = QPointF(bbox.right(), bbox.bottom())
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(accent)
                p.drawEllipse(hr, 5, 5)
                # Other corners
                for cx, cy in [(bbox.left(), bbox.top()), (bbox.right(), bbox.top()),
                                (bbox.left(), bbox.bottom())]:
                    p.drawEllipse(QPointF(cx, cy), 3, 3)
            elif hover:
                p.setPen(QPen(accent, 1, Qt.PenStyle.DotLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(bbox, 4, 4)
            p.setOpacity(effective_opacity)

        # Layer tag
        p.setOpacity(min(1.0, effective_opacity + 0.3))
        tag_font = QFont("Segoe UI", max(7, int(9 * scale)))
        tag_font.setBold(True)
        p.setFont(tag_font)
        tag_text = f" {layer.text.split(chr(10))[0][:12]} "
        tag_fm = QFontMetrics(tag_font)
        tag_w = tag_fm.horizontalAdvance(tag_text) + 8
        tag_rect = QRectF(bbox.left(), bbox.top() - tag_fm.height() - 2, tag_w, tag_fm.height() + 2)
        p.setPen(Qt.PenStyle.NoPen)
        abg = QColor(layer.accent); abg.setAlpha(200)
        p.setBrush(abg)
        p.drawRoundedRect(tag_rect, 3, 3)
        p.setPen(QColor("#1e1e2e"))
        p.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)
        p.setOpacity(effective_opacity)

        # Text rendering
        p.setFont(font)
        for i, line in enumerate(lines):
            bw = fm.horizontalAdvance(line)
            if layer.alignment == "center":
                lx = -bw / 2
            elif layer.alignment == "left":
                lx = -max_w / 2
            else:
                lx = max_w / 2 - bw
            ly = y_start + fm.height() * (i + 1) - fm.descent()

            path = QPainterPath()
            path.addText(lx, ly, font, line)

            ow = int(kf.outline_width * scale)
            if ow > 0:
                p.setPen(QPen(QColor(kf.outline_color), ow,
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                              Qt.PenJoinStyle.RoundJoin))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(path)

            if layer.shadow:
                soff = max(2, int(2 * scale))
                sp = QPainterPath()
                sp.addText(lx + soff, ly + soff, font, line)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(0, 0, 0, 128))
                p.drawPath(sp)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(kf.color))
            p.drawPath(path)

        p.restore()

    # Mouse handling
    def _rel_pos(self, mx, my):
        if self._gif_rect.width() == 0:
            return None, None
        rx = (mx - self._gif_rect.x()) / self._gif_rect.width()
        ry = (my - self._gif_rect.y()) / self._gif_rect.height()
        return max(0, min(1, rx)), max(0, min(1, ry))

    def _find_layer_at(self, rx, ry):
        if rx is None:
            return None
        best, best_d = None, float('inf')
        sf = 1.0 / max(1, self._gif_rect.width())
        for layer in reversed(self._layers):
            if not layer.is_visible_at(self._current_frame, self._total_frames):
                continue
            d = layer.hit_test(rx, ry, self._current_frame, sf)
            if d is not None and d < best_d:
                best_d = d; best = layer
        return best

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self._pan_offset_start = (self._pan_x, self._pan_y)
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        rx, ry = self._rel_pos(event.pos().x(), event.pos().y())
        if rx is None:
            return
        hit = self._find_layer_at(rx, ry)
        if hit:
            self.text_clicked.emit(hit.id)
            self._dragging = True
        else:
            self._dragging = True
            self.canvas_clicked.emit(rx, ry)

    def mouseMoveEvent(self, event):
        if self._panning:
            dx = event.position().x() - self._pan_start.x()
            dy = event.position().y() - self._pan_start.y()
            self._pan_x = self._pan_offset_start[0] + dx
            self._pan_y = self._pan_offset_start[1] + dy
            self._render()
            self.update()
            return
        rx, ry = self._rel_pos(event.pos().x(), event.pos().y())
        if self._dragging and rx is not None:
            self.text_moved.emit(rx, ry)
        elif not self._dragging:
            hit = self._find_layer_at(rx, ry)
            new_hover = hit.id if hit else -1
            if new_hover != self._hovering_id:
                self._hovering_id = new_hover
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor if hit else Qt.CursorShape.ArrowCursor))
                self._render()
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        elif event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def wheelEvent(self, event):
        mods = event.modifiers()
        delta = event.angleDelta().y()
        if mods & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            factor = 1.15 if delta > 0 else 1 / 1.15
            self._zoom = max(0.25, min(8.0, self._zoom * factor))
            self._render()
            self.update()
        else:
            # Frame step
            self.frame_step.emit(-1 if delta > 0 else 1)

    def reset_view(self):
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._render()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._base_pixmap:
            self._render()
            self.update()

    # Drag & drop GIF
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.gif'):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.gif'):
                # Signal to parent
                self.window()._load_gif_from_path(path)
                break


# ============================================================================
#  Timeline with Layer Bars
# ============================================================================

class LayerTimeline(QWidget):
    frame_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(80)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.total_frames = 1
        self.current_frame = 0
        self.layers: list[TextLayer] = []
        self.selected_id = -1

    def paintEvent(self, event):
        if self.total_frames <= 1:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        denom = max(1, self.total_frames - 1)
        margin_l, margin_r = 6, 6
        track_w = w - margin_l - margin_r

        # Background
        p.fillRect(0, 0, w, h, QColor("#181825"))

        # Frame ticks
        p.setPen(QColor("#313244"))
        tick_interval = max(1, self.total_frames // 20)
        for i in range(0, self.total_frames, tick_interval):
            x = margin_l + int(i / denom * track_w)
            p.drawLine(x, 0, x, h)

        # Layer bars
        bar_h = min(16, max(8, (h - 20) // max(1, len(self.layers))))
        bar_y = 4
        for layer in self.layers:
            fi = layer.frame_in
            fo = layer.frame_out if layer.frame_out >= 0 else self.total_frames - 1
            x1 = margin_l + int(fi / denom * track_w)
            x2 = margin_l + int(fo / denom * track_w)

            # Bar background
            color = QColor(layer.accent)
            color.setAlpha(100 if layer.id != self.selected_id else 180)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(x1, bar_y, max(4, x2 - x1), bar_h, 3, 3)

            # Keyframe diamonds
            for kf in layer.keyframes:
                kx = margin_l + int(kf.frame / denom * track_w)
                if x1 <= kx <= x2:
                    p.setBrush(QColor("#f9e2af") if layer.id == self.selected_id else QColor(layer.accent))
                    p.setPen(QPen(QColor("#1e1e2e"), 1))
                    diamond = QPainterPath()
                    dy = bar_y + bar_h / 2
                    diamond.moveTo(kx, dy - 4)
                    diamond.lineTo(kx + 4, dy)
                    diamond.lineTo(kx, dy + 4)
                    diamond.lineTo(kx - 4, dy)
                    diamond.closeSubpath()
                    p.drawPath(diamond)

            # Label
            if bar_h >= 10:
                p.setPen(QColor("#1e1e2e"))
                p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                p.drawText(x1 + 4, bar_y + bar_h - 3, layer.text.split('\n')[0][:15])

            bar_y += bar_h + 2

        # Playhead
        cx = margin_l + int(self.current_frame / denom * track_w)
        p.setPen(QPen(QColor("#f38ba8"), 2))
        p.drawLine(cx, 0, cx, h)
        # Playhead triangle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#f38ba8"))
        tri = QPainterPath()
        tri.moveTo(cx - 5, 0)
        tri.lineTo(cx + 5, 0)
        tri.lineTo(cx, 6)
        tri.closeSubpath()
        p.drawPath(tri)

        p.end()

    def mousePressEvent(self, event):
        if self.total_frames <= 1:
            return
        margin_l = 6
        track_w = self.width() - 12
        denom = max(1, self.total_frames - 1)
        frame = int((event.pos().x() - margin_l) / max(1, track_w) * denom + 0.5)
        self.frame_clicked.emit(max(0, min(self.total_frames - 1, frame)))


# ============================================================================
#  Layer List Widget
# ============================================================================

class LayerWidget(QFrame):
    selected = pyqtSignal(int)
    deleted = pyqtSignal(int)
    duplicated = pyqtSignal(int)
    visibility_changed = pyqtSignal(int, bool)

    def __init__(self, layer, is_selected):
        super().__init__()
        self.layer = layer
        self.setFixedHeight(40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        bc = layer.accent if is_selected else "#45475a"
        bg = "#1e1e2e" if is_selected else "#313244"
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 2px solid {bc}; "
            f"border-radius: 6px; padding: 2px; }}"
        )
        lo = QHBoxLayout(self)
        lo.setContentsMargins(6, 2, 6, 2)
        lo.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {layer.accent}; border-radius: 5px; border: none;")
        lo.addWidget(dot)

        vis = QPushButton("V" if layer.visible else "-")
        vis.setFixedSize(24, 24)
        vis.setStyleSheet(
            f"background: {'#45475a' if layer.visible else '#1e1e2e'}; border-radius: 4px; "
            f"font-size: 10px; padding: 0; border: none; color: {'#cdd6f4' if layer.visible else '#585b70'};"
        )
        vis.clicked.connect(lambda: (
            setattr(layer, 'visible', not layer.visible),
            self.visibility_changed.emit(layer.id, layer.visible)
        ))
        lo.addWidget(vis)

        lbl = QLabel(layer.text.split('\n')[0][:16] or "---")
        lbl.setStyleSheet(f"color: #cdd6f4; font-weight: {'600' if is_selected else '400'}; border: none;")
        lo.addWidget(lbl, 1)

        dl = QPushButton("X")
        dl.setFixedSize(24, 24)
        dl.setStyleSheet("background: transparent; color: #f38ba8; font-weight: 700; border: none; font-size: 11px; padding: 0;")
        dl.clicked.connect(lambda: self.deleted.emit(layer.id))
        lo.addWidget(dl)

    def mousePressEvent(self, event):
        self.selected.emit(self.layer.id)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        dup = menu.addAction("Duplicate Layer")
        action = menu.exec(event.globalPos())
        if action == dup:
            self.duplicated.emit(self.layer.id)


# ============================================================================
#  Main Window
# ============================================================================

class GifTextApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"GifText v{VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 820)

        self.gif_frames: list[QPixmap] = []
        self.gif_pil_frames: list[Image.Image] = []
        self.frame_durations: list[int] = []
        self.current_frame = 0
        self.total_frames = 0
        self.gif_width = 0
        self.gif_height = 0
        self.gif_path = ""

        self.layers: list[TextLayer] = []
        self.selected_layer: TextLayer | None = None
        self.undo_mgr = UndoManager()

        self.playing = False
        self.play_speed = 1.0
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self._advance_frame)

        self._recent_files: list[str] = []
        self._load_recent()

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        # Left panel
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 6, 4, 0)
        ll.setSpacing(4)

        # Toolbar
        topbar = QHBoxLayout()
        topbar.setSpacing(6)

        self.btn_load = QPushButton("Load GIF")
        self.btn_load.setObjectName("accent")
        self.btn_load.setFixedHeight(32)
        self.btn_load.clicked.connect(self._load_gif)
        topbar.addWidget(self.btn_load)

        self.btn_export = QPushButton("Export GIF")
        self.btn_export.setObjectName("accent")
        self.btn_export.setFixedHeight(32)
        self.btn_export.clicked.connect(self._export_gif)
        self.btn_export.setEnabled(False)
        topbar.addWidget(self.btn_export)

        # Save/Load project
        self.btn_save_proj = QPushButton("Save Project")
        self.btn_save_proj.setFixedHeight(32)
        self.btn_save_proj.clicked.connect(self._save_project)
        self.btn_save_proj.setEnabled(False)
        topbar.addWidget(self.btn_save_proj)

        self.btn_load_proj = QPushButton("Load Project")
        self.btn_load_proj.setFixedHeight(32)
        self.btn_load_proj.clicked.connect(self._load_project)
        topbar.addWidget(self.btn_load_proj)

        topbar.addStretch()

        # Undo/Redo
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.setFixedHeight(32)
        self.btn_undo.clicked.connect(self._undo)
        self.btn_undo.setEnabled(False)
        topbar.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("Redo")
        self.btn_redo.setFixedHeight(32)
        self.btn_redo.clicked.connect(self._redo)
        self.btn_redo.setEnabled(False)
        topbar.addWidget(self.btn_redo)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        topbar.addWidget(self.info_label)
        ll.addLayout(topbar)

        # Canvas options row
        opts = QHBoxLayout()
        opts.setSpacing(8)

        self.chk_onion = QCheckBox("Onion Skin")
        self.chk_onion.toggled.connect(self._toggle_onion)
        opts.addWidget(self.chk_onion)

        btn_reset_view = QPushButton("Reset View")
        btn_reset_view.setFixedHeight(24)
        btn_reset_view.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        btn_reset_view.clicked.connect(lambda: self.canvas.reset_view())
        opts.addWidget(btn_reset_view)

        opts.addStretch()

        opts.addWidget(QLabel("Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentIndex(2)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self.speed_combo.setFixedWidth(70)
        opts.addWidget(self.speed_combo)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #585b70; font-size: 11px; font-style: italic;")
        opts.addWidget(self.hint_label)
        ll.addLayout(opts)

        # Canvas
        self.canvas = GifCanvas()
        self.canvas.text_moved.connect(self._on_text_moved)
        self.canvas.text_clicked.connect(self._select_layer)
        self.canvas.frame_step.connect(self._step_frame)
        self.canvas.canvas_clicked.connect(self._on_canvas_click)
        ll.addWidget(self.canvas, 1)

        # Timeline
        timeline = QFrame()
        timeline.setObjectName("timeline")
        tl = QVBoxLayout(timeline)
        tl.setContentsMargins(8, 4, 8, 6)
        tl.setSpacing(3)

        self.layer_timeline = LayerTimeline()
        self.layer_timeline.frame_clicked.connect(self._set_frame)
        tl.addWidget(self.layer_timeline)

        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.btn_play = QPushButton("Play")
        self.btn_play.setFixedSize(68, 28)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_play.setEnabled(False)
        controls.addWidget(self.btn_play)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(32, 28)
        self.btn_prev.clicked.connect(lambda: self._step_frame(-1))
        self.btn_prev.setEnabled(False)
        controls.addWidget(self.btn_prev)

        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self._set_frame)
        controls.addWidget(self.frame_slider, 1)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(32, 28)
        self.btn_next.clicked.connect(lambda: self._step_frame(1))
        self.btn_next.setEnabled(False)
        controls.addWidget(self.btn_next)

        self.frame_label = QLabel("0 / 0")
        self.frame_label.setObjectName("frameLabel")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls.addWidget(self.frame_label)

        tl.addLayout(controls)
        ll.addWidget(timeline)
        splitter.addWidget(left)

        # Right panel
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_inner = QWidget()
        rl = QVBoxLayout(right_inner)
        rl.setContentsMargins(4, 6, 8, 8)
        rl.setSpacing(4)
        right_inner.setFixedWidth(310)

        # Layers
        lg = QGroupBox("Text Layers")
        ll2 = QVBoxLayout(lg)
        ll2.setSpacing(3)
        self.btn_add = QPushButton("+ Add Text Layer")
        self.btn_add.setObjectName("accent")
        self.btn_add.clicked.connect(self._add_layer)
        self.btn_add.setEnabled(False)
        ll2.addWidget(self.btn_add)
        self.layers_list = QVBoxLayout()
        self.layers_list.setSpacing(2)
        ll2.addLayout(self.layers_list)
        rl.addWidget(lg)

        # Presets
        pg = QGroupBox("Quick Presets")
        pl = QHBoxLayout(pg)
        pl.setSpacing(4)
        for name in MEME_PRESETS:
            btn = QPushButton(name)
            btn.setObjectName("preset")
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            pl.addWidget(btn)
        rl.addWidget(pg)

        # Text Properties
        tg = QGroupBox("Text")
        tgl = QGridLayout(tg)
        tgl.setVerticalSpacing(4)
        tgl.setHorizontalSpacing(6)
        r = 0

        tgl.addWidget(QLabel("Text:"), r, 0, Qt.AlignmentFlag.AlignTop)
        self.txt_input = QPlainTextEdit()
        self.txt_input.setPlaceholderText("Type meme text...\n(supports multiple lines)")
        self.txt_input.setMaximumHeight(60)
        self.txt_input.setTabChangesFocus(True)
        self.txt_input.textChanged.connect(self._on_text_changed)
        tgl.addWidget(self.txt_input, r, 1, 1, 2)
        r += 1

        tgl.addWidget(QLabel("Font:"), r, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Impact"))
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        tgl.addWidget(self.font_combo, r, 1, 1, 2)
        r += 1

        style_row = QHBoxLayout()
        self.chk_bold = QCheckBox("Bold")
        self.chk_bold.setChecked(True)
        self.chk_bold.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_bold)
        self.chk_italic = QCheckBox("Italic")
        self.chk_italic.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_italic)
        self.chk_upper = QCheckBox("CAPS")
        self.chk_upper.setChecked(True)
        self.chk_upper.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_upper)
        self.chk_shadow = QCheckBox("Shadow")
        self.chk_shadow.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_shadow)
        self.chk_bgbox = QCheckBox("BG Box")
        self.chk_bgbox.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_bgbox)
        tgl.addLayout(style_row, r, 0, 1, 3)
        r += 1

        tgl.addWidget(QLabel("Align:"), r, 0)
        self.align_combo = QComboBox()
        self.align_combo.addItems(["center", "left", "right"])
        self.align_combo.currentTextChanged.connect(self._on_align_changed)
        tgl.addWidget(self.align_combo, r, 1, 1, 2)
        rl.addWidget(tg)

        # Animation
        ag = QGroupBox("Animation")
        agl = QGridLayout(ag)
        agl.setVerticalSpacing(4)
        agl.setHorizontalSpacing(6)
        ar = 0

        agl.addWidget(QLabel("Size:"), ar, 0)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 200)
        self.spin_size.setValue(48)
        self.spin_size.valueChanged.connect(self._on_anim_prop_changed)
        agl.addWidget(self.spin_size, ar, 1, 1, 2)
        ar += 1

        agl.addWidget(QLabel("Opacity:"), ar, 0)
        self.spin_opacity = QDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setSingleStep(0.05)
        self.spin_opacity.setValue(1.0)
        self.spin_opacity.valueChanged.connect(self._on_anim_prop_changed)
        agl.addWidget(self.spin_opacity, ar, 1, 1, 2)
        ar += 1

        agl.addWidget(QLabel("Rotation:"), ar, 0)
        self.spin_rotation = QDoubleSpinBox()
        self.spin_rotation.setRange(-360, 360)
        self.spin_rotation.setSingleStep(5)
        self.spin_rotation.valueChanged.connect(self._on_anim_prop_changed)
        agl.addWidget(self.spin_rotation, ar, 1, 1, 2)
        ar += 1

        agl.addWidget(QLabel("Outline:"), ar, 0)
        self.spin_outline = QSpinBox()
        self.spin_outline.setRange(0, 20)
        self.spin_outline.setValue(3)
        self.spin_outline.valueChanged.connect(self._on_anim_prop_changed)
        agl.addWidget(self.spin_outline, ar, 1, 1, 2)
        ar += 1

        color_row = QHBoxLayout()
        self.btn_color = QPushButton("Text Color")
        self.btn_color.setFixedHeight(28)
        self.btn_color.clicked.connect(lambda: self._pick_color("text"))
        self.btn_color.setStyleSheet("background: #ffffff; color: #000; border-radius: 4px; font-weight: 600;")
        color_row.addWidget(self.btn_color)
        self.btn_outline_color = QPushButton("Outline")
        self.btn_outline_color.setFixedHeight(28)
        self.btn_outline_color.clicked.connect(lambda: self._pick_color("outline"))
        self.btn_outline_color.setStyleSheet("background: #000000; color: #fff; border-radius: 4px; font-weight: 600;")
        color_row.addWidget(self.btn_outline_color)
        agl.addLayout(color_row, ar, 0, 1, 3)
        ar += 1

        self.pos_label = QLabel("Drag text on canvas to position")
        self.pos_label.setStyleSheet("color: #585b70; font-size: 11px;")
        agl.addWidget(self.pos_label, ar, 0, 1, 3)
        ar += 1

        kf_row = QHBoxLayout()
        self.btn_set_kf = QPushButton("Set Keyframe")
        self.btn_set_kf.setObjectName("keyframeSet")
        self.btn_set_kf.setFixedHeight(30)
        self.btn_set_kf.clicked.connect(self._set_keyframe)
        kf_row.addWidget(self.btn_set_kf)
        self.btn_del_kf = QPushButton("Delete KF")
        self.btn_del_kf.setObjectName("keyframeDel")
        self.btn_del_kf.setFixedHeight(30)
        self.btn_del_kf.clicked.connect(self._delete_keyframe)
        kf_row.addWidget(self.btn_del_kf)
        self.btn_copy_kf = QPushButton("Copy KF...")
        self.btn_copy_kf.setFixedHeight(30)
        self.btn_copy_kf.clicked.connect(self._copy_keyframe_range)
        kf_row.addWidget(self.btn_copy_kf)
        agl.addLayout(kf_row, ar, 0, 1, 3)
        ar += 1

        self.kf_info = QLabel("")
        self.kf_info.setStyleSheet("color: #f9e2af; font-size: 11px;")
        self.kf_info.setWordWrap(True)
        agl.addWidget(self.kf_info, ar, 0, 1, 3)
        rl.addWidget(ag)

        # Timing
        tmg = QGroupBox("Layer Timing")
        tmgl = QGridLayout(tmg)
        tmgl.setVerticalSpacing(4)
        tr = 0

        tmgl.addWidget(QLabel("Start Frame:"), tr, 0)
        self.spin_frame_in = QSpinBox()
        self.spin_frame_in.setRange(0, 9999)
        self.spin_frame_in.valueChanged.connect(self._on_timing_changed)
        tmgl.addWidget(self.spin_frame_in, tr, 1)
        tr += 1

        tmgl.addWidget(QLabel("End Frame:"), tr, 0)
        self.spin_frame_out = QSpinBox()
        self.spin_frame_out.setRange(-1, 9999)
        self.spin_frame_out.setSpecialValueText("Last")
        self.spin_frame_out.setValue(-1)
        self.spin_frame_out.valueChanged.connect(self._on_timing_changed)
        tmgl.addWidget(self.spin_frame_out, tr, 1)
        tr += 1

        tmgl.addWidget(QLabel("Fade In:"), tr, 0)
        self.spin_fade_in = QSpinBox()
        self.spin_fade_in.setRange(0, 100)
        self.spin_fade_in.setSuffix(" frames")
        self.spin_fade_in.valueChanged.connect(self._on_timing_changed)
        tmgl.addWidget(self.spin_fade_in, tr, 1)
        tr += 1

        tmgl.addWidget(QLabel("Fade Out:"), tr, 0)
        self.spin_fade_out = QSpinBox()
        self.spin_fade_out.setRange(0, 100)
        self.spin_fade_out.setSuffix(" frames")
        self.spin_fade_out.valueChanged.connect(self._on_timing_changed)
        tmgl.addWidget(self.spin_fade_out, tr, 1)
        rl.addWidget(tmg)

        rl.addStretch()
        right_scroll.setWidget(right_inner)
        splitter.addWidget(right_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([900, 310])

        self.statusBar().showMessage(f"GifText v{VERSION} - Load a GIF to get started")

    # ================================================================
    #  GIF Loading
    # ================================================================

    def _load_gif(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Animated GIF", "", "GIF Files (*.gif);;All Files (*)"
        )
        if path:
            self._load_gif_from_path(path)

    def _load_gif_from_path(self, path):
        try:
            img = Image.open(path)
            if not hasattr(img, 'n_frames') or img.n_frames < 2:
                self.statusBar().showMessage("Not animated (needs 2+ frames)")
                return

            self.gif_frames.clear()
            self.gif_pil_frames.clear()
            self.frame_durations.clear()
            self.gif_width = img.width
            self.gif_height = img.height
            self.gif_path = path

            for i in range(img.n_frames):
                img.seek(i)
                frame = img.convert("RGBA")
                self.gif_pil_frames.append(frame.copy())
                self.frame_durations.append(max(img.info.get('duration', 100), 20))
                data = frame.tobytes("raw", "RGBA")
                qimg = QImage(data, frame.width, frame.height, QImage.Format.Format_RGBA8888)
                self.gif_frames.append(QPixmap.fromImage(qimg.copy()))

            self.total_frames = len(self.gif_frames)
            self.current_frame = 0
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.frame_slider.setValue(0)
            self.btn_play.setEnabled(True)
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(True)
            self.btn_add.setEnabled(True)
            self.btn_export.setEnabled(True)
            self.btn_save_proj.setEnabled(True)
            self.layer_timeline.total_frames = self.total_frames
            self.info_label.setText(f"{self.gif_width}x{self.gif_height} | {self.total_frames}f | {os.path.basename(path)}")
            self.hint_label.setText("Add text layers, drag to position, mousewheel = step frames, Ctrl+wheel = zoom")

            self._add_recent(path)
            self._snapshot()
            self._update_all()
            self.statusBar().showMessage(f"Loaded {os.path.basename(path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Error: {e}")

    # ================================================================
    #  Playback
    # ================================================================

    def _toggle_play(self):
        if self.playing:
            self.playing = False
            self.play_timer.stop()
            self.btn_play.setText("Play")
        else:
            self.playing = True
            self.btn_play.setText("Pause")
            self._advance_frame()

    def _advance_frame(self):
        if not self.playing or not self.gif_frames:
            return
        nxt = (self.current_frame + 1) % self.total_frames
        self.frame_slider.setValue(nxt)
        delay = int(self.frame_durations[self.current_frame] / self.play_speed)
        self.play_timer.start(max(10, delay))

    def _step_frame(self, delta):
        if self.gif_frames:
            self._set_frame(self.current_frame + delta)

    def _set_frame(self, frame):
        if not self.gif_frames:
            return
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(self.current_frame)
        self.frame_slider.blockSignals(False)
        self.frame_label.setText(f"{self.current_frame + 1} / {self.total_frames}")
        self._update_all()

    def _on_speed_changed(self, text):
        self.play_speed = float(text.replace('x', ''))

    def _update_all(self):
        if not self.gif_frames:
            return
        sel_id = self.selected_layer.id if self.selected_layer else -1
        prev_pm = self.gif_frames[self.current_frame - 1] if self.current_frame > 0 else None
        self.canvas.set_frame(
            self.gif_frames[self.current_frame], prev_pm,
            self.layers, self.current_frame, sel_id, self.total_frames
        )
        self.layer_timeline.layers = self.layers
        self.layer_timeline.current_frame = self.current_frame
        self.layer_timeline.selected_id = sel_id
        self.layer_timeline.total_frames = self.total_frames
        self.layer_timeline.update()
        self._sync_props_from_layer()
        self._update_undo_btns()

    # ================================================================
    #  Layers
    # ================================================================

    def _add_layer(self):
        layer = TextLayer(f"Name {len(self.layers) + 1}")
        layer.keyframes = [TextKeyframe(frame=0, x=0.3 + 0.2 * (len(self.layers) % 3), y=0.3)]
        layer.frame_out = -1
        self.layers.append(layer)
        self.selected_layer = layer
        self._snapshot()
        self._rebuild_layer_list()
        self._update_all()
        self.txt_input.setFocus()
        self.txt_input.selectAll()
        self.statusBar().showMessage("Added layer - type a name and drag into position")

    def _duplicate_layer(self, layer_id):
        src = next((l for l in self.layers if l.id == layer_id), None)
        if not src:
            return
        layer = TextLayer(src.text + " copy")
        layer.font_family = src.font_family
        layer.bold = src.bold
        layer.italic = src.italic
        layer.alignment = src.alignment
        layer.shadow = src.shadow
        layer.uppercase = src.uppercase
        layer.bg_box = src.bg_box
        layer.frame_in = src.frame_in
        layer.frame_out = src.frame_out
        layer.fade_in = src.fade_in
        layer.fade_out = src.fade_out
        layer.keyframes = [kf.copy() for kf in src.keyframes]
        # Offset position slightly
        for kf in layer.keyframes:
            kf.x = min(1.0, kf.x + 0.05)
            kf.y = min(1.0, kf.y + 0.05)
        self.layers.append(layer)
        self.selected_layer = layer
        self._snapshot()
        self._rebuild_layer_list()
        self._update_all()

    def _rebuild_layer_list(self):
        while self.layers_list.count():
            item = self.layers_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for layer in self.layers:
            sel = self.selected_layer and self.selected_layer.id == layer.id
            w = LayerWidget(layer, sel)
            w.selected.connect(self._select_layer)
            w.deleted.connect(self._delete_layer)
            w.duplicated.connect(self._duplicate_layer)
            w.visibility_changed.connect(lambda *_: self._update_all())
            self.layers_list.addWidget(w)

    def _select_layer(self, layer_id):
        self.selected_layer = next((l for l in self.layers if l.id == layer_id), None)
        self._rebuild_layer_list()
        self._update_all()

    def _delete_layer(self, layer_id):
        self.layers = [l for l in self.layers if l.id != layer_id]
        if self.selected_layer and self.selected_layer.id == layer_id:
            self.selected_layer = self.layers[-1] if self.layers else None
        self._snapshot()
        self._rebuild_layer_list()
        self._update_all()

    # ================================================================
    #  Canvas Interaction
    # ================================================================

    def _on_text_moved(self, rx, ry):
        if not self.selected_layer:
            return
        layer = self.selected_layer
        kf = layer.get_keyframe_at(self.current_frame)
        if kf is None:
            kf = layer.get_interpolated(self.current_frame)
            kf.frame = self.current_frame
            layer.set_keyframe(kf)
        kf.x = rx
        kf.y = ry
        self._update_all()

    def _on_canvas_click(self, rx, ry):
        if self.selected_layer:
            self._on_text_moved(rx, ry)

    def _toggle_onion(self, checked):
        self.canvas.onion_skin = checked
        self._update_all()

    # ================================================================
    #  Properties Sync
    # ================================================================

    def _sync_props_from_layer(self):
        layer = self.selected_layer
        if not layer:
            self.kf_info.setText("")
            self.pos_label.setText("No layer selected")
            return

        self._block(True)
        if self.txt_input.toPlainText() != layer.text:
            self.txt_input.setPlainText(layer.text)
        self.font_combo.setCurrentFont(QFont(layer.font_family))
        self.chk_bold.setChecked(layer.bold)
        self.chk_italic.setChecked(layer.italic)
        self.chk_upper.setChecked(layer.uppercase)
        self.chk_shadow.setChecked(layer.shadow)
        self.chk_bgbox.setChecked(layer.bg_box)
        self.align_combo.setCurrentText(layer.alignment)

        kf = layer.get_interpolated(self.current_frame)
        self.spin_size.setValue(kf.font_size)
        self.spin_opacity.setValue(kf.opacity)
        self.spin_rotation.setValue(kf.rotation)
        self.spin_outline.setValue(kf.outline_width)

        self.btn_color.setStyleSheet(
            f"background: {kf.color}; color: {'#000' if QColor(kf.color).lightness() > 128 else '#fff'}; "
            f"border-radius: 4px; font-weight: 600;"
        )
        self.btn_outline_color.setStyleSheet(
            f"background: {kf.outline_color}; color: {'#000' if QColor(kf.outline_color).lightness() > 128 else '#fff'}; "
            f"border-radius: 4px; font-weight: 600;"
        )
        self.pos_label.setText(f"Position: ({kf.x:.2f}, {kf.y:.2f})")

        existing = layer.get_keyframe_at(self.current_frame)
        kf_frames = sorted(k.frame + 1 for k in layer.keyframes)
        marker = "[KEYFRAME]" if existing else "[interpolated]"
        self.kf_info.setText(f"{marker}  KFs: {', '.join(map(str, kf_frames))}")

        self.spin_frame_in.setValue(layer.frame_in)
        self.spin_frame_out.setValue(layer.frame_out)
        self.spin_fade_in.setValue(layer.fade_in)
        self.spin_fade_out.setValue(layer.fade_out)

        self._block(False)

    def _block(self, b):
        for w in [self.txt_input, self.spin_size, self.spin_opacity,
                  self.spin_rotation, self.spin_outline, self.font_combo,
                  self.chk_bold, self.chk_italic, self.chk_upper, self.chk_shadow,
                  self.chk_bgbox, self.align_combo, self.spin_frame_in,
                  self.spin_frame_out, self.spin_fade_in, self.spin_fade_out]:
            w.blockSignals(b)

    def _on_text_changed(self):
        if not self.selected_layer:
            return
        self.selected_layer.text = self.txt_input.toPlainText()
        self._rebuild_layer_list()
        self._update_all()

    def _on_font_changed(self, font):
        if self.selected_layer:
            self.selected_layer.font_family = font.family()
            self._update_all()

    def _on_style_changed(self):
        if not self.selected_layer:
            return
        self.selected_layer.bold = self.chk_bold.isChecked()
        self.selected_layer.italic = self.chk_italic.isChecked()
        self.selected_layer.uppercase = self.chk_upper.isChecked()
        self.selected_layer.shadow = self.chk_shadow.isChecked()
        self.selected_layer.bg_box = self.chk_bgbox.isChecked()
        self._update_all()

    def _on_align_changed(self, a):
        if self.selected_layer:
            self.selected_layer.alignment = a
            self._update_all()

    def _on_anim_prop_changed(self):
        self._update_all()

    def _on_timing_changed(self):
        if not self.selected_layer:
            return
        self.selected_layer.frame_in = self.spin_frame_in.value()
        self.selected_layer.frame_out = self.spin_frame_out.value()
        self.selected_layer.fade_in = self.spin_fade_in.value()
        self.selected_layer.fade_out = self.spin_fade_out.value()
        self._update_all()

    def _pick_color(self, target):
        if not self.selected_layer:
            return
        kf = self.selected_layer.get_interpolated(self.current_frame)
        initial = QColor(kf.color if target == "text" else kf.outline_color)
        color = QColorDialog.getColor(initial, self, f"Pick {target} color")
        if not color.isValid():
            return
        layer = self.selected_layer
        existing = layer.get_keyframe_at(self.current_frame)
        if existing is None:
            existing = layer.get_interpolated(self.current_frame)
            existing.frame = self.current_frame
            layer.set_keyframe(existing)
        if target == "text":
            existing.color = color.name()
        else:
            existing.outline_color = color.name()
        self._snapshot()
        self._update_all()

    def _apply_preset(self, name):
        if not self.selected_layer:
            return
        p = MEME_PRESETS[name]
        layer = self.selected_layer
        layer.font_family = p["font"]
        layer.bold = p["bold"]
        layer.uppercase = p["upper"]
        layer.shadow = p["shadow"]
        layer.bg_box = p["bg_box"]
        # Apply to current keyframe
        kf = layer.get_keyframe_at(self.current_frame)
        if kf is None:
            kf = layer.get_interpolated(self.current_frame)
            kf.frame = self.current_frame
            layer.set_keyframe(kf)
        kf.font_size = p["size"]
        kf.color = p["color"]
        kf.outline_color = p["outline_color"]
        kf.outline_width = p["outline_width"]
        self._snapshot()
        self._update_all()
        self.statusBar().showMessage(f"Applied preset: {name}")

    # ================================================================
    #  Keyframes
    # ================================================================

    def _set_keyframe(self):
        if not self.selected_layer:
            return
        layer = self.selected_layer
        kf = layer.get_keyframe_at(self.current_frame)
        if kf is None:
            kf = layer.get_interpolated(self.current_frame)
            kf.frame = self.current_frame
        kf.font_size = self.spin_size.value()
        kf.opacity = self.spin_opacity.value()
        kf.rotation = self.spin_rotation.value()
        kf.outline_width = self.spin_outline.value()
        layer.set_keyframe(kf)
        self._snapshot()
        self._update_all()
        self.statusBar().showMessage(f"Keyframe set at frame {self.current_frame + 1}")

    def _delete_keyframe(self):
        if not self.selected_layer:
            return
        if self.selected_layer.get_keyframe_at(self.current_frame):
            self.selected_layer.remove_keyframe(self.current_frame)
            self._snapshot()
            self._update_all()
            self.statusBar().showMessage(f"Keyframe deleted at frame {self.current_frame + 1}")

    def _copy_keyframe_range(self):
        if not self.selected_layer:
            return
        layer = self.selected_layer
        kf = layer.get_keyframe_at(self.current_frame)
        if not kf:
            kf = layer.get_interpolated(self.current_frame)

        # Copy to next 10 frames (or remaining)
        count = 0
        for f in range(self.current_frame, min(self.current_frame + 10, self.total_frames)):
            new_kf = kf.copy()
            new_kf.frame = f
            layer.set_keyframe(new_kf)
            count += 1

        self._snapshot()
        self._update_all()
        self.statusBar().showMessage(
            f"Copied keyframe to {count} frames ({self.current_frame + 1}-{min(self.current_frame + 10, self.total_frames)})"
        )

    # ================================================================
    #  Undo / Redo
    # ================================================================

    def _snapshot(self):
        self.undo_mgr.snapshot(self.layers)
        self._update_undo_btns()

    def _undo(self):
        result = self.undo_mgr.undo()
        if result is not None:
            self.layers = result
            self.selected_layer = self.layers[-1] if self.layers else None
            self._rebuild_layer_list()
            self._update_all()
            self.statusBar().showMessage("Undo")

    def _redo(self):
        result = self.undo_mgr.redo()
        if result is not None:
            self.layers = result
            self.selected_layer = self.layers[-1] if self.layers else None
            self._rebuild_layer_list()
            self._update_all()
            self.statusBar().showMessage("Redo")

    def _update_undo_btns(self):
        self.btn_undo.setEnabled(self.undo_mgr.can_undo)
        self.btn_redo.setEnabled(self.undo_mgr.can_redo)

    def keyPressEvent(self, event):
        # Ctrl+Z / Ctrl+Y
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._redo()
                else:
                    self._undo()
                return
            elif event.key() == Qt.Key.Key_Y:
                self._redo()
                return
            elif event.key() == Qt.Key.Key_S:
                self._save_project()
                return
        super().keyPressEvent(event)

    # ================================================================
    #  Project Save / Load
    # ================================================================

    def _save_project(self):
        if not self.gif_path:
            return
        default = os.path.splitext(self.gif_path)[0] + ".giftext"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", default, "GifText Project (*.giftext)"
        )
        if not path:
            return
        project = {
            "version": VERSION,
            "gif_path": self.gif_path,
            "layers": [l.to_dict() for l in self.layers],
        }
        with open(path, 'w') as f:
            json.dump(project, f, indent=2)
        self.statusBar().showMessage(f"Project saved: {os.path.basename(path)}")

    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "GifText Project (*.giftext);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path) as f:
                project = json.load(f)
            gif_path = project.get("gif_path", "")
            if not os.path.exists(gif_path):
                # Try relative to project file
                alt = os.path.join(os.path.dirname(path), os.path.basename(gif_path))
                if os.path.exists(alt):
                    gif_path = alt
                else:
                    self.statusBar().showMessage(f"GIF not found: {gif_path}")
                    return

            self._load_gif_from_path(gif_path)
            TextLayer._counter = 0
            self.layers = [TextLayer.from_dict(d) for d in project.get("layers", [])]
            self.selected_layer = self.layers[0] if self.layers else None
            self._snapshot()
            self._rebuild_layer_list()
            self._update_all()
            self.statusBar().showMessage(f"Project loaded: {os.path.basename(path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Error loading project: {e}")

    # ================================================================
    #  Recent Files
    # ================================================================

    def _recent_path(self):
        return os.path.join(os.path.expanduser("~"), ".giftext_recent.json")

    def _load_recent(self):
        try:
            with open(self._recent_path()) as f:
                self._recent_files = json.load(f)[:10]
        except Exception:
            self._recent_files = []

    def _add_recent(self, path):
        path = os.path.abspath(path)
        self._recent_files = [p for p in self._recent_files if p != path]
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:10]
        try:
            with open(self._recent_path(), 'w') as f:
                json.dump(self._recent_files, f)
        except Exception:
            pass

    # ================================================================
    #  Export
    # ================================================================

    def _export_gif(self):
        if not self.gif_pil_frames:
            return

        default_name = os.path.splitext(os.path.basename(self.gif_path))[0] + "_meme.gif"
        default_dir = os.path.dirname(self.gif_path)
        path, filt = QFileDialog.getSaveFileName(
            self, "Export", os.path.join(default_dir, default_name),
            "GIF (*.gif);;WebP (*.webp);;PNG Sequence (*.png)"
        )
        if not path:
            return

        self.statusBar().showMessage("Exporting...")
        QApplication.processEvents()

        try:
            rendered = []
            for i, pil_frame in enumerate(self.gif_pil_frames):
                frame = pil_frame.copy()
                for layer in self.layers:
                    if not layer.is_visible_at(i, self.total_frames):
                        continue
                    frame = self._render_text_pil(frame, layer, i)
                rendered.append(frame)

            ext = os.path.splitext(path)[1].lower()

            if ext == '.webp':
                rgb_frames = [f.convert("RGBA") for f in rendered]
                rgb_frames[0].save(
                    path, save_all=True, append_images=rgb_frames[1:],
                    duration=self.frame_durations, loop=0, lossless=False, quality=85
                )
            elif ext == '.png':
                # PNG sequence
                base = os.path.splitext(path)[0]
                for i, frame in enumerate(rendered):
                    frame.save(f"{base}_{i:04d}.png")
            else:
                rgb_frames = [f.convert("RGB") for f in rendered]
                rgb_frames[0].save(
                    path, save_all=True, append_images=rgb_frames[1:],
                    duration=self.frame_durations, loop=0, optimize=False
                )

            self.statusBar().showMessage(f"Exported: {os.path.basename(path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Export error: {e}")

    def _render_text_pil(self, frame, layer, frame_idx):
        kf = layer.get_interpolated(frame_idx)
        text = layer.text.upper() if layer.uppercase else layer.text
        if not text:
            return frame

        fade = layer.get_fade_opacity(frame_idx, self.total_frames)
        effective_alpha = int(kf.opacity * fade * 255)
        if effective_alpha <= 0:
            return frame

        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = self._get_pil_font(layer, kf.font_size)

        lines = text.split('\n')
        line_sizes = []
        total_h = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            line_sizes.append((lw, lh))
            total_h += lh

        cx = kf.x * frame.width
        cy = kf.y * frame.height
        y_cursor = cy - total_h / 2

        text_rgb = tuple(int(kf.color[i:i+2], 16) for i in (1, 3, 5))
        outline_rgb = tuple(int(kf.outline_color[i:i+2], 16) for i in (1, 3, 5))

        # Background box
        if layer.bg_box:
            max_lw = max(s[0] for s in line_sizes)
            box_rect = [cx - max_lw / 2 - 8, cy - total_h / 2 - 8,
                        cx + max_lw / 2 + 8, cy + total_h / 2 + 8]
            draw.rounded_rectangle(box_rect, radius=4,
                                   fill=(0, 0, 0, int(160 * kf.opacity * fade)))

        for i, line in enumerate(lines):
            lw, lh = line_sizes[i]
            max_w = max(s[0] for s in line_sizes)
            if layer.alignment == "center":
                lx = cx - lw / 2
            elif layer.alignment == "left":
                lx = cx - max_w / 2
            else:
                lx = cx + max_w / 2 - lw

            if kf.outline_width > 0:
                try:
                    draw.text((lx, y_cursor), line, font=font,
                              fill=(*outline_rgb, effective_alpha),
                              stroke_width=kf.outline_width,
                              stroke_fill=(*outline_rgb, effective_alpha))
                except TypeError:
                    ow = kf.outline_width
                    for dx in range(-ow, ow + 1):
                        for dy in range(-ow, ow + 1):
                            if dx * dx + dy * dy <= ow * ow:
                                draw.text((lx + dx, y_cursor + dy), line, font=font,
                                          fill=(*outline_rgb, effective_alpha))

            if layer.shadow:
                draw.text((lx + 2, y_cursor + 2), line, font=font,
                          fill=(0, 0, 0, effective_alpha // 2))

            draw.text((lx, y_cursor), line, font=font, fill=(*text_rgb, effective_alpha))
            y_cursor += lh

        if kf.rotation != 0:
            overlay = overlay.rotate(-kf.rotation, center=(cx, cy),
                                     resample=Image.Resampling.BICUBIC, expand=False)

        return Image.alpha_composite(frame, overlay)

    def _get_pil_font(self, layer, size):
        family = layer.font_family.lower().replace(' ', '')
        candidates = []
        if layer.bold and layer.italic:
            candidates += [f"{family}bi.ttf", f"{family}z.ttf"]
        if layer.bold:
            candidates += [f"{family}bd.ttf", f"{family}b.ttf"]
        if layer.italic:
            candidates.append(f"{family}i.ttf")
        candidates.append(f"{family}.ttf")
        candidates += ["impact.ttf", "arialbd.ttf", "arial.ttf"]
        for name in candidates:
            try:
                return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
            except Exception:
                continue
        return ImageFont.load_default()


# ============================================================================
#  Entry
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)
    window = GifTextApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
