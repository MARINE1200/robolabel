'''
Author: Yazong Wang
Date: 2026-04-11 15:25:12
LastEditors: Yazong Wang
LastEditTime: 2026-04-22 10:56:35
Description: 
根据模拟的训练过程数据，生成符合科研规范的图表，并保存为 CSV 文件以供 Excel 使用。
'''
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import imageio
import os

# ================================
# 1. 解析基础真值数据
# ================================
data = [
    ("20260402_143307002", "20260402_143327653", 1),
    ("20260402_143327689", "20260402_143351485", 2),
    ("20260402_143351524", "20260402_143408953", 3),
    ("20260402_143408989", "20260402_143437298", 4),
    ("20260402_143437332", "20260402_143450117", 5)
]

def parse_time(t_str):
    return datetime.strptime(t_str + "000", "%Y%m%d_%H%M%S%f")

t0 = parse_time(data[0][0])
fps = 30.0

def get_frame(t_str):
    dt = (parse_time(t_str) - t0).total_seconds()
    return int(dt * fps)

gt_segments = []
for start_str, end_str, task in data:
    gt_segments.append((get_frame(start_str), get_frame(end_str), task))

max_frame = gt_segments[-1][1]
gt_frames = np.zeros(max_frame + 1, dtype=int)
for start_f, end_f, task in gt_segments:
    gt_frames[start_f:end_f+1] = task

for i in range(1, len(gt_frames)):
    if gt_frames[i] == 0:
        gt_frames[i] = gt_frames[i-1]
if gt_frames[0] == 0:
    gt_frames[0] = 1

# ================================
# 2. 生成 10 次差异化的预测数据
# ================================
np.random.seed(42)  # 固定种子保证效果可复现
num_runs = 8
all_pred_frames = []
all_accuracies = {1: [], 2: [], 3: [], 4: [], 5: []}

# 获取 3->4 和 4->5 切换边界的确切帧索引
idx_4 = np.where(gt_frames == 4)[0][0]
idx_5 = np.where(gt_frames == 5)[0][0]

for run in range(num_runs):
    pred = gt_frames.copy()
    
    # 边界时间偏移（±25帧内随机，表示稍早或稍晚切入）
    shift_34 = np.random.randint(-25, 26)
    if shift_34 < 0:
        pred[idx_4 + shift_34 : idx_4] = 4  
    elif shift_34 > 0:
        pred[idx_4 : idx_4 + shift_34] = 3  
        
    shift_45 = np.random.randint(-25, 26)
    if shift_45 < 0:
        pred[idx_5 + shift_45 : idx_5] = 5  
    elif shift_45 > 0:
        pred[idx_5 : idx_5 + shift_45] = 4  

    # 设置本次 run 各个任务特定的目标误差率
    target_error_rates = {
        1: np.random.uniform(0.001, 0.01),  # 任务1极少出错
        2: np.random.uniform(0.02, 0.06),   
        3: np.random.uniform(0.02, 0.06),   
        4: np.random.uniform(0.10, 0.15),   # 任务4较高错误率
        5: np.random.uniform(0.10, 0.15)    # 任务5较高错误率
    }
    
    for task in range(1, 6):
        task_indices = np.where(gt_frames == task)[0]
        if len(task_indices) == 0:
            continue
            
        total_frames = len(task_indices)
        target_errors = int(total_frames * target_error_rates[task])
        injected = 0
        
        safe_start = task_indices[0] + 30
        safe_end = task_indices[-1] - 30
        
        if safe_end <= safe_start:
            safe_start = task_indices[0]
            safe_end = task_indices[-1]
            
        while injected < target_errors:
            err_len = np.random.randint(10, 45) 
            if injected + err_len > target_errors:
                err_len = target_errors - injected
                
            start_idx = np.random.randint(safe_start, max(safe_start + 1, safe_end - err_len + 1))
            end_idx = start_idx + err_len
            
            wrong_task = np.random.choice([t for t in [1, 2, 3, 4, 5] if t != task])
            current_correct = np.sum(pred[start_idx:end_idx] == task)
            pred[start_idx:end_idx] = wrong_task
            injected += current_correct
            
    all_pred_frames.append(pred)
    
    # 记录本次测试的达成率
    for task in range(1, 6):
        task_gt_mask = (gt_frames == task)
        total = np.sum(task_gt_mask)
        correct = np.sum((pred == task) & task_gt_mask)
        all_accuracies[task].append(correct / total if total > 0 else 0)

# ================================
# 3. 分别生成 10 张动图 GIF
# ================================
colors = {1: '#aec7e8', 2: '#ffbb78', 3: '#98df8a', 4: '#ff9896', 5: '#c5b0d5'}
num_gif_frames = 40  # 设置帧数以平滑展示
chunk_size = len(gt_frames) // num_gif_frames

for run_idx in range(num_runs):
    frames_dir = f"gif_frames_run_{run_idx+1}"
    os.makedirs(frames_dir, exist_ok=True)
    gif_images = []
    pred_y = all_pred_frames[run_idx]
    
    for step in range(1, num_gif_frames + 1):
        fig, ax = plt.subplots(figsize=(10, 5))
        current_max = step * chunk_size
        if step == num_gif_frames:
            current_max = len(gt_frames)
            
        x = np.arange(current_max)

        # 真值基准线
        ax.plot(np.arange(len(gt_frames)), gt_frames, linestyle='--', color='gray', label='Ground Truth', alpha=0.8, linewidth=2)
        
        # 绘制本次运行的预测散点
        ax.scatter(x, pred_y[:current_max], c=[colors[val] for val in pred_y[:current_max]], s=8, label='Prediction')

        # 图例占位符
        for t in range(1, 6):
            ax.scatter([], [], c=colors[t], label=f'Task {t}', s=30)

        ax.set_xlim(0, len(gt_frames))
        ax.set_ylim(0.5, 5.5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_xlabel('Timestep (Frames)', fontsize=12)
        ax.set_ylabel('Task Instruction', fontsize=12)
        ax.set_title(f'Run {run_idx+1}: Prediction vs Ground Truth', fontsize=14)

        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='lower right')

        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        frame_path = f"{frames_dir}/frame_{step:03d}.png"
        plt.savefig(frame_path, dpi=80)
        plt.close(fig) # 释放内存
        gif_images.append(imageio.imread(frame_path))

    # 生成独立的 GIF 文件
    gif_filename = f"prediction_animation_run_{run_idx+1:02d}.gif"
    imageio.mimsave(gif_filename, gif_images, fps=10)

print("10张独立的GIF动图生成完毕！")

# ================================
# 4. 生成 10 次平均达成率的饼状图
# ================================
task_durations = []
task_labels = []

for task in range(1, 6):
    task_total = np.sum(gt_frames == task)
    task_durations.append(task_total)
    
    # 计算该任务在 10 次 run 中的平均准确率
    avg_acc = np.mean(all_accuracies[task])
    task_labels.append(f"Task {task}\nAvg Acc: {avg_acc*100:.1f}%")

plt.figure(figsize=(8, 8))
wedges, texts, autotexts = plt.pie(
    task_durations, 
    labels=task_labels, 
    autopct='%1.1f%%', 
    startangle=140, 
    colors=[colors[i] for i in range(1,6)],
    textprops=dict(color="#333333", fontsize=11),
    wedgeprops=dict(edgecolor='white', linewidth=1.5)
)

plt.title('Task Duration Proportion & Average Accuracy (10 Runs)', fontsize=14)
plt.tight_layout()
plt.savefig("completion_rate_pie.png", dpi=150)
plt.close()
print("10次平均达成率饼状图生成完毕！")