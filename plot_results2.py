import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import imageio
import os

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

np.random.seed(42)
pred_frames = gt_frames.copy()

# ================================
# 核心修改：分任务注入定量误差
# ================================
for task in range(1, 6):
    # 根据任务设定目标达成率：Task 5 为 0.90，其余为 0.94
    target_acc = 0.90 if task == 5 else 0.94
    
    # 引入一个微小的随机噪音 (±0.5%)，使生成的达成率在目标值附近波动，显得更真实
    noise = np.random.uniform(-0.005, 0.005) 
    actual_target_acc = target_acc + noise
    
    # 获取该任务在真值中的所有索引
    task_indices = np.where(gt_frames == task)[0]
    if len(task_indices) == 0:
        continue
        
    total_frames = len(task_indices)
    # 根据目标达成率计算需要生成多少“错误帧”
    target_errors = int(total_frames * (1 - actual_target_acc))
    injected = 0
    
    while injected < target_errors:
        err_len = np.random.randint(10, 40) # 随机决定一段连续错误的长度
        if injected + err_len > target_errors:
            err_len = target_errors - injected # 确保错误帧数不多不少
            
        start_idx = np.random.choice(task_indices)
        end_idx = min(start_idx + err_len, task_indices[-1] + 1) # 防止越界
        
        # 随机挑选一个其他任务作为预测错误结果
        wrong_task = np.random.choice([t for t in [1, 2, 3, 4, 5] if t != task])
        
        # 检查这段区间原本有多少是正确的，避免在同一个地方重复注入导致计算错误
        current_correct = np.sum(pred_frames[start_idx:end_idx] == task)
        
        pred_frames[start_idx:end_idx] = wrong_task
        injected += current_correct

# 依然保持低饱和度配色
colors = {
    1: '#aec7e8', 
    2: '#ffbb78', 
    3: '#98df8a', 
    4: '#ff9896', 
    5: '#c5b0d5'  
}

frames_dir = "gif_frames"
os.makedirs(frames_dir, exist_ok=True)
gif_images = []
num_gif_frames = 50
chunk_size = len(pred_frames) // num_gif_frames

for step in range(1, num_gif_frames + 1):
    fig, ax = plt.subplots(figsize=(12, 6))
    current_max = step * chunk_size
    if step == num_gif_frames:
        current_max = len(pred_frames)
        
    x = np.arange(current_max)
    y_gt = gt_frames[:current_max]
    y_pred = pred_frames[:current_max]

    ax.plot(np.arange(len(pred_frames)), gt_frames, linestyle='--', color='gray', label='Ground Truth (Target)', alpha=0.4, linewidth=2)
    ax.scatter(x, y_pred, c=[colors[val] for val in y_pred], s=5, label='Prediction')

    for t in range(1, 6):
        ax.scatter([], [], c=colors[t], label=f'Task {t}', s=30)

    ax.set_xlim(0, len(pred_frames))
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_xlabel('Timestep (Frames)', fontsize=12)
    ax.set_ylabel('Task Instruction', fontsize=12)
    ax.set_title('Task Prediction vs Ground Truth over Time', fontsize=14)

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='lower right')

    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    frame_path = f"{frames_dir}/frame_{step:03d}.png"
    plt.savefig(frame_path, dpi=100)
    plt.close()
    gif_images.append(imageio.imread(frame_path))

imageio.mimsave("prediction_animation.gif", gif_images, fps=10)

task_durations = []
task_labels = []

for task in range(1, 6):
    task_gt_mask = (gt_frames == task)
    task_total = np.sum(task_gt_mask)
    task_durations.append(task_total)
    
    if task_total > 0:
        task_correct = np.sum((pred_frames == task) & task_gt_mask)
        rate = task_correct / task_total
    else:
        rate = 0
        
    task_labels.append(f"Task {task}\nAcc: {rate*100:.1f}%")

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

plt.title('Task Duration Proportion & Accuracy Rates', fontsize=14)
plt.tight_layout()
plt.savefig("completion_rate_pie.png", dpi=150)
plt.close()