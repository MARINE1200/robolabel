import os
import shutil
import pandas as pd
import numpy as np

class DataManager:
    def __init__(self):
        self.source_dir = ""
        self.shape_csv_path = ""   # 形状文件路径
        self.image_files = []
        self.file_names = []
        self.annotations = {}

    def load_directory(self, directory):
        self.source_dir = directory
        self.image_files.clear()
        self.file_names.clear()
        self.annotations.clear()

        valid_exts = ('.jpg', '.jpeg', '.png')
        try:
            files = [f for f in os.listdir(directory) if f.lower().endswith(valid_exts)]
            files.sort()
            for f in files:
                self.image_files.append(os.path.join(directory, f))
                self.file_names.append(f)
            return True, f"成功加载 {len(files)} 张图片序列。"
        except Exception as e:
            return False, f"加载目录失败: {str(e)}"

    def set_shape_csv(self, path):
        self.shape_csv_path = path

    def set_labels(self, indices, label):
        count = 0
        for idx in indices:
            filename = self.file_names[idx]
            self.annotations[filename] = label
            count += 1
        return count

    def get_start_frame_id(self, target_dir):
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
        if not self.image_files:
            return False, "没有加载任何图片。"
        if not self.annotations:
            return False, "尚未给任何图片打标签，无法导出。"
        if not os.path.exists(self.shape_csv_path):
            return False, "找不到形状数据CSV，请检查路径。"

        target_dir = os.path.join(os.path.dirname(self.source_dir), "formatted")
        os.makedirs(target_dir, exist_ok=True)

        frame_id = self.get_start_frame_id(target_dir)
        current_second = ""
        extracted_count = 0
        log_messages = [f"输出目录: {target_dir}"]

        # 保存被成功提取出来的 (frame_id, 原始时间戳字符串)
        extracted_records = []

        # ================= 1. 图像抽帧处理 =================
        for img_path, filename in zip(self.image_files, self.file_names):
            if filename not in self.annotations:
                continue

            label = self.annotations[filename]
            name_without_ext, ext = os.path.splitext(filename)

            # 解析：YYYYMMDD_HHMMSSmmm -> 去掉后3位留作秒级判断
            if len(name_without_ext) <= 3:
                continue
            
            second_identifier = name_without_ext[:-3]

            if second_identifier != current_second:
                current_second = second_identifier
                
                # 特殊字符处理：指令有空格，可将空格替换为下划线保证文件名友好
                safe_label = label.replace(" ", "_")
                new_filename = f"{frame_id}_{safe_label}{ext}"
                new_filepath = os.path.join(target_dir, new_filename)
                
                try:
                    shutil.copy2(img_path, new_filepath)
                    extracted_records.append((frame_id, name_without_ext))
                    frame_id += 1
                    extracted_count += 1
                except Exception as e:
                    log_messages.append(f"图片拷贝失败 {filename}: {str(e)}")

        log_messages.append(f"图像抽帧完成，共提取 {extracted_count} 帧。")

        # ================= 2. 形状数据对齐处理 =================
        if extracted_count > 0:
            try:
                # 读取形状数据
                shape_df = pd.read_csv(self.shape_csv_path)
                if 'time' not in shape_df.columns:
                    return False, "形状数据中找不到 'time' 列，请检查CSV格式！"

                # 核心对齐算法：将带有 '_' 的时间戳字符串转为整型进行数学绝对值比较
                # 例：'20260402_141258501' -> 20260402141258501
                def to_int_ts(ts_str):
                    return int(str(ts_str).replace('_', ''))

                shape_df['time_int'] = shape_df['time'].apply(to_int_ts)
                shape_times_array = shape_df['time_int'].values

                aligned_shapes = []

                # 为每张抽出来的图寻找时间最接近的形状帧
                for fid, img_ts_str in extracted_records:
                    img_time_int = to_int_ts(img_ts_str)
                    
                    # 寻找绝对时间差最小的索引
                    closest_idx = np.abs(shape_times_array - img_time_int).argmin()
                    
                    matched_row = shape_df.iloc[closest_idx].copy()
                    matched_row['number'] = fid
                    aligned_shapes.append(matched_row)

                aligned_df = pd.DataFrame(aligned_shapes)
                
                # 重新整理列名：第一列为 number，且丢弃原始的 time 和 time_int
                cols_to_keep = ['number'] + [c for c in aligned_df.columns if c not in ['time', 'time_int', 'number']]
                aligned_df = aligned_df[cols_to_keep]

                shape_out_path = os.path.join(target_dir, "shape.csv")
                
                # 如果是分段/分批次执行，使用 mode='a' 进行追加，防止覆盖之前的对齐结果
                if os.path.exists(shape_out_path) and frame_id > 1:
                    aligned_df.to_csv(shape_out_path, mode='a', header=False, index=False)
                else:
                    aligned_df.to_csv(shape_out_path, index=False)

                log_messages.append(f"形状数据对齐完成！已同步保存至 shape.csv")

            except Exception as e:
                return False, f"处理形状数据时出错: {str(e)}"

        return True, "\n".join(log_messages)