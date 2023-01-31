from utils.ai_translator import AITranslator
import ctypes
# your windows version should >= 8.1,it will raise exception.
ctypes.windll.shcore.SetProcessDpiAwareness(2)


if __name__ == '__main__':
    translator = AITranslator()
    translator()