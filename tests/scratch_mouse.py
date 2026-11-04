import sys
import cv2
import numpy as np
from pathlib import Path
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication
from simplegif.ui.app import GifConverterApp

sys.stdout.reconfigure(encoding="utf-8")

app = QApplication.instance() or QApplication([])

vid_path = Path("test_mouse.mp4")
out = cv2.VideoWriter(str(vid_path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (120, 90))
for i in range(100):
    img = np.zeros((90, 120, 3), dtype=np.uint8)
    out.write(img)
out.release()

win = GifConverterApp()
win.show() # to ensure layout geometry is calculated
win.load_video_file(vid_path)

print("Inicial:")
print("  Label:", win.lbl_size_estimate.text())
print("  Range frames:", win.screen_options.video_preview.get_selected_range_frames())

slider = win.screen_options.video_preview.range_slider
w = slider.width()
h = slider.height()
print(f"Slider width={w}, height={h}")

# User clicks near the right end (to drag end handle)
# end_x is around w - 10
end_handle_x = slider._value_to_x(slider.end_value())
print(f"End handle x={end_handle_x}")

press_event = QMouseEvent(
    QMouseEvent.Type.MouseButtonPress,
    QPointF(end_handle_x, h / 2),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
slider.mousePressEvent(press_event)
print(f"Active handle after press on end: {slider._active_handle}")

# User drags to the middle
move_event = QMouseEvent(
    QMouseEvent.Type.MouseMove,
    QPointF(w / 2, h / 2),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
slider.mouseMoveEvent(move_event)
print("Apos mouse drag para o meio:")
print("  Label:", win.lbl_size_estimate.text())
print("  Range frames:", win.screen_options.video_preview.get_selected_range_frames())

release_event = QMouseEvent(
    QMouseEvent.Type.MouseButtonRelease,
    QPointF(w / 2, h / 2),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.NoButton,
    Qt.KeyboardModifier.NoModifier
)
slider.mouseReleaseEvent(release_event)

win.preview_controller.close()
win.close()
vid_path.unlink()
