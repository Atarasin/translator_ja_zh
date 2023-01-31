import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageGrab
from pathlib import Path
from time import time, sleep
from loguru import logger
from typing import List
from threading import Thread
import time

from utils.manga_ocr import MangaOcr
from utils.mt5_translator import MT5Translator


class AITranslator(): 
    def __init__(self):
        # 设置相关路径
        self.model_path = Path(Path(__file__).parent.parent, 'models') 
        self.model_name = {
            'ocr': 'manga_ocr_base',
            'translator': 'mt5_zh_ja_en_trimmed'
        }
        self.image_path = Path(Path(__file__).parent.parent, 'images')
        
        # 加载AI模型
        self.ocr = MangaOcr(Path(self.model_path, self.model_name['ocr'])) 
        self.mt5t = MT5Translator(Path(self.model_path, self.model_name['translator']))
        logger.info("--------------Loading Models Successfully---------------")

        # 截屏区域
        self.screenshotLeftTop = []
        self.screenshotRightBottom = []

        self.imgShow = None         # 显示图片
        self.imgTs = None           # 翻译图片
        self.imgTsResized = None
        self.imgShowCanvas = None

        # GUI设置
        self.root = tk.Tk() 
        self.root.title('AI Translator')

        self.screenshotAreaLabel = tk.StringVar(value='翻译前请先设置截屏区域')
        self.autoScreenshotFlag = tk.StringVar(value='自动翻译:关闭')
        self.isAutoTs = False
        self.autoTsInterval = 2     # s
        self.resizeFactor = -1      # 截图缩放比例

        # 界面布局
        self.__config_gui_layout()

        # 创建一个线程, 用于检测是否启动自动翻译
        self.autoTranslateTask = Thread(target=self.__autoTranslate)
        self.autoTranslateTask.daemon = True        # 设置为守护线程(主线程结束, 则守护线程结束)
        self.autoTranslateTask.start()

    # GUI整体布局
    def __config_gui_layout(self):
        # 1.菜单布局
        self.__config_menu_layout

        # 2.主界面布局
        self.__config_mainwin_layout()

    def __config_menu_layout(self):
        self.menu = tk.Menu(self.root)

        submenu = tk.Menu(self.menu, tearoff=0)
        submenu.add_command(label='Config')
        self.menu.add_cascade(label='File', menu=submenu)

        submenu = tk.Menu(self.menu, tearoff=0)
        submenu.add_command(label='Info')
        submenu.add_command(label='Help')
        self.menu.add_cascade(label='About', menu=submenu)

        self.root.config(menu=self.menu)

    # 主界面布局
    def __config_mainwin_layout(self):
        mainPanwin = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        mainPanwin.pack()

        # mainPanwin
        leftPanwin = tk.PanedWindow(mainPanwin, orient=tk.VERTICAL, width=600)
        rightPanwin = tk.PanedWindow(mainPanwin, orient=tk.VERTICAL, width=400)
        mainPanwin.add(leftPanwin)
        mainPanwin.add(rightPanwin)

        # leftPanwin
        leftTopFm = tk.LabelFrame(leftPanwin, text='按钮区')
        leftBottomFm = tk.LabelFrame(leftPanwin, text='图片显示区')
        leftPanwin.add(leftTopFm)
        leftPanwin.add(leftBottomFm)

        # rightPanwin
        rightTopFm = tk.LabelFrame(rightPanwin, text='OCR文本显示区')
        rightBottomFm = tk.LabelFrame(rightPanwin, text='文本翻译区')
        rightPanwin.add(rightTopFm)
        rightPanwin.add(rightBottomFm)

        # leftTopFm 按钮区
        tk.Button(leftTopFm, text='加载图片', command=self.__load_images).grid(row=0, padx=3, pady=3)
        tk.Button(leftTopFm, text='设置截图区域', command=self.__screenshot_area_setting).grid(row=0, column=1, padx=3, pady=3)
        tk.Button(leftTopFm, text='翻译测试', command=self.__translate).grid(row=0, column=2, padx=3, pady=3)
        tk.Button(leftTopFm, text='开启/关闭自动翻译', command=self.__autoTranslateSwitch).grid(row=0, column=3, padx=3, pady=3)

        # leftBottomFm 图片显示区
        leftBtLabel = tk.Label(leftBottomFm, textvariable=self.screenshotAreaLabel, font=('微软黑雅',15))
        leftBtLabel.pack(side=tk.TOP, anchor=tk.W)
        leftBtLabel2 = tk.Label(leftBottomFm, textvariable=self.autoScreenshotFlag, font=('微软黑雅',15))
        leftBtLabel2.pack(side=tk.TOP, anchor=tk.W)
        self.leftBtCanvas = tk.Canvas(leftBottomFm, bg='white', width=600, height=600)
        self.leftBtCanvas.pack(side=tk.BOTTOM)

        # rightTopFm OCR文本显示区
        self.rightOcrText = tk.Text(rightTopFm, bg='white')
        self.rightOcrText.pack(side=tk.TOP)

        # rightBottomFm 文本翻译区
        self.rightTsText = tk.Text(rightBottomFm, bg='white')
        self.rightTsText.pack(side=tk.BOTTOM)

    # 通过截屏加载图片, 并获得截屏坐标
    def __screenshot_area_setting(self):
        if not self.screenshotLeftTop or not self.screenshotRightBottom:
            # 初始化设置截屏区域
            logger.info("Initialize Screenshot Area")
        else:
            # 重新设置截屏区域
            logger.info("Reset Screenshot Area")
            self.screenshotLeftTop.clear()
            self.screenshotRightBottom.clear()
        
        # 设置截图区域时应关闭自动截图
        self.isAutoTs = False
        self.autoScreenshotFlag.set('自动翻译:关闭')
        
        # Step 1: 主界面最小化
        self.root.state('icon')
        sleep(0.2)

        # Step 2: 通过引用传递返回截屏区域坐标
        screenshotArea = ScreenshotArea(self.root, self.screenshotLeftTop, self.screenshotRightBottom)
        self.root.wait_window(screenshotArea.top)   # 等待截图界面退出
        logger.debug(f'Outer Screenshot Area: {self.screenshotLeftTop}, {self.screenshotRightBottom}')

        # Step 3: 截屏并显示图片
        if not self.screenshotLeftTop or not self.screenshotRightBottom:
            self.screenshotAreaLabel.set('请重新设置截屏区域')
            return
        else:
            self.imgTs = ImageGrab.grab(bbox=(self.screenshotLeftTop[0] + 1, self.screenshotLeftTop[1], 
                                                self.screenshotRightBottom[0] + 1, self.screenshotRightBottom[1]))
            self.__show_images_in_canvas()
            self.screenshotAreaLabel.set(f'截屏区域坐标为: {self.screenshotLeftTop}, {self.screenshotRightBottom}')
        
        # Step 4: 主界面恢复
        self.root.state('normal')
        sleep(0.2)

    # 将显示的图像缩放到合适的尺寸
    def __resize_image(self):
        if self.imgTs.width < self.leftBtCanvas.winfo_width() and self.imgTs.height < self.leftBtCanvas.winfo_height():
            logger.debug('No Need to resize the image')
            self.imgTsResized = self.imgTs
        else:
            logger.debug('Need to resize the image')
            self.resizeFactor = max([self.imgTs.width / self.leftBtCanvas.winfo_width(), 
                                        self.imgTs.height / self.leftBtCanvas.winfo_height()])
            self.imgTsResized = self.imgTs.resize((round(self.imgTs.width / self.resizeFactor), round(self.imgTs.height / self.resizeFactor)))

    def __show_images_in_canvas(self):
        if not self.imgTs:
            return
        self.__resize_image()
        self.imgShow = ImageTk.PhotoImage(self.imgTsResized)      # 必须是全局变量, 否则图片无法正常显示

        # 删除上一个截图
        if self.imgShowCanvas:
            self.leftBtCanvas.delete(self.imgShowCanvas)
        self.imgShowCanvas = self.leftBtCanvas.create_image(self.leftBtCanvas.winfo_height() // 2, self.leftBtCanvas.winfo_width() // 2, image=self.imgShow)

    def __autoTranslateSwitch(self):
        if not self.screenshotLeftTop or not self.screenshotRightBottom:
            self.screenshotAreaLabel.set('截屏区域还未设置')
            self.isAutoTs = False
            return

        # 开启/关闭定时器任务
        self.isAutoTs = not self.isAutoTs
        if self.isAutoTs:
            self.autoScreenshotFlag.set('自动翻译:开启')
        else:
            self.autoScreenshotFlag.set('自动翻译:关闭')
        
    # 自动翻译线程(daemon)
    def __autoTranslate(self):
        logger.info('Autotranslate Thread is starting...')
        # time.sleep(100)
        while True:
            if self.isAutoTs:
                logger.debug('Autotranslating...')
                self.imgTs = ImageGrab.grab(bbox=(self.screenshotLeftTop[0] + 1, self.screenshotLeftTop[1], 
                                            self.screenshotRightBottom[0] + 1, self.screenshotRightBottom[1]))
                self.__show_images_in_canvas()
                self.__translate()
            time.sleep(self.autoTsInterval)
    
    # 从文件中选择图片加载
    def __load_images(self):
        imgPath = filedialog.askopenfilename(title='load images')
        self.imgTs = Image.open(imgPath)
        self.__show_images_in_canvas()

    def __translate(self):
        if not self.imgTs:
            self.rightOcrText.delete('1.0', tk.END)
            self.rightTsText.delete('1.0', tk.END)
            self.rightOcrText.insert(tk.END, "This no image need to translate.")
            return

        # OCR识别
        ja_text = self.ocr(self.imgTs)
        self.rightOcrText.delete('1.0', tk.END)
        self.rightOcrText.insert(tk.END, ja_text)

        # 文本翻译
        zh_text = self.mt5t(ja_text)
        self.rightTsText.delete('1.0', tk.END)
        self.rightTsText.insert(tk.END, zh_text)
    
    def __call__(self):
        self.root.mainloop()

# 设置截屏区域
class ScreenshotArea:
    def __init__(self, root: tk.Tk, screenshotLeftTop: List, screenshotRightBottom: List):
        # 存储截屏左上角坐标
        self.leftTopX = tk.IntVar()
        self.leftTopY = tk.IntVar()

        # 待返回的区域坐标
        self.leftTop = screenshotLeftTop
        self.rightBottom = screenshotRightBottom

        # 是否开始截屏
        self.isScreenshot = False
        self.screenshotRect = None

        # 获得显示器像素
        self.screenWidth = root.winfo_screenwidth()
        self.screenHeight = root.winfo_screenheight()

        self.top = tk.Toplevel(root, width=self.screenWidth, height=self.screenHeight)
        self.top.overrideredirect(True)     # 不显示最大最小化按钮

        self.canvas = tk.Canvas(self.top, width=self.screenWidth, height=self.screenHeight, bg='white')
        self.screenshotImg = ImageGrab.grab()       # 全屏截图
        self.screenshotTk = ImageTk.PhotoImage(self.screenshotImg)
        self.canvas.create_image(self.screenWidth // 2, self.screenHeight // 2, image=self.screenshotTk)
        self.canvas.bind('<ButtonPress-1>', self.__onLeftMousePress)
        self.canvas.bind('<ButtonRelease-1>', self.__onLeftMouseRelease)
        self.canvas.bind('<B1-Motion>', self.__onLeftMouseMove)
        self.canvas.pack()

    def __onLeftMousePress(self, event):
        self.leftTopX.set(event.x)
        self.leftTopY.set(event.y)
        self.isScreenshot = True

    def __onLeftMouseMove(self, event):
        if not self.isScreenshot:
            return
        
        if self.screenshotRect:
            self.canvas.delete(self.screenshotRect)
        self.screenshotRect = self.canvas.create_rectangle(self.leftTopX.get(), self.leftTopY.get(), event.x, event.y, outline='black')

    # 当鼠标释放时, 保存此时的截图区域坐标
    # TODO: 不限制于左上角和右下角, 也可以是左下角和右上角(未解决)
    def __onLeftMouseRelease(self, event):
        # 此时不再画图
        self.isScreenshot = False

        # list引用传递
        if self.leftTopX.get() < event.x:
            self.leftTop.append(self.leftTopX.get())
            self.leftTop.append(self.leftTopY.get())
            self.rightBottom.append(event.x)
            self.rightBottom.append(event.y)
        else:
            self.leftTop.append(event.x)
            self.leftTop.append(event.y)
            self.rightBottom.append(self.leftTopX.get())
            self.rightBottom.append(self.leftTopY.get())

        logger.info(f'Inner Screenshot Area: {self.leftTop}, {self.rightBottom}')

        self.top.destroy()
    