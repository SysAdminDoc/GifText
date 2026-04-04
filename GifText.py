"""
GifText v0.1.0 - Animated GIF Text Editor
Add smooth animated text to GIFs for meme creation.
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
    QColorDialog, QFileDialog, QScrollArea, QFrame, QSplitter,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem,
    QCheckBox, QLineEdit, QFontComboBox, QGroupBox, QGridLayout,
    QSizePolicy, QToolBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QRectF, pyqtSignal, QSize, QByteArray, QBuffer,
    QIODevice
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPainter, QFont, QPen, QBrush, QIcon,
    QAction, QFontMetrics, QPainterPath, QKeySequence, QCursor
)
from PIL import Image, ImageDraw, ImageFont, ImageSequence, ImageFilter
import io
import struct

VERSION = "0.1.0"

# ─── Dark Theme ──────────────────────────────────────────────────────────────

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QMenuBar, QMenu {
    background-color: #181825;
    color: #cdd6f4;
}
QMenu::item:selected {
    background-color: #45475a;
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
QPushButton#accent {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: 600;
}
QPushButton#accent:hover {
    background-color: #74c7ec;
}
QPushButton#danger {
    background-color: #f38ba8;
    color: #1e1e2e;
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
    background: #89b4fa;
    border-radius: 3px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
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
}
QLabel#title {
    font-size: 18px;
    font-weight: 700;
    color: #89b4fa;
}
QLabel#frameLabel {
    font-size: 14px;
    font-weight: 600;
    color: #f9e2af;
    min-width: 100px;
}
QFrame#layerItem {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
}
QFrame#layerItem[selected="true"] {
    border-color: #89b4fa;
    background-color: #1e1e2e;
}
QFrame#timeline {
    background-color: #181825;
    border-top: 1px solid #45475a;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
}
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #45475a;
    background: #313244;
}
QCheckBox::indicator:checked {
    background: #89b4fa;
    border-color: #89b4fa;
}
"""


# ─── Data Models ─────────────────────────────────────────────────────────────

class TextKeyframe:
    """Properties of a text layer at a specific frame."""
    def __init__(self, frame=0, x=0.5, y=0.5, font_size=48, opacity=1.0,
                 color="#ffffff", outline_color="#000000", outline_width=3,
                 rotation=0.0):
        self.frame = frame
        self.x = x          # 0..1 relative to GIF width
        self.y = y          # 0..1 relative to GIF height
        self.font_size = font_size
        self.opacity = opacity
        self.color = color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.rotation = rotation

    def copy(self):
        return copy.deepcopy(self)


class TextLayer:
    """A text element with keyframed animation."""
    _counter = 0

    def __init__(self, text="YOUR TEXT"):
        TextLayer._counter += 1
        self.id = TextLayer._counter
        self.text = text
        self.font_family = "Impact"
        self.bold = True
        self.italic = False
        self.alignment = "center"  # left, center, right
        self.keyframes: list[TextKeyframe] = [TextKeyframe()]
        self.visible = True
        self.shadow = False
        self.uppercase = True

    def get_interpolated(self, frame: int) -> TextKeyframe:
        """Get smoothly interpolated properties at a given frame."""
        if not self.keyframes:
            return TextKeyframe(frame)
        if len(self.keyframes) == 1:
            kf = self.keyframes[0].copy()
            kf.frame = frame
            return kf

        sorted_kfs = sorted(self.keyframes, key=lambda k: k.frame)

        # Before first keyframe
        if frame <= sorted_kfs[0].frame:
            kf = sorted_kfs[0].copy()
            kf.frame = frame
            return kf
        # After last keyframe
        if frame >= sorted_kfs[-1].frame:
            kf = sorted_kfs[-1].copy()
            kf.frame = frame
            return kf

        # Find surrounding keyframes
        for i in range(len(sorted_kfs) - 1):
            if sorted_kfs[i].frame <= frame <= sorted_kfs[i + 1].frame:
                k1, k2 = sorted_kfs[i], sorted_kfs[i + 1]
                span = k2.frame - k1.frame
                if span == 0:
                    return k1.copy()
                t = (frame - k1.frame) / span
                # Smooth ease-in-out
                t = t * t * (3 - 2 * t)
                return self._lerp(k1, k2, t, frame)

        return sorted_kfs[-1].copy()

    def _lerp(self, k1: TextKeyframe, k2: TextKeyframe, t: float, frame: int) -> TextKeyframe:
        kf = TextKeyframe(frame=frame)
        kf.x = k1.x + (k2.x - k1.x) * t
        kf.y = k1.y + (k2.y - k1.y) * t
        kf.font_size = int(k1.font_size + (k2.font_size - k1.font_size) * t)
        kf.opacity = k1.opacity + (k2.opacity - k1.opacity) * t
        kf.outline_width = int(k1.outline_width + (k2.outline_width - k1.outline_width) * t)
        kf.rotation = k1.rotation + (k2.rotation - k1.rotation) * t
        # Color interpolation
        c1 = QColor(k1.color)
        c2 = QColor(k2.color)
        r = int(c1.red() + (c2.red() - c1.red()) * t)
        g = int(c1.green() + (c2.green() - c1.green()) * t)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
        kf.color = QColor(r, g, b).name()
        c1 = QColor(k1.outline_color)
        c2 = QColor(k2.outline_color)
        r = int(c1.red() + (c2.red() - c1.red()) * t)
        g = int(c1.green() + (c2.green() - c1.green()) * t)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
        kf.outline_color = QColor(r, g, b).name()
        return kf

    def get_keyframe_at(self, frame: int) -> TextKeyframe | None:
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


# ─── Canvas ──────────────────────────────────────────────────────────────────

class GifCanvas(QLabel):
    """Canvas that displays the current GIF frame with text overlays."""
    text_moved = pyqtSignal(float, float)  # relative x, y

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #11111b; border-radius: 8px;")

        self._base_pixmap = None
        self._layers: list[TextLayer] = []
        self._current_frame = 0
        self._dragging = False
        self._drag_layer: TextLayer | None = None
        self._gif_rect = QRectF()

    def set_frame(self, pixmap: QPixmap, layers: list, frame: int):
        self._base_pixmap = pixmap
        self._layers = layers
        self._current_frame = frame
        self._render()

    def _render(self):
        if not self._base_pixmap:
            return

        # Scale pixmap to fit widget while maintaining aspect ratio
        canvas_w, canvas_h = self.width(), self.height()
        pw, ph = self._base_pixmap.width(), self._base_pixmap.height()
        scale = min(canvas_w / pw, canvas_h / ph, 2.0)  # cap at 2x for small GIFs
        sw, sh = int(pw * scale), int(ph * scale)
        ox = (canvas_w - sw) // 2
        oy = (canvas_h - sh) // 2
        self._gif_rect = QRectF(ox, oy, sw, sh)

        result = QPixmap(canvas_w, canvas_h)
        result.fill(QColor("#11111b"))
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw checkerboard background for transparency
        checker_size = 8
        for cy in range(oy, oy + sh, checker_size):
            for cx in range(ox, ox + sw, checker_size):
                grid = ((cx - ox) // checker_size + (cy - oy) // checker_size) % 2
                painter.fillRect(cx, cy, checker_size, checker_size,
                                 QColor("#2a2a3a") if grid else QColor("#232336"))

        # Draw GIF frame
        painter.drawPixmap(ox, oy, sw, sh, self._base_pixmap)

        # Draw text layers
        for layer in self._layers:
            if not layer.visible:
                continue
            kf = layer.get_interpolated(self._current_frame)
            self._draw_text(painter, layer, kf, ox, oy, sw, sh, scale)

        painter.end()
        self.setPixmap(result)

    def _draw_text(self, painter: QPainter, layer: TextLayer, kf: TextKeyframe,
                   ox, oy, sw, sh, scale):
        text = layer.text.upper() if layer.uppercase else layer.text
        if not text:
            return

        font = QFont(layer.font_family, int(kf.font_size * scale))
        font.setBold(layer.bold)
        font.setItalic(layer.italic)
        painter.setFont(font)

        # Text position (relative coords to absolute)
        tx = ox + kf.x * sw
        ty = oy + kf.y * sh

        painter.save()
        painter.translate(tx, ty)
        if kf.rotation != 0:
            painter.rotate(kf.rotation)
        painter.setOpacity(kf.opacity)

        fm = QFontMetrics(font)
        lines = text.split('\n')
        total_h = fm.height() * len(lines)
        y_start = -total_h / 2

        for i, line in enumerate(lines):
            bw = fm.horizontalAdvance(line)
            if layer.alignment == "center":
                lx = -bw / 2
            elif layer.alignment == "left":
                lx = -sw * 0.4
            else:
                lx = sw * 0.4 - bw
            ly = y_start + fm.height() * (i + 1) - fm.descent()

            # Outline
            outline_w = int(kf.outline_width * scale)
            if outline_w > 0:
                path = QPainterPath()
                path.addText(lx, ly, font, line)
                painter.setPen(QPen(QColor(kf.outline_color), outline_w,
                                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                    Qt.PenJoinStyle.RoundJoin))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)

            # Shadow
            if layer.shadow:
                shadow_off = max(2, int(2 * scale))
                path_s = QPainterPath()
                path_s.addText(lx + shadow_off, ly + shadow_off, font, line)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(0, 0, 0, 128))
                painter.drawPath(path_s)

            # Fill
            path = QPainterPath()
            path.addText(lx, ly, font, line)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(kf.color))
            painter.drawPath(path)

        painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._gif_rect.contains(event.pos().x(), event.pos().y()):
            self._dragging = True
            self._update_drag_pos(event.pos().x(), event.pos().y())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._update_drag_pos(event.pos().x(), event.pos().y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def _update_drag_pos(self, mx, my):
        if self._gif_rect.width() == 0:
            return
        rx = (mx - self._gif_rect.x()) / self._gif_rect.width()
        ry = (my - self._gif_rect.y()) / self._gif_rect.height()
        rx = max(0, min(1, rx))
        ry = max(0, min(1, ry))
        self.text_moved.emit(rx, ry)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()


# ─── Layer List Item ─────────────────────────────────────────────────────────

class LayerWidget(QFrame):
    selected = pyqtSignal(int)
    deleted = pyqtSignal(int)
    visibility_changed = pyqtSignal(int, bool)

    def __init__(self, layer: TextLayer):
        super().__init__()
        self.layer = layer
        self.setObjectName("layerItem")
        self.setFixedHeight(44)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.vis_btn = QPushButton("V")
        self.vis_btn.setFixedSize(28, 28)
        self.vis_btn.setCheckable(True)
        self.vis_btn.setChecked(True)
        self.vis_btn.clicked.connect(lambda c: self.visibility_changed.emit(layer.id, c))
        layout.addWidget(self.vis_btn)

        self.label = QLabel(f"  {layer.text[:20]}")
        self.label.setStyleSheet("color: #cdd6f4;")
        layout.addWidget(self.label, 1)

        del_btn = QPushButton("X")
        del_btn.setObjectName("danger")
        del_btn.setFixedSize(28, 28)
        del_btn.clicked.connect(lambda: self.deleted.emit(layer.id))
        layout.addWidget(del_btn)

    def mousePressEvent(self, event):
        self.selected.emit(self.layer.id)

    def set_selected(self, sel: bool):
        self.setProperty("selected", "true" if sel else "false")
        self.setStyleSheet(
            f"QFrame#layerItem {{ border-color: {'#89b4fa' if sel else '#45475a'}; "
            f"background-color: {'#1e1e2e' if sel else '#313244'}; "
            f"border: 1px solid; border-radius: 6px; padding: 6px; }}"
        )

    def update_label(self):
        self.label.setText(f"  {self.layer.text[:20]}")


# ─── Keyframe Indicator Bar ─────────────────────────────────────────────────

class KeyframeBar(QWidget):
    """Visual bar showing keyframe positions on the timeline."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(20)
        self.total_frames = 1
        self.keyframe_positions: list[int] = []
        self.current_frame = 0

    def paintEvent(self, event):
        if self.total_frames <= 1:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        # Track line
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#313244"))
        painter.drawRoundedRect(0, h // 2 - 2, w, 4, 2, 2)

        # Keyframe diamonds
        for kf_frame in self.keyframe_positions:
            x = int(kf_frame / max(1, self.total_frames - 1) * w)
            painter.setBrush(QColor("#f9e2af"))
            painter.setPen(QPen(QColor("#1e1e2e"), 1))
            path = QPainterPath()
            path.moveTo(x, h // 2 - 6)
            path.lineTo(x + 6, h // 2)
            path.lineTo(x, h // 2 + 6)
            path.lineTo(x - 6, h // 2)
            path.closeSubpath()
            painter.drawPath(path)

        # Current frame indicator
        cx = int(self.current_frame / max(1, self.total_frames - 1) * w)
        painter.setBrush(QColor("#89b4fa"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 4, h // 2 - 4, 8, 8)

        painter.end()


# ─── Main Window ─────────────────────────────────────────────────────────────

class GifTextApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"GifText v{VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self.gif_frames: list[QPixmap] = []
        self.gif_pil_frames: list[Image.Image] = []
        self.frame_durations: list[int] = []
        self.current_frame = 0
        self.total_frames = 0
        self.gif_width = 0
        self.gif_height = 0

        self.layers: list[TextLayer] = []
        self.selected_layer: TextLayer | None = None

        self.playing = False
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self._advance_frame)

        self._build_ui()
        self._show_empty_state()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ── Left: Canvas + Timeline ──
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 4, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_load = QPushButton("Load GIF")
        btn_load.setObjectName("accent")
        btn_load.clicked.connect(self._load_gif)
        toolbar.addWidget(btn_load)

        self.btn_export = QPushButton("Export GIF")
        self.btn_export.setObjectName("accent")
        self.btn_export.clicked.connect(self._export_gif)
        self.btn_export.setEnabled(False)
        toolbar.addWidget(self.btn_export)

        toolbar.addStretch()

        self.size_label = QLabel("")
        self.size_label.setStyleSheet("color: #a6adc8;")
        toolbar.addWidget(self.size_label)

        left_layout.addLayout(toolbar)

        # Canvas
        self.canvas = GifCanvas()
        self.canvas.text_moved.connect(self._on_text_moved)
        left_layout.addWidget(self.canvas, 1)

        # Timeline
        timeline = QFrame()
        timeline.setObjectName("timeline")
        tl_layout = QVBoxLayout(timeline)
        tl_layout.setContentsMargins(12, 8, 12, 8)

        # Keyframe bar
        self.kf_bar = KeyframeBar()
        tl_layout.addWidget(self.kf_bar)

        # Frame slider row
        slider_row = QHBoxLayout()

        self.btn_play = QPushButton("Play")
        self.btn_play.setFixedWidth(70)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_play.setEnabled(False)
        slider_row.addWidget(self.btn_play)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedWidth(36)
        self.btn_prev.clicked.connect(lambda: self._set_frame(self.current_frame - 1))
        self.btn_prev.setEnabled(False)
        slider_row.addWidget(self.btn_prev)

        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self._set_frame)
        slider_row.addWidget(self.frame_slider, 1)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedWidth(36)
        self.btn_next.clicked.connect(lambda: self._set_frame(self.current_frame + 1))
        self.btn_next.setEnabled(False)
        slider_row.addWidget(self.btn_next)

        self.frame_label = QLabel("0 / 0")
        self.frame_label.setObjectName("frameLabel")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slider_row.addWidget(self.frame_label)

        tl_layout.addLayout(slider_row)
        left_layout.addWidget(timeline)

        splitter.addWidget(left)

        # ── Right: Properties Panel ──
        right = QWidget()
        right.setFixedWidth(320)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 8, 8, 8)

        # Layers section
        layers_group = QGroupBox("Text Layers")
        layers_layout = QVBoxLayout(layers_group)

        btn_row = QHBoxLayout()
        self.btn_add_layer = QPushButton("+ Add Text")
        self.btn_add_layer.setObjectName("accent")
        self.btn_add_layer.clicked.connect(self._add_layer)
        self.btn_add_layer.setEnabled(False)
        btn_row.addWidget(self.btn_add_layer)
        layers_layout.addLayout(btn_row)

        self.layers_container = QVBoxLayout()
        self.layers_container.setSpacing(4)
        layers_layout.addLayout(self.layers_container)
        layers_layout.addStretch()

        right_layout.addWidget(layers_group)

        # Properties section
        props_group = QGroupBox("Text Properties")
        props_layout = QGridLayout(props_group)
        props_layout.setVerticalSpacing(6)
        row = 0

        props_layout.addWidget(QLabel("Text:"), row, 0)
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Enter text...")
        self.txt_input.textChanged.connect(self._on_text_changed)
        props_layout.addWidget(self.txt_input, row, 1, 1, 2)
        row += 1

        props_layout.addWidget(QLabel("Font:"), row, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Impact"))
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        props_layout.addWidget(self.font_combo, row, 1, 1, 2)
        row += 1

        # Style toggles
        style_row = QHBoxLayout()
        self.chk_bold = QCheckBox("Bold")
        self.chk_bold.setChecked(True)
        self.chk_bold.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_bold)
        self.chk_italic = QCheckBox("Italic")
        self.chk_italic.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_italic)
        self.chk_upper = QCheckBox("UPPER")
        self.chk_upper.setChecked(True)
        self.chk_upper.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_upper)
        self.chk_shadow = QCheckBox("Shadow")
        self.chk_shadow.toggled.connect(self._on_style_changed)
        style_row.addWidget(self.chk_shadow)
        props_layout.addLayout(style_row, row, 0, 1, 3)
        row += 1

        # Alignment
        props_layout.addWidget(QLabel("Align:"), row, 0)
        self.align_combo = QComboBox()
        self.align_combo.addItems(["center", "left", "right"])
        self.align_combo.currentTextChanged.connect(self._on_align_changed)
        props_layout.addWidget(self.align_combo, row, 1, 1, 2)
        row += 1

        right_layout.addWidget(props_group)

        # Animation section
        anim_group = QGroupBox("Animation (per frame)")
        anim_layout = QGridLayout(anim_group)
        anim_layout.setVerticalSpacing(6)
        arow = 0

        anim_layout.addWidget(QLabel("Font Size:"), arow, 0)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 200)
        self.spin_size.setValue(48)
        self.spin_size.valueChanged.connect(self._on_anim_changed)
        anim_layout.addWidget(self.spin_size, arow, 1, 1, 2)
        arow += 1

        anim_layout.addWidget(QLabel("Opacity:"), arow, 0)
        self.spin_opacity = QDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setSingleStep(0.05)
        self.spin_opacity.setValue(1.0)
        self.spin_opacity.valueChanged.connect(self._on_anim_changed)
        anim_layout.addWidget(self.spin_opacity, arow, 1, 1, 2)
        arow += 1

        anim_layout.addWidget(QLabel("Rotation:"), arow, 0)
        self.spin_rotation = QDoubleSpinBox()
        self.spin_rotation.setRange(-360, 360)
        self.spin_rotation.setSingleStep(5)
        self.spin_rotation.setValue(0)
        self.spin_rotation.valueChanged.connect(self._on_anim_changed)
        anim_layout.addWidget(self.spin_rotation, arow, 1, 1, 2)
        arow += 1

        anim_layout.addWidget(QLabel("Outline:"), arow, 0)
        self.spin_outline = QSpinBox()
        self.spin_outline.setRange(0, 20)
        self.spin_outline.setValue(3)
        self.spin_outline.valueChanged.connect(self._on_anim_changed)
        anim_layout.addWidget(self.spin_outline, arow, 1, 1, 2)
        arow += 1

        # Color buttons
        color_row = QHBoxLayout()
        self.btn_color = QPushButton("Text Color")
        self.btn_color.clicked.connect(lambda: self._pick_color("text"))
        self.btn_color.setStyleSheet("background-color: #ffffff; color: #000000; border-radius: 4px;")
        color_row.addWidget(self.btn_color)
        self.btn_outline_color = QPushButton("Outline")
        self.btn_outline_color.clicked.connect(lambda: self._pick_color("outline"))
        self.btn_outline_color.setStyleSheet("background-color: #000000; color: #ffffff; border-radius: 4px;")
        color_row.addWidget(self.btn_outline_color)
        anim_layout.addLayout(color_row, arow, 0, 1, 3)
        arow += 1

        # Position display
        self.pos_label = QLabel("Position: drag on canvas")
        self.pos_label.setStyleSheet("color: #a6adc8; font-style: italic;")
        anim_layout.addWidget(self.pos_label, arow, 0, 1, 3)
        arow += 1

        # Keyframe buttons
        kf_row = QHBoxLayout()
        self.btn_set_kf = QPushButton("Set Keyframe")
        self.btn_set_kf.setObjectName("keyframeSet")
        self.btn_set_kf.clicked.connect(self._set_keyframe)
        kf_row.addWidget(self.btn_set_kf)
        self.btn_del_kf = QPushButton("Delete KF")
        self.btn_del_kf.setObjectName("keyframeDel")
        self.btn_del_kf.clicked.connect(self._delete_keyframe)
        kf_row.addWidget(self.btn_del_kf)
        anim_layout.addLayout(kf_row, arow, 0, 1, 3)
        arow += 1

        self.kf_info = QLabel("")
        self.kf_info.setStyleSheet("color: #f9e2af;")
        anim_layout.addWidget(self.kf_info, arow, 0, 1, 3)

        right_layout.addWidget(anim_group)
        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        # Status bar
        self.statusBar().showMessage("Load a GIF to get started")

    def _show_empty_state(self):
        self.canvas.setText("Load an animated GIF to begin")
        self.canvas.setStyleSheet(
            "background-color: #11111b; border-radius: 8px; color: #585b70; "
            "font-size: 16px; qproperty-alignment: AlignCenter;"
        )

    # ── GIF Loading ──

    def _load_gif(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Animated GIF", "",
            "GIF Files (*.gif);;All Files (*)"
        )
        if not path:
            return

        try:
            img = Image.open(path)
            if not hasattr(img, 'n_frames') or img.n_frames < 2:
                self.statusBar().showMessage("Not an animated GIF (needs 2+ frames)")
                return

            self.gif_frames.clear()
            self.gif_pil_frames.clear()
            self.frame_durations.clear()

            self.gif_width = img.width
            self.gif_height = img.height

            # Extract all frames
            for i in range(img.n_frames):
                img.seek(i)
                frame = img.convert("RGBA")
                self.gif_pil_frames.append(frame.copy())

                duration = img.info.get('duration', 100)
                self.frame_durations.append(max(duration, 20))

                # Convert to QPixmap
                data = frame.tobytes("raw", "RGBA")
                qimg = QImage(data, frame.width, frame.height, QImage.Format.Format_RGBA8888)
                self.gif_frames.append(QPixmap.fromImage(qimg.copy()))

            self.total_frames = len(self.gif_frames)
            self.current_frame = 0

            # Update UI
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.frame_slider.setValue(0)
            self.btn_play.setEnabled(True)
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(True)
            self.btn_add_layer.setEnabled(True)
            self.btn_export.setEnabled(True)
            self.kf_bar.total_frames = self.total_frames
            self.size_label.setText(f"{self.gif_width}x{self.gif_height} | {self.total_frames} frames")

            self.canvas.setStyleSheet("background-color: #11111b; border-radius: 8px;")
            self._update_canvas()
            self.statusBar().showMessage(f"Loaded: {os.path.basename(path)}")

        except Exception as e:
            self.statusBar().showMessage(f"Error loading GIF: {e}")

    # ── Playback ──

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
        next_f = (self.current_frame + 1) % self.total_frames
        self.frame_slider.setValue(next_f)
        delay = self.frame_durations[self.current_frame] if self.current_frame < len(self.frame_durations) else 100
        self.play_timer.start(delay)

    def _set_frame(self, frame: int):
        if not self.gif_frames:
            return
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(self.current_frame)
        self.frame_slider.blockSignals(False)
        self.frame_label.setText(f"{self.current_frame + 1} / {self.total_frames}")
        self._update_canvas()
        self._update_props_from_layer()

    def _update_canvas(self):
        if not self.gif_frames:
            return
        self.canvas.set_frame(self.gif_frames[self.current_frame], self.layers, self.current_frame)
        self._update_kf_bar()

    # ── Layers ──

    def _add_layer(self):
        layer = TextLayer()
        # Set initial keyframe with current interpolated position
        kf = TextKeyframe(frame=0, x=0.5, y=0.5)
        layer.keyframes = [kf]
        self.layers.append(layer)
        self._select_layer(layer.id)
        self._rebuild_layer_list()
        self._update_canvas()
        self.statusBar().showMessage(f"Added text layer #{layer.id}")

    def _rebuild_layer_list(self):
        # Clear existing
        while self.layers_container.count():
            item = self.layers_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for layer in self.layers:
            w = LayerWidget(layer)
            w.selected.connect(self._select_layer)
            w.deleted.connect(self._delete_layer)
            w.visibility_changed.connect(self._toggle_layer_vis)
            w.set_selected(self.selected_layer and self.selected_layer.id == layer.id)
            self.layers_container.addWidget(w)

    def _select_layer(self, layer_id: int):
        self.selected_layer = next((l for l in self.layers if l.id == layer_id), None)
        # Update selection visuals
        for i in range(self.layers_container.count()):
            w = self.layers_container.itemAt(i).widget()
            if isinstance(w, LayerWidget):
                w.set_selected(w.layer.id == layer_id)
        self._update_props_from_layer()
        self._update_kf_bar()

    def _delete_layer(self, layer_id: int):
        self.layers = [l for l in self.layers if l.id != layer_id]
        if self.selected_layer and self.selected_layer.id == layer_id:
            self.selected_layer = self.layers[-1] if self.layers else None
        self._rebuild_layer_list()
        self._update_canvas()

    def _toggle_layer_vis(self, layer_id: int, visible: bool):
        for l in self.layers:
            if l.id == layer_id:
                l.visible = visible
        self._update_canvas()

    # ── Properties Sync ──

    def _update_props_from_layer(self):
        """Update property controls from selected layer at current frame."""
        layer = self.selected_layer
        if not layer:
            return

        self._block_signals(True)

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
            f"background-color: {kf.color}; color: {'#000' if QColor(kf.color).lightness() > 128 else '#fff'}; border-radius: 4px;"
        )
        self.btn_outline_color.setStyleSheet(
            f"background-color: {kf.outline_color}; color: {'#000' if QColor(kf.outline_color).lightness() > 128 else '#fff'}; border-radius: 4px;"
        )

        self.pos_label.setText(f"Position: ({kf.x:.2f}, {kf.y:.2f})")

        # Keyframe info
        existing_kf = layer.get_keyframe_at(self.current_frame)
        kf_frames = sorted([k.frame for k in layer.keyframes])
        self.kf_info.setText(
            f"{'[KF SET]' if existing_kf else '[interpolated]'}  |  "
            f"Keyframes: {', '.join(str(f+1) for f in kf_frames)}"
        )

        self._block_signals(False)

    def _block_signals(self, block: bool):
        for w in [self.txt_input, self.spin_size, self.spin_opacity,
                  self.spin_rotation, self.spin_outline, self.font_combo,
                  self.chk_bold, self.chk_italic, self.chk_upper, self.chk_shadow,
                  self.align_combo]:
            w.blockSignals(block)

    def _on_text_changed(self, text):
        if self.selected_layer:
            self.selected_layer.text = text
            # Update layer list label
            for i in range(self.layers_container.count()):
                w = self.layers_container.itemAt(i).widget()
                if isinstance(w, LayerWidget) and w.layer.id == self.selected_layer.id:
                    w.update_label()
            self._update_canvas()

    def _on_font_changed(self, font):
        if self.selected_layer:
            self.selected_layer.font_family = font.family()
            self._update_canvas()

    def _on_style_changed(self):
        if self.selected_layer:
            self.selected_layer.bold = self.chk_bold.isChecked()
            self.selected_layer.italic = self.chk_italic.isChecked()
            self.selected_layer.uppercase = self.chk_upper.isChecked()
            self.selected_layer.shadow = self.chk_shadow.isChecked()
            self._update_canvas()

    def _on_align_changed(self, align):
        if self.selected_layer:
            self.selected_layer.alignment = align
            self._update_canvas()

    def _on_anim_changed(self):
        """When animation properties change, update the current keyframe or interpolated preview."""
        if not self.selected_layer:
            return
        # Just update the canvas preview — actual keyframe set via Set Keyframe button
        self._update_canvas()

    def _on_text_moved(self, rx, ry):
        """Drag handler — immediately updates keyframe at current frame."""
        if not self.selected_layer:
            return

        layer = self.selected_layer
        # Get or create keyframe at current frame
        kf = layer.get_keyframe_at(self.current_frame)
        if kf is None:
            # Auto-create keyframe when dragging
            kf = layer.get_interpolated(self.current_frame)
            kf.frame = self.current_frame
            layer.set_keyframe(kf)

        kf.x = rx
        kf.y = ry
        self.pos_label.setText(f"Position: ({rx:.2f}, {ry:.2f})")
        self._update_canvas()
        self._update_kf_bar()
        self._update_props_from_layer()

    def _pick_color(self, target):
        if not self.selected_layer:
            return
        kf = self.selected_layer.get_interpolated(self.current_frame)
        initial = QColor(kf.color if target == "text" else kf.outline_color)
        color = QColorDialog.getColor(initial, self, f"Pick {target} color")
        if color.isValid():
            # Store color for next keyframe set
            if target == "text":
                self._pending_color = color.name()
                self.btn_color.setStyleSheet(
                    f"background-color: {color.name()}; color: {'#000' if color.lightness() > 128 else '#fff'}; border-radius: 4px;"
                )
            else:
                self._pending_outline_color = color.name()
                self.btn_outline_color.setStyleSheet(
                    f"background-color: {color.name()}; color: {'#000' if color.lightness() > 128 else '#fff'}; border-radius: 4px;"
                )
            self._update_canvas()

    # ── Keyframes ──

    def _set_keyframe(self):
        """Set a keyframe at the current frame with current property values."""
        if not self.selected_layer:
            return

        layer = self.selected_layer
        existing = layer.get_keyframe_at(self.current_frame)
        if existing:
            kf = existing
        else:
            kf = layer.get_interpolated(self.current_frame)
            kf.frame = self.current_frame

        kf.font_size = self.spin_size.value()
        kf.opacity = self.spin_opacity.value()
        kf.rotation = self.spin_rotation.value()
        kf.outline_width = self.spin_outline.value()

        if hasattr(self, '_pending_color'):
            kf.color = self._pending_color
            del self._pending_color
        if hasattr(self, '_pending_outline_color'):
            kf.outline_color = self._pending_outline_color
            del self._pending_outline_color

        layer.set_keyframe(kf)
        self._update_canvas()
        self._update_kf_bar()
        self._update_props_from_layer()
        self.statusBar().showMessage(f"Keyframe set at frame {self.current_frame + 1}")

    def _delete_keyframe(self):
        if not self.selected_layer:
            return
        layer = self.selected_layer
        if layer.get_keyframe_at(self.current_frame):
            layer.remove_keyframe(self.current_frame)
            self._update_canvas()
            self._update_kf_bar()
            self._update_props_from_layer()
            self.statusBar().showMessage(f"Keyframe deleted at frame {self.current_frame + 1}")

    def _update_kf_bar(self):
        if self.selected_layer:
            self.kf_bar.keyframe_positions = [kf.frame for kf in self.selected_layer.keyframes]
        else:
            self.kf_bar.keyframe_positions = []
        self.kf_bar.current_frame = self.current_frame
        self.kf_bar.total_frames = self.total_frames
        self.kf_bar.update()

    # ── Export ──

    def _export_gif(self):
        if not self.gif_pil_frames:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export GIF", "", "GIF Files (*.gif)"
        )
        if not path:
            return

        self.statusBar().showMessage("Exporting...")
        QApplication.processEvents()

        try:
            rendered_frames = []
            for i, pil_frame in enumerate(self.gif_pil_frames):
                frame = pil_frame.copy()
                for layer in self.layers:
                    if not layer.visible:
                        continue
                    frame = self._render_text_pil(frame, layer, i)
                # Convert RGBA to P mode for GIF
                rendered_frames.append(frame)

            # Save as GIF
            if rendered_frames:
                # Convert frames to a format suitable for GIF saving
                output_frames = []
                for frame in rendered_frames:
                    # Create a new image with white background for transparency
                    bg = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                    bg.paste(frame, (0, 0))
                    # Quantize to 256 colors
                    rgb_frame = bg.convert("RGB")
                    output_frames.append(rgb_frame)

                output_frames[0].save(
                    path,
                    save_all=True,
                    append_images=output_frames[1:],
                    duration=self.frame_durations,
                    loop=0,
                    optimize=False
                )

            self.statusBar().showMessage(f"Exported to {os.path.basename(path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Export error: {e}")

    def _render_text_pil(self, frame: Image.Image, layer: TextLayer, frame_idx: int) -> Image.Image:
        """Render text onto a PIL frame."""
        kf = layer.get_interpolated(frame_idx)
        text = layer.text.upper() if layer.uppercase else layer.text
        if not text:
            return frame

        # Create text overlay with alpha
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to get a good font
        font_size = kf.font_size
        font = None
        font_paths = [
            f"C:/Windows/Fonts/{layer.font_family.lower().replace(' ', '')}.ttf",
            f"C:/Windows/Fonts/{layer.font_family.lower().replace(' ', '')}bd.ttf" if layer.bold else None,
            f"C:/Windows/Fonts/{layer.font_family.lower().replace(' ', '')}i.ttf" if layer.italic else None,
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        for fp in font_paths:
            if fp:
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()

        # Calculate position
        lines = text.split('\n')
        line_bboxes = []
        total_h = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            line_bboxes.append((w, h))
            total_h += h

        cx = kf.x * frame.width
        cy = kf.y * frame.height
        y_cursor = cy - total_h / 2

        text_color = tuple(int(kf.color[i:i+2], 16) for i in (1, 3, 5))
        outline_color = tuple(int(kf.outline_color[i:i+2], 16) for i in (1, 3, 5))
        alpha = int(kf.opacity * 255)

        for i, line in enumerate(lines):
            lw, lh = line_bboxes[i]
            if layer.alignment == "center":
                lx = cx - lw / 2
            elif layer.alignment == "left":
                lx = frame.width * 0.1
            else:
                lx = frame.width * 0.9 - lw

            # Draw outline
            if kf.outline_width > 0:
                ow = kf.outline_width
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx * dx + dy * dy <= ow * ow:
                            draw.text((lx + dx, y_cursor + dy), line, font=font,
                                      fill=(*outline_color, alpha))

            # Draw shadow
            if layer.shadow:
                draw.text((lx + 2, y_cursor + 2), line, font=font,
                          fill=(0, 0, 0, alpha // 2))

            # Draw text
            draw.text((lx, y_cursor), line, font=font,
                      fill=(*text_color, alpha))

            y_cursor += lh

        # Handle rotation
        if kf.rotation != 0:
            # Rotate overlay around text center point
            rotated = overlay.rotate(-kf.rotation, center=(cx, cy),
                                     resample=Image.Resampling.BICUBIC, expand=False)
            overlay = rotated

        # Composite
        frame = Image.alpha_composite(frame, overlay)
        return frame


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)

    window = GifTextApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
