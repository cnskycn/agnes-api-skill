#!/usr/bin/env python3
"""
Agnes AI 图片多图合成测试

功能：测试角色+场景多图合成，对比5种不同提示词策略

测试结果（已验证）：
- 策略 D（仅输入场景图+文字描述角色）= 角色外观保留最好
- 策略 E（极详细描述）= 总体最佳（场景融合最自然）
- 核心限制：Agnes AI 多图合成是"参考重生成"，角色外观必然漂移

使用方法：
    python test_image_compose.py

输出：
- 5张测试合成图（PNG格式）
- 对比HTML页面（可在浏览器中查看）
"""

import os
import json
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


def download_image(url, save_path):
    """下载图片到本地"""
    print(f"[INFO] 下载图片: {save_path}")
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"[OK] 图片已保存!")
            return True
        else:
            print(f"[ERROR] 下载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] 下载失败: {e}")
        return False


def compose_images(char_url, scene_url, prompt, output_path, strategy_name):
    """合成角色图和场景图"""
    print(f"\n{'='*60}")
    print(f"合成测试: {strategy_name}")
    print(f"{'='*60}")
    
    # 构建请求
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt,
        "size": "1024x1024",
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
        output_path_full = os.path.join(OUTPUT_DIR, output_path)
        return download_image(result_url, output_path_full)
        
    except Exception as e:
        print(f"[ERROR] 合成失败: {e}")
        return False


def create_comparison_html(results):
    """创建对比 HTML 页面"""
    print(f"\n[INFO] 创建对比页面...")
    
    html_path = os.path.join(OUTPUT_DIR, "comparison.html")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agnes AI 图片合成测试对比</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; }
        .test-case { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .images { display: flex; justify-content: space-around; flex-wrap: wrap; }
        .image-box { text-align: center; margin: 10px; }
        .image-box img { max-width: 100%; height: auto; border-radius: 4px; }
        .prompt { background: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 3px solid #4CAF50; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Agnes AI 图片合成测试对比</h1>
""")
        
        for result in results:
            f.write(f"""
        <div class="test-case">
            <h2>{result['name']}</h2>
            <div class="prompt">
                <strong>提示词:</strong><br>
                {result['prompt']}
            </div>
            <div class="images">
                <div class="image-box">
                    <img src="{result['path']}" alt="{result['name']}">
                    <p>合成结果</p>
                </div>
            </div>
        </div>
""")
        
        f.write("""
    </div>
</body>
</html>
""")
    
    print(f"[OK] 对比页面已创建: {html_path}")
    return html_path


def main():
    """主函数"""
    print("="*60)
    print("Agnes AI 图片多图合成测试")
    print("="*60)
    
    # 步骤1: 生成测试用的角色图和场景图
    print("\n步骤1: 生成测试图片...")
    
    char_url = generate_image("anime girl with black hair, blue hoodie, front view", size="1024x1024")
    if not char_url:
        print("[ERROR] 角色图生成失败")
        return
    
    time.sleep(2)
    
    scene_url = generate_image("cherry blossom campus, anime background, no people", size="1024x1024")
    if not scene_url:
        print("[ERROR] 场景图生成失败")
        return
    
    print(f"\n[OK] 测试图片已生成")
    print(f"[INFO] 角色图 URL: {char_url[:50]}...")
    print(f"[INFO] 场景图 URL: {scene_url[:50]}...")
    
    # 保存原图
    download_image(char_url, os.path.join(OUTPUT_DIR, "character_original.png"))
    download_image(scene_url, os.path.join(OUTPUT_DIR, "scene_original.png"))
    
    # 步骤2: 测试5种提示词策略
    print("\n步骤2: 测试5种提示词策略...")
    
    test_cases = [
        {
            "name": "策略A - 强身份约束",
            "prompt": "保持角色的完整外观特征（黑发、蓝卫衣），将角色放入樱花校园场景中，保持角色身份完全一致",
            "output": "testA_strong_identity.png"
        },
        {
            "name": "策略B - 指定图片顺序",
            "prompt": "第一张图是角色，第二张图是场景，将角色自然地融入场景中",
            "output": "testB_order_matters.png"
        },
        {
            "name": "策略C - 仅角色图",
            "prompt": "将这张角色图自然地融入樱花校园场景中，保持角色外观不变",
            "output": "testC_char_only.png"
        },
        {
            "name": "策略D - 仅场景图（推荐）",
            "prompt": "一个黑发、穿蓝色卫衣的 anime 女孩站在樱花校园里，阳光透过樱花树洒在她身上",
            "output": "testD_scene_only.png"
        },
        {
            "name": "策略E - 极详细描述（总体最佳）",
            "prompt": "一个黑色长发、穿着淡蓝色连帽卫衣的 anime 女孩，站在樱花盛开的校园里，花瓣缓缓飘落，阳光透过树枝洒在她身上，角色外观完全保持，场景融合自然，anime 风格",
            "output": "testE_detailed.png"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}/{len(test_cases)}: {test_case['name']}")
        
        # 策略D特殊处理：只输入场景图
        if "策略D" in test_case['name']:
            success = compose_images(scene_url, None, test_case['prompt'], test_case['output'], test_case['name'])
        else:
            success = compose_images(char_url, scene_url, test_case['prompt'], test_case['output'], test_case['name'])
        
        if success:
            results.append({
                "name": test_case['name'],
                "prompt": test_case['prompt'],
                "path": test_case['output']
            })
        
        # 等待速率限制
        if i < len(test_cases):
            print(f"\n[INFO] 等待速率限制（70秒）...")
            time.sleep(70)
    
    # 步骤3: 创建对比页面
    if results:
        html_path = create_comparison_html(results)
        print(f"\n[OK] 测试完成!")
        print(f"[INFO] 对比页面: {html_path}")
        print(f"[INFO] 请在浏览器中打开查看结果")
    else:
        print(f"\n[ERROR] 所有测试都失败了")


if __name__ == "__main__":
    main()
