import sys
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from ui.main_window import MainWindowUI
from core.data_manager import DataManager

class AnnotatorController:
    def __init__(self):
        self.ui = MainWindowUI()
        self.data_manager = DataManager()
        self.connect_signals()

    def connect_signals(self):
        self.ui.browse_btn.clicked.connect(self.browse_folder)
        self.ui.image_list.itemSelectionChanged.connect(self.display_selected_image)
        self.ui.apply_label_btn.clicked.connect(self.apply_labels_to_selection)
        self.ui.format_btn.clicked.connect(self.execute_format)

    def log(self, msg):
        self.ui.log_output.append(msg)
        scrollbar = self.ui.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_folder(self):
        directory = QFileDialog.getExistingDirectory(self.ui, "选择原始图片序列文件夹")
        if directory:
            self.ui.path_input.setText(directory)
            success, msg = self.data_manager.load_directory(directory)
            self.log(msg)
            
            if success:
                self.update_list_widget()

    def update_list_widget(self):
        self.ui.image_list.clear()
        for filename in self.data_manager.file_names:
            # 如果已有标签，显示在界面上
            label = self.data_manager.annotations.get(filename, "")
            display_text = f"{filename}  [{label}]" if label else filename
            self.ui.image_list.addItem(display_text)

    def display_selected_image(self):
        selected_items = self.ui.image_list.selectedIndexes()
        # 只有在单选时才更新预览图，避免多选时疯狂刷新
        if len(selected_items) == 1:
            row = selected_items[0].row()
            img_path = self.data_manager.image_files[row]
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.ui.image_preview.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.ui.image_preview.setPixmap(scaled_pixmap)

    def apply_labels_to_selection(self):
        selected_indices = [item.row() for item in self.ui.image_list.selectedIndexes()]
        if not selected_indices:
            QMessageBox.warning(self.ui, "提示", "请先在列表中选中需要标注的图片！")
            return

        label_text = self.ui.label_input.text().strip()
        if not label_text:
            QMessageBox.warning(self.ui, "提示", "请输入有效的标签文本！")
            return

        # 更新后端数据
        count = self.data_manager.set_labels(selected_indices, label_text)
        self.log(f"已为 {count} 张图片打上标签: [{label_text}]")
        
        # 刷新前端列表展示
        for row in selected_indices:
            filename = self.data_manager.file_names[row]
            self.ui.image_list.item(row).setText(f"{filename}  [{label_text}]")

    def execute_format(self):
        reply = QMessageBox.question(
            self.ui, '确认操作', 
            '确定所有段落都已经标注完毕并执行 1Hz 抽帧吗？\n(未打标签的图片将被忽略)',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log("\n>>> 开始执行格式化抽帧...")
            success, result_msg = self.data_manager.format_and_export()
            self.log(result_msg)
            
            if success:
                QMessageBox.information(self.ui, "完成", "抽帧与重命名已成功完成！")
            else:
                QMessageBox.warning(self.ui, "错误", result_msg)

    def run(self):
        self.ui.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    controller = AnnotatorController()
    controller.run()
    
    sys.exit(app.exec())