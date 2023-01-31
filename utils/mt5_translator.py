from pathlib import Path

import torch
from loguru import logger
from transformers import (
    T5Tokenizer, MT5ForConditionalGeneration,
    Text2TextGenerationPipeline,
)


class MT5Translator:
    def __init__(self, pretrained_model_name_or_path='K024/mt5-zh-ja-en-trimmed', force_cpu=False) -> None:
        logger.info(f'Loading MT5 model from {pretrained_model_name_or_path}')
        self.tokenizer = T5Tokenizer.from_pretrained(pretrained_model_name_or_path)
        self.model = MT5ForConditionalGeneration.from_pretrained(pretrained_model_name_or_path)
        
        if not force_cpu and torch.cuda.is_available():
            logger.info('Using CUDA')
            self.pipe = Text2TextGenerationPipeline(
                model=self.model,
                tokenizer=self.tokenizer,
                device=0
            )
        else:
            logger.info('Using CPU')
            self.pipe = Text2TextGenerationPipeline(
                model=self.model,
                tokenizer=self.tokenizer,
            )
        
        logger.info('Translator ready')

    def __call__(self, sentence: str) -> str:
        sentence = "ja2zh: " + sentence
        result = self.pipe(sentence, max_length=100, num_beams=4)
        return result[0]['generated_text']


if __name__ == "__main__":
    sentence = "お目にかかれて、嬉しいです。"
    mt5t = MT5Translator(r"models\\mt5_zh_ja_en_trimmed", force_cpu=True)
    print(mt5t(sentence))
