from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt

class ParameterInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("마스크 파라미터 설정")
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Mask blur parameter (0 ~ 10)
        blur_layout = QHBoxLayout()
        blur_label = QLabel("Mask blur:")
        self.blur_input = QSpinBox()
        self.blur_input.setRange(0, 10)  # 범위 수정
        self.blur_input.setValue(0)
        self.blur_input.setSuffix(" px")
        blur_input_info = QLabel("(범위: 0 ~ 10px)")
        blur_input_info.setStyleSheet("color: gray; font-size: 10px;")

        blur_layout.addWidget(blur_label)
        blur_layout.addWidget(self.blur_input)
        blur_layout.addWidget(blur_input_info)
        blur_layout.addStretch()
        layout.addLayout(blur_layout)

        # Mask offset parameter (-10 ~ 10)
        offset_layout = QHBoxLayout()
        offset_label = QLabel("Mask offset:")
        self.offset_input = QSpinBox()
        self.offset_input.setRange(-10, 10)  # 범위 수정
        self.offset_input.setValue(0)
        self.offset_input.setSuffix(" px")
        offset_input_info = QLabel("(범위: -10 ~ 10px)")
        offset_input_info.setStyleSheet("color: gray; font-size: 10px;")

        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.offset_input)
        offset_layout.addWidget(offset_input_info)
        offset_layout.addStretch()
        layout.addLayout(offset_layout)

        # Invert output parameter
        invert_layout = QHBoxLayout()
        invert_label = QLabel("Invert output:")
        self.invert_input = QCheckBox()
        self.invert_input.setChecked(False)
        invert_layout.addWidget(invert_label)
        invert_layout.addWidget(self.invert_input)
        invert_layout.addStretch()
        layout.addLayout(invert_layout)

        # 설명 추가
        info_label = QLabel("선택된 모든 이미지에 동일한 파라미터가 적용됩니다.")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 창 크기 조정
        self.setFixedSize(self.sizeHint())

    def get_parameters(self):
        return {
            'mask_blur': self.blur_input.value(),
            'mask_offset': self.offset_input.value(),
            'invert_output': self.invert_input.isChecked()
        }