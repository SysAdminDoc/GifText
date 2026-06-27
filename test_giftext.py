#!/usr/bin/env python3

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from GifText import (
    GifTextApp,
    TextKeyframe,
    TextLayer,
    build_path_keyframes,
    sample_cubic_path,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication


class PathAnimationTests(unittest.TestCase):
    def test_cubic_path_samples_endpoints_and_midpoint(self):
        points = [(0.1, 0.2), (0.3, 0.0), (0.8, 1.0), (0.9, 0.7)]

        self.assertEqual(sample_cubic_path(points, 0.0), (0.1, 0.2))
        self.assertEqual(sample_cubic_path(points, 1.0), (0.9, 0.7))

        mid_x, mid_y = sample_cubic_path(points, 0.5)
        self.assertGreater(mid_x, 0.1)
        self.assertLess(mid_x, 0.9)
        self.assertGreater(mid_y, 0.2)
        self.assertLess(mid_y, 0.7)

    def test_path_keyframes_preserve_non_position_properties(self):
        layer = TextLayer("path")
        layer.keyframes = [
            TextKeyframe(frame=0, x=0.0, y=0.0, font_size=40, opacity=0.5, rotation=15.0),
            TextKeyframe(frame=3, x=1.0, y=1.0, font_size=80, opacity=1.0, rotation=45.0),
        ]
        points = [(0.0, 0.25), (0.25, 0.0), (0.75, 1.0), (1.0, 0.75)]

        keyframes = build_path_keyframes(layer, points, start_frame=0, frame_count=4)

        self.assertEqual([kf.frame for kf in keyframes], [0, 1, 2, 3])
        self.assertEqual((keyframes[0].x, keyframes[0].y), (0.0, 0.25))
        self.assertEqual((keyframes[-1].x, keyframes[-1].y), (1.0, 0.75))
        self.assertEqual(keyframes[0].font_size, 40)
        self.assertEqual(keyframes[-1].font_size, 80)
        self.assertAlmostEqual(keyframes[-1].rotation, 45.0)

    def test_layer_path_metadata_round_trips(self):
        layer = TextLayer("round trip")
        layer.path_points = [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6), (0.7, 0.8)]
        layer.path_start_frame = 2
        layer.path_end_frame = 12

        restored = TextLayer.from_dict(layer.to_dict())

        self.assertEqual(restored.path_points, layer.path_points)
        self.assertEqual(restored.path_start_frame, 2)
        self.assertEqual(restored.path_end_frame, 12)


class PathAnimationAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_finish_path_capture_generates_editable_layer_keyframes(self):
        window = GifTextApp()
        frames = [QPixmap(16, 16) for _ in range(5)]
        layer = TextLayer("app path")
        window.gif_frames = frames
        window.total_frames = len(frames)
        window.current_frame = 1
        window.layers = [layer]
        window.selected_layer = layer
        window.path_capture_layer_id = layer.id
        window.spin_path_span.setValue(3)

        window._finish_path_capture([(0.1, 0.1), (0.2, 0.0), (0.8, 1.0), (0.9, 0.9)])

        self.assertEqual(layer.path_start_frame, 1)
        self.assertEqual(layer.path_end_frame, 3)
        self.assertEqual([kf.frame for kf in sorted(layer.keyframes, key=lambda k: k.frame)], [0, 1, 2, 3])
        self.assertEqual((layer.get_keyframe_at(1).x, layer.get_keyframe_at(1).y), (0.1, 0.1))
        self.assertEqual((layer.get_keyframe_at(3).x, layer.get_keyframe_at(3).y), (0.9, 0.9))
        window.close()


if __name__ == "__main__":
    unittest.main()
