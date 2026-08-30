#!/usr/bin/env python3
"""
生成"角色在场景中"的合成图（推荐工作流）

问题：Agnes AI 视频生成的 `keyframes` 模式会导致角色慢慢透明消失
原因：在两张图片之间插值，角色图（第一帧）渐变到场景图（最后一帧）

解决方案：
1. 先生成"角色在场景中"的合成图（使用图片生成 API）
2. 再用这张合成图生成视频（只用一张图，避免插值问题）

使用方法：
    python generate_composite_image.py

输出：
- `composite_image.png` - 合成图
- 可直接用于视频生成
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


def generate_image(prompt, size="1024x1024", save_path=None):
    """生成图片并返回 URL，可选保存到本地"""
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
        
        # 可选：下载图片到本地
        if save_path:
            print(f"[INFO] 保存图片到: {save_path}")
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"[OK] 图片已保存!")
        
        return image_url
    except Exception as e:
        print(f"[ERROR] 图片生成失败: {e}")
        return None


def composite_images(char_url, scene_url, prompt, output_path):
    """合成角色图和场景图，生成"角色在场景中"的合成图"""
    print(f"\n{'='*60}")
    print(f"合成图片: 角色 + 场景")
    print(f"{'='*60}")
    
    # 构建请求
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt,
        "size": "1152x768",  # 视频比例
        "image": [char_url, scene_url]
    }
    
    print(f"[INFO] 创建合成任务...")
    print(f"[INFO] 提示词: {prompt[:80]}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/images/generations",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"[ERROR] 合成失败: {response.status_code}")
            print(f"[ERROR] 响应: {response.text}")
            return False
        
        data = response.json()
        result_url = data["data"][0]["url"]
        
        print(f"[OK] 合成成功!")
        print(f"[INFO] 结果 URL: {result_url[:100]}...")
        
        # 下载结果
        print(f"[INFO] 下载合成图...")
        output_path_full = os.path.join(OUTPUT_DIR, output_path)
        img_response = requests.get(result_url, timeout=30)
        if img_response.status_code == 200:
            with open(output_path_full, 'wb') as f:
                f.write(img_response.content)
            print(f"[OK] 合成图已保存: {output_path_full}")
            return output_path_full
        else:
            print(f"[ERROR] 下载失败: {img_response.status_code}")
            return False
        
    except Exception as e:
        print(f"[ERROR] 合成失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("生成"角色在场景中"的合成图")
    print("推荐工作流：先合成图片，再生成视频")
    print("="*60)
    
    # 步骤1: 生成角色图和场景图
    print("\n步骤1: 生成角色图和场景图...")
    
    char_url = generate_image(
        "anime girl with black hair, blue hoodie, front view, high quality",
        size="768x1024"
    )
    if not char_url:
        print("[ERROR] 角色图生成失败")
        return
    
    time.sleep(2)
    
    scene_url = generate_image(
        "cherry blossom campus, anime background, NO people, empty scene, high quality",
        size="1152x768"
    )
    if not scene_url:
        print("[ERROR] 场景图生成失败")
        return
    
    print(f"\n[OK] 测试图片已生成")
    
    # 保存原图
    generate_image("anime girl with black hair, blue hoodie", save_path=os.path.join(OUTPUT_DIR, "character.png"))
    generate_image("cherry blossom campus, NO people", save_path=os.path.join(OUTPUT_DIR, "scene.png"))
    
    # 步骤2: 合成图片
    print("\n步骤2: 合成角色和场景...")
    
    # 使用策略E（总体最佳）
    composite_prompt = "一个黑色长发、穿着淡蓝色连帽卫衣的 anime 女孩，站在樱花盛开的校园里，花瓣缓缓飘落，阳光透过树枝洒在她身上，角色外观完全保持，场景融合自然，anime 风格，高质量"
    
    composite_path = composite_images(
        char_url,
        scene_url,
        composite_prompt,
        "composite_image.png"
    )
    
    if not composite_path:
        print("[ERROR] 合成失败")
        return
    
    print(f"\n{'='*60}")
    print("合成完成!")
    print(f"{'='*60}")
    print(f"\n[OK] 合成图已保存: {composite_path}")
    print(f"\n下一步:")
    print(f"  1. 查看合成图，确认角色和场景是否融合自然")
    print(f"  2. 如果效果满意，运行 video_from_composite.py 生成视频")
    print(f"  3. 如果效果不满意，修改提示词重新合成")
    print(f"\n提示: 合成图路径: {composite_path}")


if __name__ == "__main__":
    main()
