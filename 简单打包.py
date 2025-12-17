#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def simple_build():
    """简单的打包方法"""
    print("开始简单打包...")
    
    # 检查pyinstaller
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装PyInstaller...")
        os.system("pip install pyinstaller")
    
    # 打包命令
    print("打包标签生成器...")
    os.system('pyinstaller --onefile --name="标签生成器" generate_pdf.py')
    
    print("打包图片裁剪工具...")
    os.system('pyinstaller --onefile --name="图片裁剪转PDF" crop_images_to_pdf.py')
    
    print("打包完成！请查看dist文件夹")

if __name__ == "__main__":
    simple_build()
    input("按任意键退出...")
