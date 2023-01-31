# README

## 功能介绍

本项目是一个自动日语翻译机。可以人为确定截屏区域，然后借助OCR以及日语翻译的AI模型来实现自动翻译的功能。

## AI模型
- translator: https://huggingface.co/K024/mt5-zh-ja-en-trimmed
- ocr: https://huggingface.co/kha-white/manga-ocr-base

## TODO

- 确定截屏区域的两个坐标点，应该有两种情况：左上和右下 | 左下和右上；
- OCR模型的精度不够，需要寻找其它模型；
- 输出翻译界面，可以认为调整界面的位置以及大小；