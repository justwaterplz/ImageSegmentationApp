from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView,
                             QCheckBox, QLabel, QHBoxLayout, QAbstractItemView,
                             QTableWidgetSelectionRange, QMessageBox, QMenu, QAction, QPushButton, QProgressDialog,
                             QApplication)
from PyQt5.QtGui import QIcon, QPixmap, QColor, QImage, QCursor
from PyQt5.QtCore import Qt, QFileInfo, QSize, pyqtSignal, QThreadPool
from core.services.load_image_worker import LoadImageWorker
import os
import sys
import subprocess


class FileListWidget(QTableWidget):
    file_clicked = pyqtSignal(str, str)
    files_selected = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        self.allowed_formats = {'.jpg', '.jpeg', '.png', '.bmp'}
        self.thumbnail_size = QSize(100, 100)
        self.all_selected = False

        self.thread_pool = QThreadPool()
        self.current_worker = None

        # 프로그레스 다이얼로그 초기화
        self.progress_dialog = None

    def setup_ui(self):
        # 테이블 기본 설정
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(['이미지'])
        self.verticalHeader().setDefaultSectionSize(60)
        self.setShowGrid(False)

        # 스타일 설정
        self.setStyleSheet("""  
            QTableWidget {
                background-color: white;
                selection-background-color: #d0d0d0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 1px;
                border: 1px solid #d0d0d0;
                border-bottom: 2px solid #a0a0a0;
            }
            QTableWidget::item {
                border-bottom: 1px solid #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #14cee3
            }
            QTableWidget::item:selected:!active {
                background-color: #14cee3;
                color: black;
            }
        """)

        # 헤더 설정
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)

        # 스크롤바 설정
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 선택 모드 설정
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # 전체 선택 버튼을 위한 컨테이너 위젯 생성
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        # 테이블 위젯을 컨테이너에 추가
        self.container_layout.addWidget(self)

        # 전체 선택 버튼 추가
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.setEnabled(False)  # 초기에 비활성화
        self.container_layout.addWidget(self.select_all_btn)

    def get_container(self):
        return self.container

    def setup_connections(self):
        self.cellClicked.connect(self.on_item_clicked)
        self.cellDoubleClicked.connect(self.open_image_doubleclick)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.select_all_btn.clicked.connect(self.toggle_select_all)

    # image upload 관련 함수
    def cancel_loading(self):
        if self.current_worker:
            self.current_worker.stop()
        self.progress_dialog = None

    def update_progress(self, value):
        if self.progress_dialog and not self.progress_dialog.wasCanceled():
            self.progress_dialog.setValue(value)

    def loading_finished(self):
        if self.progress_dialog:
            self.progress_dialog.close()
        self.progress_dialog = None
        self.select_all_btn.setEnabled(self.rowCount() > 0)
        self.viewport().update()

    def loading_error(self, error_msg):
        if self.progress_dialog:
            self.progress_dialog.close()
        self.progress_dialog = None
        QMessageBox.warning(self, "오류", f"이미지 로딩 중 오류가 발생했습니다: {error_msg}")

    def add_file_to_list(self, file_paths):
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        # 유효한 파일만 필터링
        valid_files = [f for f in file_paths if self.is_allowed_format(f)]

        if not valid_files:
            return

        # 프로그레스 다이얼로그 설정
        self.progress_dialog = QProgressDialog("이미지 로딩 중...", "취소", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(500)
        self.progress_dialog.canceled.connect(self.cancel_loading)

        # 워커 생성 및 시그널 연결
        worker = LoadImageWorker(valid_files, self.thumbnail_size)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.image_loaded.connect(self.add_single_image)
        worker.signals.finished.connect(self.loading_finished)
        worker.signals.error.connect(self.loading_error)

        self.current_worker = worker
        self.thread_pool.start(worker)

    def add_single_image(self, file_path, thumbnail):
        try:
            row_position = self.rowCount()
            self.insertRow(row_position)

            widget = self.create_item_widget_with_thumbnail(file_path, thumbnail)
            self.setCellWidget(row_position, 0, widget)

        except Exception as e:
            print(f"Error adding image to list: {str(e)}")
            if self.rowCount() > row_position:
                self.removeRow(row_position)

    def create_item_widget_with_thumbnail(self, file_path, thumbnail):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)

        checkbox = QCheckBox()
        checkbox.stateChanged.connect(
            lambda state: self.on_checkbox_changed(state, self.indexAt(widget.pos()).row()))
        layout.addWidget(checkbox)

        icon_label = QLabel()
        icon_label.setPixmap(QPixmap.fromImage(thumbnail))
        layout.addWidget(icon_label)

        file_name_label = QLabel(os.path.basename(file_path))
        file_name_label.setStyleSheet("padding-left: 5px;")
        layout.addWidget(file_name_label)

        widget.setProperty("file_path", file_path)
        layout.addStretch()

        return widget

    def clear(self):
        self.setRowCount(0)
        self.clearSelection()
        self.viewport().update()
        # 리스트가 비워지면 전체 선택 버튼 비활성화
        self.select_all_btn.setEnabled(False)
        self.all_selected = False
        self.select_all_btn.setText("전체 선택")

    def create_item_widget(self, file_path):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)

        # 체크박스 추가
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(
            lambda state: self.on_checkbox_changed(state, self.indexAt(widget.pos()).row()))
        layout.addWidget(checkbox)

        # 썸네일 이미지
        icon_label = QLabel()
        try:
            thumbnail = self.create_thumbnail(file_path)
            icon_label.setPixmap(thumbnail)
        except Exception as e:
            print(f"썸네일 생성 실패: {str(e)}")
            icon_label.setPixmap(QIcon().pixmap(24, 24))
        layout.addWidget(icon_label)

        # 파일명 라벨
        file_name_label = QLabel(os.path.basename(file_path))
        file_name_label.setStyleSheet("padding-left: 5px;")
        layout.addWidget(file_name_label)

        widget.setProperty("file_path", file_path)
        layout.addStretch()

        return widget

    def create_thumbnail(self, file_path):
        try:
            image = QImage(file_path)
            if image.isNull():
                raise Exception("이미지를 불러올 수 없습니다")

            # 이미지 크기가 너무 크면 축소
            if image.width() > 1000 or image.height() > 1000:
                image = image.scaled(1000, 1000, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            thumbnail = image.scaled(self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            return QPixmap.fromImage(thumbnail)
        except Exception as e:
            print(f"썸네일 생성 실패: {str(e)}")
            return QIcon().pixmap(self.thumbnail_size)
        finally:
            # 명시적으로 리소스 해제
            image = None

    def is_allowed_format(self, file_path):
        _, file_format = os.path.splitext(file_path)
        return file_format.lower() in self.allowed_formats

    def on_item_clicked(self, row, column):
        widget = self.cellWidget(row, column)
        if widget:
            checkbox = widget.layout().itemAt(0).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(not checkbox.isChecked())

    def on_checkbox_changed(self, state, row):
        self.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, 0), state == Qt.Checked)
        color = QColor('#d0d0d0') if state == Qt.Checked else QColor('white')
        self.cellWidget(row, 0).setStyleSheet(f"background-color: {color.name()};")
        self.files_selected.emit(self.get_selected_files())

    def get_selected_files(self):
        selected_files = []
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if checkbox.isChecked():
                    file_path = widget.property("file_path")
                    selected_files.append(file_path)
        return selected_files

    def clear(self):
        self.setRowCount(0)
        self.clearSelection()
        self.viewport().update()

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        delete_action = QAction("삭제", self)
        delete_action.triggered.connect(self.delete_selected_items)
        context_menu.addAction(delete_action)
        context_menu.exec_(QCursor.pos())

    def delete_selected_items(self):
        selected_rows = set(index.row() for index in self.selectedIndexes())
        if not selected_rows:
            QMessageBox.information(self, "알림", "삭제할 항목을 선택해주세요.")
            return

        total_rows = len(selected_rows)
        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"선택한 {total_rows}개의 항목을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # 역순으로 정렬하여 삭제 (인덱스 변화 방지)
        for row in sorted(selected_rows, reverse=True):
            self.removeRow(row)

        self.clearSelection()
        QMessageBox.information(self, "삭제 완료", f"{total_rows}개의 항목이 삭제되었습니다.")
        print(f"삭제 후 테이블 총 행 수: {self.rowCount()}")

        # 리스트가 비었을 때 전체 선택 버튼 상태 업데이트
        if self.rowCount() == 0:
            self.select_all_btn.setEnabled(False)
            self.all_selected = False
            self.select_all_btn.setText("전체 선택")

    def toggle_select_all(self):
        if self.rowCount() == 0:  # 안전 검사 추가
            self.select_all_btn.setEnabled(False)
            return

        self.all_selected = not self.all_selected
        self.select_all_btn.setText("전체 해제" if self.all_selected else "전체 선택")

        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(self.all_selected)

    def open_image_doubleclick(self, row, column):
        widget = self.cellWidget(row, column)
        if widget:
            file_path = widget.property("file_path")
            if file_path:
                try:
                    if sys.platform == 'win32':
                        os.startfile(file_path)
                    elif sys.platform == 'darwin':
                        subprocess.call(['open', file_path])
                    else:
                        subprocess.call(['xdg-open', file_path])
                except Exception as e:
                    print(f"파일 열기 실패: {str(e)}")