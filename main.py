import sys
import os
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QListWidget, QTextEdit, QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt

class EndoAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("内镜序列标注与格式化工具 (Python 版)")
        self.resize(1200, 800)
        
        self.source_dir = ""
        self.image_files = []
        
        self.init_ui()

    def init_ui(self):
        # 主部件与全局布局
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
        self.path_input.setPlaceholderText("请选择包含时间戳图片的原始文件夹...")
        self.path_input.setReadOnly(True)
        self.browse_btn = QPushButton("浏览目录")
        self.browse_btn.clicked.connect(self.browse_folder)
        dir_layout.addWidget(self.path_input)
        dir_layout.addWidget(self.browse_btn)
        left_panel.addLayout(dir_layout)

        # 2. 图片列表
        left_panel.addWidget(QLabel("图片序列浏览 (按时间戳排序):"))
        self.image_list = QListWidget()
        self.image_list.setMaximumWidth(400)
        self.image_list.currentRowChanged.connect(self.display_image)
        left_panel.addWidget(self.image_list)

        # 3. 标签输入与格式化按钮
        action_layout = QHBoxLayout()
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("输入文本指令 (如: advance_into_duodenal_bulb)")
        self.format_btn = QPushButton("执行格式化抽帧")
        # 设置按钮样式使其更醒目
        self.format_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.format_btn.clicked.connect(self.format_images)
        action_layout.addWidget(self.label_input)
        action_layout.addWidget(self.format_btn)
        left_panel.addLayout(action_layout)

        # 4. 日志输出
        left_panel.addWidget(QLabel("运行日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        left_panel.addWidget(self.log_output)

        # ================= 右侧图片预览 =================
        self.image_preview = QLabel("请在左侧选择图片")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("background-color: #2e2e2e; color: #ffffff;")
        self.image_preview.setMinimumSize(640, 480)

        # 组合左右面板，设置比例为 1:2
        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.image_preview, 2)

    def log(self, message):
        """向日志框追加信息并滚动到底部"""
        self.log_output.append(message)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "选择图片序列文件夹")
        if directory:
            self.source_dir = directory
            self.path_input.setText(directory)
            self.load_images()

    def load_images(self):
        self.image_list.clear()
        self.image_files.clear()

        valid_exts = ('.jpg', '.jpeg', '.png')
        try:
            files = [f for f in os.listdir(self.source_dir) if f.lower().endswith(valid_exts)]
            # 确保按时间戳(文件名)升序排列
            files.sort() 
            
            for f in files:
                abs_path = os.path.join(self.source_dir, f)
                self.image_files.append(abs_path)
                self.image_list.addItem(f)

            self.log(f"成功加载 {len(self.image_files)} 张图片。")
            if self.image_files:
                self.image_list.setCurrentRow(0)
                
        except Exception as e:
            self.log(f"加载目录失败: {str(e)}")

    def display_image(self, row):
        if row < 0 or row >= len(self.image_files):
            return
            
        img_path = self.image_files[row]
        pixmap = QPixmap(img_path)
        
        if not pixmap.isNull():
            # 动态缩放以适应预览框大小
            scaled_pixmap = pixmap.scaled(
                self.image_preview.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled_pixmap)
        else:
            self.image_preview.setText("图片加载失败")

    def resizeEvent(self, event):
        """窗口大小改变时，重新缩放当前显示的图片"""
        super().resizeEvent(event)
        current_row = self.image_list.currentRow()
        if current_row >= 0:
            self.display_image(current_row)

    def get_start_frame_id(self, target_dir):
        """扫描输出目录，自动获取下一个可用的 frame_id，防止文件覆盖"""
        if not os.path.exists(target_dir):
            return 1
            
        max_id = 0
        for f in os.listdir(target_dir):
            if f.endswith(('.jpg', '.png')):
                parts = f.split('_', 1)
                if len(parts) >= 2 and parts[0].isdigit():
                    max_id = max(max_id, int(parts[0]))
        return max_id + 1

    def format_images(self):
        if not self.image_files:
            QMessageBox.warning(self, "警告", "请先选择包含图片的文件夹！")
            return
            
        label_text = self.label_input.text().strip()
        if not label_text:
            QMessageBox.warning(self, "警告", "执行格式化前，请先输入指令标签！")
            return

        # 确定输出目录：在源目录的同级创建一个 formatted 文件夹
        parent_dir = os.path.dirname(self.source_dir)
        target_dir = os.path.join(parent_dir, "formatted")
        os.makedirs(target_dir, exist_ok=True)

        # 获取起始序号
        frame_id = self.get_start_frame_id(target_dir)
        initial_frame_id = frame_id

        self.log("\n--- 开始格式化抽帧 ---")
        self.log(f"标签: {label_text}")
        self.log(f"起始序号: {frame_id}")
        self.log(f"输出目录: {target_dir}")

        current_second = ""
        extracted_count = 0

        # 遍历处理图片
        for img_path in self.image_files:
            filename = os.path.basename(img_path)
            name_without_ext, ext = os.path.splitext(filename)

            # 假设时间戳格式如 20260402141503723，前 14 位代表秒
            if len(name_without_ext) < 14:
                continue
                
            second_str = name_without_ext[:14]

            # 遇到新的一秒，保留第一张
            if second_str != current_second:
                current_second = second_str
                
                # 构造新文件名，例：1_advance_through_esophagus.jpg
                new_filename = f"{frame_id}_{label_text}{ext}"
                new_filepath = os.path.join(target_dir, new_filename)
                
                try:
                    shutil.copy2(img_path, new_filepath)
                    self.log(f"提取: {filename} -> {new_filename}")
                    frame_id += 1
                    extracted_count += 1
                except Exception as e:
                    self.log(f"拷贝失败 {filename}: {str(e)}")

        self.log(f"--- 处理完成！本次提取 {extracted_count} 帧 ---")
        QMessageBox.information(
            self, "完成", 
            f"抽帧完成！\n本次共提取 {extracted_count} 帧。\n文件已存入:\n{target_dir}"
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置全局样式，使其更贴近现代系统外观
    app.setStyle("Fusion")
    
    window = EndoAnnotator()
    window.show()
    sys.exit(app.exec())