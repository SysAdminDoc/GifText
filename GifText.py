"""
GifText v0.2.0 - Animated GIF Text Editor
Add smooth animated text to GIFs for meme creation.
Click-to-select text on canvas, drag to reposition, mousewheel to step frames.
"""

import sys
import os
import math
import copy

def _bootstrap():
    """Auto-install dependencies before imports."""
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
    QColorDialog, QFileDialog, QFrame, QSplitter, QCheckBox, QLineEdit,
    QFontComboBox, QGroupBox, QGridLayout, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPainter, QFont, QPen, QBrush,
    QFontMetrics, QPainterPath, QCursor, QWheelEvent
)
from PIL import Image, ImageDraw, ImageFont
import io

VERSION = "0.2.0"

# Layer accent colors for identification
LAYER_COLORS = [
    "#89b4fa", "#a6e3a1", "#f9e2af", "#f38ba8", "#cba6f7",
    "#fab387", "#94e2d5", "#f5c2e7", "#74c7ec", "#b4befe",
]

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QToolBar {
    background-color: #181825;
    border: none;
    padding: 4px;
    spacing: 6px;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
    border-color: #313244;
}
QPushButton#accent {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: 600;
}
QPushButton#accent:hover {
    background-color: #74c7ec;
}
QPushButton#accent:disabled {
    background-color: #45475a;
    color: #585b70;
}
QPushButton#danger {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#danger:hover {
    background-color: #eba0ac;
}
QPushButton#keyframeSet {
    background-color: #a6e3a1;
    color: #1e1e2e;
    font-weight: 600;
}
QPushButton#keyframeSet:hover {
    background-color: #94e2d5;
}
QPushButton#keyframeDel {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: #585b70;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #89b4fa;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #313244;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #89b4fa;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #585b70;
    border-radius: 3px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QLabel#frameLabel {
    font-size: 15px;
    font-weight: 700;
    color: #f9e2af;
    min-width: 110px;
}
QFrame#layerItem {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QFrame#timeline {
    background-color: #181825;
    border-top: 1px solid #45475a;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    font-size: 12px;
}
QCheckBox { spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 3px;
    border: 1px solid #45475a;
    background: #313244;
}
QCheckBox::indicator:checked {
    background: #89b4fa;
    border-color: #89b4fa;
}
QSplitter::handle {
    background: #313244;
    width: 2px;
}
"""


# ============================================================================
#  Data Models
# ============================================================================

class TextKeyframe:
    """Properties of a text layer at a specific frame."""
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


class TextLayer:
    """A text element with keyframed animation."""
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
        self.accent = LAYER_COLORS[(self.id - 1) % len(LAYER_COLORS)]

    def get_interpolated(self, frame: int) -> TextKeyframe:
        if not self.keyframes:
            return TextKeyframe(frame)
        if len(self.keyframes) == 1:
            kf = self.keyframes[0].copy()
            kf.frame = frame
            return kf

        sorted_kfs = sorted(self.keyframes, key=lambda k: k.frame)

        if frame <= sorted_kfs[0].frame:
            kf = sorted_kfs[0].copy()
            kf.frame = frame
            return kf
        if frame >= sorted_kfs[-1].frame:
            kf = sorted_kfs[-1].copy()
            kf.frame = frame
            return kf

        for i in range(len(sorted_kfs) - 1):
            if sorted_kfs[i].frame <= frame <= sorted_kfs[i + 1].frame:
                k1, k2 = sorted_kfs[i], sorted_kfs[i + 1]
                span = k2.frame - k1.frame
                if span == 0:
                    return k1.copy()
                t = (frame - k1.frame) / span
                t = t * t * (3 - 2 * t)  # smoothstep
                return self._lerp(k1, k2, t, frame)

        return sorted_kfs[-1].copy()

    def _lerp(self, k1, k2, t, frame):
        def mix(a, b): return a + (b - a) * t
        def mix_color(c1, c2):
            a, b = QColor(c1), QColor(c2)
            return QColor(
                int(mix(a.red(), b.red())),
                int(mix(a.green(), b.green())),
                int(mix(a.blue(), b.blue()))
            ).name()

        kf = TextKeyframe(frame=frame)
        kf.x = mix(k1.x, k2.x)
        kf.y = mix(k1.y, k2.y)
        kf.font_size = int(mix(k1.font_size, k2.font_size))
        kf.opacity = mix(k1.opacity, k2.opacity)
        kf.outline_width = int(mix(k1.outline_width, k2.outline_width))
        kf.rotation = mix(k1.rotation, k2.rotation)
        kf.color = mix_color(k1.color, k2.color)
        kf.outline_color = mix_color(k1.outline_color, k2.outline_color)
        return kf

    def get_keyframe_at(self, frame: int):
        for kf in self.keyframes:
            if kf.frame == frame:
                return kf
        return None

    def set_keyframe(self, kf: TextKeyframe):
        for i, existing in enumerate(self.keyframes):
            if existing.frame == kf.frame:
                self.keyframes[i] = kf
                return
        self.keyframes.append(kf)

    def remove_keyframe(self, frame: int):
        self.keyframes = [kf for kf in self.keyframes if kf.frame != frame]
        if not self.keyframes:
            self.keyframes = [TextKeyframe()]

    def hit_test(self, rx, ry, frame, scale_factor=1.0):
        """Check if relative coords (rx,ry) are near this text. Returns distance or None."""
        kf = self.get_interpolated(frame)
        # Approximate text bounding box in relative coords
        # font_size 48 at 400px wide ~= 0.3 width for short text
        char_w = (kf.font_size * 0.6 * len(self.text)) * scale_factor
        char_h = kf.font_size * 1.2 * scale_factor
        half_w = char_w / 2
        half_h = char_h / 2

        # Distance from center
        dx = abs(rx - kf.x)
        dy = abs(ry - kf.y)

        if dx < half_w + 0.02 and dy < half_h + 0.02:
            return math.sqrt(dx * dx + dy * dy)
        return None


# ============================================================================
#  Canvas - click to select, drag to move, mousewheel to step frames
# ============================================================================

class GifCanvas(QWidget):
    text_moved = pyqtSignal(float, float)
    text_clicked = pyqtSignal(int)           # layer id
    frame_step = pyqtSignal(int)             # +1 or -1
    canvas_clicked = pyqtSignal(float, float)  # click on empty area

    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

        self._base_pixmap: QPixmap | None = None
        self._layers: list[TextLayer] = []
        self._selected_id: int = -1
        self._current_frame = 0
        self._gif_rect = QRectF()
        self._dragging = False
        self._hovering_id = -1
        self._rendered = QPixmap()

    def set_frame(self, pixmap: QPixmap, layers: list, frame: int, selected_id: int):
        self._base_pixmap = pixmap
        self._layers = layers
        self._current_frame = frame
        self._selected_id = selected_id
        self._render()
        self.update()

    def paintEvent(self, event):
        if self._rendered.isNull():
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("#11111b"))
            p.setPen(QColor("#585b70"))
            p.setFont(QFont("Segoe UI", 14))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load an animated GIF to begin")
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
        scale = min(cw / pw, ch / ph, 3.0)
        sw, sh = int(pw * scale), int(ph * scale)
        ox = (cw - sw) // 2
        oy = (ch - sh) // 2
        self._gif_rect = QRectF(ox, oy, sw, sh)

        result = QPixmap(cw, ch)
        result.fill(QColor("#11111b"))
        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Checkerboard
        cs = 10
        for cy in range(oy, oy + sh, cs):
            for cx in range(ox, ox + sw, cs):
                g = ((cx - ox) // cs + (cy - oy) // cs) % 2
                p.fillRect(cx, cy, min(cs, ox + sw - cx), min(cs, oy + sh - cy),
                           QColor("#2a2a3a") if g else QColor("#232336"))

        p.drawPixmap(ox, oy, sw, sh, self._base_pixmap)

        # Draw each text layer
        for layer in self._layers:
            if not layer.visible:
                continue
            kf = layer.get_interpolated(self._current_frame)
            is_selected = (layer.id == self._selected_id)
            is_hover = (layer.id == self._hovering_id)
            self._draw_text_layer(p, layer, kf, ox, oy, sw, sh, scale, is_selected, is_hover)

        p.end()
        self._rendered = result

    def _draw_text_layer(self, p: QPainter, layer: TextLayer, kf: TextKeyframe,
                         ox, oy, sw, sh, scale, selected, hover):
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
        p.setOpacity(kf.opacity)

        fm = QFontMetrics(font)
        lines = text.split('\n')
        total_h = fm.height() * len(lines)
        y_start = -total_h / 2

        # Compute bounding rect for selection box
        max_w = max(fm.horizontalAdvance(l) for l in lines) if lines else 0
        bbox = QRectF(-max_w / 2 - 6, y_start - 6, max_w + 12, total_h + 12)

        # Selection / hover indicator
        if selected or hover:
            p.setOpacity(1.0)
            accent = QColor(layer.accent)
            if selected:
                # Dashed selection box
                pen = QPen(accent, 2, Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(bbox, 4, 4)
                # Corner handles
                for cx, cy in [(bbox.left(), bbox.top()), (bbox.right(), bbox.top()),
                                (bbox.left(), bbox.bottom()), (bbox.right(), bbox.bottom())]:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(accent)
                    p.drawEllipse(QPointF(cx, cy), 4, 4)
            elif hover:
                pen = QPen(accent, 1, Qt.PenStyle.DotLine)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(bbox, 4, 4)
            p.setOpacity(kf.opacity)

        # Layer tag (small colored label)
        p.setOpacity(min(1.0, kf.opacity + 0.3))
        tag_font = QFont("Segoe UI", max(7, int(9 * scale)))
        tag_font.setBold(True)
        p.setFont(tag_font)
        tag_text = f" {layer.text[:12]} "
        tag_fm = QFontMetrics(tag_font)
        tag_w = tag_fm.horizontalAdvance(tag_text) + 8
        tag_rect = QRectF(bbox.left(), bbox.top() - tag_fm.height() - 2, tag_w, tag_fm.height() + 2)
        p.setPen(Qt.PenStyle.NoPen)
        accent_bg = QColor(layer.accent)
        accent_bg.setAlpha(200)
        p.setBrush(accent_bg)
        p.drawRoundedRect(tag_rect, 3, 3)
        p.setPen(QColor("#1e1e2e"))
        p.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)
        p.setOpacity(kf.opacity)

        # Draw text with outline
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

            # Outline
            ow = int(kf.outline_width * scale)
            if ow > 0:
                p.setPen(QPen(QColor(kf.outline_color), ow,
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                              Qt.PenJoinStyle.RoundJoin))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(path)

            # Shadow
            if layer.shadow:
                soff = max(2, int(2 * scale))
                sp = QPainterPath()
                sp.addText(lx + soff, ly + soff, font, line)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(0, 0, 0, 128))
                p.drawPath(sp)

            # Fill
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(kf.color))
            p.drawPath(path)

        p.restore()

    # ── Mouse handling ──

    def _rel_pos(self, mx, my):
        """Convert widget coords to relative GIF coords."""
        if self._gif_rect.width() == 0:
            return None, None
        rx = (mx - self._gif_rect.x()) / self._gif_rect.width()
        ry = (my - self._gif_rect.y()) / self._gif_rect.height()
        return max(0, min(1, rx)), max(0, min(1, ry))

    def _find_layer_at(self, rx, ry):
        """Find the closest visible layer under the cursor."""
        if rx is None:
            return None
        best_layer = None
        best_dist = float('inf')
        scale_factor = 1.0 / max(1, self._gif_rect.width())
        for layer in reversed(self._layers):  # top layers first
            if not layer.visible:
                continue
            d = layer.hit_test(rx, ry, self._current_frame, scale_factor)
            if d is not None and d < best_dist:
                best_dist = d
                best_layer = layer
        return best_layer

    def mousePressEvent(self, event):
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
        rx, ry = self._rel_pos(event.pos().x(), event.pos().y())
        if self._dragging and rx is not None:
            self.text_moved.emit(rx, ry)
        elif not self._dragging:
            # Hover detection
            hit = self._find_layer_at(rx, ry)
            new_hover = hit.id if hit else -1
            if new_hover != self._hovering_id:
                self._hovering_id = new_hover
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor if hit else Qt.CursorShape.ArrowCursor))
                self._render()
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self.frame_step.emit(-1)
        elif delta < 0:
            self.frame_step.emit(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._base_pixmap:
            self._render()
            self.update()


# ============================================================================
#  Keyframe Bar
# ============================================================================

class KeyframeBar(QWidget):
    frame_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(24)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.total_frames = 1
        self.keyframe_positions: list[int] = []
        self.current_frame = 0
        self.accent = "#89b4fa"

    def paintEvent(self, event):
        if self.total_frames <= 1:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        denom = max(1, self.total_frames - 1)

        # Track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#313244"))
        p.drawRoundedRect(0, h // 2 - 2, w, 4, 2, 2)

        # Keyframe diamonds
        for kf_f in self.keyframe_positions:
            x = int(kf_f / denom * (w - 12)) + 6
            p.setBrush(QColor("#f9e2af"))
            p.setPen(QPen(QColor("#1e1e2e"), 1))
            path = QPainterPath()
            path.moveTo(x, h // 2 - 7)
            path.lineTo(x + 7, h // 2)
            path.lineTo(x, h // 2 + 7)
            path.lineTo(x - 7, h // 2)
            path.closeSubpath()
            p.drawPath(path)

        # Current frame marker
        cx = int(self.current_frame / denom * (w - 12)) + 6
        p.setBrush(QColor(self.accent))
        p.setPen(QPen(QColor("#1e1e2e"), 1))
        p.drawEllipse(QPointF(cx, h / 2), 5, 5)
        p.end()

    def mousePressEvent(self, event):
        if self.total_frames <= 1:
            return
        w = self.width()
        denom = max(1, self.total_frames - 1)
        frame = int((event.pos().x() - 6) / max(1, w - 12) * denom + 0.5)
        frame = max(0, min(self.total_frames - 1, frame))
        self.frame_clicked.emit(frame)


# ============================================================================
#  Layer List Widget
# ============================================================================

class LayerWidget(QFrame):
    selected = pyqtSignal(int)
    deleted = pyqtSignal(int)
    visibility_changed = pyqtSignal(int, bool)

    def __init__(self, layer: TextLayer, is_selected: bool):
        super().__init__()
        self.layer = layer
        self.setObjectName("layerItem")
        self.setFixedHeight(42)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        border_color = layer.accent if is_selected else "#45475a"
        bg = "#1e1e2e" if is_selected else "#313244"
        self.setStyleSheet(
            f"QFrame#layerItem {{ background-color: {bg}; border: 2px solid {border_color}; "
            f"border-radius: 6px; padding: 2px; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)

        # Color dot
        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background-color: {layer.accent}; border-radius: 6px; border: none;")
        layout.addWidget(dot)

        # Visibility
        self.vis_btn = QPushButton("V" if layer.visible else "-")
        self.vis_btn.setFixedSize(26, 26)
        self.vis_btn.setStyleSheet(
            f"background-color: {'#45475a' if layer.visible else '#1e1e2e'}; "
            f"border-radius: 4px; font-size: 11px; padding: 0; border: none; "
            f"color: {'#cdd6f4' if layer.visible else '#585b70'};"
        )
        self.vis_btn.clicked.connect(self._toggle_vis)
        layout.addWidget(self.vis_btn)

        # Label
        self.label = QLabel(layer.text[:18] or "---")
        self.label.setStyleSheet(f"color: #cdd6f4; font-weight: {'600' if is_selected else '400'}; border: none;")
        layout.addWidget(self.label, 1)

        # Delete
        del_btn = QPushButton("X")
        del_btn.setFixedSize(26, 26)
        del_btn.setStyleSheet(
            "background-color: transparent; color: #f38ba8; font-weight: 700; "
            "border: none; font-size: 12px; padding: 0;"
        )
        del_btn.clicked.connect(lambda: self.deleted.emit(layer.id))
        layout.addWidget(del_btn)

    def _toggle_vis(self):
        self.layer.visible = not self.layer.visible
        self.vis_btn.setText("V" if self.layer.visible else "-")
        self.visibility_changed.emit(self.layer.id, self.layer.visible)

    def mousePressEvent(self, event):
        self.selected.emit(self.layer.id)


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

        self.playing = False
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self._advance_frame)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        # ── Left Panel: Canvas + Timeline ──
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 8, 4, 0)
        ll.setSpacing(6)

        # Top bar
        topbar = QHBoxLayout()
        self.btn_load = QPushButton("Load GIF")
        self.btn_load.setObjectName("accent")
        self.btn_load.setFixedHeight(34)
        self.btn_load.clicked.connect(self._load_gif)
        topbar.addWidget(self.btn_load)

        self.btn_export = QPushButton("Export GIF")
        self.btn_export.setObjectName("accent")
        self.btn_export.setFixedHeight(34)
        self.btn_export.clicked.connect(self._export_gif)
        self.btn_export.setEnabled(False)
        topbar.addWidget(self.btn_export)

        topbar.addStretch()
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        topbar.addWidget(self.info_label)
        ll.addLayout(topbar)

        # Hint
        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #585b70; font-size: 11px; font-style: italic;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ll.addWidget(self.hint_label)

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
        tl.setContentsMargins(12, 6, 12, 8)
        tl.setSpacing(4)

        self.kf_bar = KeyframeBar()
        self.kf_bar.frame_clicked.connect(self._set_frame)
        tl.addWidget(self.kf_bar)

        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.btn_play = QPushButton("Play")
        self.btn_play.setFixedSize(72, 30)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_play.setEnabled(False)
        controls.addWidget(self.btn_play)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(34, 30)
        self.btn_prev.clicked.connect(lambda: self._step_frame(-1))
        self.btn_prev.setEnabled(False)
        controls.addWidget(self.btn_prev)

        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self._set_frame)
        controls.addWidget(self.frame_slider, 1)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(34, 30)
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

        # ── Right Panel: Layers + Properties ──
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_inner = QWidget()
        rl = QVBoxLayout(right_inner)
        rl.setContentsMargins(4, 8, 8, 8)
        rl.setSpacing(6)
        right_inner.setFixedWidth(310)

        # ── Layers ──
        layers_grp = QGroupBox("Text Layers")
        layers_l = QVBoxLayout(layers_grp)
        layers_l.setSpacing(4)

        self.btn_add = QPushButton("+ Add Text Layer")
        self.btn_add.setObjectName("accent")
        self.btn_add.clicked.connect(self._add_layer)
        self.btn_add.setEnabled(False)
        layers_l.addWidget(self.btn_add)

        self.layers_list = QVBoxLayout()
        self.layers_list.setSpacing(3)
        layers_l.addLayout(self.layers_list)
        rl.addWidget(layers_grp)

        # ── Text Properties ──
        txt_grp = QGroupBox("Text")
        tg = QGridLayout(txt_grp)
        tg.setVerticalSpacing(5)
        tg.setHorizontalSpacing(6)
        r = 0

        tg.addWidget(QLabel("Text:"), r, 0)
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Type meme text...")
        self.txt_input.textChanged.connect(self._on_text_changed)
        tg.addWidget(self.txt_input, r, 1, 1, 2)
        r += 1

        tg.addWidget(QLabel("Font:"), r, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Impact"))
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        tg.addWidget(self.font_combo, r, 1, 1, 2)
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
        tg.addLayout(style_row, r, 0, 1, 3)
        r += 1

        tg.addWidget(QLabel("Align:"), r, 0)
        self.align_combo = QComboBox()
        self.align_combo.addItems(["center", "left", "right"])
        self.align_combo.currentTextChanged.connect(self._on_align_changed)
        tg.addWidget(self.align_combo, r, 1, 1, 2)
        rl.addWidget(txt_grp)

        # ── Animation Properties ──
        anim_grp = QGroupBox("Animation")
        ag = QGridLayout(anim_grp)
        ag.setVerticalSpacing(5)
        ag.setHorizontalSpacing(6)
        ar = 0

        ag.addWidget(QLabel("Size:"), ar, 0)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 200)
        self.spin_size.setValue(48)
        self.spin_size.valueChanged.connect(self._on_anim_prop_changed)
        ag.addWidget(self.spin_size, ar, 1, 1, 2)
        ar += 1

        ag.addWidget(QLabel("Opacity:"), ar, 0)
        self.spin_opacity = QDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setSingleStep(0.05)
        self.spin_opacity.setValue(1.0)
        self.spin_opacity.valueChanged.connect(self._on_anim_prop_changed)
        ag.addWidget(self.spin_opacity, ar, 1, 1, 2)
        ar += 1

        ag.addWidget(QLabel("Rotation:"), ar, 0)
        self.spin_rotation = QDoubleSpinBox()
        self.spin_rotation.setRange(-360, 360)
        self.spin_rotation.setSingleStep(5)
        self.spin_rotation.setValue(0)
        self.spin_rotation.valueChanged.connect(self._on_anim_prop_changed)
        ag.addWidget(self.spin_rotation, ar, 1, 1, 2)
        ar += 1

        ag.addWidget(QLabel("Outline:"), ar, 0)
        self.spin_outline = QSpinBox()
        self.spin_outline.setRange(0, 20)
        self.spin_outline.setValue(3)
        self.spin_outline.valueChanged.connect(self._on_anim_prop_changed)
        ag.addWidget(self.spin_outline, ar, 1, 1, 2)
        ar += 1

        # Colors
        color_row = QHBoxLayout()
        self.btn_color = QPushButton("Text Color")
        self.btn_color.setFixedHeight(30)
        self.btn_color.clicked.connect(lambda: self._pick_color("text"))
        self.btn_color.setStyleSheet("background: #ffffff; color: #000; border-radius: 4px; font-weight: 600;")
        color_row.addWidget(self.btn_color)
        self.btn_outline_color = QPushButton("Outline")
        self.btn_outline_color.setFixedHeight(30)
        self.btn_outline_color.clicked.connect(lambda: self._pick_color("outline"))
        self.btn_outline_color.setStyleSheet("background: #000000; color: #fff; border-radius: 4px; font-weight: 600;")
        color_row.addWidget(self.btn_outline_color)
        ag.addLayout(color_row, ar, 0, 1, 3)
        ar += 1

        # Position
        self.pos_label = QLabel("Drag text on canvas to position")
        self.pos_label.setStyleSheet("color: #585b70; font-size: 11px;")
        ag.addWidget(self.pos_label, ar, 0, 1, 3)
        ar += 1

        # Keyframe controls
        kf_row = QHBoxLayout()
        self.btn_set_kf = QPushButton("Set Keyframe")
        self.btn_set_kf.setObjectName("keyframeSet")
        self.btn_set_kf.setFixedHeight(32)
        self.btn_set_kf.clicked.connect(self._set_keyframe)
        kf_row.addWidget(self.btn_set_kf)
        self.btn_del_kf = QPushButton("Delete KF")
        self.btn_del_kf.setObjectName("keyframeDel")
        self.btn_del_kf.setFixedHeight(32)
        self.btn_del_kf.clicked.connect(self._delete_keyframe)
        kf_row.addWidget(self.btn_del_kf)
        ag.addLayout(kf_row, ar, 0, 1, 3)
        ar += 1

        self.kf_info = QLabel("")
        self.kf_info.setStyleSheet("color: #f9e2af; font-size: 11px;")
        self.kf_info.setWordWrap(True)
        ag.addWidget(self.kf_info, ar, 0, 1, 3)

        rl.addWidget(anim_grp)

        # ── Tips ──
        tips_grp = QGroupBox("Tips")
        tips_l = QVBoxLayout(tips_grp)
        tips = QLabel(
            "1. Click text on canvas to select it\n"
            "2. Drag to reposition\n"
            "3. Mousewheel on canvas = step frames\n"
            "4. Drag again on new frame = auto keyframe\n"
            "5. Text smoothly moves between keyframes"
        )
        tips.setStyleSheet("color: #a6adc8; font-size: 11px; line-height: 1.4;")
        tips.setWordWrap(True)
        tips_l.addWidget(tips)
        rl.addWidget(tips_grp)

        rl.addStretch()
        right_scroll.setWidget(right_inner)
        splitter.addWidget(right_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([900, 310])

        self.statusBar().showMessage("GifText v" + VERSION + " - Load a GIF to get started")

    # ====================================================================
    #  GIF Loading
    # ====================================================================

    def _load_gif(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Animated GIF", "", "GIF Files (*.gif);;All Files (*)"
        )
        if not path:
            return

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
            self.kf_bar.total_frames = self.total_frames
            self.info_label.setText(
                f"{self.gif_width}x{self.gif_height} | {self.total_frames} frames | "
                f"{os.path.basename(path)}"
            )
            self.hint_label.setText(
                "Click [+ Add Text Layer] to add names, then drag them into position. "
                "Mousewheel on canvas to step frames."
            )
            self._update_all()
            self.statusBar().showMessage(f"Loaded {os.path.basename(path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Error: {e}")

    # ====================================================================
    #  Playback
    # ====================================================================

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
        delay = self.frame_durations[self.current_frame]
        self.play_timer.start(delay)

    def _step_frame(self, delta: int):
        if not self.gif_frames:
            return
        self._set_frame(self.current_frame + delta)

    def _set_frame(self, frame: int):
        if not self.gif_frames:
            return
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(self.current_frame)
        self.frame_slider.blockSignals(False)
        self.frame_label.setText(f"{self.current_frame + 1} / {self.total_frames}")
        self._update_all()

    def _update_all(self):
        if not self.gif_frames:
            return
        sel_id = self.selected_layer.id if self.selected_layer else -1
        self.canvas.set_frame(self.gif_frames[self.current_frame], self.layers,
                              self.current_frame, sel_id)
        self._update_kf_bar()
        self._sync_props_from_layer()

    # ====================================================================
    #  Layers
    # ====================================================================

    def _add_layer(self):
        layer = TextLayer(f"Name {len(self.layers) + 1}")
        layer.keyframes = [TextKeyframe(frame=0, x=0.3 + 0.2 * (len(self.layers) % 3), y=0.3)]
        self.layers.append(layer)
        self.selected_layer = layer
        self._rebuild_layer_list()
        self._update_all()
        self.txt_input.setFocus()
        self.txt_input.selectAll()
        self.statusBar().showMessage(f"Added layer - type a name and drag it into position")

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
            w.visibility_changed.connect(self._on_vis_changed)
            self.layers_list.addWidget(w)

    def _select_layer(self, layer_id: int):
        self.selected_layer = next((l for l in self.layers if l.id == layer_id), None)
        self._rebuild_layer_list()
        self._update_all()

    def _delete_layer(self, layer_id: int):
        self.layers = [l for l in self.layers if l.id != layer_id]
        if self.selected_layer and self.selected_layer.id == layer_id:
            self.selected_layer = self.layers[-1] if self.layers else None
        self._rebuild_layer_list()
        self._update_all()

    def _on_vis_changed(self, layer_id, visible):
        self._update_all()

    # ====================================================================
    #  Canvas Interaction
    # ====================================================================

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
        # If we have a selected layer but clicked empty space, move it there
        if self.selected_layer:
            self._on_text_moved(rx, ry)

    # ====================================================================
    #  Properties Sync
    # ====================================================================

    def _sync_props_from_layer(self):
        layer = self.selected_layer
        if not layer:
            self.kf_info.setText("")
            self.pos_label.setText("No layer selected")
            return

        self._block(True)
        self.txt_input.setText(layer.text)
        self.font_combo.setCurrentFont(QFont(layer.font_family))
        self.chk_bold.setChecked(layer.bold)
        self.chk_italic.setChecked(layer.italic)
        self.chk_upper.setChecked(layer.uppercase)
        self.chk_shadow.setChecked(layer.shadow)
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
        self.kf_info.setText(f"{marker}  Keyframes at frames: {', '.join(map(str, kf_frames))}")

        self.kf_bar.accent = layer.accent
        self._block(False)

    def _block(self, b):
        for w in [self.txt_input, self.spin_size, self.spin_opacity,
                  self.spin_rotation, self.spin_outline, self.font_combo,
                  self.chk_bold, self.chk_italic, self.chk_upper, self.chk_shadow,
                  self.align_combo]:
            w.blockSignals(b)

    def _on_text_changed(self, text):
        if not self.selected_layer:
            return
        self.selected_layer.text = text
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
        self._update_all()

    def _on_align_changed(self, a):
        if self.selected_layer:
            self.selected_layer.alignment = a
            self._update_all()

    def _on_anim_prop_changed(self):
        # Live preview: update canvas but don't auto-create keyframe
        self._update_all()

    def _pick_color(self, target):
        if not self.selected_layer:
            return
        kf = self.selected_layer.get_interpolated(self.current_frame)
        initial = QColor(kf.color if target == "text" else kf.outline_color)
        color = QColorDialog.getColor(initial, self, f"Pick {target} color")
        if not color.isValid():
            return

        # Auto-set keyframe with new color
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
        self._update_all()

    # ====================================================================
    #  Keyframes
    # ====================================================================

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
        self._update_all()
        self.statusBar().showMessage(f"Keyframe set at frame {self.current_frame + 1}")

    def _delete_keyframe(self):
        if not self.selected_layer:
            return
        if self.selected_layer.get_keyframe_at(self.current_frame):
            self.selected_layer.remove_keyframe(self.current_frame)
            self._update_all()
            self.statusBar().showMessage(f"Keyframe deleted at frame {self.current_frame + 1}")

    def _update_kf_bar(self):
        if self.selected_layer:
            self.kf_bar.keyframe_positions = [k.frame for k in self.selected_layer.keyframes]
        else:
            self.kf_bar.keyframe_positions = []
        self.kf_bar.current_frame = self.current_frame
        self.kf_bar.total_frames = self.total_frames
        self.kf_bar.update()

    # ====================================================================
    #  Export
    # ====================================================================

    def _export_gif(self):
        if not self.gif_pil_frames:
            return

        default_name = os.path.splitext(os.path.basename(self.gif_path))[0] + "_meme.gif"
        default_dir = os.path.dirname(self.gif_path)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export GIF", os.path.join(default_dir, default_name),
            "GIF Files (*.gif)"
        )
        if not path:
            return

        self.statusBar().showMessage("Exporting...")
        QApplication.processEvents()

        try:
            output_frames = []
            for i, pil_frame in enumerate(self.gif_pil_frames):
                frame = pil_frame.copy()
                for layer in self.layers:
                    if not layer.visible:
                        continue
                    frame = self._render_text_pil(frame, layer, i)
                output_frames.append(frame.convert("RGB"))

            output_frames[0].save(
                path, save_all=True, append_images=output_frames[1:],
                duration=self.frame_durations, loop=0, optimize=False
            )
            self.statusBar().showMessage(f"Exported: {os.path.basename(path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Export error: {e}")

    def _render_text_pil(self, frame: Image.Image, layer: TextLayer, frame_idx: int) -> Image.Image:
        kf = layer.get_interpolated(frame_idx)
        text = layer.text.upper() if layer.uppercase else layer.text
        if not text:
            return frame

        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        font = self._get_pil_font(layer, kf.font_size)

        lines = text.split('\n')
        line_sizes = []
        total_h = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            line_sizes.append((w, h))
            total_h += h

        cx = kf.x * frame.width
        cy = kf.y * frame.height
        y_cursor = cy - total_h / 2

        text_rgb = tuple(int(kf.color[i:i+2], 16) for i in (1, 3, 5))
        outline_rgb = tuple(int(kf.outline_color[i:i+2], 16) for i in (1, 3, 5))
        alpha = int(kf.opacity * 255)

        for i, line in enumerate(lines):
            lw, lh = line_sizes[i]
            max_w = max(s[0] for s in line_sizes)
            if layer.alignment == "center":
                lx = cx - lw / 2
            elif layer.alignment == "left":
                lx = cx - max_w / 2
            else:
                lx = cx + max_w / 2 - lw

            # Outline via stroke_width if available, else manual offsets
            if kf.outline_width > 0:
                try:
                    draw.text((lx, y_cursor), line, font=font,
                              fill=(*outline_rgb, alpha),
                              stroke_width=kf.outline_width,
                              stroke_fill=(*outline_rgb, alpha))
                except TypeError:
                    ow = kf.outline_width
                    for dx in range(-ow, ow + 1):
                        for dy in range(-ow, ow + 1):
                            if dx * dx + dy * dy <= ow * ow:
                                draw.text((lx + dx, y_cursor + dy), line, font=font,
                                          fill=(*outline_rgb, alpha))

            if layer.shadow:
                draw.text((lx + 2, y_cursor + 2), line, font=font, fill=(0, 0, 0, alpha // 2))

            draw.text((lx, y_cursor), line, font=font, fill=(*text_rgb, alpha))
            y_cursor += lh

        if kf.rotation != 0:
            overlay = overlay.rotate(-kf.rotation, center=(cx, cy),
                                     resample=Image.Resampling.BICUBIC, expand=False)

        return Image.alpha_composite(frame, overlay)

    def _get_pil_font(self, layer: TextLayer, size: int):
        family = layer.font_family.lower().replace(' ', '')
        candidates = []
        if layer.bold and layer.italic:
            candidates.append(f"{family}bi.ttf")
            candidates.append(f"{family}z.ttf")
        if layer.bold:
            candidates.append(f"{family}bd.ttf")
            candidates.append(f"{family}b.ttf")
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
