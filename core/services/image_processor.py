# core/services/image_processor.py
import logging
import traceback

from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from core.dialog.parameter_input_dialog import ParameterInputDialog
from utils.worker_thread import WorkerThread
import os

class ImageProcessor(QObject):
    progress_updated = pyqtSignal(int)
    process_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    image_processed = pyqtSignal(str, dict)

    def __init__(self, main_ui):
        super().__init__()
        self.main_ui = main_ui
        self.progress = None
        self.worker = None
        # self.api_url = "http://mldinos.sogang.ac.kr:58888/image/"
        self.api_url = "http://172.16.6.92:58888/image/"

    def send_selected_images(self, selected_files):
        try:
            if not selected_files:
                self.error_occurred.emit("선택된 파일이 없습니다.")
                return

            # Show parameter input dialog
            param_dialog = ParameterInputDialog(self.main_ui)
            if param_dialog.exec_() != ParameterInputDialog.Accepted:
                return

            parameters = param_dialog.get_parameters()
            self.setup_progress_dialog()

            # Initialize and start worker thread with parameters
            self.worker = WorkerThread(selected_files, self.api_url, parameters)
            self.worker.progress.connect(self.update_progress)
            self.worker.result.connect(self.handle_single_result)
            self.worker.finished.connect(self.process_results)
            self.worker.error.connect(self.handle_error)

            self.worker.start()

        except Exception as e:
            error_msg = f"이미지 전송 준비 중 오류가 발생했습니다: {str(e)}"
            self.error_occurred.emit(error_msg)
            QMessageBox.critical(self.main_ui, "오류", error_msg)

    def setup_progress_dialog(self):
        self.progress = QProgressDialog("이미지 처리 중...", "취소", 0, 100, self.main_ui)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setWindowTitle("처리 진행 상황")
        self.progress.setAutoReset(False)
        self.progress.setAutoClose(False)
        self.progress.setValue(0)
        self.progress.canceled.connect(self.cancel_processing)
        self.progress.show()

    def handle_single_result(self, result):
        try:
            file_path, result_data = result

            self.image_processed.emit(file_path, result_data)

        except Exception as e:
            self.error_occurred.emit(f"결과 처리 중 오류 발생: {str(e)}")

    def process_results(self, results):
        try:
            if not results:
                QMessageBox.warning(self.main_ui, "경고", "처리된 결과가 없습니다.")
                return

            successful_count = len(results)
            QMessageBox.information(
                self.main_ui,
                "완료",
                f"{successful_count}개의 이미지가 처리되었습니다."
            )

            self.process_finished.emit()

        except Exception as e:
            error_msg = f"결과 처리 중 오류가 발생했습니다: {str(e)}"
            self.error_occurred.emit(error_msg)
            QMessageBox.critical(self.main_ui, "오류", error_msg)

        finally:
            if self.progress:
                self.progress.cancel()
                self.progress = None

    def cancel_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.error_occurred.emit("처리가 사용자에 의해 취소되었습니다.")

    def update_progress(self, value):
        if self.progress is not None:
            self.progress.setValue(value)
        self.progress_updated.emit(value)

    def handle_error(self, error_message):
        self.error_occurred.emit(f"처리 중 오류 발생: {error_message}")