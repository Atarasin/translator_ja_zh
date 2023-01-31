from pathlib import Path
from time import time

from utils.manga_ocr import MangaOcr
from utils.mt5_translator import MT5Translator


model_path = Path(Path(__file__).parent, 'models')
model_name = {
    'ocr': 'manga_ocr_base',
    'translator': 'mt5_zh_ja_en_trimmed'
}

image_path = Path(Path(__file__).parent, 'images')

# Step 1: 初始化模型
ocr = MangaOcr(Path(model_path, model_name['ocr']))
mt5t = MT5Translator(Path(model_path, model_name['translator']))

# Step 2: 推理images文件夹内的所有图片
total_used = 0
for i, path in enumerate(image_path.iterdir()):
    print(f"{i}: {path} is inferring...")
    start = time()
    # 1.ocr
    ja_text = ocr(path)
    print(f"ocr time: {time() - start}")
    # 2.translator
    zh_text = mt5t(ja_text)
    print(f"total time: {time() - start}")
    print(f"result: {zh_text}")

    total_used += time() - start

print(f"total used time: {total_used}")


