#!/usr/bin/env python3
"""
从合成图生成视频（推荐工作流）

问题：Agnes AI 视频生成的 `keyframes` 模式会导致角色慢慢透明消失
原因：在两张图片之间插值，角色图（第一帧）渐变到场景图（最后一帧）

解决方案：
1. 先生成"角色在场景中"的合成图（使用 generate_composite_image.py）
2. 再用这张合成图生成视频（只用一张图，避免插值问题）

使用方法：
    python video_from_composite.py

前置条件：
- 已经运行 generate_composite_image.py 生成了合成图
- 或者手动准备一张"角色在场景中"的合成图

输出：
- `output_video.mp4` - 最终视频
- 角色持续可见，不会消失
"""

import os
import time
import requests
from openai import OpenAI

# ========== 配置区域 ==========
API_KEY = "sk-ll5Knbh5VOgpFNoKAJ8Ax0W2QHcXRxupN7RY3SYgwLsAeF2O"  # 修改为你的 API Key
BASE_URL = "https://apihub.agnes-ai.cn"

# 合成图路径（修改为你的合成图路径）
COMPOSITE_IMAGE_PATH = "./output/composite_image.png"

# 输出目录
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 初始化 OpenAI 客户端
client = OpenAI(api_key=API_KEY, base_url=f"{BASE_URL}/v1")

# HTTP 请求头
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
# ====================================


def upload_image_to_url(image_path):
    """将本地图片上传到公网（返回 URL）"""
    print(f"[INFO] 上传图片: {image_path}")
    
    # 方法1: 使用 Agnes API 重新生成（获取 URL）
    # 注意：这会重新生成图片，可能不是原图
    print(f"[WARN] 注意: 需要先将本地图片上传到公网图床")
    print(f"[INFO] 推荐图床: https://sm.ms/ 或 https://imgbb.com/")
    print(f"[INFO] 请手动上传 {image_path} 并输入 URL")
    
    image_url = input("请输入图片 URL: ").strip()
    
    if not image_url:
        print(f"[ERROR] URL 不能为空")
        return None
    
    print(f"[OK] 图片 URL: {image_url[:100]}...")
    return image_url


def create_video_task(prompt, image_url, num_frames=121, frame_rate=24):
    """创建视频生成任务（只用一张图）"""
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": prompt,
        "image": image_url,  # 只用一张图
        "width": 1152,
        "height": 768,
        "num_frames": num_frames,
        "frame_rate": frame_rate
    }
    
    print(f"\n[INFO] 创建视频任务...")
    print(f"[INFO] 提示词: {prompt[:80]}...")
    print(f"[INFO] 图片: 1张（合成图）")
    
    response = requests.post(
        f"{BASE_URL}/v1/videos",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"[ERROR] 创建任务失败: {response.status_code}")
        print(f"[ERROR] 响应: {response.text}")
        return None
    
    data = response.json()
    task_id = data.get("task_id")
    video_id = data.get("video_id")
    
    print(f"[OK] 任务创建成功!")
    print(f"[INFO] Task ID: {task_id}")
    print(f"[INFO] Video ID: {video_id}")
    
    return {
        "task_id": task_id,
        "video_id": video_id,
        "status": data.get("status")
    }


def poll_video_result(video_id, max_wait=600):
    """轮询视频生成结果（最长等待 10 分钟）"""
    print(f"[INFO] 轮询视频结果（最长 {max_wait} 秒）...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            result = requests.get(
                f"{BASE_URL}/agnesapi?video_id={video_id}",
                headers=HEADERS,
                timeout=30
            ).json()
            
            status = result.get("status")
            progress = result.get("progress", 0)
            
            elapsed = int(time.time() - start_time)
            print(f"[POLL] {elapsed}秒 - 状态: {status}, 进度: {progress}%")
            
            if status == "completed":
                video_url = result.get("remixed_from_video_id") or result.get("video_url")
                print(f"[OK] 视频生成完成!")
                print(f"[INFO] 视频 URL: {video_url}")
                return video_url
            
            elif status == "failed":
                error = result.get("error", "未知错误")
                print(f"[ERROR] 视频生成失败: {error}")
                return None
            
            time.sleep(10)
            
        except Exception as e:
            print(f"[ERROR] 轮询错误: {e}")
            time.sleep(10)
    
    print(f"[ERROR] 超时（{max_wait}秒）")
    return None


def download_video(video_url, output_path):
    """下载视频到本地"""
    print(f"[INFO] 下载视频...")
    
    try:
        response = requests.get(video_url, stream=True, timeout=120)
        if response.status_code != 200:
            print(f"[ERROR] 下载失败: {response.status_code}")
            return False
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[OK] 视频已下载: {output_path} ({file_size:.2f} MB)")
        return True
    except Exception as e:
        print(f"[ERROR] 下载失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("从合成图生成视频（推荐工作流）")
    print("避免角色消失问题")
    print("="*60)
    
    # 步骤1: 检查合成图是否存在
    print("\n步骤1: 检查合成图...")
    
    if not os.path.exists(COMPOSITE_IMAGE_PATH):
        print(f"[ERROR] 合成图不存在: {COMPOSITE_IMAGE_PATH}")
        print(f"\n请先运行 generate_composite_image.py 生成合成图")
        print(f"或者修改 COMPOSITE_IMAGE_PATH 为你的合成图路径")
        return
    
    print(f"[OK] 合成图存在: {COMPOSITE_IMAGE_PATH}")
    
    # 步骤2: 上传合成图到公网（获取 URL）
    print("\n步骤2: 上传合成图到公网...")
    
    composite_url = upload_image_to_url(COMPOSITE_IMAGE_PATH)
    if not composite_url:
        return
    
    # 步骤3: 创建视频生成任务
    print("\n步骤3: 创建视频生成任务...")
    
    # 使用正面提示词（已验证效果更好）
    video_prompt = "The character with black hair and blue hoodie is walking in the cherry blossom scene, she remains clearly visible throughout the video, gentle breeze, petals floating, anime style"
    
    task_info = create_video_task(
        prompt=video_prompt,
        image_url=composite_url
    )
    
    if not task_info:
        print("[ERROR] 创建任务失败")
        return
    
    # 步骤4: 轮询结果
    print("\n步骤4: 等待视频生成（2-4分钟）...")
    
    video_url = poll_video_result(task_info["video_id"])
    
    if not video_url:
        print("[ERROR] 视频生成失败")
        return
    
    # 步骤5: 下载视频
    print("\n步骤5: 下载视频...")
    
    output_path = os.path.join(OUTPUT_DIR, "output_video.mp4")
    if not download_video(video_url, output_path):
        return
    
    print(f"\n{'='*60}")
    print("视频生成完成!")
    print(f"{'='*60}")
    print(f"\n[OK] 视频已保存: {output_path}")
    print(f"\n重要说明:")
    print(f"  - 使用合成图生成视频，角色不会消失")
    print(f"  - 如果角色仍然消失，说明合成图效果不好")
    print(f"  - 请重新运行 generate_composite_image.py 生成更好的合成图")
    print(f"\n提示: 视频路径: {output_path}")


if __name__ == "__main__":
    main()
