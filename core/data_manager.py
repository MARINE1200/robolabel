import os
import shutil

class DataManager:
    def __init__(self):
        self.source_dir = ""
        self.image_files = []      # 存储完整路径
        self.file_names = []       # 存储纯文件名
        self.annotations = {}      # 字典: {原始文件名: 文本标签}

    def load_directory(self, directory):
        self.source_dir = directory
        self.image_files.clear()
        self.file_names.clear()
        self.annotations.clear()

        valid_exts = ('.jpg', '.jpeg', '.png')
        try:
            files = [f for f in os.listdir(directory) if f.lower().endswith(valid_exts)]
            files.sort()  # 按时间戳排序
            
            for f in files:
                self.image_files.append(os.path.join(directory, f))
                self.file_names.append(f)
                
            return True, f"成功加载 {len(files)} 张图片序列。"
        except Exception as e:
            return False, f"加载目录失败: {str(e)}"

    def set_labels(self, indices, label):
        """为指定的索引打上标签"""
        count = 0
        for idx in indices:
            filename = self.file_names[idx]
            self.annotations[filename] = label
            count += 1
        return count

    def get_start_frame_id(self, target_dir):
        """自动寻找下一个合法的 frame_id，防止覆盖历史数据"""
        if not os.path.exists(target_dir):
            return 1
        max_id = 0
        for f in os.listdir(target_dir):
            if f.endswith(('.jpg', '.png')):
                parts = f.split('_', 1)
                if len(parts) >= 2 and parts[0].isdigit():
                    max_id = max(max_id, int(parts[0]))
        return max_id + 1

    def format_and_export(self):
        """执行最终的一秒一帧抽帧逻辑"""
        if not self.image_files:
            return False, "没有加载任何图片。"
        if not self.annotations:
            return False, "尚未给任何图片打标签，无法导出。"

        target_dir = os.path.join(os.path.dirname(self.source_dir), "formatted")
        os.makedirs(target_dir, exist_ok=True)

        frame_id = self.get_start_frame_id(target_dir)
        current_second = ""
        extracted_count = 0
        log_messages = []

        log_messages.append(f"输出目录: {target_dir}")

        for img_path, filename in zip(self.image_files, self.file_names):
            # 只处理被打过标签的图片，没打标签的视为过渡废片，直接跳过
            if filename not in self.annotations:
                continue

            label = self.annotations[filename]
            name_without_ext, ext = os.path.splitext(filename)

            # 核心时间戳解析逻辑：去掉最后3位毫秒，剩下的就是“秒”级标识
            # 例: 20260402_141503723 -> 去掉723 -> 20260402_141503
            if len(name_without_ext) <= 3:
                continue
                
            second_identifier = name_without_ext[:-3]

            # 遇到新的一秒
            if second_identifier != current_second:
                current_second = second_identifier
                
                new_filename = f"{frame_id}_{label}{ext}"
                new_filepath = os.path.join(target_dir, new_filename)
                
                try:
                    shutil.copy2(img_path, new_filepath)
                    log_messages.append(f"提取: {filename} -> {new_filename}")
                    frame_id += 1
                    extracted_count += 1
                except Exception as e:
                    log_messages.append(f"拷贝失败 {filename}: {str(e)}")

        log_messages.append(f"\n--- 格式化完成！本次共提取 {extracted_count} 帧 ---")
        return True, "\n".join(log_messages)