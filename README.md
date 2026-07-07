# Agnes Image 2.1 Flash — Gradio Web UI

基于 [Agnes Image 2.1 Flash](https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash) 模型的文生图 / 图生图 Web 应用，使用 [Gradio](https://www.gradio.app/) 构建界面，采用 [PEP 723](https://peps.python.org/pep-0723/) 内联依赖声明，可通过 [`uv`](https://docs.astral.sh/uv/) 零配置运行。

## 功能特性

- **文生图 (Text-to-Image)**：根据自然语言提示词生成高质量图像。
- **图生图 (Image-to-Image)**：上传参考图 + 提示词进行风格转换、场景重构，保留原始构图。
- **多种输出尺寸**：内置 `1024x768`、`768x1024`、`1024x1024`、`1536x1024`、`1024x1536` 等常用尺寸。
- **Base64 / URL 自动降级**：优先使用 Base64 直传，若 API 返回 URL 则自动下载兜底。
- **环境变量配置**：API Key 通过 `.env` 文件注入，不硬编码、不入仓库。

## 快速开始

### 1. 前置依赖

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)（推荐，用于自动管理依赖）

安装 uv（Windows PowerShell）：

```powershell
python -m pip install uv
```

### 2. 配置 API Key

在项目根目录创建 `.env` 文件（已在 `.gitignore` 中排除）：

```env
AGNES_API_KEY=你的Agnes_API_Key
# 可选，一般保持默认即可：
# AGNES_API_URL=https://apihub.agnes-ai.com/v1/images/generations
# AGNES_MODEL=agnes-image-2.1-flash
# GRADIO_SHARE=0       # 设为1可开启Gradio公网分享链接
# GRADIO_PORT=8912     # 自定义监听端口
```

API Key 可在 [Agnes AI 控制台](https://agnes-ai.com/) 获取。

### 3. 启动应用

```powershell
python -m uv run main.py
```

首次运行时 `uv` 会自动创建虚拟环境并安装 `gradio`、`pillow`、`requests`、`python-dotenv` 等依赖。

启动成功后，浏览器访问：

```
http://127.0.0.1:8912
```

## 使用说明

1. 在左侧 **提示词 (Prompt)** 框输入图像描述（推荐结构：`[主体] + [场景/环境] + [风格] + [光照] + [构图] + [质量要求]`）。
2. 选择 **输出尺寸 (Size)**。
3. （可选）上传 **参考图** 开启图生图模式，提示词中需明确描述改变什么、保留什么。
4. 点击 **开始生成**，右侧会展示生成结果。

### 提示词示例

文生图：

```
日出时分薄雾峡谷上方的发光浮空城市，电影级写实风格，广角构图，丰富的建筑细节，柔和的金色光线，高视觉密度
```

图生图：

```
将白天街道场景改为电影级赛博朋克夜景，添加霓虹招牌和湿滑路面倒影，同时保留原始街道布局、相机角度和主要建筑形状。
```

## 测试

运行自动化测试（分别验证文生图和图生图 API 通路）：

```powershell
python -m uv run test_api.py
```

生成的测试图片会保存到 `outputs/` 目录。

## 项目结构

```
lovart-assets/
├── .env                # 本地环境变量（不提交）
├── .gitignore
├── main.py             # Gradio 应用入口
├── test_api.py         # API 测试脚本
├── outputs/            # 生成图片输出目录（仅 .gitkeep 提交）
└── README.md
```

## API 兼容性说明

Agnes Image 2.1 Flash 使用 OpenAI DALL-E 风格的 `/v1/images/generations` 端点，但参数位置有以下注意事项（已在代码中处理）：

- `response_format` **不能** 放在请求体顶层，必须放在 `extra_body` 内。
- 图生图的输入图像数组 `image` 也放在 `extra_body` 内，支持公网 URL 或 Data URI Base64。
- 不要传 `tags: ["img2img"]`，图生图只需提供 `image` 字段即可。
- 官方建议客户端超时时间 60~360 秒。

## 定价

截至文档编写时，Agnes Image 2.1 Flash 当前价格为 **$0 / 张**（限免），原价 $0.003/张。请以 [官方定价页](https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash#定价) 为准。

## License

仅供个人学习与原型验证使用。
