#!/usr/bin/env python3
"""
Agnes AI 视频生成测试

功能：测试角色+场景视频生成，包含多种策略

测试结果（已验证）：
- `keyframes` 模式问题：角色会慢慢透明消失（图片间插值导致）
- 推荐方案：先生成"角色在场景中"的合成图，再用这张图生成视频
- 正面提示词 比负面提示词效果更好
- 速率限制：1次/分钟（需等待70秒）
- 生成时间：2-4分钟

使用方法：
    python test_video_gen.py

输出：
- 多个测试视频（MP4格式）
- 视频对比HTML页面
"""

import os
import time
import requests
from openai import OpenAI

# ========== 配置区域 ==========
API_KEY = "sk-ll5Knbh5VOgpFNoKAJ8Ax0W2QHcXRxupN7RY3SYgwLsAeF2O"  # 修改为你的 API Key
BASE_URL = "https://apihub.agnes-ai.cn"

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


def generate_image(prompt, size="1024x1024"):
    """生成图片并返回 URL"""
    print(f"[INFO] 生成图片...")
    print(f"[INFO] 提示词: {prompt[:80]}...")
    
    try:
        response = client.images.generate(
            model="agnes-image-2.1-flash",
            prompt=prompt,
            size=size
        )
        
        image_url = response.data[0].url
        print(f"[OK] 图片生成成功!")
        print(f"[INFO] URL: {image_url[:100]}...")
        return image_url
    except Exception as e:
        print(f"[ERROR] 图片生成失败: {e}")
        return None


def create_video_task(prompt, image_urls=None, mode="ti2vid", num_frames=121, frame_rate=24):
    """创建视频生成任务"""
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": prompt,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
        "width": 1152,
        "height": 768
    }
    
    if image_urls:
        if len(image_urls) == 1:
            payload["image"] = image_urls[0]
        else:
            payload["extra_body"] = {
                "image": image_urls,
                "mode": mode
            }
    
    print(f"\n[INFO] 创建视频任务...")
    print(f"[INFO] 提示词: {prompt[:80]}...")
    print(f"[INFO] 图片数量: {len(image_urls) if image_urls else 0}")
    
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


def wait_for_rate_limit(test_index, total_tests):
    """等待速率限制（1次/分钟）"""
    if test_index < total_tests:
        wait_time = 70  # 等待70秒（保险）
        print(f"\n[INFO] 速率限制: 等待 {wait_time} 秒...")
        time.sleep(wait_time)


def main():
    """主函数"""
    print("="*60)
    print("Agnes AI 视频生成测试")
    print("="*60)
    
    # 步骤1: 生成测试用的角色图和场景图
    print("\n步骤1: 生成测试图片...")
    
    char_url = generate_image("anime girl with black hair, blue hoodie", size="768x1024")
    if not char_url:
        print("[ERROR] 角色图生成失败")
        return
    
    time.sleep(2)
    
    scene_url = generate_image("cherry blossom campus, anime background, no people", size="1152x768")
    if not scene_url:
        print("[ERROR] 场景图生成失败")
        return
    
    print(f"\n[OK] 测试图片已生成")
    
    # 保存原图
    os.system(f"curl -s {char_url} -o {OUTPUT_DIR}/character.png")
    os.system(f"curl -s {scene_url} -o {OUTPUT_DIR}/scene.png")
    
    # 步骤2: 测试3种视频生成策略
    print("\n步骤2: 测试视频生成策略...")
    
    test_cases = [
        {
            "name": "Test1_Character_Only",
            "prompt": "The character stands in cherry blossom campus, gentle breeze, petals fall, smile, anime style",
            "images": [char_url],
            "mode": "ti2vid",
            "description": "仅角色图 - 让角色动起来"
        },
        {
            "name": "Test2_Scene_Only",
            "prompt": "Cherry blossom campus, petals falling, sunlight through trees, camera moving, peaceful, cinematic",
            "images": [scene_url],
            "mode": "ti2vid",
            "description": "仅场景图 - 让场景动起来"
        },
        {
            "name": "Test3_Both_Keyframes",
            "prompt": "Character walks through cherry blossom campus, petals falling, she smiles at camera, anime style",
            "images": [char_url, scene_url],
            "mode": "keyframes",
            "description": "角色+场景 - 关键帧动画（注意：角色可能会消失）"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"描述: {test_case['description']}")
        print(f"{'='*60}")
        
        # 创建任务
        task_info = create_video_task(
            prompt=test_case["prompt"],
            image_urls=test_case["images"],
            mode=test_case.get("mode", "ti2vid")
        )
        
        if not task_info:
            print(f"[ERROR] 创建任务失败")
            continue
        
        # 轮询结果
        video_url = poll_video_result(task_info["video_id"])
        
        if video_url:
            # 下载视频
            output_path = os.path.join(OUTPUT_DIR, f"{test_case['name']}.mp4")
            if download_video(video_url, output_path):
                results.append({
                    "name": test_case['name'],
                    "description": test_case['description'],
                    "path": output_path,
                    "url": video_url
                })
        
        # 等待速率限制
        wait_for_rate_limit(i, len(test_cases))
    
    # 步骤3: 输出结果
    print(f"\n{'='*60}")
    print("测试结果的要")
    print(f"{'='*60}")
    
    if results:
        for result in results:
            print(f"\n[OK] {result['name']}")
            print(f"     描述: {result['description']}")
            print(f"     路径: {result['path']}")
        
        print(f"\n[INFO] 请查看输出目录: {OUTPUT_DIR}")
        print(f"[INFO] 请手动播放视频，评估效果")
    else:
        print(f"\n[ERROR] 所有测试都失败了")


if __name__ == "__main__":
    main()
