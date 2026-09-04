# Agnes Image API 参考文档

## 基础信息

| 项目 | 内容 |
|------|------|
| API 基础地址 | `https://apihub.agnes-ai.cn/v1` |
| 认证方式 | Bearer Token（API Key） |
| Key 获取 | https://platform.agnes-ai.com |
| 协议 | OpenAI 兼容 |
| 免费政策 | 无限期免费（有速率和调用量上限，RPM ≤ 20） |

## 可用模型

| 模型名称 | 模态 | 用途 | 重要说明 |
|----------|------|------|----------|
| **`agnes-image-2.5-flash`** | 图像 | **文生图 + 图生图 + 多图合成** | **最新一代，全面优于 2.1-flash，支持档位 size + ratio，免费** |
| `agnes-image-2.1-flash` | 图像 | 文生图 + 图生图（兼容备用） | 历史版本，可用但质量不如 2.5-flash |
| `agnes-image-2.0-flash` | 图像 | 多图合成 + 需 seed 复现 | 仅用于需要 `seed` 的场景 |
| `agnes-2.0-flash` | 文本 | 对话/文本生成 | 支持 Thinking 模式 |
| `agnes-video-v2.0` | 视频 | 文生视频/图生视频/多图视频/关键帧动画 | 异步任务 API，支持完整参数 |
| `agnes-video-2.5-flash` | 视频 | 新一代快速视频模型 | 需要 `mode` 参数，30秒完成，720P |

## 图像 API 端点

### POST /v1/images/generations

#### agnes-image-2.5-flash 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `"agnes-image-2.5-flash"` |
| `prompt` | string | 是 | 图像生成或编辑指令 |
| `size` | string | 否 | 输出尺寸档位（推荐：`"1K"`/`"2K"`/`"3K"`/`"4K"`），也兼容 `"1024x768"` 历史精确尺寸 |
| `ratio` | string | 否 | 宽高比，与 size 配合：`"1:1"`（默认）、`"3:4"`、`"4:3"`、`"16:9"`、`"9:16"`、`"2:3"`、`"3:2"`、`"21:9"` |
| `return_base64` | boolean | 否 | 文生图返回 Base64 时用 `true` |
| `extra_body.image` | array | 图生图必填 | 输入图像 URL 或 Data URI 数组，单张/多张均可 |
| `extra_body.response_format` | string | 否 | `"url"`（默认）或 `"b64_json"`，**必须放 `extra_body` 里** |
| `extra_body.tags` | — | 不需要 | 2.5-flash 图生图不需要 `tags` |

> ⚠️ **2.5-flash 图生图不需要 `tags: ["img2img"]`**！只需在 `extra_body.image` 中提供输入图像。
> ⚠️ **`response_format` 必须放 `extra_body` 里**！放顶层会导致 400 错误。
> ⚠️ **`agnes-image-2.5-flash` 不支持 `seed` 参数**，设置会导致 422 错误。

**尺寸参考表（size + ratio 组合输出尺寸）**：

| 档位 | 1:1 | 16:9 | 9:16 | 3:4 |
|------|-----|------|------|-----|
| 1K | 1024×1024 | 1312×736 | 736×1312 | 864×1152 |
| 2K | 2048×2048 | 2624×1472 | 1472×2624 | 1728×2304 |
| 3K | 3072×3072 | 3936×2208 | 2208×3936 | 2592×3456 |
| 4K | 4096×4096 | 5248×2944 | 2944×5248 | 3456×4608 |

#### agnes-image-2.1-flash 参数（兼容备用）

与 2.5-flash 相同参数，但 `ratio` 不可用，仅支持精确尺寸如 `"1024x768"`。

#### agnes-image-2.0-flash 参数（仅多图合成时用）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `"agnes-image-2.0-flash"` |
| `prompt` | string | 是 | 编辑/合成指令 |
| `size` | string | 否 | 输出尺寸 |
| `seed` | integer | 否 | 随机种子，固定值可复现结果 |
| `extra_body.tags` | array | 多图合成必填 | `["img2img"]` |
| `extra_body.image` | array | 必填 | 输入图像 URL 数组 |
| `extra_body.response_format` | — | 不支持 | 2.0-flash 不支持此参数，去掉 |

> ⚠️ **`agnes-image-2.0-flash` 不支持 `response_format`**，设置会导致 400 错误。只返回 URL。

#### 响应格式

URL 输出：
```json
{
  "created": 1780000000,
  "data": [
    {
      "url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
      "b64_json": null,
      "revised_prompt": null
    }
  ]
}
```

Base64 输出：
```json
{
  "created": 1780000000,
  "data": [
    {
      "url": null,
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA...",
      "revised_prompt": null
    }
  ]
}
```

## 视频 API 端点

### POST /v1/videos（创建视频任务）

异步视频生成任务端点。先提交任务获取 `video_id`，再通过 GET 获取结果。

#### agnes-video-v2.0 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model` | string | 是 | — | `"agnes-video-v2.0"` |
| `prompt` | string | 是 | — | 视频内容文本描述 |
| `image` | string | 否 | — | 图生视频：单张图片 URL |
| `height` | integer | 否 | 768 | 视频高度 |
| `width` | integer | 否 | 1152 | 视频宽度 |
| `num_frames` | integer | 否 | — | 帧数，必须 `≤ 441` 且遵循 `8n+1` 规则 |
| `frame_rate` | number | 否 | 24 | 帧率，范围 1–60 |
| `num_inference_steps` | integer | 否 | — | 推理步数 |
| `seed` | integer | 否 | — | 随机种子，保证结果可复现 |
| `negative_prompt` | string | 否 | — | 反向提示词 |
| `extra_body.image` | array | 否 | — | 多图/关键帧模式的图片 URL 数组 |
| `extra_body.mode` | string | 否 | — | `"keyframes"` |

#### agnes-video-2.5-flash 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `"agnes-video-2.5-flash"` |
| `prompt` | string | 是 | 视频内容文本描述 |
| `mode` | string | 是 | `"text"`、`"keyframe"` 或 `"reference"` |
| `seconds` | string | 否 | 视频时长，`"4"`–`"12"`，默认 `"5"` |
| `size` | string | 否 | **固定为 `"720P"`** |
| `aspect_ratio` | string | 否 | `"16:9"`（默认）、`"4:3"`、`"9:16"`、`"1:1"` 等 |
| `seed` | integer | 否 | 随机种子 |
| `negative_prompt` | string | 否 | 反向提示词 |

**模式专用参数**：

| 参数 | 适用模式 | 说明 |
|------|----------|------|
| `first_frame` | `keyframe` | 首帧图片 URL |
| `last_frame` | `keyframe` | 尾帧图片 URL |
| `images` | `reference` | 参考图片 URL 数组（最多 5 张） |

> ⚠️ **重要限制**：
> - **不支持 `videos` 字段**（Flash 版本不支持视频输入）
> - **`mode` 必须明确指定**
> - **`size` 必须为 `"720P"`**

**查询端点**（推荐）：
```
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash
```

> ⚠️ 使用 `mode=keyframe` 或 `mode=reference` 创建的任务，**必须**在查询时带上 `model_name=agnes-video-2.5-flash`，否则返回 404。

**查询端点**（推荐）：
```
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash
```

> ⚠️ 使用 `mode=keyframe` 或 `mode=reference` 创建的任务，**必须**在查询时带上 `model_name=agnes-video-2.5-flash`，否则返回 404。

#### 创建任务响应

```json
{
  "id": "task_YOUR_TASK_ID",
  "task_id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "object": "video",
  "model": "agnes-video-v2.0",
  "status": "queued",
  "progress": 0,
  "created_at": 1780457477,
  "seconds": "10.0",
  "size": "1280x768"
}
```

### 获取视频结果

**⚠️ 重要：查询端点注意事项**

| 方式 | 端点 | 说明 |
|:----|:-----|:------|
| **推荐（v2.0）** | `GET https://apihub.agnes-ai.cn/v1/videos/<TASK_ID>` | 使用 task_id 查询 |
| **2.5-flash** | `GET https://apihub.agnes-ai.cn/v1/videos/<TASK_ID>` | 同 v2.0，URL 在 metadata.url |
| ~~旧方式~~ | ~~`GET https://apihub.agnes-ai.cn/agnesapi?video_id=<VIDEO_ID>`~~ | `.cn` 网关返回 404，不可用 |
| 兼容旧版 | `GET https://apihub.agnes-ai.com/v1/videos/<TASK_ID>` | 旧网关，稳定可用 |

> ⚠️ `.cn` 网关的 `/agnesapi?video_id=` 端点返回 404，**不要使用**。直接用 `/v1/videos/{task_id}` 查询。

> ⚠️ 如果视频查询超过 5 分钟，请尝试切换到 `.com` 网关：`GET https://apihub.agnes-ai.com/v1/videos/<TASK_ID>`

#### 任务状态

| 状态 | 说明 |
|------|------|
| `queued` | 队列等待 |
| `in_progress` | 生成中 |
| `completed` | 已完成 |
| `failed` | 失败 |

#### 完成响应

```json
{
  "id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "model": "agnes-video-v2.0",
  "object": "video",
  "status": "completed",
  "progress": 100,
  "seconds": "10.0",
  "size": "1280x768",
  "remixed_from_video_id": "https://storage.googleapis.com/agnes-aigc/aigc/videos/2026/06/03/video_xxxxxx.mp4",
  "error": null
}
```

> ⚠️ **视频 URL 字段位置因模型而异**：
> - `agnes-video-v2.0`：`url` 或 `remixed_from_video_id`
> - `agnes-video-2.5-flash`：`metadata.url`

## 错误码

| HTTP 状态码 | 含义 | 处理方式 |
|-------------|------|----------|
| 400 | 请求参数错误（如 `response_format` 放顶层） | 检查参数位置和类型 |
| 401 | 认证失败 | 检查 API Key 是否正确 |
| 404 | 任务不存在 | 检查 `task_id` 或 `video_id` 是否正确 |
| 429 | 请求超限 | 等待后重试（免费层 RPM ≤ 20） |
| 500 | 服务端错误 | 稍后重试 |
| 503 | 服务繁忙 | 稍后重试 |

## 官方文档链接

- 概述：https://agnes-ai.com/zh-Hans/docs/overview
- Image 2.1 Flash：https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash
- Video V2.0：https://agnes-ai.com/zh-Hans/docs/agnes-video-v20
