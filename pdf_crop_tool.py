#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageChops
import tempfile

def find_pdf_files(folder_path):
    """递归查找所有PDF文件"""
    pdf_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def crop_pdf_pages(input_pdf_path, output_pdf_path):
    """裁剪PDF每一页的空白区域"""
    try:
        # 打开PDF文档
        pdf_document = fitz.open(input_pdf_path)
        
        # 创建新的PDF文档
        new_pdf = fitz.open()
        
        total_pages = len(pdf_document)
        print(f"    处理 {total_pages} 页...")
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            
            # 将页面转换为图片
            mat = fitz.Matrix(2.0, 2.0)  # 放大倍数，提高质量
            pix = page.get_pixmap(matrix=mat)
            
            # 使用内存缓冲区而不是临时文件
            img_data = pix.tobytes("png")
            
            # 转换为PIL图像
            from io import BytesIO
            img_stream = BytesIO(img_data)
            
            with Image.open(img_stream) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 获取图片像素数据并裁剪
                pixels = img.load()
                width, height = img.size
                
                # 定义白色阈值
                white_threshold = 240
                
                # 找边界
                # 找上边界
                top = 0
                for y in range(height):
                    found_content = False
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        if r < white_threshold or g < white_threshold or b < white_threshold:
                            found_content = True
                            break
                    if found_content:
                        top = y
                        break
                
                # 找下边界
                bottom = height - 1
                for y in range(height - 1, -1, -1):
                    found_content = False
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        if r < white_threshold or g < white_threshold or b < white_threshold:
                            found_content = True
                            break
                    if found_content:
                        bottom = y
                        break
                
                # 找左边界
                left = 0
                for x in range(width):
                    found_content = False
                    for y in range(height):
                        r, g, b = pixels[x, y]
                        if r < white_threshold or g < white_threshold or b < white_threshold:
                            found_content = True
                            break
                    if found_content:
                        left = x
                        break
                
                # 找右边界
                right = width - 1
                for x in range(width - 1, -1, -1):
                    found_content = False
                    for y in range(height):
                        r, g, b = pixels[x, y]
                        if r < white_threshold or g < white_threshold or b < white_threshold:
                            found_content = True
                            break
                    if found_content:
                        right = x
                        break
                
                # 裁剪图片
                if left < right and top < bottom:
                    cropped = img.crop((left, top, right + 1, bottom + 1))
                else:
                    cropped = img
                
                # 转换为RGB模式（如果还不是）
                if cropped.mode != 'RGB':
                    cropped = cropped.convert('RGB')
                
                # 保存裁剪后的图片到内存
                output_stream = BytesIO()
                cropped.save(output_stream, format='PNG', dpi=(300, 300))
                output_stream.seek(0)
                
                # 创建新页面并插入图片
                img_rect = fitz.Rect(0, 0, cropped.width, cropped.height)
                new_page = new_pdf.new_page(width=cropped.width, height=cropped.height)
                new_page.insert_image(img_rect, stream=output_stream.getvalue())
            
            print(f"    完成第 {page_num + 1}/{total_pages} 页")
        
        # 保存新PDF
        new_pdf.save(output_pdf_path)
        new_pdf.close()
        pdf_document.close()
        
        return True
        
    except Exception as e:
        print(f"    ❌ 处理PDF失败: {e}")
        # 确保文件被正确关闭
        try:
            if 'new_pdf' in locals():
                new_pdf.close()
            if 'pdf_document' in locals():
                pdf_document.close()
        except:
            pass
        return False

def process_folder(input_folder, output_folder):
    """处理整个文件夹"""
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 查找所有PDF文件
    pdf_files = find_pdf_files(input_folder)
    
    if not pdf_files:
        print(f"在 {input_folder} 中没有找到PDF文件")
        return 0
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    processed_count = 0
    
    for i, pdf_path in enumerate(pdf_files):
        print(f"\n处理文件 {i+1}/{len(pdf_files)}: {os.path.relpath(pdf_path, input_folder)}")
        
        # 计算相对路径
        rel_path = os.path.relpath(pdf_path, input_folder)
        output_pdf_path = os.path.join(output_folder, rel_path)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_pdf_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理PDF
        if crop_pdf_pages(pdf_path, output_pdf_path):
            print(f"  ✓ 处理完成: {os.path.basename(pdf_path)}")
            processed_count += 1
        else:
            print(f"  ❌ 处理失败: {os.path.basename(pdf_path)}")
    
    return processed_count

def main():
    """主函数"""
    try:
        current_dir = os.getcwd()
        input_folder = os.path.join(current_dir, "要处理的文件夹")
        output_folder = os.path.join(current_dir, "处理好的文件夹")
        
        print("=== PDF空白裁剪工具 ===")
        print(f"程序运行目录: {current_dir}")
        print(f"输入文件夹: 要处理的文件夹")
        print(f"输出文件夹: 处理好的文件夹")
        
        # 检查输入文件夹是否存在
        if not os.path.exists(input_folder):
            print(f"\n❌ 错误: 找不到文件夹 '要处理的文件夹'")
            print(f"请确保以下文件夹结构:")
            print(f"  程序所在目录/")
            print(f"  ├── pdf_crop_tool.exe")
            print(f"  └── 要处理的文件夹/")
            print(f"      ├── 子文件夹1/")
            print(f"      │   ├── 文件1.pdf")
            print(f"      │   └── 文件2.pdf")
            print(f"      └── 子文件夹2/")
            print(f"          └── 文件3.pdf")
            
            print(f"\n当前目录中的文件夹:")
            try:
                items = os.listdir(current_dir)
                folders = [item for item in items if os.path.isdir(os.path.join(current_dir, item))]
                for folder in folders:
                    print(f"  - {folder}/")
            except:
                print("  无法列出文件夹")
            
            input("\n按回车键退出...")
            return
        
        print(f"✓ 找到输入文件夹")
        
        # 处理文件夹
        print(f"\n开始处理PDF文件...")
        processed_count = process_folder(input_folder, output_folder)
        
        print(f"\n=== 处理完成 ===")
        print(f"成功处理: {processed_count} 个PDF文件")
        print(f"输出位置: 处理好的文件夹")
        
        if processed_count > 0:
            print(f"\n所有PDF的空白边缘已被裁剪并保存到输出文件夹")
        
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("请联系技术支持")
    
    # 程序结束前暂停
    input("\n按回车键退出...")

if __name__ == "__main__":
    # 检查依赖
    try:
        import fitz  # PyMuPDF
        from PIL import Image
    except ImportError as e:
        print("❌ 错误: 缺少必要组件")
        print("缺少的库:", str(e))
        print("这是一个打包问题，请联系技术支持")
        input("按回车键退出...")
        exit(1)
    
    main()
