# /// script
# dependencies = [
#  "gradio>=4.0.0",
#  "pillow>=10.0.0",
#  "requests>=2.31.0",
#  "python-dotenv>=1.0.0",
# ]
# ///

"""
Quick test script for Agnes Image 2.1 Flash: text-to-image and image-to-image.
Saves results to outputs/ directory.
"""
import sys
import os
import time

# Ensure we can import from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image
import io

# Import the core functions and config from main.py
import main

def create_test_input_image(path: str) -> str:
    """Create a simple 512x512 test image (red square with blue circle hint) for img2img testing."""
    img = Image.new("RGB", (512, 512), (220, 50, 50))
    # Draw a crude blue circle using pixels
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse((156, 156, 356, 356), fill=(50, 100, 220))
    img.save(path, format="PNG")
    return path

def test_text_to_image():
    print("=" * 60)
    print("[TEST 1] 文生图 (text-to-image)")
    print("=" * 60)
    prompt = "一只穿着宇航服的橘猫漂浮在太空中，地球背景，电影级写实风格，高细节"
    size = "1024x768"
    t0 = time.time()
    result = main.synthesize(prompt, None, size)
    elapsed = time.time() - t0
    if result is None:
        print(f"[FAIL] 文生图失败，耗时 {elapsed:.1f}s")
        return False
    out_path = os.path.join(main.OUTPUT_DIR, "test_text2img.png")
    result.save(out_path)
    print(f"[PASS] 文生图成功，耗时 {elapsed:.1f}s，保存到 {out_path}，尺寸 {result.size}")
    return True

def test_image_to_image():
    print("=" * 60)
    print("[TEST 2] 图生图 (image-to-image)")
    print("=" * 60)
    input_path = os.path.join(main.OUTPUT_DIR, "test_input.png")
    create_test_input_image(input_path)
    input_img = Image.open(input_path)
    prompt = "将图像转换为赛博朋克风格，保留圆形主体，添加霓虹灯光和雨夜街道背景"
    size = "1024x768"
    t0 = time.time()
    result = main.synthesize(prompt, input_img, size)
    elapsed = time.time() - t0
    if result is None:
        print(f"[FAIL] 图生图失败，耗时 {elapsed:.1f}s")
        return False
    out_path = os.path.join(main.OUTPUT_DIR, "test_img2img.png")
    result.save(out_path)
    print(f"[PASS] 图生图成功，耗时 {elapsed:.1f}s，保存到 {out_path}，尺寸 {result.size}")
    return True

if __name__ == "__main__":
    os.makedirs(main.OUTPUT_DIR, exist_ok=True)
    print(f"API URL: {main.AGNES_API_URL}")
    print(f"MODEL:   {main.AGNES_MODEL}")
    print(f"KEY:     {main.AGNES_API_KEY[:8]}...{main.AGNES_API_KEY[-4:]}" if len(main.AGNES_API_KEY) > 12 else "KEY NOT SET")
    print()
    r1 = test_text_to_image()
    print()
    r2 = test_image_to_image()
    print()
    print("=" * 60)
    print(f"结果: 文生图 {'PASS' if r1 else 'FAIL'} | 图生图 {'PASS' if r2 else 'FAIL'}")
    print("=" * 60)
