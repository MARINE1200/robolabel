from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QListWidget, 
                             QTextEdit, QAbstractItemView)
from PyQt6.QtCore import Qt

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("内镜序列分段标注与抽帧工具 (MVC架构)")
        self.resize(1200, 800)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ================= 左侧控制面板 =================
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(10, 10, 10, 10)
        left_panel.setSpacing(15)

        # 1. 文件夹选择
        dir_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("请选择原始图片序列文件夹...")
        self.path_input.setReadOnly(True)
        self.browse_btn = QPushButton("浏览目录")
        dir_layout.addWidget(self.path_input)
        dir_layout.addWidget(self.browse_btn)
        left_panel.addLayout(dir_layout)

        # 2. 图片列表 (启用多选)
        left_panel.addWidget(QLabel("图片序列 (按住 Shift 或 Ctrl 多选):"))
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_list.setMaximumWidth(450)
        left_panel.addWidget(self.image_list)

        # 3. 分段打标签区域
        label_layout = QHBoxLayout()
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("输入标签 (如: navigate_stomach)")
        self.apply_label_btn = QPushButton("为选中项打标签")
        self.apply_label_btn.setStyleSheet("background-color: #2196F3; color: white;")
        label_layout.addWidget(self.label_input)
        label_layout.addWidget(self.apply_label_btn)
        left_panel.addLayout(label_layout)

        # 4. 最终操作：格式化抽帧
        self.format_btn = QPushButton("完成标注，执行 1Hz 抽帧并导出")
        self.format_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        left_panel.addWidget(self.format_btn)

        # 5. 日志输出
        left_panel.addWidget(QLabel("运行日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        left_panel.addWidget(self.log_output)

        # ================= 右侧图片预览 =================
        self.image_preview = QLabel("在左侧选择单张图片预览")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.image_preview.setMinimumSize(640, 480)

        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.image_preview, 2)