import sys
import cv2
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import QApplication
from simplegif.ui.app import GifConverterApp

sys.stdout.reconfigure(encoding="utf-8")

app = QApplication.instance() or QApplication([])

vid_path = Path("test_debug.mp4")
out = cv2.VideoWriter(str(vid_path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (120, 90))
for i in range(100):
    img = np.zeros((90, 120, 3), dtype=np.uint8)
    out.write(img)
out.release()

win = GifConverterApp()
win.load_video_file(vid_path)

print("Inicial:")
print("  Estimativa:", win.lbl_size_estimate.text())
print("  Range frames:", win.screen_options.video_preview.get_selected_range_frames())
print("  Range time:", win.screen_options.video_preview.get_selected_time_range())

# Simular arraste de slider
win.screen_options.video_preview.range_slider.set_values(50, 99, emit_signals=True)
print("\nApos slider set_values(50, 99):")
print("  Estimativa:", win.lbl_size_estimate.text())
print("  Range frames:", win.screen_options.video_preview.get_selected_range_frames())
print("  Range time:", win.screen_options.video_preview.get_selected_time_range())

# Simular arraste pelo mouse no slider
slider = win.screen_options.video_preview.range_slider
slider._active_handle = "start"
slider._update_from_mouse(slider._value_to_x(70))
print("\nApos _update_from_mouse start para 70:")
print("  Estimativa:", win.lbl_size_estimate.text())
print("  Range frames:", win.screen_options.video_preview.get_selected_range_frames())
print("  Range time:", win.screen_options.video_preview.get_selected_time_range())

# Simular mudança de spinbox
win.screen_options.video_preview.spin_start_time.setValue(8.0)
win.screen_options.video_preview.spin_end_time.setValue(9.0)
print("\nApos spinbox 8.0 a 9.0:")
print("  Estimativa:", win.lbl_size_estimate.text())
print("  Range frames:", win.screen_options.video_preview.get_selected_range_frames())
print("  Range time:", win.screen_options.video_preview.get_selected_time_range())

vid_path.unlink()
