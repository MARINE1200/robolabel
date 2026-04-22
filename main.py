import sys
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSettings

from ui.main_window import MainWindowUI
from core.data_manager import DataManager

class AnnotatorController:
    def __init__(self):
        self.ui = MainWindowUI()
        self.data_manager = DataManager()
        
        # 初始化配置，用于记录上次打开的路径
        self.settings = QSettings("MedicalRobotics", "EndoAnnotator")
        self.last_dir = self.settings.value("last_dir", "")

        self.connect_signals()

    def connect_signals(self):
        self.ui.browse_btn.clicked.connect(self.browse_folder)
        self.ui.browse_shape_btn.clicked.connect(self.browse_shape_csv)
        self.ui.image_list.itemSelectionChanged.connect(self.display_selected_image)
        self.ui.apply_label_btn.clicked.connect(self.apply_labels_to_selection)
        self.ui.format_btn.clicked.connect(self.execute_export)

    def log(self, msg):
        self.ui.log_output.append(msg)
        scrollbar = self.ui.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_folder(self):
        # 默认打开上次记住的路径
        directory = QFileDialog.getExistingDirectory(self.ui, "选择原始图片序列文件夹", self.last_dir)
        if directory:
            self.last_dir = directory
            self.settings.setValue("last_dir", directory) # 保存路径
            
            self.ui.path_input.setText(directory)
            success, msg = self.data_manager.load_directory(directory)
            self.log(msg)
            
            if success:
                self.update_list_widget()

    def browse_shape_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(self.ui, "选择原始形状数据 CSV", self.last_dir, "CSV Files (*.csv)")
        if filepath:
            self.ui.shape_input.setText(filepath)
            self.data_manager.set_shape_csv(filepath)
            self.log(f"已加载形状数据路径: {filepath}")

    def update_list_widget(self):
        self.ui.image_list.clear()
        for filename in self.data_manager.file_names:
            label = self.data_manager.annotations.get(filename, "")
            display_text = f"{filename}  [{label}]" if label else filename
            self.ui.image_list.addItem(display_text)

    def display_selected_image(self):
        selected_items = self.ui.image_list.selectedIndexes()
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

        # 直接从下拉框获取标签内容
        label_text = self.ui.label_combo.currentText()
        
        count = self.data_manager.set_labels(selected_indices, label_text)
        self.log(f"已为 {count} 张图片打上标签:\n-> {label_text}")
        
        for row in selected_indices:
            filename = self.data_manager.file_names[row]
            self.ui.image_list.item(row).setText(f"{filename}  [{label_text}]")

    def execute_export(self):
        if not self.data_manager.shape_csv_path:
            QMessageBox.warning(self.ui, "提示", "请先选择包含了运动和形状数据的原始 CSV 文件！")
            return

        reply = QMessageBox.question(
            self.ui, '确认操作', 
            '确定标注完毕，并生成最终的 labeled_data.csv 吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log("\n>>> 开始处理标签组合与点位重排...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            # 调用全新的导出函数
            success, result_msg = self.data_manager.export_labeled_csv()
            
            QApplication.restoreOverrideCursor()
            self.log(result_msg)
            
            if success:
                QMessageBox.information(self.ui, "完成", "数据文件已成功生成！")
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