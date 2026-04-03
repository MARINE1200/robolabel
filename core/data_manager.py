import os
import shutil
import pandas as pd
import numpy as np

class DataManager:
    def __init__(self):
        self.source_dir = ""
        self.shape_csv_path = ""
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
            # 字典赋值天然支持覆盖操作 (Req 2)
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

    def generate_label_txt(self, target_dir):
        """生成 label.txt 记录连续的标注段落 (Req 3)"""
        records = []
        start_file = None
        end_file = None
        current_label = None

        for filename in self.file_names:
            label = self.annotations.get(filename, None)
            
            # 如果标签发生了变化（或者从有标签变为无标签，无标签变为有标签）
            if label != current_label:
                if current_label is not None:
                    records.append(f"{start_file} {end_file} {current_label}\n")
                if label is not None:
                    start_file = filename
                    current_label = label
                else:
                    current_label = None
                    
            if label is not None:
                end_file = filename

        # 最后一组收尾
        if current_label is not None:
            records.append(f"{start_file} {end_file} {current_label}\n")

        label_txt_path = os.path.join(target_dir, "label.txt")
        # 采用追加或覆盖，这里推荐直接覆盖本次该文件夹内的结果
        with open(label_txt_path, "w", encoding='utf-8') as f:
            f.writelines(records)
            
        return label_txt_path

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

        # --- 1. 生成并导出原始的 label.txt ---
        txt_path = self.generate_label_txt(target_dir)
        log_messages.append(f"标注情况已导出至: {txt_path}")

        extracted_records = []

        # --- 2. 图像 1Hz 抽帧处理 ---
        for img_path, filename in zip(self.image_files, self.file_names):
            if filename not in self.annotations:
                continue

            label = self.annotations[filename]
            name_without_ext, ext = os.path.splitext(filename)

            if len(name_without_ext) <= 3:
                continue
            
            # 例如 '20260402_141258501' -> '20260402_141258'
            second_identifier = name_without_ext[:-3]

            if second_identifier != current_second:
                current_second = second_identifier
                
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

        # --- 3. 形状数据同秒匹配 (Req 1) ---
        if extracted_count > 0:
            try:
                shape_df = pd.read_csv(self.shape_csv_path)
                shape_df['time_str'] = shape_df['time'].astype(str)
                shape_df['time_int'] = shape_df['time_str'].str.replace('_', '').astype(int)

                aligned_shapes = []
                # 获取除了辅助列之外的所有列（预期为21个坐标列）
                coord_cols = [c for c in shape_df.columns if c not in ['time', 'time_str', 'time_int']]

                for fid, img_ts_str in extracted_records:
                    # 提取该图所在的秒级字符串 (例如 20260402_141258)
                    second_id = img_ts_str[:-3]
                    
                    # 强约束：只在同一秒的数据中查找
                    same_sec_df = shape_df[shape_df['time_str'].str.startswith(second_id)]
                    
                    if same_sec_df.empty:
                        # 在同一秒内找不到数据，全部设为 0
                        zero_row = {col: 0.0 for col in coord_cols}
                        zero_row['number'] = fid
                        aligned_shapes.append(zero_row)
                    else:
                        # 在同一秒内寻找最近时间戳
                        img_time_int = int(img_ts_str.replace('_', ''))
                        closest_idx = (same_sec_df['time_int'] - img_time_int).abs().idxmin()
                        matched_row = same_sec_df.loc[closest_idx].copy()
                        
                        # 提炼最终所需格式
                        final_row = {col: matched_row[col] for col in coord_cols}
                        final_row['number'] = fid
                        aligned_shapes.append(final_row)

                aligned_df = pd.DataFrame(aligned_shapes)
                # 调整列顺序：number 在前
                cols_to_keep = ['number'] + coord_cols
                aligned_df = aligned_df[cols_to_keep]

                shape_out_path = os.path.join(target_dir, "shape.csv")
                
                if os.path.exists(shape_out_path) and frame_id - extracted_count > 1:
                    aligned_df.to_csv(shape_out_path, mode='a', header=False, index=False)
                else:
                    aligned_df.to_csv(shape_out_path, index=False)

                log_messages.append(f"形状数据对齐完成 (未匹配项已置0)！")

            except Exception as e:
                return False, f"处理形状数据时出错: {str(e)}"

        return True, "\n".join(log_messages)