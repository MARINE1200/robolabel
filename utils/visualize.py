'''
Author: Yazong Wang
Date: 2026-04-03 16:36:49
LastEditors: Yazong Wang
LastEditTime: 2026-04-22 10:56:10
Description: 
根据预测标签和原始图像，生成带有科研风 HUD 标签的 MP4 视频。
每个指令对应一种颜色，标签文本自动换行，背景为半透明磨砂黑框，增强视觉效果和可读性。
'''
import cv2
import os

# 定义 5 种指令的科研风颜色映射 (OpenCV 使用 BGR 格式)
COLOR_MAP = {
    "Pass through the epiglottis and enter the esophagus": (255, 191, 0),     # 深度天蓝 (Deep Sky Blue)
    "Traverse the esophagus": (144, 238, 144),                                # 浅翠绿 (Light Green)
    "Locate the lesser curvature": (0, 255, 255),                             # 亮黄色 (Yellow)
    "Adjust to reach the vicinity of the pylorus": (0, 165, 255),             # 警示橙 (Orange)
    "Pass through the pylorus and enter the duodenum": (255, 105, 180)        # 亮品红 (Hot Pink)
}

def create_labeled_video(raw_img_dir, label_txt_path, output_mp4, fps=30):
    """
    读取原始图片和标注区间文件，合成带有科研风 HUD 标签的 MP4 视频。
    """
    print(f"正在读取配置...")
    print(f"原始图像目录: {raw_img_dir}")
    print(f"标注文件路径: {label_txt_path}")
    
    # 1. 解析 label.txt
    ranges = []
    if not os.path.exists(label_txt_path):
        print(f"错误: 找不到文件 {label_txt_path}")
        return

    with open(label_txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=2) 
            if len(parts) == 3:
                ranges.append((parts[0], parts[1], parts[2]))
                
    if not ranges:
        print("未在 label.txt 中找到有效的标注信息。")
        return

    # 2. 收集并排序原始图片
    valid_exts = ('.jpg', '.jpeg', '.png')
    images = sorted([img for img in os.listdir(raw_img_dir) if img.lower().endswith(valid_exts)])
    
    if not images:
        print(f"错误: 文件夹 {raw_img_dir} 中没有图片。")
        return

    # 3. 初始化 VideoWriter
    first_img_path = os.path.join(raw_img_dir, images[0])
    first_frame = cv2.imread(first_img_path)
    if first_frame is None:
        print("无法读取图片，请检查路径中是否含有中文字符！")
        return
        
    height, width, _ = first_frame.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_mp4, fourcc, fps, (width, height))

    print(f"视频分辨率: {width}x{height}, 帧率: {fps}")
    print(f"开始合成视频，共 {len(images)} 帧，请稍候...")

    # 科研风 UI 渲染参数
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.65       # 缩小字体
    thickness = 2           # 字体线宽
    line_spacing = 8        # 多行文本的行间距
    pad_x, pad_y = 15, 12   # 半透明背景框的内边距
    start_x, start_y = 20, 30 # HUD 起始位置

    written_count = 0
    for img_name in images:
        label = ""
        
        for start_img, end_img, lbl in ranges:
            if start_img <= img_name <= end_img:
                label = lbl
                break

        img_path = os.path.join(raw_img_dir, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        if label:
            # 1. 文本换行处理
            display_text = label
            if display_text == "Pass through the epiglottis and enter the esophagus":
                # 在 and 之前换行
                display_text = "Pass through the epiglottis\nand enter the esophagus"
            elif display_text == "Adjust to reach the vicinity of the pylorus":
                # 在 and 之前换行
                display_text = "Adjust to reach the vicinity \nof the pylorus"
            elif display_text == "Pass through the pylorus and enter the duodenum":
                # 在 and 之前换行
                display_text = "Pass through the pylorus and \nenter the duodenum"
            lines = display_text.split('\n')
            
            # 2. 获取对应的颜色，如果不在字典中则默认使用白色
            color = COLOR_MAP.get(label, (255, 255, 255))

            # 3. 计算多行文本占据的整体尺寸 (用于画半透明黑框)
            max_width = 0
            total_height = 0
            text_sizes = []
            
            for line in lines:
                (w, h), baseline = cv2.getTextSize(line, font, font_scale, thickness)
                max_width = max(max_width, w)
                total_height += h + baseline
                text_sizes.append((w, h, baseline))
            
            total_height += (len(lines) - 1) * line_spacing

            # 4. 绘制半透明科研风 HUD 背景
            box_x2 = start_x + max_width + pad_x * 2
            box_y2 = start_y + total_height + pad_y * 2
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (start_x, start_y), (box_x2, box_y2), (0, 0, 0), -1) # 纯黑框
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame) # 融合比例 0.6，形成半透明磨砂效果

            # 5. 逐行绘制文本
            curr_y = start_y + pad_y
            for i, line in enumerate(lines):
                w, h, baseline = text_sizes[i]
                curr_y += h # OpenCV 画字是以左下角为基准线的，需向下偏移
                cv2.putText(
                    frame, 
                    line, 
                    (start_x + pad_x, curr_y), 
                    font, 
                    font_scale, 
                    color, 
                    thickness, 
                    cv2.LINE_AA
                )
                curr_y += baseline + line_spacing
        # 可视化
        cv2.imshow("Labeled Video Preview", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("视频预览已关闭，继续合成剩余帧...")
            cv2.destroyAllWindows()
            break

        out.write(frame)
        written_count += 1
        
        if written_count % 100 == 0:
            print(f"已处理 {written_count} / {len(images)} 帧...")

    out.release()
    print(f"合成完成！视频已保存至: {output_mp4}")

if __name__ == "__main__":
    # --- 单独运行脚本测试区 ---
    # 请修改为你实际运行时的目录
    
    RAW_IMAGES = r"D:\Dataset\DuodenoAutoIntervation\20260402PreERCPData\episode3\img" 
    LABEL_FILE = r"D:\Dataset\DuodenoAutoIntervation\20260402PreERCPData\episode3\formatted\label_vis.txt"
    OUTPUT_VIDEO = r".\visualization_2.mp4"
    
    create_labeled_video(RAW_IMAGES, LABEL_FILE, OUTPUT_VIDEO, fps=30)