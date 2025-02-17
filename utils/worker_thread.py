# core/services/worker_thread.py

from PyQt5.QtCore import QThread, pyqtSignal
import requests
import logging
import os
import time
import json
from typing import List, Dict


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(tuple)  # (file_path, response)
    finished = pyqtSignal(list)  # List of (file_path, response) tuples
    error = pyqtSignal(str)

    def __init__(self, image_files: List[str], api_url: str, parameters: Dict):
        super().__init__()
        self.image_files = image_files
        self.api_url = api_url
        self.parameters = parameters
        self.results = []
        self._is_running = True

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def wait_for_result(self, session, token, max_retries=30):
        """이미지 처리 결과를 기다림"""
        for i in range(max_retries):
            try:
                response = session.get(f"{self.api_url}{token}")
                response.raise_for_status()
                result = response.json()

                self.logger.info(f"Polling result: {result}")

                # API 응답 구조에 맞게 처리
                if result.get('result_images'):
                    return {
                        'results': [{
                            'result_images': [
                                {'image': url} for url in result['result_images']
                            ]
                        }]
                    }

                time.sleep(2)

            except requests.RequestException as e:
                self.logger.error(f"Network error checking result: {str(e)}")
                time.sleep(2)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON response: {str(e)}")
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error checking result: {str(e)}")
                time.sleep(2)

        return None

    def run(self):
        try:
            total_files = len(self.image_files)
            session = requests.Session()

            for index, image_path in enumerate(self.image_files):
                if not self._is_running:
                    break

                try:
                    self.logger.info(f"Processing file {index + 1}/{total_files}: {image_path}")

                    # Prepare multipart form data
                    with open(image_path, 'rb') as img_file:
                        files = {
                            'image': (
                                os.path.basename(image_path),
                                img_file,
                                'image/jpeg' if image_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                            )
                        }

                        # Add parameters to the request
                        data = {
                            'mask_blur': str(self.parameters['mask_blur']),
                            'mask_offset': str(self.parameters['mask_offset']),
                            'invert_output': str(self.parameters['invert_output']).lower()
                        }

                        # Upload image and get token
                        upload_response = session.post(self.api_url, files=files, data=data)
                        upload_response.raise_for_status()
                        upload_result = upload_response.json()

                        if 'image_token' in upload_result:
                            token = upload_result['image_token']
                            self.logger.info(f"Got token: {token}")

                            # Wait for processing result
                            result = self.wait_for_result(session, token)
                            if result:
                                self.results.append((image_path, result))
                                self.result.emit((image_path, result))
                            else:
                                raise Exception("처리 결과를 받지 못했습니다.")

                    # Update progress
                    progress = int(((index + 1) / total_files) * 100)
                    self.progress.emit(progress)

                except Exception as e:
                    error_msg = f"Error processing {os.path.basename(image_path)}: {str(e)}"
                    self.logger.error(error_msg)
                    self.error.emit(error_msg)
                    continue

            if self._is_running:
                self.logger.info(f"Processing completed. {len(self.results)} files processed.")
                self.progress.emit(100)
                self.finished.emit(self.results)

        except Exception as e:
            error_msg = f"Critical worker thread error: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)

        finally:
            session.close()
            self.logger.info("Worker thread finished")
# # core/services/worker_thread.py
#
# from PyQt5.QtCore import QThread, pyqtSignal
# import requests
# import logging
# import os
# import time
# from typing import List, Dict
#
#
# class WorkerThread(QThread):
#     progress = pyqtSignal(int)
#     result = pyqtSignal(tuple)  # (file_path, response)
#     finished = pyqtSignal(list)  # List of (file_path, response) tuples
#     error = pyqtSignal(str)
#
#     def __init__(self, image_files: List[str], api_url: str, parameters: Dict):
#         super().__init__()
#         self.image_files = image_files
#         self.api_url = api_url
#         self.parameters = parameters
#         self.results = []
#         self._is_running = True
#
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
#
#         def wait_for_result(self, session, token, max_retries=30):
#             """이미지 처리 결과를 기다림"""
#             for i in range(max_retries):
#                 try:
#                     response = session.get(f"{self.api_url}{token}")
#                     response.raise_for_status()
#                     result = response.json()
#
#                     self.logger.info(f"Polling result: {result}")
#
#                     # 수정된 부분: API 응답 구조에 맞게 변경
#                     if result.get('result_images'):
#                         return {
#                             'results': [{
#                                 'result_images': [
#                                     {'image': url} for url in result['result_images']
#                                 ]
#                             }]
#                         }
#
#                     time.sleep(2)
#
#                 except Exception as e:
#                     self.logger.error(f"Error checking result: {str(e)}")
#                     time.sleep(2)
#
#             return None
#
#
#     def run(self):
#         try:
#             total_files = len(self.image_files)
#             session = requests.Session()
#
#             for index, image_path in enumerate(self.image_files):
#                 if not self._is_running:
#                     break
#
#                 try:
#                     self.logger.info(f"Processing file {index + 1}/{total_files}: {image_path}")
#
#                     # Prepare multipart form data with correct parameter names
#                     files = {
#                         'image': (
#                             os.path.basename(image_path),
#                             open(image_path, 'rb'),
#                             'image/jpeg' if image_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
#                         )
#                     }
#
#                     # Add parameters with correct names to the request
#                     data = {
#                         'mask_blur': str(self.parameters['mask_blur']),
#                         'mask_offset': str(self.parameters['mask_offset']),
#                         'invert_output': str(self.parameters['invert_output']).lower()
#                     }
#
#                     # Send request
#                     response = session.post(self.api_url, files=files, data=data)
#                     response.raise_for_status()
#
#                     result = response.json()
#                     self.results.append((image_path, result))
#                     self.result.emit((image_path, result))
#
#                     # Update progress
#                     progress = int(((index + 1) / total_files) * 100)
#                     self.progress.emit(progress)
#
#                 except Exception as e:
#                     error_msg = f"Error processing {image_path}: {str(e)}"
#                     self.logger.error(error_msg)
#                     self.error.emit(error_msg)
#                     continue
#
#             if self._is_running:
#                 self.progress.emit(100)
#                 self.finished.emit(self.results)
#
#         except Exception as e:
#             error_msg = f"Worker thread error: {str(e)}"
#             self.logger.error(error_msg)
#             self.error.emit(error_msg)
