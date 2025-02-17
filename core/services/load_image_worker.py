from PyQt5.QtCore import QThread, pyqtSignal, QRunnable, QThreadPool, Qt, QObject
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QProgressDialog, QApplication
import os

class LoadImageWorker(QRunnable):
    class Signals(QObject):
        progress = pyqtSignal(int)
        finished = pyqtSignal()
        error = pyqtSignal(str)
        image_loaded = pyqtSignal(str, QImage)

    def __init__(self, file_paths, thumbnail_size):
        super().__init__()
        self.signals = self.Signals()
        self.file_paths = file_paths
        self.thumbnail_size = thumbnail_size
        self.is_running = True

    def run(self):
        try:
            total = len(self.file_paths)
            for i, file_path in enumerate(self.file_paths):
                if not self.is_running:
                    break

                try:
                    image = QImage(file_path)
                    if not image.isNull():
                        if image.width() > 1000 or image.height() > 1000:
                            image = image.scaled(1000, 1000, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                        thumbnail = image.scaled(self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.signals.image_loaded.emit(file_path, thumbnail)

                    self.signals.progress.emit(int((i + 1) * 100 / total))
                except Exception as e:
                    print(f"Error processing image {file_path}: {str(e)}")

            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

    def stop(self):
        self.is_running = False