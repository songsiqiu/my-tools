#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PIL import Image
from reportlab.pdfgen import canvas
import tempfile

def find_images_in_folder(folder_path):
    """扫描文件夹中的图片文件"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
    image_files = []
    
    for filename in os.listdir(folder_path):
        if os.path.splitext(filename.lower())[1] in image_extensions:
            image_files.append(os.path.join(folder_path, filename))
    
    return sorted(image_files)

def crop_whitespace(image_path):
    """裁剪图片周围的空白区域"""
    try:
        # 打开图片
        img = Image.open(image_path)
        print(f"  原始尺寸: {img.size}")
        
        # 转换为RGBA模式处理透明度
        if img.mode == 'RGBA':
            # 对于有透明度的图片，先转换为白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 获取图片像素数据
        pixels = img.load()
        width, height = img.size
        
        # 定义白色阈值
        white_threshold = 250
        
        # 从四个方向找边界
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
        
        print(f"  检测到边界: 左={left}, 上={top}, 右={right}, 下={bottom}")
        
        # 裁剪图片
        if left < right and top < bottom:
            cropped = img.crop((left, top, right + 1, bottom + 1))
            print(f"  裁剪后尺寸: {cropped.size}")
            return cropped
        else:
            print("  未检测到有效边界，返回原图")
            return img
            
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")
        return None

def image_to_pdf(img_path, output_dir):
    """将单张图片转换为PDF"""
    try:
        cropped_img = crop_whitespace(img_path)
        if cropped_img is None:
            return False
        
        # 生成PDF文件名（使用原图片名称）
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        output_pdf = os.path.join(output_dir, f"{base_name}.pdf")
        
        # 创建PDF
        c = canvas.Canvas(output_pdf, pagesize=cropped_img.size)
        
        # 保存图片到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            cropped_img.save(temp_file.name, 'PNG')
            
            # 将图片添加到PDF
            c.drawImage(temp_file.name, 0, 0, 
                      width=cropped_img.size[0], 
                      height=cropped_img.size[1])
            c.save()
            
            # 删除临时文件
            os.unlink(temp_file.name)
        
        print(f"  ✓ 生成PDF: {base_name}.pdf")
        return True
        
    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        return False

def main():
    """主函数"""
    try:
        # 使用当前工作目录，而不是脚本所在目录
        current_dir = os.getcwd()
        
        print("=== 图片裁剪转PDF工具 ===")
        print(f"程序运行目录: {current_dir}")
        
        print("正在扫描图片文件...")
        image_files = find_images_in_folder(current_dir)
        
        if not image_files:
            print(f"\n❌ 当前文件夹中没有找到图片文件")
            print(f"支持的图片格式: .jpg, .jpeg, .png, .bmp, .tiff, .tif, .gif")
            print(f"\n请将图片文件放在程序同一目录下:")
            print(f"  1. 图片裁剪转PDF.exe")
            print(f"  2. 需要处理的图片文件")
            
            print(f"\n当前文件夹中的文件:")
            try:
                files = os.listdir(current_dir)
                for file in files:
                    print(f"  - {file}")
            except:
                print("  无法列出文件")
            
            input("\n按回车键退出...")
            return
        
        print(f"✓ 找到 {len(image_files)} 张图片:")
        for img in image_files:
            print(f"  - {os.path.basename(img)}")
        
        print("\n开始处理图片...")
        processed_count = 0
        
        for i, img_path in enumerate(image_files):
            print(f"\n处理图片 {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
            if image_to_pdf(img_path, current_dir):
                processed_count += 1
        
        print(f"\n=== 处理完成 ===")
        print(f"成功处理: {processed_count}/{len(image_files)} 张图片")
        
        if processed_count > 0:
            print(f"生成的PDF文件已保存在当前目录")
        
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("请联系技术支持")
    
    # 程序结束前暂停
    input("\n按回车键退出...")

if __name__ == "__main__":
    # 检查依赖
    try:
        from PIL import Image
        import reportlab
    except ImportError as e:
        print("❌ 错误: 缺少必要组件")
        print("这是一个打包问题，请联系技术支持")
        input("按回车键退出...")
        exit(1)
    
    main()
