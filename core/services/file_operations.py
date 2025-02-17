import os
import sys
import json
from PyQt5.QtWidgets import QFileDialog, QVBoxLayout, QWidget, QMessageBox
from utils.path_manager import PathManager

# from core.widget.file_list_widget import FileListWidget
# 파일 관련 기능들을 묶어 코드 분할한다.
class FileOperations:
    def __init__(self, parent_widget: QWidget, config_file: str):
        self.parent_widget = parent_widget
        self.widget_file_list = None

        # 앱 데이터 디렉토리 설정
        self.app_data_dir = self.get_app_data_dir()
        self.config_file = os.path.join(self.app_data_dir, 'config.json')

        # 초기 디렉토리 로드
        self.load_dir = self.load_directory()

    def load_files(self, traceback=None):
        try:
            # 파일 선택 다이얼로그 표시
            supported_file_format = ["jpg", "jpeg", "png", "bmp"]
            image_filter = "Images (" + " ".join([f"*.{fmt}" for fmt in supported_file_format]) + ")"
            file_names, _ = QFileDialog.getOpenFileNames(self.parent_widget, "파일 열기", self.load_dir, image_filter)

            if file_names:
                # 선택된 파일이 너무 많은 경우 경고
                if len(file_names) > 100:
                    reply = QMessageBox.warning(
                        self.parent_widget,
                        "경고",
                        f"총 {len(file_names)}개의 파일을 로드하려고 합니다. 계속하시겠습니까?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return

                # 파일 리스트에 추가
                try:
                    self.widget_file_list.add_file_to_list(file_names)
                except Exception as e:
                    QMessageBox.critical(
                        self.parent_widget,
                        "오류",
                        f"파일 로딩 중 오류가 발생했습니다: {str(e)}"
                    )
                    return

                # 마지막으로 선택한 디렉토리 저장
                new_directory = os.path.dirname(file_names[-1])
                self.save_directory(new_directory)
                self.load_dir = new_directory

        except Exception as e:
            QMessageBox.critical(
                self.parent_widget,
                "오류",
                f"파일 로드 중 오류가 발생했습니다: {str(e)}"
            )

    def load_directory(self):
        try:
            # 기본 다운로드 폴더 경로 설정
            default_dir = os.path.join(os.path.expanduser('~'), 'Downloads')

            if not os.path.exists(self.config_file):
                # 설정 파일이 없으면 기본값으로 생성
                self.save_directory(default_dir)
                return default_dir

            with open(self.config_file, 'r', encoding='utf-8') as f:
                try:
                    config = json.load(f)
                    saved_dir = config.get('load_dir', '')

                    # 저장된 디렉토리가 존재하는지 확인
                    if saved_dir and os.path.exists(saved_dir):
                        return saved_dir
                    else:
                        # 저장된 디렉토리가 없거나 존재하지 않으면 기본값 사용
                        self.save_directory(default_dir)
                        return default_dir

                except json.JSONDecodeError:
                    # JSON 파싱 에러시 파일 새로 생성
                    self.save_directory(default_dir)
                    return default_dir

        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {str(e)}")
            return os.path.join(os.path.expanduser('~'), 'Downloads')

    def save_directory(self, directory):
        try:
            # 디렉토리가 실제로 존재하는지 확인
            if not os.path.exists(directory):
                print(f"경고: 존재하지 않는 디렉토리입니다 - {directory}")
                return

            # 설정 파일 디렉토리가 없으면 생성
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)

            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    # JSON 파싱 에러시 새로운 설정으로 덮어쓰기
                    pass

            config['load_dir'] = directory

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"디렉토리 저장 중 오류 발생: {str(e)}")
            # 에러 발생시에도 계속 진행할 수 있도록 함

    def get_selected_files(self):
        try:
            return self.widget_file_list.get_selected_files()
        except Exception as e:
            print(f"선택된 파일 가져오기 실패: {str(e)}")
            return []

    def clear_file_list(self):
        try:
            self.widget_file_list.clear()
        except Exception as e:
            print(f"파일 리스트 초기화 실패: {str(e)}")

    # config.json 생성 위치 수정
    @staticmethod
    def get_app_data_dir():
        """앱 데이터 저장 디렉토리 경로 반환"""
        app_name = "ImageSegmentTool"

        if sys.platform == 'win32':
            app_data = os.path.join(os.environ['APPDATA'], app_name)
        else:
            # Linux/Mac의 경우
            app_data = os.path.join(os.path.expanduser('~'), f'.{app_name}')

        # 디렉토리가 없으면 생성
        if not os.path.exists(app_data):
            os.makedirs(app_data)

        return app_data

    def get_config_path(self):
        """설정 파일 경로 반환"""
        return os.path.join(self.get_app_data_dir(), 'config.json')
