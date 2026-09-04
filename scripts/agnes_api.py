#!/usr/bin/env python3
"""
Agnes API 生成脚本
支持：
  1. 文本对话（Chat） — agnes-2.0-flash（支持流式、Thinking、工具调用）
  2. 文生图（Text-to-Image） — agnes-image-2.5-flash（首选）、agnes-image-2.1-flash（兼容）
  3. 图生图/编辑（Image-to-Image） — agnes-image-2.5-flash（推荐，无需 tags）
  4. 多图合成（Multi-Image Composition） — agnes-image-2.5-flash（首选）或 agnes-image-2.0-flash（需 seed）
  5. 文生视频/图生视频/关键帧动画（异步任务） — agnes-video-v2.0 / agnes-video-2.5-flash

用法:
  # 首次使用：引导式配置 API Key（只需运行一次）
  python agnes_api.py setup

  # 文本对话
  python agnes_api.py chat --prompt "你好，请介绍一下自己" --stream
  python agnes_api.py chat --prompt "用Python写一个贪吃蛇游戏" --system "你是一位资深Python工程师" --thinking

  # 文生图（默认用 2.5-flash）
  python agnes_api.py image --prompt "一只柴犬在樱花树下" --size 2K --ratio 16:9

  # 图生图（编辑图片）
  python agnes_api.py image --prompt "改成水彩画风格" --size 2K --ratio 4:3 --image "https://example.com/photo.jpg"

  # 多图合成
  python agnes_api.py image --prompt "融合两张图" --size 2K --image "https://ex.com/a.jpg" --image "https://ex.com/b.jpg"

  # 旧模型兼容
  python agnes_api.py image --prompt "测试" --model agnes-image-2.1-flash --size 1024x1024

  # 文生视频
  python agnes_api.py video --prompt "A cinematic shot of a cat walking on the beach" --frames 121 --fps 24

  # 图生视频（2.5-flash）
  python agnes_api.py video --prompt "A cat walking on beach" --model agnes-video-2.5-flash --mode text

  # 关键帧视频（2.5-flash）
  python agnes_api.py video --prompt "Transition" --model agnes-video-2.5-flash --mode keyframe --image first.jpg --image second.jpg

API Key 配置（三种方式，优先级从高到低）:
  1. 命令行参数: --api-key sk-xxx
  2. 环境变量:   AGNES_API_KEY=sk-xxx
  3. 配置文件:   ~/.agnes/config.json  （运行 setup 子命令自动创建）
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from openai import OpenAI

API_BASE = "https://apihub.agnes-ai.cn/v1"
CONFIG_DIR = os.path.expanduser("~/.agnes")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_api_key() -> str | None:
    """按优先级读取 API Key：环境变量 > 配置文件"""
    key = os.environ.get("AGNES_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            key = cfg.get("api_key", "")
            if key:
                return key.strip()
        except Exception:
            pass
    return None


def save_api_key(key: str):
    """保存 API Key 到本地配置文件"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg["api_key"] = key.strip()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"✅ API Key 已保存到 {CONFIG_FILE}")


def get_api_key() -> str:
    key = load_api_key()
    if key:
        return key
    print("""
╔══════════════════════════════════════════════════════════════╗
║  尚未配置 Agnes API Key                                        ║
║                                                                ║
║  请先注册并获取免费 API Key：                                   ║
║  1. 访问 https://platform.agnes-ai.com                        ║
║  2. 注册账号（支持邮箱/手机验证码登录）                         ║
║  3. 登录后进入「API 管理」→「创建 API Key」                   ║
║  4. 复制生成的 Key（格式如 sk-xxxxxxxx...）                    ║
║                                                                ║
║  💡 提示：运行以下命令可引导式保存 Key（只需一次）：           ║
║     python agnes_api.py setup                                   ║
╚══════════════════════════════════════════════════════════════╝
""")
    key = input("请输入 Agnes API Key: ").strip()
    if not key:
        print("错误：API Key 不能为空", file=sys.stderr)
        sys.exit(1)
    save = input("是否保存到本地（~/.agnes/config.json）避免下次输入？(Y/n): ").strip().lower()
    if save != "n":
        save_api_key(key)
    return key


def cmd_setup(args):
    """引导用户注册并保存 API Key"""
    print("""
==========================================================
  Agnes AI API Key 配置向导
==========================================================

  Step 1: 注册账号
    访问 👉 https://platform.agnes-ai.com
    - 点击右上角「注册」
    - 支持邮箱注册或手机验证码登录
    - 注册完成后自动登录

  Step 2: 创建 API Key
    - 登录后点击顶部导航「API 管理」
    - 点击「创建 API Key」按钮
    - 给 Key 取个名字（如：my-key）
    - 点击「生成」，复制显示的 Key
    - ⚠️ Key 只显示一次，请务必复制保存！

  Step 3: 粘贴 Key 到下方
==========================================================

提示：Agnes AI API 完全免费，无限期开放
""")
    key = input("请粘贴你的 API Key（以 sk- 开头）：").strip()
    if not key:
        print("❌ 未输入 Key，已取消。")
        sys.exit(1)
    if not key.startswith("sk-"):
        print("⚠️ 警告：API Key 通常以 sk- 开头，请确认是否输入正确？")
        confirm = input("仍要继续？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            sys.exit(0)

    save_api_key(key)

    # 测试 Key 是否有效
    print("\n正在测试 API Key...")
    try:
        client = OpenAI(api_key=key, base_url=API_BASE)
        response = client.chat.completions.create(
            model="agnes-2.0-flash",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10,
        )
        print(f"✅ API Key 有效！模型响应：{response.choices[0].message.content}")
    except Exception as e:
        print(f"⚠️ API Key 测试失败：{e}")
        print("请检查 Key 是否正确，或重新运行 python agnes_api.py setup")
        sys.exit(1)

    print(f"""
==========================================================
  ✅ 配置完成！
==========================================================

  以后运行以下命令时无需再输入 Key：
    python agnes_api.py image --prompt "一只猫"
    python agnes_api.py video --prompt "A cat walking"
    python agnes_api.py chat  --prompt "你好"

  配置文件位置：{CONFIG_FILE}
  如需更换 Key，重新运行：python agnes_api.py setup
==========================================================
""")


def resolve_images(images: list[str]) -> list[str]:
    """将图片路径列表统一为 URL（本地路径转 data URI）"""
    urls = []
    for img in images:
        if img.startswith(("http://", "https://", "data:")):
            urls.append(img)
        else:
            if not os.path.exists(img):
                print(f"错误: 文件不存在 - {img}", file=sys.stderr)
                sys.exit(1)
            with open(img, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(img)[1].lower()
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".webp": "image/webp",
                    ".gif": "image/gif"}.get(ext, "image/png")
            urls.append(f"data:{mime};base64,{b64}")
    return urls


# ─── 图像生成 ─────────────────────────────────────────────


def cmd_image(args):
    api_key = get_api_key()
    client = OpenAI(api_key=api_key, base_url=API_BASE)

    # 模型选择逻辑（对照官方文档 2026-09-04）：
    # - 文生图/图生图/多图合成：默认 agnes-image-2.5-flash（首选）
    # - 需要 seed 复现：agnes-image-2.0-flash
    # - 指定旧模型时按用户选择
    model = args.model or "agnes-image-2.5-flash"
    is_img2img = args.images is not None and len(args.images) > 0
    multi_image = is_img2img and len(args.images) > 1

    # 多图合成且需要 seed → 强制 2.0-flash
    if multi_image and args.seed is not None:
        model = "agnes-image-2.0-flash"

    kwargs = {"model": model, "prompt": args.prompt}

    # size 和 ratio 参数
    if args.size:
        kwargs["size"] = args.size
    if args.ratio:
        kwargs["ratio"] = args.ratio

    if is_img2img:
        extra = {"image": resolve_images(args.images)}
        # 2.0-flash 多图合成必须加 tags
        if model == "agnes-image-2.0-flash":
            extra["tags"] = ["img2img"]
        else:
            # 2.5-flash / 2.1-flash：不需要 tags
            pass
        # response_format 只对支持的模式添加
        if model != "agnes-image-2.0-flash" and args.output_format == "b64_json":
            extra["response_format"] = "b64_json"
        kwargs["extra_body"] = extra
    else:
        # 纯文生图可用 return_base64（2.5-flash 支持）
        if args.output_format == "b64_json":
            kwargs["return_base64"] = True

    if args.seed is not None:
        kwargs["seed"] = args.seed

    print(f"使用模型: {model}")
    print(f"Prompt: {args.prompt}")
    size_info = f"{args.size}" if args.size else "default"
    if args.ratio:
        size_info += f" + ratio={args.ratio}"
    print(f"尺寸: {size_info}")
    if multi_image:
        print(f"多图合成（{len(args.images)} 张）")
        if model == "agnes-image-2.0-flash":
            print("⚠️ 使用 2.0-flash（支持 seed 复现）")

    try:
        response = client.images.generate(**kwargs)
    except Exception as e:
        print(f"API 调用失败: {e}", file=sys.stderr)
        sys.exit(1)

    for i, data in enumerate(response.data):
        if args.output_format == "b64_json":
            result = data.b64_json
            print(f"图片 {i+1}: (base64, {len(result)} chars)")
        else:
            result = data.url
            print(f"图片 {i+1}: {result[:80]}...")
        if args.save and i == 0:
            if args.output_format == "url":
                print(f"正在下载到: {args.save} ...")
                urllib.request.urlretrieve(result, args.save)
                print(f"已保存: {args.save}")
            else:
                with open(args.save, "wb") as f:
                    f.write(base64.b64decode(result))
                print(f"已保存（base64）: {args.save}")


# ─── 视频生成 ─────────────────────────────────────────────


def cmd_video(args):
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 根据模型选择参数
    if args.model == "agnes-video-2.5-flash":
        # 2.5-flash：三种模式支持
        body = {
            "model": "agnes-video-2.5-flash",
            "prompt": args.prompt,
            "mode": args.mode,  # "text", "keyframe", or "reference"
            "size": "720P",
            "seconds": str(args.seconds),
        }
        if args.aspect_ratio:
            body["aspect_ratio"] = args.aspect_ratio
        if args.seconds:
            body["seconds"] = str(args.seconds)
        if args.negative:
            body["negative_prompt"] = args.negative
        if args.seed is not None:
            body["seed"] = args.seed

        # 处理图片参数
        if args.images and len(args.images) > 0:
            urls = resolve_images(args.images)
            if args.mode in ("keyframe", "reference"):
                if args.mode == "keyframe":
                    if len(urls) >= 1:
                        body["first_frame"] = urls[0]
                    if len(urls) >= 2:
                        body["last_frame"] = urls[1]
                else:  # reference
                    body["images"] = urls[:5]  # 最多5张
        else:
            if args.mode != "text":
                print(f"警告: mode={args.mode} 需要图片输入，将自动切换为 text 模式", file=sys.stderr)
                body["mode"] = "text"

        print(f"使用模型: agnes-video-2.5-flash")
        print(f"Prompt: {args.prompt}")
        print(f"模式: {body['mode']}")
        print(f"尺寸: 720P, {body.get('aspect_ratio', '16:9')}")
        print(f"时长: {body['seconds']}秒")
    else:
        # v2.0：完整参数支持
        body = {
            "model": "agnes-video-v2.0",
            "prompt": args.prompt,
            "height": args.height,
            "width": args.width,
            "num_frames": args.frames,
            "frame_rate": args.fps,
        }

        if args.negative:
            body["negative_prompt"] = args.negative
        if args.seed is not None:
            body["seed"] = args.seed

        # 处理图片参数
        if args.images and len(args.images) > 0:
            urls = resolve_images(args.images)
            if args.mode == "keyframes" or len(args.images) > 1:
                body["extra_body"] = {"image": urls}
                if args.mode == "keyframes":
                    body["extra_body"]["mode"] = "keyframes"
            else:
                body["image"] = urls[0]

        seconds = args.frames / args.fps

        # 校验 num_frames 是否合法
        VALID_FRAMES = {81, 121, 161, 201, 241, 281, 321, 361, 401, 441}
        if args.frames not in VALID_FRAMES:
            print(f"错误: num_frames={args.frames} 非法！仅支持: {sorted(VALID_FRAMES)}", file=sys.stderr)
            sys.exit(1)

        print(f"使用模型: agnes-video-v2.0")
        print(f"Prompt: {args.prompt}")
        print(f"尺寸: {args.width}x{args.height}")
        print(f"时长: ~{seconds:.1f}s ({args.frames}帧 @ {args.fps}fps)")
        print(f"模式: {args.mode if args.mode == 'keyframes' else '标准'}")

    # 创建任务
    import requests
    try:
        resp = requests.post(f"{API_BASE}/videos",
                             headers=headers, json=body, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"创建任务失败: {e}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    task_id = data.get("task_id") or data.get("id")
    video_id = data.get("video_id", "")
    print(f"任务创建成功: {task_id}")
    print(f"Video ID: {video_id}")

    # 轮询结果（优先使用 video_id + agnesapi 推荐方式）
    poll_interval = args.poll
    timeout_total = args.timeout
    start_time = time.time()
    use_agnesapi = bool(video_id)  # 有 video_id 就用推荐方式

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_total:
            print(f"超时退出（{timeout_total}s）", file=sys.stderr)
            print(f"可手动查询:")
            print(f"  推荐: GET https://apihub.agnes-ai.cn/agnesapi?video_id={video_id}")
            print(f"  旧版: GET {API_BASE}/videos/{task_id}")
            sys.exit(1)

        try:
            if use_agnesapi:
                query_url = f"https://apihub.agnes-ai.cn/agnesapi?video_id={video_id}"
            else:
                query_url = f"{API_BASE}/videos/{task_id}"
            result = requests.get(query_url, headers=headers, timeout=30).json()
        except Exception as e:
            print(f"查询失败: {e}，{poll_interval}s 后重试...")
            time.sleep(poll_interval)
            continue

        status = result.get("status", "unknown")
        progress = result.get("progress", 0)
        print(f"[{elapsed:.0f}s] 状态: {status}  进度: {progress}%")

        if status == "completed":
            # 视频 URL 位置因模型而异：
            # - v2.0: result["url"] 或 result["remixed_from_video_id"]
            # - 2.5-flash: result["metadata"]["url"]
            video_url = (result.get("video_url") or
                        result.get("url") or
                        result.get("remixed_from_video_id") or
                        (result.get("metadata") or {}).get("url"))
            if not video_url:
                print(f"错误: 响应中没有视频 URL，完整响应: {json.dumps(result, indent=2)}", file=sys.stderr)
                sys.exit(1)
            print(f"视频生成完成!")
            print(f"视频 URL: {video_url}")
            if args.save:
                print(f"正在下载到: {args.save} ...")
                urllib.request.urlretrieve(video_url, args.save)
                print(f"已保存: {args.save}")
            break
        elif status == "failed":
            err = result.get("error", "未知错误")
            print(f"生成失败: {err}", file=sys.stderr)
            sys.exit(1)

        time.sleep(poll_interval)


# ─── 文本对话 ─────────────────────────────────────────────


def cmd_chat(args):
    """文本对话（agnes-2.0-flash / agnes-1.5-flash）"""
    api_key = get_api_key()
    client = OpenAI(api_key=api_key, base_url=API_BASE)

    messages = [{"role": "user", "content": args.prompt}]
    if args.system:
        messages.insert(0, {"role": "system", "content": args.system})

    kwargs = {
        "model": args.model,
        "messages": messages,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.stream:
        kwargs["stream"] = True
    if args.thinking:
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}

    print(f"模型: {args.model}")
    print(f"System: {args.system or '(无)'}")
    print(f"User: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}")
    print()

    try:
        if args.stream:
            print("--- 流式输出 ---")
            full = ""
            for chunk in client.chat.completions.create(**kwargs):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full += content
            print()
            if args.save:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(full)
                print(f"\n已保存: {args.save}")
        else:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            print(content)
            if args.save:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"\n已保存: {args.save}")
    except Exception as e:
        print(f"API 调用失败: {e}", file=sys.stderr)
        sys.exit(1)


# ─── 主入口 ─────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Agnes API - 文本对话 / 图像生成 / 视频生成"
    )
    parser.add_argument("--save", type=str, help="保存结果到本地路径")
    parser.add_argument("--api-key", type=str, help="API Key（优先级高于环境变量）")

    sub = parser.add_subparsers(dest="command", required=True)

    # image 子命令
    img_p = sub.add_parser("image", help="图像生成（文生图/图生图/多图合成）")
    img_p.add_argument("--prompt", type=str, required=True, help="图片描述或编辑指令")
    img_p.add_argument("--model", type=str, default=None,
                       choices=["agnes-image-2.5-flash", "agnes-image-2.1-flash", "agnes-image-2.0-flash"],
                       help="图像模型（默认 agnes-image-2.5-flash）")
    img_p.add_argument("--size", type=str, default=None,
                       help="输出尺寸。推荐档位：1K/2K/3K/4K，或精确如 1024x1024")
    img_p.add_argument("--ratio", type=str, default=None,
                       help="宽高比（仅 2.5-flash 有效）：1:1/3:4/4:3/16:9/9:16/2:3/3:2/21:9")
    img_p.add_argument("--image", type=str, action="append", dest="images",
                       help="输入图片（URL 或本地路径，多张触发多图合成）")
    img_p.add_argument("--output-format", type=str,
                       choices=["url", "b64_json"], default="url",
                       help="输出格式：url（默认，下载到本地）或 b64_json（base64编码）")
    img_p.add_argument("--seed", type=int, default=None, help="随机种子（仅 2.0-flash 支持）")
    img_p.set_defaults(func=cmd_image)

    # video 子命令
    vid_p = sub.add_parser("video", help="视频生成（文生视频/图生视频/关键帧）")
    vid_p.add_argument("--prompt", type=str, required=True, help="视频内容描述")
    vid_p.add_argument("--image", type=str, action="append", dest="images",
                       help="输入图片 URL 或本地路径")
    vid_p.add_argument("--mode", type=str, choices=["text", "keyframe", "reference", "keyframes"],
                       default="text", help="生成模式（2.5-flash 支持 text/keyframe/reference）")
    vid_p.add_argument("--model", type=str, choices=["agnes-video-v2.0", "agnes-video-2.5-flash"],
                       default="agnes-video-v2.0", help="视频模型")
    vid_p.add_argument("--aspect-ratio", type=str, default=None,
                       help="视频宽高比（仅 2.5-flash 有效）：16:9/4:3/9:16/1:1")
    vid_p.add_argument("--seconds", type=int, default=5,
                       help="视频时长（仅 2.5-flash 有效，4-12秒）")
    vid_p.add_argument("--width", type=int, default=1152, help="视频宽度（仅 v2.0 有效）")
    vid_p.add_argument("--height", type=int, default=768, help="视频高度（仅 v2.0 有效）")
    vid_p.add_argument("--frames", type=int, default=121,
                       help="帧数，合法值: 81/121/161/201/241/281/321/361/401/441（仅 v2.0）")
    vid_p.add_argument("--fps", type=float, default=24,
                       help="帧率（1-60）（仅 v2.0 有效）")
    vid_p.add_argument("--negative", type=str, help="负向提示词")
    vid_p.add_argument("--seed", type=int, help="随机种子")
    vid_p.add_argument("--poll", type=int, default=10,
                       help="轮询间隔（秒）")
    vid_p.add_argument("--timeout", type=int, default=600,
                       help="超时时间（秒）")
    vid_p.add_argument("--save", type=str, help="视频保存路径")
    vid_p.set_defaults(func=cmd_video)

    # chat 子命令
    chat_p = sub.add_parser("chat", help="文本对话（agnes-2.0-flash）")
    chat_p.add_argument("--prompt", type=str, required=True, help="用户输入文本")
    chat_p.add_argument("--system", type=str, help="系统提示词（System Prompt）")
    chat_p.add_argument("--model", type=str, default="agnes-2.0-flash",
                        help="文本模型（仅 agnes-2.0-flash）")
    chat_p.add_argument("--temperature", type=float, default=0.7,
                        help="温度参数 0-2（默认0.7，创意任务可提高）")
    chat_p.add_argument("--max-tokens", type=int, default=4096,
                        help="最大输出 token 数")
    chat_p.add_argument("--stream", action="store_true",
                        help="流式输出（逐字显示）")
    chat_p.add_argument("--thinking", action="store_true",
                        help="启用 Thinking 模式（仅 agnes-2.0-flash）")
    chat_p.add_argument("--save", type=str, help="保存回复到文件")
    chat_p.set_defaults(func=cmd_chat)

    # setup 子命令
    setup_p = sub.add_parser("setup", help="引导式配置 API Key（首次使用必选）")
    setup_p.set_defaults(func=cmd_setup)

    args = parser.parse_args()

    if args.api_key:
        os.environ["AGNES_API_KEY"] = args.api_key

    args.func(args)


if __name__ == "__main__":
    main()
