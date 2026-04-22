import os
import pandas as pd
import io

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
            # 修改点：将按照字典序排序改为按照数字序号大小排序 (0, 1, 2...10)
            files.sort(key=lambda x: int(os.path.splitext(x)[0]))
            
            for f in files:
                self.image_files.append(os.path.join(directory, f))
                self.file_names.append(f)
            return True, f"成功加载 {len(files)} 张图片序列。"
        except ValueError:
            return False, "加载失败：图片命名必须为纯数字序号（例如 0.jpg, 1.jpg）。请检查文件夹内是否有其他非数字命名的文件。"
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

    def export_labeled_csv(self):
        """物理级去除末尾逗号，插入标签列，并重排点位顺序"""
        if not self.shape_csv_path or not os.path.exists(self.shape_csv_path):
            return False, "找不到数据 CSV，请先选择包含运动和形状数据的 CSV 文件。"

        try:
            # ================= 1. 物理级文本清洗 =================
            # 读取原始文件的所有行
            with open(self.shape_csv_path, 'r', encoding='utf-8-sig') as f:
                raw_lines = f.readlines()

            cleaned_lines = []
            for line in raw_lines:
                # 剥离换行符和末尾可能的空格
                line_clean = line.rstrip('\n\r ')
                # 如果以逗号结尾，直接切掉最后一个字符
                if line_clean.endswith(','):
                    line_clean = line_clean[:-1]
                cleaned_lines.append(line_clean)

            # 将清洗后的文本重新拼接成一个大字符串
            cleaned_csv_text = '\n'.join(cleaned_lines)

            # ================= 2. 读取到 Pandas 中 =================
            # 使用 io.StringIO 欺骗 pandas，让它以为在读一个格式完美的文件
            df = pd.read_csv(io.StringIO(cleaned_csv_text))
            
            original_cols = list(df.columns)
            first_col_name = original_cols[0] # 稳稳拿到 'No.'

            # ================= 3. 匹配并写入 Label =================
            labels = []
            for _, row in df.iterrows():
                try:
                    idx = str(int(row[first_col_name]))
                except ValueError:
                    idx = str(row[first_col_name])

                label = ""
                for ext in ['.jpg', '.png', '.jpeg']:
                    filename = f"{idx}{ext}"
                    if filename in self.annotations:
                        label = self.annotations[filename]
                        break
                labels.append(label)

            # 在第 1 列和第 2 列之间插入 label
            df.insert(1, 'label', labels)

            # ================= 4. 重排坐标点位顺序 =================
            # 正确顺序：1, 2, 5, 3, 6, 4, 7
            base_cols = []
            pt_cols = {i: [] for i in range(1, 8)}

            for col in df.columns:
                c_clean = col.strip()
                if c_clean in ['x1', 'y1', 'z1']: pt_cols[1].append(col)
                elif c_clean in ['x2', 'y2', 'z2']: pt_cols[2].append(col)
                elif c_clean in ['x3', 'y3', 'z3']: pt_cols[3].append(col)
                elif c_clean in ['x4', 'y4', 'z4']: pt_cols[4].append(col)
                elif c_clean in ['x5', 'y5', 'z5']: pt_cols[5].append(col)
                elif c_clean in ['x6', 'y6', 'z6']: pt_cols[6].append(col)
                elif c_clean in ['x7', 'y7', 'z7']: pt_cols[7].append(col)
                else:
                    base_cols.append(col)

            new_col_order = list(base_cols)
            for pt in [1, 2, 5, 3, 6, 4, 7]:
                new_col_order.extend(pt_cols[pt])

            df = df[new_col_order]

            # ================= 5. 导出文件 =================
            target_dir = os.path.dirname(self.source_dir)
            out_path = os.path.join(target_dir, "labeled_data.csv")
            
            df.to_csv(out_path, index=False)

            return True, f"标注数据整合完成，文件已保存至:\n{out_path}"

        except Exception as e:
            return False, f"生成导出文件时出错: {str(e)}"