from pathlib import Path

def get_jpg_files(folder_path, output_txt):
    # 指定文件夹路径
    p = Path(folder_path)
    
    # 搜索目录下所有的 jpg 文件 (忽略大小写可以使用 r'*. [jJ][pP][gG]')
    # glob 也可以换成 rglob 来递归搜索子目录
    jpg_files = list(p.glob('*.jpg'))
    
    # 提取文件名并排序
    file_names = sorted([f.name for f in jpg_files])
    
    # 写入文件
    with open(output_txt, 'w', encoding='utf-8') as f:
        for name in file_names:
            f.write(name + '\n')
            
    print(f"成功！已将 {len(file_names)} 个文件名保存至 {output_txt}")

# 使用示例
get_jpg_files(r'D:\Dataset\DuodenoAutoIntervation\20260402PreERCPData\episode3\img', r'.\file_list.txt')