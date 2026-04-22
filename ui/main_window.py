from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QListWidget, 
                             QTextEdit, QAbstractItemView, QComboBox)
from PyQt6.QtCore import Qt

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("内镜序列分段标注与抽帧工具")
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

        # 1. 图像文件夹选择
        dir_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("请选择原始图片序列文件夹...")
        self.path_input.setReadOnly(True)
        self.browse_btn = QPushButton("浏览图像目录")
        dir_layout.addWidget(self.path_input)
        dir_layout.addWidget(self.browse_btn)
        left_panel.addLayout(dir_layout)

        # 2. 形状CSV选择 (新增)
        shape_layout = QHBoxLayout()
        self.shape_input = QLineEdit()
        self.shape_input.setPlaceholderText("请选择原始形状数据 CSV 文件...")
        self.shape_input.setReadOnly(True)
        self.browse_shape_btn = QPushButton("选择data.csv")
        shape_layout.addWidget(self.shape_input)
        shape_layout.addWidget(self.browse_shape_btn)
        left_panel.addLayout(shape_layout)

        # 3. 图片列表 (启用多选)
        left_panel.addWidget(QLabel("图片序列 (按住 Shift 或 Ctrl 多选):"))
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_list.setMaximumWidth(480)
        left_panel.addWidget(self.image_list)

        # 4. 分段打标签区域 (改为下拉选择)
        label_layout = QHBoxLayout()
        self.label_combo = QComboBox()
        self.label_combo.addItems([
            "Pass through the epiglottis and enter the esophagus",
            "Traverse the esophagus",
            "Locate the lesser curvature",
            "Adjust to reach the vicinity of the pylorus",
            "Pass through the pylorus and enter the duodenum"
        ])
        self.label_combo.setStyleSheet("padding: 4px;")
        
        self.apply_label_btn = QPushButton("为选中项打标签")
        self.apply_label_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 4px;")
        
        label_layout.addWidget(self.label_combo, 7) # 比例7
        label_layout.addWidget(self.apply_label_btn, 3) # 比例3
        left_panel.addLayout(label_layout)

        # 5. 最终操作：格式化抽帧
        self.format_btn = QPushButton("完成标注，生成 labeled_data.csv")
        self.format_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        left_panel.addWidget(self.format_btn)

        # 6. 日志输出
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