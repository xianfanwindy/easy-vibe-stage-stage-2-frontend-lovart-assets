# /// script
# dependencies = [
#  "gradio>=4.0.0",
#  "pillow>=10.0.0",
#  "requests>=2.31.0",
#  "python-dotenv>=1.0.0",
# ]
# ///

import gradio as gr
import requests
import base64
from PIL import Image
import io
import os
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件（与 main.py 同目录）
load_dotenv()

# 配置 API 信息（Agnes Image 2.1 Flash）
AGNES_API_URL: str = os.getenv("AGNES_API_URL", "https://apihub.agnes-ai.com/v1/images/generations")
AGNES_API_KEY: str = os.getenv("AGNES_API_KEY", "")
AGNES_MODEL: str = os.getenv("AGNES_MODEL", "agnes-image-2.1-flash")
OUTPUT_DIR: str = "outputs"

# 支持的尺寸（Agnes 支持自定义，这里给出常用选项）
SIZE_CHOICES = ["1024x768", "768x1024", "1024x1024", "1536x1024", "1024x1536"]

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


def image_to_base64_data_uri(image: Image.Image) -> str:
    """
    将 PIL 图像转换为 Data URI Base64 格式（Agnes 图生图输入支持此格式）。
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def base64_to_image(base64_str: str) -> Optional[Image.Image]:
    """
    将纯 base64 字符串转换为 PIL Image。
    """
    try:
        image_bytes = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        print(f"Base64 解码失败: {e}")
        return None


def url_to_image(url: str) -> Optional[Image.Image]:
    """
    下载 URL 图片并转换为 PIL Image（兜底方案，当 API 返回 URL 而非 Base64 时使用）。
    """
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content))
    except Exception as e:
        print(f"下载 URL 图片失败: {e}")
        return None


def synthesize(prompt: str, input_image: Optional[Image.Image], size: str) -> Optional[Image.Image]:
    """
    调用 Agnes Image 2.1 Flash API 进行文生图或图生图。
    """
    if not prompt or not prompt.strip():
        gr.Warning("请输入提示词")
        return None

    print(f">>> 开始任务: {prompt[:50]}... | 模式: {'图生图' if input_image else '文生图'} | size: {size}")

    if not AGNES_API_KEY:
        gr.Error("请在 main.py 同目录下创建 .env 文件并配置 AGNES_API_KEY=你的密钥")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AGNES_API_KEY}",
    }

    # 统一 payload 结构：response_format 统一放在 extra_body 内（实测这是唯一稳定生效的方式）
    extra_body: dict = {"response_format": "b64_json"}

    if input_image is not None:
        # 图生图：在 extra_body 内加入 image 数组（Data URI Base64）
        img_data_uri = image_to_base64_data_uri(input_image)
        extra_body["image"] = [img_data_uri]

    payload = {
        "model": AGNES_MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": extra_body,
    }

    try:
        # Agnes 官方建议超时 60~360s
        response = requests.post(AGNES_API_URL, headers=headers, json=payload, timeout=180)

        if response.status_code != 200:
            error_msg = f"API 请求失败: {response.status_code} - {response.text[:500]}"
            print(error_msg)
            gr.Error(error_msg)
            return None

        result = response.json()
        print(f"API 响应 keys: {list(result.keys())}")

        # Agnes 返回格式: {"created": ..., "data": [{"url": ..., "b64_json": ..., "revised_prompt": ...}]}
        data_list = result.get("data")
        if not data_list or not isinstance(data_list, list) or len(data_list) == 0:
            gr.Warning("API 返回结果中没有 data 字段")
            print(f"完整响应: {str(result)[:500]}")
            return None

        item = data_list[0]
        b64_str = item.get("b64_json")
        url = item.get("url")

        # 优先用 Base64；如果没有则兜底下载 URL
        if b64_str:
            output_image = base64_to_image(b64_str)
        elif url:
            print(f">>> b64_json 为空，降级使用 URL 下载: {url[:80]}...")
            output_image = url_to_image(url)
        else:
            gr.Warning("返回结果中既没有 b64_json 也没有 url")
            print(f"data[0] 内容: {str(item)[:300]}")
            return None

        if output_image:
            return output_image

        gr.Error("图片解码/下载失败")
        return None

    except requests.exceptions.Timeout:
        gr.Error("请求超时（>180s），复杂图像可能需要更久，请稍后重试或减小尺寸")
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        gr.Error(f"发生未知错误: {str(e)}")
        return None


# Gradio 界面配置
with gr.Blocks(title="Agnes Image 2.1 Flash Generator") as app:
    gr.Markdown("# Agnes Image 2.1 Flash 文生图 / 图生图")
    gr.Markdown(
        "基于 [Agnes Image 2.1 Flash](https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash) 模型，"
        "支持文生图、图生图、构图保留与高信息密度图像生成。"
    )

    with gr.Row():
        with gr.Column():
            prompt_input = gr.Textbox(
                label="提示词 (Prompt)",
                placeholder="例如: 日出时分薄雾峡谷上方的发光浮空城市，电影级写实风格，广角构图，高视觉密度",
                lines=3,
            )
            size_input = gr.Dropdown(
                label="输出尺寸 (Size)",
                choices=SIZE_CHOICES,
                value="1024x768",
            )
            image_input = gr.Image(
                label="参考图 (可选，上传后启用图生图)",
                type="pil",
                height=300,
            )
            submit_btn = gr.Button("开始生成", variant="primary")

        with gr.Column():
            image_output = gr.Image(label="生成结果", format="png")

    submit_btn.click(
        fn=synthesize,
        inputs=[prompt_input, image_input, size_input],
        outputs=image_output,
    )

if __name__ == "__main__":
    # share 通过环境变量控制：GRADIO_SHARE=1 python main.py 开启公网分享
    share = os.getenv("GRADIO_SHARE", "0") == "1"
    port = int(os.getenv("GRADIO_PORT", "8912"))
    # 绕过代理访问 localhost（避免 IDE 沙箱/系统代理导致的 502）
    for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(proxy_var, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    # show_error=False 避免启动健康检查失败导致进程退出（Trae沙箱环境下代理会拦截localhost）
    app.launch(share=share, server_name="127.0.0.1", server_port=port, show_error=False)
