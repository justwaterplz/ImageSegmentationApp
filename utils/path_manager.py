import json
import logging
import os
import sys

from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox


class PathManager:
    @staticmethod
    def get_app_data_dir():
        """앱 데이터 저장 디렉토리 경로 반환"""
        app_name = "ImageSegmentTool"

        if sys.platform == 'win32':
            app_data = os.path.join(os.environ['APPDATA'], app_name)
        else:
            # Linux/Mac
            app_data = os.path.join(os.path.expanduser('~'), f'.{app_name}')

        # 디렉토리가 없으면 생성
        if not os.path.exists(app_data):
            os.makedirs(app_data)

        return app_data

    @staticmethod
    def get_config_path():
        """설정 파일 경로 반환"""
        return os.path.join(PathManager.get_app_data_dir(), 'config.json')

    @staticmethod
    def get_log_path():
        """로그 파일 경로 반환"""
        return os.path.join(PathManager.get_app_data_dir(), 'image_processor.log')
