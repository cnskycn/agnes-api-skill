---
name: agnes-api-skill
description: 通过 Agnes AI 模型进行文生图、图生图、多图合成及文生视频/图生视频。当用户要求生成、编辑、修改图片或生成视频时触发。OpenAI 兼容接口，API Key 免费获取。
agent_created: true
---

# Agnes Image & Video API

## Overview

Agnes AI API 调用 Agnes AI 实验室的图像和视频生成模型，覆盖两大模态：

- **图像**：Agnes-Image-2.1-Flash（文生图）、Agnes-Image-2.0-Flash（图生图/多图合成）
- **视频**：Agnes-Video-2.5-Flash（新一代快速视频模型）、Agnes-Video-V2.0（经典视频模型）

图像接口兼容 OpenAI `/v1/images/generations` 协议，视频采用异步任务模式（`POST /v1/videos` + `GET /v1/videos/{task_id}`）。

**免费政策**：自 2026年6月1日起无限期免费开放，需在 platform.agnes-ai.com 注册获取 API Key。

## 快速开始（首次使用必读）

### 第一步：获取免费 API Key

Agnes AI 完全免费，按以下步骤获取 API Key（只需操作一次）：

1. **打开注册页面**  
   浏览器访问：https://platform.agnes-ai.com  
   → 点击右上角「注册」按钮

2. **注册账号**  
   支持两种方式：
   - 邮箱注册：输入邮箱 → 收取验证码 → 设置密码
   - 手机注册：输入手机号 → 收取短信验证码 → 设置密码

3. **创建 API Key**  
   登录后：
   - 点击顶部导航栏「**API 管理**」
   - 点击「**创建 API Key**」按钮
   - 给 Key 取个名字（如 `my-pc`，随意填）
   - 点击「**生成**」
   - **⚠️ 重要：Key 只显示一次！** 立即点击复制，保存到记事本

   API Key 格式示例：`sk-ll5Knbh5VOgpFNoKAJ8Ax0W2QHcXRxupN7RY3SYgwLsAeF2O`

4. **验证 Key 是否有效**  
   注册后免费额度立即生效，无需绑卡或付费。

### 第二步：配置 API Key（两种方案）

**方案 A — 运行引导式配置（推荐，最简单）**

```bash
python agnes_api.py setup
```

脚本会：
- 提示你粘贴 API Key
- 自动保存到 `~/.agnes/config.json`
- 测试 Key 是否有效
- 以后运行任何命令都不再需要输入 Key

**方案 B — 手动配置（适合开发者）**

设置环境变量：
```bash
# Linux / macOS
export AGNES_API_KEY="sk-你的Key"

# Windows PowerShell
$env:AGNES_API_KEY="sk-你的Key"
```

或直接编辑配置文件：
```bash
# 创建配置文件
echo '{"api_key": "sk-你的Key"}' > ~/.agnes/config.json
```

### 第三步：开始使用

配置完成后，直接运行命令即可：

```bash
# 生成图片
python agnes_api.py image --prompt "一只柴犬在樱花树下" --size 1024x1024 --save result.jpg

# 生成视频
python agnes_api.py video --prompt "A cat walking on the beach" --frames 121 --save result.mp4

# 文本对话
python agnes_api.py chat --prompt "你好，介绍一下你自己" --stream
```

> 💡 **提示**：如果看到 `尚未配置 Agnes API Key` 的提示，说明你跳过了第二步，请先运行 `python agnes_api.py setup`。

## Prerequisites

- **API Key**：免费注册获取，详见上方「快速开始」章节
- **Python 依赖**：`pip install openai requests`（仅本地运行脚本需要）

## Core Capabilities

### 模型选择指南

| 需求场景 | 推荐模型 | 原因 |
|----------|----------|------|
| 从零生成图片（文生图） | `agnes-image-2.1-flash` | 针对高信息密度图像专项优化 |
| 编辑现有图片（单图图生图） | `agnes-image-2.1-flash` | 支持图生图，**不需要 tags**，更简单 |
| 多图合成/融合（将多张图合并为一张） | `agnes-image-2.1-flash` | 实测可传多张图做融合，**无需 tags** |
| 多图合成且需要固定种子 | `agnes-image-2.0-flash` | 需要 `tags: ["img2img"]`，支持 `seed` |
| **视频生成（速度优先）** | **`agnes-video-2.5-flash`** | **新一代快速模型，30秒完成，720P/5秒，支持 text/reference/keyframe 三种模式** |
| **视频生成（质量/参数优先）** | `agnes-video-v2.0` | 支持自定义分辨率、帧数、帧率 + 图生视频 |

> ⚠️ **重要**：`agnes-image-2.1-flash` **支持图生图与多图合成**！只需在 `extra_body.image` 中传入图片 URL 数组，**不需要** `tags: ["img2img"]`。相比 2.0-flash，2.1-flash 更省事。
> `agnes-image-2.0-flash` 仅在需要 `seed` 复现结果或明确使用 `tags: ["img2img"]` 时使用。

### 1. 文生图（Text-to-Image）

使用 `agnes-image-2.1-flash` 模型，通过文本描述直接生成图片。

**接口**：`POST /v1/images/generations`

**参数**：

| 参数 | 必填 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| `model` | 是 | string | 模型名称，固定为 `"agnes-image-2.1-flash"` | — |
| `prompt` | 是 | string | 图片描述文本，越详细越好 | `"一只可爱的柴犬在樱花树下睡觉"` |
| `size` | 否 | string | 输出图像尺寸 | `"1024x1024"`, `"1024x768"`, `"768x1024"` |
| `extra_body.image` | 否 | array | 输入图像 URL 数组（图生图时用） | `["https://..."]` |
| `extra_body.response_format` | 否 | string | 响应格式，默认返回 URL | `"url"` |

> ⚠️ **`agnes-image-2.1-flash` 不支持 `seed` 参数**，设置会导致 422 错误。如需复现结果请使用 `agnes-image-2.0-flash`。
> 
> ⚠️ **`response_format` 不能放在顶层**！必须放在 `extra_body` 里（如 `extra_body.response_format: "url"`），否则会报 400 错误。也可省略，默认返回 URL。

**文生图 + Base64 输出**（不需要额外参数，用 `return_base64: true`）：

```python
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="一只可爱的柴犬在樱花树下睡觉",
    size="1024x1024",
    extra_body={
        "response_format": "b64_json"  # 返回 base64 编码
    }
)
print(response.data[0].b64_json[:50], "...")  # base64 字符串
```

### 2. 图生图/图片编辑（Image-to-Image）

> ⚠️ **重要（对照官方文档 2026-07-01）**：`agnes-image-2.1-flash` **也支持图生图**，且**不需要 `tags` 参数**！推荐优先使用 2.1-flash。
> `agnes-image-2.0-flash` 仅用于**多图合成**（唯一支持）或需要 `seed` 复现结果的场景。

#### 2.1 使用 `agnes-image-2.1-flash` 图生图（推荐）

最简单的方式：在 `extra_body.image` 中传入图片 URL 即可，**不需要 `tags`**。

**参数**：

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `model` | 顶层 | 是 | `"agnes-image-2.1-flash"` |
| `prompt` | 顶层 | 是 | 编辑指令，描述要做的修改 |
| `size` | 顶层 | 否 | 输出尺寸 |
| `extra_body.image` | extra_body | 是 | 输入图片 URL 列表（单张或多张） |
| `extra_body.response_format` | extra_body | 否 | `"url"`（默认）或 `"b64_json"` |

> ⚠️ **`response_format` 必须放在 `extra_body` 里**！放在顶层会导致 400 错误。

**Python 调用示例（单图编辑，URL 输出）**：

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的 Agnes API Key",
    base_url="https://apihub.agnes-ai.cn/v1"
)

# 单图编辑（推荐方式，用 agnes-image-2.1-flash）
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="把这张照片改成水彩画风格，保留原始构图",
    size="1024x768",
    extra_body={
        "image": ["https://example.com/photo.png"],
        "response_format": "url"
    }
)
print(response.data[0].url)
```

**Python 调用示例（本地图片，Base64 输出）**：

```python
import base64

# 读取本地图片转为 Data URI
with open("photo.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"

# 图生图（Base64 输出，图片不需要公网 URL）
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="Make the object orange while preserving the original composition",
    size="1024x768",
    extra_body={
        "image": [data_uri],
        "response_format": "b64_json"
    }
)
print(response.data[0].b64_json[:50], "...")
```

#### 2.2 使用 `agnes-image-2.0-flash`（仅多图合成或需要 seed 时用）

> ⚠️ `agnes-image-2.0-flash` 的图生图**需要** `extra_body.tags: ["img2img"]`，且**不支持** `extra_body.response_format`（会导致 400 错误）。

```python
# 仅当需要固定种子复现结果时使用 2.0-flash
response = client.images.generate(
    model="agnes-image-2.0-flash",
    prompt="把这张照片改成赛博朋克风格",
    size="1024x1024",
    seed=42,  # 固定种子，相同种子+相同输入 = 相同输出
    extra_body={
        "tags": ["img2img"],
        "image": ["https://example.com/photo.png"]
    }
)
print(response.data[0].url)
```

### 3. 多图合成（Multi-Image Composition）

> ⚠️ **多图合成（将多张参考图融合为一张）可用 `agnes-image-2.1-flash`，也可以继续用 `agnes-image-2.0-flash`**。
>
> 当前实测结果（2026-07-15）：
> - **`2.1-flash`**：在 `extra_body.image` 中传多张图即可，**不需要 `tags`**，实测已能融合角色+场景。
> - **`2.0-flash`**：需要 `extra_body.tags: ["img2img"]`，支持 `seed`。
>
> 官方 2.1 文档只文档化了单图图生图示例，未明确说明多图融合行为，但接口层面已可正常工作。若追求稳定/复现，推荐 2.1-flash 测试通过后再大规模使用，或继续用 2.0-flash + `tags`。

使用 `agnes-image-2.1-flash`（多图合成，无需 tags）：

```python
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="Keep the character's appearance unchanged and place her naturally into the cherry-blossom scene, anime style",
    size="1024x1024",
    extra_body={
        "image": [
            "https://example.com/character.png",  # 第一张参考图（如角色）
            "https://example.com/scene.png"        # 第二张参考图（如场景）
        ],
        "response_format": "url"  # 可选
    }
)
```

使用 `agnes-image-2.0-flash`（多图合成，需要 tags）：

```python
response = client.images.generate(
    model="agnes-image-2.0-flash",
    prompt="将人物自然地融入背景场景中，保持光影一致，日系动漫风格",
    size="1024x1024",
    extra_body={
        "tags": ["img2img"],
        "image": [
            "https://example.com/character.png",
            "https://example.com/scene.png"
        ]
        # ⚠️ 不要加 response_format（2.0-flash 不支持）
    }
)
```

**关键差异**：

| 策略 | Prompt 示例 | 效果 | 适用场景 |
|------|------------|------|---------|
| 直接合并 | "将人物自然地融入背景场景中，保持光影一致" | 写实风，融合自然 | 写实项目 |
| 保持身份 | "保持人物的完整外观和特征，将其放置在场景环境中" | 叙事感强，氛围好 | 通用 |
| 视觉小说风格 | "日系动漫风格，视觉小说立绘，将角色融入背景，保持动漫画风统一" | ⭐ 动漫风完美统一 | **VN/视觉小说项目推荐** |

#### ⚠️ 重要：角色一致性局限性

**核心发现**（2026-07-01 实测验证）：

Agnes AI 的多图合成功能，**本质上是"参考输入图片进行重新生成"，而不是"将角色图贴到场景图中"**。

这意味着：
- ❌ **即使使用最强的提示词约束，角色外观仍然会有一定变化**
- ❌ 发色、服装、姿态、面部特征都可能被模型"重新诠释"
- ✅ 场景融合效果可以达到很自然的程度

**测试结果**（5种提示词策略对比）：

| 策略 | 角色外观保留 | 场景融合 | 总体评分 | 说明 |
|------|------------|---------|---------|------|
| A. 强身份约束（英文） | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 详细列举特征，但效果有限 |
| B. 指定图片顺序 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 明确图片分工，帮助不大 |
| C. 仅输入角色图+文字描述场景 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 角色保留较好，场景融合一般 |
| D. 仅输入场景图+文字描述角色 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **角色外观保留最好** |
| E. 极详细的描述（推荐） | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **总体最佳：场景融合最自然** |

**关键发现**：
- ✅ **策略 D**：只输入场景图 + 文字描述角色 → **角色外观保留最好**
- ✅ **策略 E**：同时输入两张图 + 极详细描述 → **场景融合最自然，总体最佳**
- 💡 **选择建议**：如果需要严格保留角色外观选 D，如果需要最佳整体效果选 E

**结论**：
- ✅ **策略 E（极详细的描述）** 是总体最佳选择
- ✅ **策略 D** 在角色外观保留上也有不错表现
- ⚠️ **如果需要 100% 保留角色外观**，请使用传统图片叠加方案（见下方）

#### 推荐方案选择

**方案 A：AI 合成（适合创意设计）**
- 使用策略 E 的提示词模板
- 接受角色外观有一定变化
- 优点是场景融合最自然

**方案 B：传统图片叠加（适合严格角色一致性）**
- 用 PIL/OpenCV 将角色图精确叠加到场景图上
- 角色外观 100% 保留
- 可选：用 Agnes AI 对合成图进行风格统一处理

**代码示例（方案 B）**：

```python
from PIL import Image

# 读取角色图和场景图
character = Image.open("character.png").convert("RGBA")
scene = Image.open("scene.png").convert("RGBA")

# 调整角色大小
character_resized = character.resize((400, 600))

# 计算位置（居中底部）
x = (scene.width - character_resized.width) // 2
y = scene.height - character_resized.height - 50

# 叠加
scene.paste(character_resized, (x, y), character_resized)
scene.save("composed.png")
```

#### 策略 E 提示词模板（推荐）

```
角色描述：[详细描述角色的外观特征，包括发色、服装、姿态、表情等]
场景描述：[详细描述场景的环境、光线、天气、时间等]
将角色自然地融入到场景中，保持角色的所有外观特征完全不变，
场景光影与角色协调统一，[目标风格，如：日系动漫风格/写实摄影风格]
```

### 4. 视频生成（Agnes-Video-V2.0 / Agnes-Video-2.5-Flash）

Agnes-Video-V2.0 是一款电影级视频生成模型，支持文生视频、图生视频、多图视频生成和关键帧动画。
**agnes-video-2.5-flash** 是新一代快速视频模型，速度更快但参数更少。
使用**异步任务工作流**，先提交任务获取 `task_id`/`video_id`，再轮询获取结果。

> 💡 **音频说明**：生成的视频**自带音频**（音画同出，AAC 编码），无需额外配音或参数设置。模型会根据 prompt 描述自动生成环境音效、背景音乐，**以及口语对话**。**支持中英文双语**，实测可在 prompt 中描述具体台词（如"说'欢迎光临，请坐'"），模型会尝试按描述内容生成。
> 
> ⚠️ **注意**：台词内容由模型按场景理解生成，不一定 100% 复现 prompt 中指定的文字。如需精确配音/旁白，建议后期用 TTS 工具合成。

#### 4.1 创建视频任务

**端点**：`POST https://apihub.agnes-ai.cn/v1/videos`

> ⚠️ **重要：新模型参数差异**
> - `agnes-video-2.5-flash`：**三种模式** — `text`（文生视频）、`keyframe`（首尾帧控制）、`reference`（图片参考）
> - `agnes-video-2.5-flash`：**`size` 固定为 `"720P"`**（实测 `"960P"`/`"2K"` 返回 400）
> - `agnes-video-2.5-flash`：**`seconds` 是字符串**，支持 `"4"`–`"12"`，默认 `"5"`
> - `agnes-video-2.5-flash`：**`aspect_ratio` 可选**，如 `"16:9"`、`"4:3"`、`"9:16"`、`"1:1"`
> - `agnes-video-v2.0`：支持完整参数（width/height/num_frames/frame_rate）

**2.5-flash 请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `"agnes-video-2.5-flash"` |
| `prompt` | string | 是 | 视频内容文本描述 |
| `mode` | string | 是 | `"text"` / `"keyframe"` / `"reference"` |
| `seconds` | string | 否 | 时长 `"4"`–`"12"`，默认 `"5"` |
| `size` | string | 否 | **固定 `"720P"`** |
| `aspect_ratio` | string | 否 | `"16:9"`（默认）、`"4:3"`、`"9:16"`、`"1:1"` 等 |
| `seed` | integer | 否 | 随机种子 |
| `first_frame` | string | keyframe | 首帧图片 URL |
| `last_frame` | string | keyframe | 尾帧图片 URL |
| `images` | array | reference | 参考图片 URL 数组（最多 5 张） |

> ⚠️ **Flash 专属限制**：
> - **不支持 `videos` 字段**（视频输入）
> - **`size` 必须为 `"720P"`**
> - **`mode` 必须明确指定**

**创建任务响应**：
```json
{
  "id": "task_YOUR_TASK_ID",
  "task_id": "task_YOUR_TASK_ID",
  "object": "video",
  "model": "agnes-video-v2.0",
  "status": "queued",
  "progress": 0,
  "created_at": 1780457477,
  "seconds": "10.0",
  "size": "1280x768"
}
```

#### 4.2 获取视频结果

**⚠️ 重要：查询端点注意事项**

| 方式 | 端点 | 说明 |
|:----|:-----|:------|
| **推荐（2.5-flash）** | `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash` | **必须带 `model_name`**，适用于 text/keyframe/reference 全部模式 |
| 仅 text 模式 | `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>` | 不带 `model_name` 仅适用于 mode=text 创建的任务 |

> ⚠️ **关键发现**：
> - **不使用 `.cn` 网关的 `/agnesapi`**：该端点对非 text 模式返回 404
> - **必须带 `model_name=agnes-video-2.5-flash`**：keyframe/reference 模式不带此参数会返回 404
> - 建议每隔 1-2 秒查询一次，直至 `status` 变为 `completed` 或 `failed`

**任务状态**：

| 状态 | 说明 |
|------|------|
| `queued` | 任务在队列中等待 |
| `in_progress` | 视频正在生成中 |
| `completed` | 视频生成完成 |
| `failed` | 视频生成失败 |

> ⚠️ **视频 URL 字段位置因模型而异**：
> - `agnes-video-v2.0`：顶层 `url` 或 `remixed_from_video_id`
> - `agnes-video-2.5-flash`：`metadata.url`
> - 代码示例应同时检查这些位置

**任务状态**：

| 状态 | 说明 |
|------|------|
| `queued` | 任务在队列中等待 |
| `in_progress` | 视频正在生成中 |
| `completed` | 视频生成完成 |
| `failed` | 视频生成失败 |

> ⚠️ **视频 URL 字段位置因模型而异**：
> - `agnes-video-v2.0`：顶层 `url` 或 `remixed_from_video_id`
> - `agnes-video-2.5-flash`：`metadata.url`
> - 代码示例应同时检查这些位置

> ⚠️ **速率限制**：可能返回 `429 Too Many Requests`，建议在轮询代码中处理重试。

**完成响应**：
```json
{
  "id": "task_YOUR_TASK_ID",
  "model": "agnes-video-v2.0",
  "object": "video",
  "status": "completed",
  "progress": 100,
  "seconds": "10.0",
  "size": "1280x768",
  "url": "https://platform-outputs.agnes-ai.space/videos/agnes-video-v2.0/video_xxxxxx.mp4"
}
```

#### 4.3 调用方式示例

**文生视频**：
```bash
curl -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "A cinematic shot of a cat walking on the beach at sunset, soft ocean waves, warm golden lighting, realistic motion",
    "height": 768,
    "width": 1152,
    "num_frames": 121,
    "frame_rate": 24
  }'
```

**图生视频**（将图片动画化）：
```bash
curl -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "The woman slowly turns around and looks back at the camera, natural facial expression, cinematic camera movement",
    "image": "https://example.com/image.png",
    "num_frames": 121,
    "frame_rate": 24
  }'
```

**多图视频**（多张参考图像指导生成）：
```bash
curl -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Create a smooth transformation scene between the two reference images, cinematic lighting, consistent character identity, natural motion",
    "extra_body": {
      "image": ["https://example.com/image1.png", "https://example.com/image2.png"]
    },
    "num_frames": 121,
    "frame_rate": 24
  }'
```

**关键帧动画**：
```bash
curl -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Generate a smooth cinematic transition between the keyframes, maintaining visual consistency and natural camera movement",
    "extra_body": {
      "image": ["https://example.com/keyframe1.png", "https://example.com/keyframe2.png"],
      "mode": "keyframes"
    },
    "num_frames": 121,
    "frame_rate": 24
  }'
```

#### 4.4 Python 轮询示例

```python
import requests, time

API_KEY = "your-api-key"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 创建任务
resp = requests.post("https://apihub.agnes-ai.cn/v1/videos", headers=HEADERS, json={
    "model": "agnes-video-v2.0",
    "prompt": "A cinematic shot of a cat walking on the beach at sunset",
    "height": 768,
    "width": 1152,
    "num_frames": 121,
    "frame_rate": 24
})
data = resp.json()
task_id = data["task_id"]
video_id = data["video_id"]  # 推荐使用 video_id 查询
print(f"Task created: {task_id}")
print(f"Video ID: {video_id}")

# 轮询结果（使用推荐方式 - video_id + /agnesapi）
while True:
    result = requests.get(
        f"https://apihub.agnes-ai.cn/agnesapi?video_id={video_id}",
        headers=HEADERS
    ).json()
    status = result["status"]
    progress = result.get("progress", 0)
    print(f"Status: {status}, Progress: {progress}%")
    if status == "completed":
        # 视频 URL 在 url 字段
        video_url = result.get("url")
        print(f"Video URL: {video_url}")
        break
    elif status == "failed":
        print(f"Failed: {result.get('error')}")
        break
    time.sleep(5)
```

#### 4.5 角色+场景视频生成最佳实践（2026-07-02 实测）

> ⚠️ **核心发现**：`keyframes` 模式会在多张图片之间插值，导致**角色慢慢透明消失**。

**问题现象**：
- 输入角色图 + 场景图，使用 `keyframes` 模式
- 视频第一帧显示角色，然后角色**逐渐变透明**，最后只显示场景
- 原因：`keyframes` 模式在两张图片之间插值，角色图（第一帧）渐变到场景图（最后一帧）

**推荐工作流**（避免角色消失）：

```
步骤1: 先生成"角色在场景中"的合成图
  └─ 使用多图合成功能（agnes-image-2.0-flash + tags: ["img2img"]）
  └─ 生成一张真正融合的图片

步骤2: 用合成图生成视频
  └─ 只输入一张合成图（不使用 keyframes 模式）
  └─ 避免插值问题，角色不会消失
```

**代码示例**（完整工作流）：

```python
# 步骤1: 生成合成图
response = client.images.generate(
    model="agnes-image-2.0-flash",
    prompt="角色自然地融入场景，日系动漫风格",
    size="1152x768",
    extra_body={
        "tags": ["img2img"],
        "image": [character_url, scene_url]
    }
)
composite_url = response.data[0].url

# 等待速率限制（70秒）
time.sleep(70)

# 步骤2: 用合成图生成视频
resp = requests.post(f"{BASE_URL}/v1/videos", headers=HEADERS, json={
    "model": "agnes-video-v2.0",
    "prompt": "角色在场景中走动，说话，动漫风格",
    "image": composite_url,  # 只用一张合成图
    "width": 1152,
    "height": 768,
    "num_frames": 121,
    "frame_rate": 24
})
```

**提示词策略**（视频生成）：

| 策略 | 说明 | 效果 |
|------|------|------|
| ✅ 正面提示词 | "character remains visible throughout" | **推荐**，效果更好 |
| ❌ 负面提示词 | "NO fading, NOT disappearing" | 效果较差，模型可能不理解 |
| ✅ 强调持续可见 | "character is OPAQUE and FULLY VISIBLE in every frame" | 有帮助 |
| ✅ 描述具体动作 | "walking from left to right, talking with lip movements" | 动作更自然 |

**速率限制**：
- ⚠️ **1次/分钟**（实测）
- 建议等待 **70秒** 再发起下一次请求
- 否则会返回 `429 Too Many Requests`

**生成时间**：
- 通常 **2-4分钟**（120-250秒）
- 轮询间隔建议 **10秒**

**角色说话动画**：
- ✅ 可以生成角色"说话"的动画
- ❌ **不是精确的口型同步**（lip-sync）
- 如需精确口型同步，建议使用专门工具（如 Wav2Lip、SadTalker）
```

### 5. 文本对话（Chat）

使用 `agnes-2.0-flash` 模型，通过标准 OpenAI Chat Completions 接口调用。

> **特性**：支持中文对话、256K 上下文、流式输出（SSE）、Thinking 模式、工具调用（Function Calling）、图片理解

**Python 调用示例**：

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的 Agnes API Key",
    base_url="https://apihub.agnes-ai.cn/v1"
)

# 基础对话
response = client.chat.completions.create(
    model="agnes-2.0-flash",
    messages=[{"role": "user", "content": "你好，请介绍一下Agnes AI的视频模型"}]
)
print(response.choices[0].message.content)

# 带 System Prompt 和流式输出
stream = client.chat.completions.create(
    model="agnes-2.0-flash",
    messages=[
        {"role": "system", "content": "你是一位资深Python工程师，回答简洁专业。"},
        {"role": "user", "content": "用Python实现一个快速排序算法"}
    ],
    temperature=0.3,
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# 启用 Thinking 模式（适合复杂推理）
response = client.chat.completions.create(
    model="agnes-2.0-flash",
    messages=[{"role": "user", "content": "分析这段代码的性能瓶颈并给出优化方案..."}],
    extra_body={"chat_template_kwargs": {"enable_thinking": True}}
)
```

## Workflow Decision Tree

```
用户请求生成/编辑图片
│
├─ 文生图（无输入图片）？
│   └─ 使用 agnes-image-2.1-flash（文生图）
│
├─ 图生图（提供了图片）？
│   ├─ 单图编辑 → 推荐使用 `agnes-image-2.1-flash`（不需要 tags）
│   ├─ 多图合成 → 推荐 `agnes-image-2.1-flash`（无需 tags，实测已可融合）；需要 `seed` 时用 `agnes-image-2.0-flash`（需要 `tags: ["img2img"]`）
│
├─ 用户需要生成视频？
│   ├─ 纯文本描述 → 文生视频（无 image 参数）
│   ├─ 单张图片动画化 → 图生视频（image 参数传单 URL）
│   ├─ 多张图片引导 → 多图视频（extra_body.image）
│   └─ 关键帧过渡 → 关键帧动画（extra_body.mode: "keyframes"）
│   └─ 结果 → 异步任务：先创建（POST /v1/videos），再轮询（GET /agnesapi?video_id=）
│
└─ 用户需要纯文本对话？
    ├─ 通用对话 → 使用 agnes-2.0-flash
    ├─ 需要流式输出 → 设置 `stream: true`
    ├─ 需要思考过程 → 设置 `chat_template_kwargs: { enable_thinking: true }`
    └─ 需要工具调用 → 提供 `tools` 参数
```

## Local Image Handling

当用户提供本地图片路径进行图生图时，处理步骤：

1. 使用 Python 读取本地图片并转为 base64
2. 通过 data URI 格式或上传到可公网访问的临时存储
3. 将 URL 传入 `extra_body.image` 字段

**从本地图片生成 data URI 示例**：

```python
import base64

with open("photo.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")
    uri = f"data:image/jpeg;base64,{b64}"
```

## Tips & Best Practices

### 图像

- **Prompt 优化**：文生图时 prompt 应详细描述场景、风格、光线、构图等元素。推荐结构：`[主体] + [场景/环境] + [风格] + [光照] + [构图] + [质量要求]`
- **图生图优先用 2.1-flash**：不需要 `tags`，`response_format` 放 `extra_body` 里，质量更好
- **多图合成只能用 2.0-flash**：需要 `extra_body.tags: ["img2img"]`，不支持 `response_format`
- **尺寸选择**：常用 `"1024x1024"`（正方形）、`"1024x768"`（横屏）、`"768x1024"`（竖屏/视觉小说推荐）
- **多图合成风格控制**：在 prompt 中明确指定目标风格，如"日系动漫风格"、"水彩画风格"，否则默认输出写实摄影风
- **角色一致性**：`agnes-image-2.1-flash` 不支持 `seed`，每次生成角色会有差异。如需一致性：
  1. 用 `agnes-image-2.0-flash` + 固定 `seed` 生成角色
  2. 或用传统图像叠加（PIL/OpenCV）将角色立绘放到背景上
- **本地图片处理**：无法公网访问的图片用 Data URI Base64 传入 `extra_body.image`

### 视频

- **文生视频 Prompt 结构**：`[主体] + [动作] + [场景] + [镜头运动] + [光照] + [风格]`
- **图生视频 Prompt**：描述哪些部分需要运动，同时保持关键主体稳定
- **多图视频 Prompt**：描述输入图片之间的关系和过渡方式
- **关键帧 Prompt**：清晰描述帧与帧之间的过渡关系
- **自带音频**：生成视频自动含环境音/背景音乐/口语对话，中英文双语支持，可在 prompt 中描述具体台词
- **Prompt 语言**：视频 prompt **强烈建议用英文**，中文可用但效果不如英文稳定
- **中文 Prompt 出现英文文字** 的缓解方法：
  - 在 prompt 中明确约束：`"The shop sign displays Chinese text '欢迎光临', NO English letters"`
  - 使用 `negative_prompt`：加入 `"English text, English letters"`
- **参数推荐**：
  | 使用场景 | 推荐设置 |
  |----------|----------|
  | 标准视频 | `width: 1152, height: 768, num_frames: 121, frame_rate: 24` |
  | 短视频社交 | `num_frames: 81 或 121, frame_rate: 24` |
  | 更平滑运动 | 更高的 `frame_rate`（24 或 30） |
  | 可复现结果 | 设置固定 `seed` |
  | 关键帧过渡 | `extra_body.mode: "keyframes"` |
  | 避免不需要的内容 | 使用 `negative_prompt` |
- **定价**：$0/秒（当前免费）

### 通用

- **免费层限制**：免费 API 有速率和调用量上限（RPM ≤ 20），适合开发测试和个人轻量使用
- **Skill 集成**：可先文生图再图生视频，组合使用

### 文本对话

- **模型**：仅使用 `agnes-2.0-flash`
- **Thinking 模式**：`extra_body={"chat_template_kwargs": {"enable_thinking": True}}`
- **Temperature 调节**：确定性任务 0.1-0.3，创意写作 0.7-1.0
- **流式输出**：设置 `stream: true`

## 常见错误 & 接入检查清单

### ❌ 常见错误对照表

| 错误信息 | 错误码 | 原因 | 修复方式 |
|----------|--------|------|---------|
| `UnsupportedParamsError: Setting response_format is not supported` | 400 | `response_format` 放在顶层（应放 `extra_body`）| 改为 `extra_body.response_format: "url"` |
| 同样错误（2.0-flash） | 400 | `agnes-image-2.0-flash` 不支持 `response_format` | 去掉 `response_format`（2.0 只返回 URL）|
| `UnprocessableEntityError` / `seed` 报错 | 422 | `agnes-image-2.1-flash` 不支持 `seed` | 改用 2.0-flash 或去掉 `seed` |
| `Images.generate() got unexpected keyword argument 'tags'` | — | `tags` 放顶层而非 `extra_body` | 改为 `extra_body={"tags": [...]}` |
| `Setting n is not supported` | 400 | 图像模型不支持 `n` | 去掉 `n`，多次调用 |
| 图生图没效果（当作文生图） | — | 2.0-flash 忘了加 `tags: ["img2img"]` | 在 `extra_body` 加 `tags` |
| 视频任务一直 `queued` > 5分钟 | — | 用 `task_id` 查询（应用 `video_id`）| 用 `GET /agnesapi?video_id=<VIDEO_ID>` |
| `429 Too Many Requests` | 429 | 速率限制（RPM ≤ 20） | 降低频率，加重试 |

### ✅ 接入检查清单

1. **API Key 有效** — `sk-` 开头，在 platform.agnes-ai.com 创建
2. **Base URL 正确** — `https://apihub.agnes-ai.cn/v1`（不要漏 `/v1`）
3. **模型名称正确** — 2.1-flash（文生图/图生图/多图合成）、2.0-flash（多图合成 + 支持 `seed`）、video-v2.0、agnes-2.0-flash（对话）
4. **图生图参数正确**：
   - 2.1-flash：`extra_body.image` 传 URL 数组，不需要 `tags` ✅
   - 2.0-flash 多图合成：`extra_body.tags = ["img2img"]` ✅
   - `response_format`：2.1 支持（放 `extra_body`），2.0 **不支持** ⚠️
5. **视频查询正确** — 保存 `video_id`，用 `/agnesapi?video_id=` 轮询，视频 URL 在 `url` 字段

### 参数支持矩阵（图像模型）

| 参数 | `2.1-flash` | `2.0-flash` | 说明 |
|------|------------|------------|------|
| `prompt` | ✅ 必填 | ✅ 必填 | — |
| `size` | ✅ 可选 | ✅ 可选 | — |
| `seed` | ❌ 不支持 | ✅ 可选 | 2.0 可复现结果 |
| `extra_body.image` | ✅ 可选 | ✅ 必填 | 输入图 URL 数组，支持单张/多张 |
| `extra_body.response_format` | ✅ 可选 | ❌ 不支持 | 2.1 放 `extra_body`，2.0 不支持 |
| `extra_body.tags` | ❌ 不需要 | ✅ 必填 | 多图合成设 `["img2img"]`（2.1 不需要） |
| `n` / `quality` / `style` | ❌ | ❌ | 均不支持 |

## Resources

### scripts/
- `agnes_api.py` — Python 封装脚本，支持 `image`（文生图/图生图）和 `video`（文生视频/图生视频/关键帧）两个子命令

### references/
- `api_reference.md` — 详细的 API 参数参考文档（含图像和视频）
