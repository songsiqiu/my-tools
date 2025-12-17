#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black

def read_txt_file(filename):
    """读取txt文件并按组分割内容"""
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 按空行分割成组
    groups = content.strip().split('\n\n')
    return groups

def calculate_optimal_font_size(canvas_obj, lines, font_name, page_width, page_height, margin):
    """计算最优字体大小，使文本尽可能占满页面"""
    # 可用宽度和高度
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin
    
    # 从较大字体开始尝试，更激进地使用页面空间
    for font_size in range(80, 12, -2):  # 从80号字体开始，递减到12号
        line_height = font_size * 1.2  # 减少行间距，让文本更紧凑
        total_height = len(lines) * line_height
        
        # 检查高度是否合适，使用95%的可用高度
        if total_height > available_height * 0.95:
            continue
            
        # 检查宽度是否合适
        max_width = 0
        for line in lines:
            if line.strip():
                text_width = canvas_obj.stringWidth(line, font_name, font_size)
                max_width = max(max_width, text_width)
        
        # 如果最长行的宽度小于可用宽度的95%，这个字体大小合适
        if max_width <= available_width * 0.95:
            return font_size, line_height
    
    # 如果没找到合适的，返回最小字体
    return 14, 14 * 1.2

def calculate_optimal_layout(canvas_obj, lines, font_name, page_width, margin):
    """计算最优布局，返回字体大小、行高和所需页面高度"""
    available_width = page_width - 2 * margin
    
    # 从较大字体开始尝试
    for font_size in range(80, 12, -2):
        line_height = font_size * 1.1  # 进一步减少行间距
        
        # 检查宽度是否合适
        max_width = 0
        for line in lines:
            if line.strip():
                text_width = canvas_obj.stringWidth(line, font_name, font_size)
                max_width = max(max_width, text_width)
        
        # 如果最长行的宽度小于可用宽度的95%，这个字体大小合适
        if max_width <= available_width * 0.95:
            # 计算所需的页面高度，增加顶部边距避免截断
            total_text_height = len(lines) * line_height
            required_height = total_text_height + margin * 2 + font_size * 0.3  # 增加顶部边距
            return font_size, line_height, required_height
    
    # 如果没找到合适的，返回最小字体
    font_size = 14
    line_height = font_size * 1.1
    total_text_height = len(lines) * line_height
    required_height = total_text_height + margin * 2 + font_size * 0.3
    return font_size, line_height, required_height

def create_pdf(groups, output_filename):
    """创建PDF文件"""
    # 基础页面宽度保持1000像素
    base_width = 1000
    margin = 20  # 进一步减少页边距
    
    # 尝试设置中文字体
    font_name = 'Helvetica'  # 默认字体
    try:
        # Windows系统常见中文字体
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    font_name = 'ChineseFont'
                    print(f"成功加载中文字体: {font_path}")
                    break
                except Exception as font_error:
                    print(f"加载字体失败 {font_path}: {font_error}")
                    continue
                    
    except Exception as e:
        print(f"字体设置失败，使用默认字体: {e}")
    
    # 创建临时canvas用于测量
    temp_canvas = canvas.Canvas("temp.pdf", pagesize=(base_width, 1000))
    
    # 预计算所有组的布局信息
    layouts = []
    for group in groups:
        lines = [line for line in group.strip().split('\n') if line.strip()]
        font_size, line_height, required_height = calculate_optimal_layout(
            temp_canvas, lines, font_name, base_width, margin
        )
        layouts.append({
            'lines': lines,
            'font_size': font_size,
            'line_height': line_height,
            'page_height': max(required_height, 200)  # 稍微增加最小高度确保不截断
        })
    
    # 删除临时canvas文件
    try:
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")
    except:
        pass
    
    # 创建实际的PDF
    c = None
    
    for i, layout in enumerate(layouts):
        # 为每页创建合适的页面大小
        page_size = (base_width, int(layout['page_height']))
        
        if c is None:
            c = canvas.Canvas(output_filename, pagesize=page_size)
        else:
            c.setPageSize(page_size)
            c.showPage()
        
        # 设置字体
        c.setFont(font_name, layout['font_size'])
        
        # 计算起始位置，增加顶部边距避免截断
        page_width, page_height = page_size
        # 从顶部留出足够空间，避免中文字体被截断
        start_y = page_height - margin - layout['font_size'] * 0.8  # 增加顶部空间
        start_x = margin
        
        # 绘制每一行
        for j, line in enumerate(layout['lines']):
            y_position = start_y - (j * layout['line_height'])
            c.drawString(start_x, y_position, line)
    
    if c:
        c.save()
        print(f"PDF文件已生成: {output_filename}")
    else:
        print("没有内容可生成PDF")

def main():
    """主函数"""
    try:
        # 使用当前工作目录，而不是脚本所在目录
        current_dir = os.getcwd()
        input_file = os.path.join(current_dir, '1.txt')
        output_file = os.path.join(current_dir, 'output.pdf')
        
        print("=== 标签生成器 ===")
        print(f"程序运行目录: {current_dir}")
        print(f"查找数据文件: 1.txt")
        
        # 检查1.txt文件是否存在
        if not os.path.exists(input_file):
            print(f"\n❌ 错误: 找不到数据文件 '1.txt'")
            print(f"请确保以下文件在同一文件夹中:")
            print(f"  1. 标签生成器.exe")
            print(f"  2. 1.txt (数据文件)")
            print(f"\n当前文件夹中的文件:")
            try:
                files = os.listdir(current_dir)
                for file in files:
                    print(f"  - {file}")
            except:
                print("  无法列出文件")
            
            print(f"\n请将1.txt文件放在程序同一目录下后重新运行")
            input("\n按回车键退出...")
            return
        
        print(f"✓ 找到数据文件: 1.txt")
        
        # 读取并处理文件
        try:
            groups = read_txt_file(input_file)
            print(f"✓ 成功读取数据，共找到 {len(groups)} 组标签数据")
        except Exception as e:
            print(f"\n❌ 读取文件失败: {e}")
            print("请检查1.txt文件格式是否正确")
            input("\n按回车键退出...")
            return
        
        if not groups:
            print(f"\n❌ 数据文件为空或格式不正确")
            print("请检查1.txt文件内容")
            input("\n按回车键退出...")
            return
        
        # 生成PDF
        print("开始生成PDF...")
        create_pdf(groups, output_file)
        
        if os.path.exists(output_file):
            print(f"✓ PDF生成成功: output.pdf")
        else:
            print(f"❌ PDF生成失败")
            
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("请联系技术支持")
    
    # 程序结束前暂停，让用户看到结果
    input("\n按回车键退出...")

if __name__ == "__main__":
    # 检查依赖
    try:
        import reportlab
    except ImportError:
        print("❌ 错误: 缺少必要组件")
        print("这是一个打包问题，请联系技术支持")
        input("按回车键退出...")
        exit(1)
    
    main()
