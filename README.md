# Agnes AI API Skill

WorkBuddy 技能：Agnes AI 模型集成（文生图、图生图、多图合成、文生视频、图生视频）

## 🎬 实战案例：漫剧平台

基于本技能构建的实战项目：

**🌟 漫剧生成平台**: https://app-8it1txke4nwh.appmiaoda.com/

**平台功能**：
- ✅ 角色+场景智能合成
- ✅ AI 视频生成（角色动画、场景动画）
- ✅ 多图合成策略优化（基于实测经验）
- ✅ 批量漫剧生成

**技术实现**：
- 使用 Agnes AI API（图片生成、视频生成）
- 应用本技能的提示词策略（策略 E 为总体最佳）
- 采用推荐工作流（先合成图片，再生成视频）
- 解决 `keyframes` 模式的角色消失问题

---

## 📋 功能特性

### 1. 图片生成
- ✅ 文生图（Text-to-Image）
- ✅ 图生图（Image-to-Image）
- ✅ 多图合成（Multi-image Composition）
- ✅ 支持 `agnes-image-2.0-flash` 和 `agnes-image-2.1-flash`

### 2. 视频生成
- ✅ 文生视频（Text-to-Video）
- ✅ 图生视频（Image-to-Video）
- ✅ 关键帧动画（Keyframes）
- ✅ 支持 `agnes-video-v2.0`

### 3. 实测经验（已验证）
- ✅ **图片合成**：策略 D（角色保留最好）、策略 E（总体最佳）
- ✅ **视频生成**：避免 `keyframes` 模式，使用合成图工作流
- ✅ **提示词策略**：正面提示词效果最好
- ⚠️ **速率限制**：视频生成 1次/分钟

---

## 🚀 快速开始

### 安装

将此技能复制到你的 WorkBuddy 技能目录：
```bash
cp -r agnes-api-skill ~/.workbuddy/skills/
```

### 使用示例

#### 示例1：生成图片
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://apihub.agnes-ai.cn/v1"
)

response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="anime girl with black hair, blue hoodie",
    size="1024x1024"
)

image_url = response.data[0].url
print(f"Generated: {image_url}")
```

#### 示例2：多图合成（策略 E - 推荐）
```python
import requests

# 使用策略 E：极详细描述
payload = {
    "model": "agnes-image-2.1-flash",
    "prompt": "一个黑色长发、穿着淡蓝色连帽卫衣的 anime 女孩，站在樱花盛开的校园里，花瓣缓缓飘落，阳光透过树枝洒在她身上，角色外观完全保持，场景融合自然，anime 风格",
    "size": "1024x1024",
    "image": [character_url, scene_url]  # 角色图 + 场景图
}

response = requests.post(
    "https://apihub.agnes-ai.cn/v1/images/generations",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json=payload
)

result_url = response.json()["data"][0]["url"]
```

#### 示例3：视频生成（推荐工作流）
```python
# 步骤1: 先生成合成图（避免角色消失）
composite_url = generate_composite_image(...)

# 步骤2: 用合成图生成视频
payload = {
    "model": "agnes-video-v2.0",
    "prompt": "Character walks in cherry blossom scene, remains visible, anime style",
    "image": composite_url,  # 只用一张图
    "width": 1152,
    "height": 768
}

response = requests.post(
    "https://apihub.agnes-ai.cn/v1/videos",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json=payload
)

video_id = response.json()["video_id"]

# 步骤3: 轮询结果
while True:
    result = requests.get(
        f"https://apihub.agnes-ai.cn/agnesapi?video_id={video_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()
    
    if result["status"] == "completed":
        video_url = result["remixed_from_video_id"]
        break
    
    time.sleep(10)
```

---

## 📚 文档结构

```
agnes-api-skill/
├── README.md              # 本文件（使用指南）
├── SKILL.md               # WorkBuddy 技能定义（详细文档）
├── examples/              # 示例脚本
│   ├── README.md          # 示例说明
│   ├── test_image_compose.py      # 图片合成测试
│   ├── test_video_gen.py          # 视频生成测试
│   ├── generate_composite_image.py  # 生成合成图（推荐）
│   └── video_from_composite.py      # 从合成图生成视频
├── references/            # API 参考文档
└── scripts/              # 辅助脚本
```

---

## 📊 实测经验总结

### 图片合成策略对比

| 策略 | 角色保留 | 场景融合 | 总体评分 | 推荐场景 |
|------|---------|---------|---------|---------|
| A. 强身份约束 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 不推荐 |
| B. 指定图片顺序 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 不推荐 |
| C. 仅角色图 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 通用 |
| D. 仅场景图 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **角色保留优先** |
| E. 极详细描述 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **总体最佳** |

**结论**：
- 需要严格角色一致性 → 使用**策略 D**
- 需要最佳整体效果 → 使用**策略 E**（推荐）

### 视频生成关键发现

1. **`keyframes` 模式问题**：角色会慢慢透明消失
   - 原因：在两张图片之间插值
   - 解决：先生成合成图，再用合成图生成视频

2. **提示词策略**：正面描述效果最好
   - ✅ "角色持续可见"
   - ❌ "角色不要消失"

3. **速率限制**：1次/分钟（实测）
   - 建议等待70秒（保险）

---

## 🔧 配置

### API Key
获取 API Key：https://platform.agnes-ai.com

### 速率限制
- 图片生成：无限期免费（Agnes AI 政策）
- 视频生成：1次/分钟

---

## 📝 注意事项

1. **图片 URL 有效期**：约 24 小时
2. **视频生成时间**：2-4 分钟
3. **网络要求**：需要访问 `https://apihub.agnes-ai.cn`
4. **角色一致性**：无法保证100%一致（模型固有局限性）

---

## 🐛 常见问题

### Q1: 多图合成后角色外观变化很大？
**A**: 这是模型固有局限性。Agnes AI 多图合成是"参考重生成"，不是"像素级融合"。如需严格角色一致，使用传统图片叠加（PIL/OpenCV）。

### Q2: 视频中角色慢慢消失？
**A**: 这是 `keyframes` 模式的插值问题。解决方案：先生成"角色在场景中"的合成图，再用这张图生成视频。

### Q3: 速率限制错误？
**A**: 视频生成限制 1次/分钟。等待70秒后重试。

---

## 📚 参考资料

- **Agnes AI 平台**：https://platform.agnes-ai.com
- **API 文档**：见 `references/` 目录
- **漫剧平台案例**：https://app-8it1txke4nwh.appmiaoda.com/

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

**作者**：WorkBuddy AI  
**更新时间**：2026-07-02  
**基于**：Agnes AI API 实测经验（2026年7月）

---

## 📄 许可证

MIT License
