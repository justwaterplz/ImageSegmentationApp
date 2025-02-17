import logging
from io import BytesIO

import requests
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QProgressBar, QMessageBox, QScrollArea, QFileDialog,
                             QSizePolicy)
from PyQt5.QtCore import Qt

from core.services.image_processor import ImageProcessor
from core.widget.file_list_widget import FileListWidget
from core.services.file_operations import FileOperations
from utils.path_manager import PathManager

import os

class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()

        self.setWindowTitle("Image Segment Tool")
        self.setMinimumSize(1600, 900)

        self.file_ops = FileOperations(self, None)
        # Config file setup
        self.config_file = "config.json"

        # Main widget setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Create panels
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)  # 1:2 ratio
        main_layout.addWidget(right_panel, 2)

        # Initialize file operations
        self.file_ops = FileOperations(self, self.config_file)
        self.file_ops.widget_file_list = self.file_list_widget

        self.image_processor = ImageProcessor(self)
        self.processed_files = [] # 처리된 이미지
        # Setup connections
        self.setup_connections()

    def create_left_panel(self):
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # File load button
        self.load_btn = QPushButton("파일 불러오기")
        self.load_btn.setStyleSheet("""
            QPushButton {
                min-height: 6px;
            }
        """)
        left_layout.addWidget(self.load_btn)

        # File list widget
        self.file_list_widget = FileListWidget()
        left_layout.addWidget(self.file_list_widget.get_container())  # get_container() 메서드 사용

        return left_panel

    def create_right_panel(self):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(20)  # 위젯 간 간격 증가

        # Image viewer container
        viewer_container = QWidget()
        viewer_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)  # 수직 크기 정책 변경
        viewer_container.setStyleSheet("""
            QWidget {
                background-color: #e0e0e0;
                border-radius: 5px;
            }
        """)
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setSpacing(10)

        # Image display area
        image_container = QWidget()
        image_container.setFixedSize(650, 650)
        image_container.setStyleSheet("""
            QWidget {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
            }
        """)
        image_layout = QVBoxLayout(image_container)

        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_preview)
        viewer_layout.addWidget(image_container, alignment=Qt.AlignHCenter)

        # Navigation bar
        nav_bar = QWidget()
        nav_bar.setFixedHeight(40)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(10, 0, 10, 0)

        nav_button_style = """
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
        """

        self.prev_btn = QPushButton("이전")
        self.next_btn = QPushButton("다음")
        self.page_label = QLabel("0/0")
        self.remove_btn = QPushButton("제거")

        self.prev_btn.setStyleSheet(nav_button_style)
        self.next_btn.setStyleSheet(nav_button_style)
        self.remove_btn.setStyleSheet(nav_button_style)
        self.page_label.setStyleSheet("color: #333333; font-weight: bold;")

        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)

        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.remove_btn)
        nav_layout.addStretch()

        viewer_layout.addWidget(nav_bar)
        right_layout.addWidget(viewer_container)

        # Control panel
        control_panel = QWidget()
        control_panel.setFixedHeight(100)  # 컨트롤 패널 높이 고정
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Horizontal button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)

        control_button_style = """
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 10px;
                min-height: 30px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
        """

        self.process_btn = QPushButton("이미지 전송")
        self.download_all_btn = QPushButton("전체 이미지 다운로드")
        self.download_current_btn = QPushButton("현재 이미지 다운로드")

        self.process_btn.setStyleSheet(control_button_style)
        self.download_all_btn.setStyleSheet(control_button_style)
        self.download_current_btn.setStyleSheet(control_button_style)

        self.download_all_btn.setEnabled(False)
        self.download_current_btn.setEnabled(False)

        # Add buttons horizontally
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.download_current_btn)
        button_layout.addWidget(self.download_all_btn)

        control_layout.addWidget(button_container)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
            }
        """)

        control_layout.addWidget(self.progress_bar)
        right_layout.addWidget(control_panel)

        # 연결 및 초기화
        self.processed_images = []
        self.current_index = -1

        self.prev_btn.clicked.connect(self.show_previous_image)
        self.next_btn.clicked.connect(self.show_next_image)
        self.download_current_btn.clicked.connect(self.download_current_image)
        self.download_all_btn.clicked.connect(self.download_all_images)

        return right_panel

    def create_image_item(self, original_path, result_url):
        """개별 이미지 아이템 위젯 생성"""
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)

        # 이미지 표시
        image_label = QLabel()
        response = requests.get(result_url)
        img_data = BytesIO(response.content)
        pixmap = QPixmap()
        pixmap.loadFromData(img_data.getvalue())
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)

        # 파일명과 다운로드 버튼을 위한 컨테이너
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)

        filename_label = QLabel(os.path.basename(original_path))
        download_btn = QPushButton("다운로드")
        download_btn.clicked.connect(lambda: self.download_image(result_url))

        info_layout.addWidget(filename_label)
        info_layout.addWidget(download_btn)

        item_layout.addWidget(image_label)
        item_layout.addWidget(info_widget)

        return item_widget

    def setup_connections(self):

        # File operations
        self.load_btn.clicked.connect(self.file_ops.load_files)
        self.file_list_widget.file_clicked.connect(self.show_preview)

        # Process button - explicitly connect to process_selected_images
        self.process_btn.clicked.connect(self.process_selected_images)

        # Image processor signals
        self.image_processor.progress_updated.connect(self.update_progress)
        self.image_processor.error_occurred.connect(self.handle_error)
        self.image_processor.process_finished.connect(self.handle_process_complete)
        self.image_processor.image_processed.connect(self.handle_processed_image)
        self.remove_btn.clicked.connect(self.remove_current_result)

    def process_selected_images(self):
        """Called when the process button is clicked"""

        # Get selected files
        files_to_process = self.file_ops.get_selected_files()

        if not files_to_process:
            QMessageBox.warning(self, "경고", "처리할 이미지를 선택해주세요.")
            return

        # Start processing with ImageProcessor
        try:
            self.image_processor.send_selected_images(files_to_process)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"이미지 처리 시작 중 오류가 발생했습니다: {str(e)}")

    def update_progress(self, value):
        # """진행 상태 업데이트"""
        # self.progress_bar.setValue(value)
        # # 100%에 도달하면 리셋 예약
        # if value >= 100:
        #     def reset_progress():
        #         self.progress_bar.setValue(0)
        #
        #     from PyQt5.QtCore import QTimer
        #     QTimer.singleShot(500, reset_progress)
        """진행 상태 업데이트"""
        self.progress_bar.setValue(value)

    def show_preview(self, file_path, mode):
        if mode == "preview":
            self.preview_label.setText(f"Selected: {os.path.basename(file_path)}")

    def handle_error(self, error_message):
        QMessageBox.critical(self, "오류", error_message)

    def handle_process_complete(self):
        """모든 이미지 처리가 완료된 후 호출"""
        for file_path in self.processed_files:
            for row in range(self.file_list_widget.rowCount()):
                widget = self.file_list_widget.cellWidget(row, 0)
                if widget and widget.property("file_path") == file_path:
                    self.file_list_widget.removeRow(row)
                    break

        self.processed_files = []

        # progress bar 리셋
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, lambda: self.progress_bar.setValue(0))

    def handle_processed_image(self, file_path, result_data):
        """처리된 이미지 결과 추가"""
        try:
            if isinstance(result_data, dict) and 'results' in result_data and result_data['results']:
                result = result_data['results'][0]
                if result.get('result_images'):
                    image_url = result['result_images'][0]['image']
                    self.processed_images.append((file_path, image_url))
                    self.processed_files.append(file_path)  # 추가: 처리된 파일 경로 기록

                    # 첫 이미지인 경우 표시
                    if len(self.processed_images) == 1:
                        self.current_index = 0
                        self.show_current_image()

                    # 현재 페이지 레이블 업데이트
                    self.update_page_label()

                    # 버튼 상태 업데이트
                    self.update_navigation_buttons()
                    self.download_all_btn.setEnabled(True)
                    self.download_current_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"이미지 처리 결과 표시 중 오류 발생: {str(e)}")

    def update_page_label(self):
        """페이지 레이블 업데이트"""
        total_images = len(self.processed_images)
        current_page = self.current_index + 1 if self.current_index >= 0 else 0
        self.page_label.setText(f"{current_page}/{total_images}")

    def show_current_image(self):
        if 0 <= self.current_index < len(self.processed_images):
            _, image_url = self.processed_images[self.current_index]

            response = requests.get(image_url)
            img_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data.getvalue())

            # Scale image while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(780, 780, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_preview.setPixmap(scaled_pixmap)

            # 페이지 레이블 업데이트를 별도 함수로 분리
            self.update_page_label()
            self.remove_btn.setEnabled(True)

    def show_previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
            self.update_navigation_buttons()

    def show_next_image(self):
        if self.current_index < len(self.processed_images) - 1:
            self.current_index += 1
            self.show_current_image()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.processed_images) - 1)

    def download_current_image(self):
        if 0 <= self.current_index < len(self.processed_images):
            file_path, image_url = self.processed_images[self.current_index]
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            suggested_name = f"{base_name}_result.png"

            save_path, _ = QFileDialog.getSaveFileName(
                self, "이미지 저장",
                os.path.join(os.path.expanduser("~"), "Downloads", suggested_name),
                "Images (*.png *.jpg)"
            )

            if save_path:
                self.download_image(image_url, save_path)

    def download_all_images(self):
        if not self.processed_images:
            return

        # 저장할 디렉토리 선택
        dir_path = QFileDialog.getExistingDirectory(
            self, "저장할 폴더 선택",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )

        if dir_path:
            try:
                for idx, (file_path, image_url) in enumerate(self.processed_images):
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    save_path = os.path.join(dir_path, f"{base_name}_result.png")
                    self.download_image(image_url, save_path)

                    # Update progress
                    progress = int(((idx + 1) / len(self.processed_images)) * 100)
                    self.progress_bar.setValue(progress)

                QMessageBox.information(self, "완료", f"모든 이미지가 저장되었습니다.\n저장 위치: {dir_path}")
                self.progress_bar.setValue(0)

            except Exception as e:
                QMessageBox.critical(self, "오류", f"이미지 저장 중 오류 발생: {str(e)}")

    def download_image(self, url, save_path):
        try:
            response = requests.get(url)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                f.write(response.content)

        except Exception as e:
            raise Exception(f"다운로드 중 오류 발생: {str(e)}")

    def remove_current_result(self):
        if 0 <= self.current_index < len(self.processed_images):
            # 현재 이미지 정보 저장
            removed_image = self.processed_images.pop(self.current_index)

            # 이미지가 더 있는 경우
            if self.processed_images:
                if self.current_index >= len(self.processed_images):
                    # 마지막 이미지였다면 이전 이미지로
                    self.current_index = len(self.processed_images) - 1
                self.show_current_image()
            else:
                # 모든 이미지가 제거된 경우
                self.current_index = -1
                self.image_preview.clear()
                self.page_label.setText("0/0")
                self.download_current_btn.setEnabled(False)
                self.download_all_btn.setEnabled(False)
                self.remove_btn.setEnabled(False)

            # 네비게이션 버튼 상태 업데이트
            self.update_navigation_buttons()
