#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

def install_dependencies():
    """安装打包所需的依赖"""
    required_packages = [
        'pyinstaller',
        'reportlab', 
        'Pillow',
        'PyMuPDF'  # 添加PDF处理库
    ]
    
    for package in required_packages:
        try:
            print(f"安装 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:
            print(f"安装 {package} 失败")
            return False
    return True

def build_exe():
    """打包exe文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查文件是否存在
    scripts = [
        ('generate_pdf.py', '标签生成器'),
        ('crop_images_to_pdf.py', '图片裁剪转PDF'),
        ('pdf_crop_tool.py', 'PDF空白裁剪工具')
    ]
    
    for script_file, exe_name in scripts:
        script_path = os.path.join(current_dir, script_file)
        if not os.path.exists(script_path):
            print(f"错误: 找不到 {script_file}")
            return False
    
    # 打包所有程序
    for script_file, exe_name in scripts:
        print(f"正在打包 {exe_name}...")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--console',
            f'--name={exe_name}',
            '--distpath=dist',
            '--workpath=build',
            script_file
        ]
        
        try:
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=current_dir, check=True, capture_output=True, text=True)
            print(f"{exe_name} 打包成功")
        except subprocess.CalledProcessError as e:
            print(f"打包 {exe_name} 失败: {e}")
            if e.stdout:
                print(f"输出: {e.stdout}")
            if e.stderr:
                print(f"错误: {e.stderr}")
            return False
        except FileNotFoundError:
            print("错误: 找不到PyInstaller")
            return False
    
    return True

def create_readme():
    """创建使用说明"""
    readme_content = """
# 工具使用说明

## 标签生成器.exe
- 功能：根据1.txt文件内容生成PDF标签
- 使用方法：
  1. 将"标签生成器.exe"和"1.txt"放在同一文件夹
  2. 双击运行"标签生成器.exe"
  3. 程序会自动读取1.txt并生成output.pdf

## 图片裁剪转PDF.exe  
- 功能：裁剪图片空白边缘并转换为PDF
- 使用方法：
  1. 将"图片裁剪转PDF.exe"和图片文件放在同一文件夹
  2. 双击运行"图片裁剪转PDF.exe"
  3. 程序会自动处理所有图片并生成对应的PDF文件

## PDF空白裁剪工具.exe
- 功能：批量裁剪PDF文件每页的空白边缘
- 使用方法：
  1. 创建文件夹结构：程序目录/要处理的文件夹/各种PDF文件
  2. 双击运行"PDF空白裁剪工具.exe"
  3. 程序会递归处理所有PDF并输出到"处理好的文件夹"

## 注意事项
- 确保文件夹有读写权限
- PDF处理需要较多时间，请耐心等待
- 程序运行时请勿移动或删除相关文件
"""
    
    with open('使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)

def main():
    """主函数"""
    print("开始打包程序...")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 安装依赖
    if not install_dependencies():
        print("依赖安装失败，请手动安装：pip install pyinstaller reportlab Pillow PyMuPDF")
        return
    
    # 打包exe
    if build_exe():
        print("\n打包完成！")
        print("生成的文件位于 dist 文件夹中：")
        print("- 标签生成器.exe")
        print("- 图片裁剪转PDF.exe")
        print("- PDF空白裁剪工具.exe")
        
        # 创建说明文件
        create_readme()
        print("- 使用说明.txt")
        
        print("\n请将exe文件和使用说明.txt一起提供给客户")
        
        # 检查生成的文件
        dist_dir = "dist"
        if os.path.exists(dist_dir):
            files = os.listdir(dist_dir)
            print(f"\ndist目录中的文件: {files}")
        
    else:
        print("打包失败！")
        print("请检查:")
        print("1. 是否已正确安装所有依赖: pip install pyinstaller reportlab Pillow PyMuPDF")
        print("2. 是否有足够的磁盘空间")
        print("3. 是否有写入权限")

if __name__ == "__main__":
    main()
