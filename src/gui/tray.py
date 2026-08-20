# -*- coding: utf-8 -*-
"""
系统托盘支持
窗口关闭后最小化到托盘后台运行；--tray 启动时无窗口纯后台
"""

import sys
import threading
from pathlib import Path


def create_tray_icon(app=None, on_show=None, on_clean=None, on_quit=None):
    """
    创建系统托盘图标

    Args:
        app: 主窗口对象（可被 show 方法唤起）
        on_show (callable): 显示主窗口回调
        on_clean (callable): 立即清理回调
        on_quit (callable): 退出程序回调

    Returns:
        pystray.Icon | None: 托盘图标，pystray 不可用时返回 None
    """
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("⚠️ pystray 不可用，无法使用托盘后台运行")
        return None

    # 生成一个简单的文件夹图标（64x64）
    def _make_icon_image():
        img = Image.new("RGB", (64, 64), (240, 240, 240))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([12, 18, 52, 52], radius=4, fill=(66, 133, 244))
        d.rounded_rectangle([16, 22, 48, 48], radius=3, fill=(255, 255, 255))
        d.line([24, 34, 40, 34], fill=(66, 133, 244), width=3)
        d.line([24, 41, 36, 41], fill=(66, 133, 244), width=3)
        return img

    menu_items = []
    if on_show:
        menu_items.append(pystray.MenuItem("打开主界面", lambda: on_show(), default=True))
    if on_clean:
        menu_items.append(pystray.MenuItem("立即清理", lambda: on_clean()))
    menu_items.append(pystray.Menu.SEPARATOR)
    if on_quit:
        menu_items.append(pystray.MenuItem("退出", lambda: on_quit()))

    icon = pystray.Icon(
        "smart_file_cleaner",
        _make_icon_image(),
        "智能文档清理器",
        pystray.Menu(*menu_items),
    )
    return icon


def run_tray_loop(icon):
    """
    在后台线程运行托盘循环

    Args:
        icon: pystray.Icon 实例

    Returns:
        threading.Thread: 托盘线程
    """
    if icon is None:
        return None
    thread = threading.Thread(target=icon.run, name="tray-icon", daemon=True)
    thread.start()
    return thread
