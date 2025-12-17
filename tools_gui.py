#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多功能工具箱 - 可视化界面 v2.0
整合: 标签生成器、图片裁剪转PDF、PDF空白裁剪工具
"""

import os
import sys
import threading
import tempfile
from io import BytesIO
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 导入所需库
try:
    from PIL import Image
    import fitz  # PyMuPDF
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:
    print(f"缺少依赖库: {e}")
    print("请安装: pip install Pillow PyMuPDF reportlab")
    sys.exit(1)


class ToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多功能工具箱 v2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(700, 500)
        
        # 设置样式
        self.setup_styles()
        
        # 创建主框架
        self.create_ui()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 设置Notebook标签样式
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', 
                       padding=[20, 10], 
                       font=('微软雅黑', 11, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', '#4a90d9'), ('!selected', '#c0c0c0')],
                 foreground=[('selected', '#000000'), ('!selected', '#333333')],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # 设置按钮样式
        style.configure('Action.TButton', 
                       font=('微软雅黑', 11, 'bold'),
                       padding=[20, 10])
        
        # 设置LabelFrame样式
        style.configure('TLabelframe', padding=10)
        style.configure('TLabelframe.Label', font=('微软雅黑', 10, 'bold'))
        
    def create_ui(self):
        """创建用户界面"""
        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建三个功能页面
        self.create_label_generator_tab()
        self.create_image_to_pdf_tab()
        self.create_pdf_crop_tab()
        
    def create_label_generator_tab(self):
        """创建标签生成器页面 - 直接输入文本"""
        # 创建主容器
        container = ttk.Frame(self.notebook)
        self.notebook.add(container, text="  📝 标签生成器  ")
        
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas, padding=15)
        
        # 配置Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_frame = canvas.create_window((0, 0), window=frame, anchor="nw")
        
        # 绑定滚动事件
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # 鼠标滚轮支持
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # 顶部说明
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text="直接输入标签内容，生成PDF", 
                 font=('微软雅黑', 10)).pack(side=tk.LEFT)
        ttk.Label(desc_frame, text="（每组标签用空行分隔）", 
                 font=('微软雅黑', 9), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        # 文本输入区域
        input_frame = ttk.LabelFrame(frame, text="📋 输入标签内容", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.label_text = scrolledtext.ScrolledText(input_frame, height=12, 
                                                    font=('Consolas', 11),
                                                    wrap=tk.WORD,
                                                    relief=tk.SUNKEN,
                                                    borderwidth=1)
        self.label_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.label_text.insert(tk.END, "标签1第一行\n标签1第二行\n\n标签2第一行\n标签2第二行")
        
        # 输出文件选择
        output_frame = ttk.LabelFrame(frame, text="📁 输出文件", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        self.label_output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.label_output_var, 
                 font=('微软雅黑', 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览...", 
                  command=self.browse_label_output).pack(side=tk.LEFT, padx=(10, 0))
        
        # 执行按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="🚀 生成PDF标签", style='Action.TButton',
                  command=self.run_label_generator).pack()
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="📜 运行日志", padding=5)
        log_frame.pack(fill=tk.X)
        
        self.label_log = scrolledtext.ScrolledText(log_frame, height=4, state='disabled',
                                                   font=('Consolas', 9))
        self.label_log.pack(fill=tk.X)
        
        # 打开文件/文件夹按钮
        open_btn_frame = ttk.Frame(log_frame)
        open_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(open_btn_frame, text="📂 打开输出文件夹", 
                  command=self.open_label_output_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(open_btn_frame, text="📄 打开输出文件", 
                  command=self.open_label_output_file).pack(side=tk.LEFT, padx=2)
        
    def create_image_to_pdf_tab(self):
        """创建图片裁剪转PDF页面 - 支持多种模式"""
        # 创建主容器
        container = ttk.Frame(self.notebook)
        self.notebook.add(container, text="  🖼️ 图片裁剪转PDF  ")
        
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas, padding=15)
        
        # 配置Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_frame = canvas.create_window((0, 0), window=frame, anchor="nw")
        
        # 绑定滚动事件
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # 顶部说明
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text="自动裁剪图片空白区域并转换为PDF", 
                 font=('微软雅黑', 10)).pack(side=tk.LEFT)
        ttk.Label(desc_frame, text="支持: jpg, png, bmp, tiff, gif", 
                 font=('微软雅黑', 9), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        # 输入选择
        input_frame = ttk.LabelFrame(frame, text="📂 选择图片", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 文件列表显示
        self.img_files_listbox = tk.Listbox(input_frame, height=6, 
                                            font=('Consolas', 9),
                                            selectmode=tk.EXTENDED)
        self.img_files_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮行
        btn_row = ttk.Frame(input_frame)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="📁 选择文件夹", 
                  command=self.browse_img_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="📄 选择文件", 
                  command=self.browse_img_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="🗑️ 清空列表", 
                  command=self.clear_img_list).pack(side=tk.LEFT, padx=2)
        
        self.img_files = []  # 存储选中的文件路径
        
        # 处理模式选择
        mode_frame = ttk.LabelFrame(frame, text="⚙️ 处理模式", padding=10)
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.img_mode_var = tk.StringVar(value="separate")
        
        modes = [
            ("separate", "📑 分别转换（每张图片生成单独PDF）"),
            ("merge", "📚 合并为一个PDF"),
        ]
        
        for value, text in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.img_mode_var,
                           value=value).pack(anchor=tk.W, pady=2)
        
        # 输出设置
        output_frame = ttk.LabelFrame(frame, text="📁 输出设置", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        self.img_output_var = tk.StringVar()
        ttk.Label(output_frame, text="输出位置:").pack(anchor=tk.W)
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X, pady=5)
        ttk.Entry(output_row, textvariable=self.img_output_var,
                 font=('微软雅黑', 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_row, text="选择文件夹", 
                  command=self.browse_img_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_row, text="选择文件", 
                  command=self.browse_img_output_file).pack(side=tk.LEFT)
        
        # 执行按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="🚀 开始转换", style='Action.TButton',
                  command=self.run_image_to_pdf).pack()
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="📜 运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.img_log = scrolledtext.ScrolledText(log_frame, height=6, state='disabled',
                                                 font=('Consolas', 9))
        self.img_log.pack(fill=tk.BOTH, expand=True)
        
        # 打开文件/文件夹按钮
        open_btn_frame = ttk.Frame(log_frame)
        open_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(open_btn_frame, text="📂 打开输出文件夹", 
                  command=self.open_img_output_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(open_btn_frame, text="📄 打开输出文件", 
                  command=self.open_img_output_file).pack(side=tk.LEFT, padx=2)
        
    def create_pdf_crop_tab(self):
        """创建PDF空白裁剪页面"""
        # 创建主容器
        container = ttk.Frame(self.notebook)
        self.notebook.add(container, text="  📄 PDF空白裁剪  ")
        
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas, padding=15)
        
        # 配置Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_frame = canvas.create_window((0, 0), window=frame, anchor="nw")
        
        # 绑定滚动事件
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # 顶部说明
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text="裁剪PDF文件每一页的空白边缘", 
                 font=('微软雅黑', 10)).pack(side=tk.LEFT)
        ttk.Label(desc_frame, text="支持递归处理子文件夹", 
                 font=('微软雅黑', 9), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        # 输入文件夹选择
        input_frame = ttk.LabelFrame(frame, text="📂 PDF文件夹", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.pdf_input_var = tk.StringVar()
        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X)
        ttk.Entry(input_row, textvariable=self.pdf_input_var,
                 font=('微软雅黑', 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_row, text="浏览...", 
                  command=self.browse_pdf_input).pack(side=tk.LEFT, padx=(10, 0))
        
        # 输出文件夹选择
        output_frame = ttk.LabelFrame(frame, text="📁 输出文件夹", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        self.pdf_output_var = tk.StringVar()
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X)
        ttk.Entry(output_row, textvariable=self.pdf_output_var,
                 font=('微软雅黑', 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_row, text="浏览...", 
                  command=self.browse_pdf_output).pack(side=tk.LEFT, padx=(10, 0))
        
        # 执行按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="🚀 开始裁剪", style='Action.TButton',
                  command=self.run_pdf_crop).pack()
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="📜 运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.pdf_log = scrolledtext.ScrolledText(log_frame, height=8, state='disabled',
                                                 font=('Consolas', 9))
        self.pdf_log.pack(fill=tk.BOTH, expand=True)
        
        # 打开文件夹按钮
        open_btn_frame = ttk.Frame(log_frame)
        open_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(open_btn_frame, text="📂 打开输出文件夹", 
                  command=self.open_pdf_output_folder).pack(side=tk.LEFT, padx=2)

    # ============ 文件浏览方法 ============
    def browse_label_output(self):
        filename = filedialog.asksaveasfilename(
            title="保存PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        if filename:
            self.label_output_var.set(filename)
            
    def browse_img_folder(self):
        """选择图片文件夹"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
            for filename in sorted(os.listdir(folder)):
                if os.path.splitext(filename.lower())[1] in image_extensions:
                    full_path = os.path.join(folder, filename)
                    if full_path not in self.img_files:
                        self.img_files.append(full_path)
                        self.img_files_listbox.insert(tk.END, filename)
            
            # 自动设置输出文件夹
            if not self.img_output_var.get():
                self.img_output_var.set(folder)
                
    def browse_img_files(self):
        """选择多个图片文件"""
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff;*.tif;*.gif"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            for f in files:
                if f not in self.img_files:
                    self.img_files.append(f)
                    self.img_files_listbox.insert(tk.END, os.path.basename(f))
            
            # 自动设置输出文件夹
            if not self.img_output_var.get():
                self.img_output_var.set(os.path.dirname(files[0]))
                
    def clear_img_list(self):
        """清空图片列表"""
        self.img_files = []
        self.img_files_listbox.delete(0, tk.END)
        
    def browse_img_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.img_output_var.set(folder)
            
    def browse_img_output_file(self):
        """选择输出PDF文件（合并模式）"""
        filename = filedialog.asksaveasfilename(
            title="保存PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        if filename:
            self.img_output_var.set(filename)
            
    def browse_pdf_input(self):
        folder = filedialog.askdirectory(title="选择PDF文件夹")
        if folder:
            self.pdf_input_var.set(folder)
            
    def browse_pdf_output(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.pdf_output_var.set(folder)
    
    # ============ 打开文件/文件夹方法 ============
    def open_label_output_folder(self):
        """打开标签生成器输出文件夹"""
        output = self.label_output_var.get()
        if output:
            folder = os.path.dirname(output)
            if os.path.exists(folder):
                os.startfile(folder)
            else:
                messagebox.showwarning("提示", "文件夹不存在")
        else:
            messagebox.showwarning("提示", "请先设置输出文件路径")
            
    def open_label_output_file(self):
        """打开标签生成器输出文件"""
        output = self.label_output_var.get()
        if output and os.path.exists(output):
            os.startfile(output)
        else:
            messagebox.showwarning("提示", "输出文件不存在，请先生成")
            
    def open_img_output_folder(self):
        """打开图片转PDF输出文件夹"""
        output = self.img_output_var.get()
        if output:
            folder = output if os.path.isdir(output) else os.path.dirname(output)
            if os.path.exists(folder):
                os.startfile(folder)
            else:
                messagebox.showwarning("提示", "文件夹不存在")
        else:
            messagebox.showwarning("提示", "请先设置输出位置")
            
    def open_img_output_file(self):
        """打开图片转PDF输出文件（合并模式）"""
        output = self.img_output_var.get()
        if output:
            if output.lower().endswith('.pdf') and os.path.exists(output):
                os.startfile(output)
            elif os.path.isdir(output):
                # 如果是文件夹，打开文件夹
                os.startfile(output)
            else:
                messagebox.showwarning("提示", "输出文件不存在，请先转换")
        else:
            messagebox.showwarning("提示", "请先设置输出位置")
            
    def open_pdf_output_folder(self):
        """打开PDF裁剪输出文件夹"""
        output = self.pdf_output_var.get()
        if output and os.path.exists(output):
            os.startfile(output)
        else:
            messagebox.showwarning("提示", "输出文件夹不存在")
            
    # ============ 日志方法 ============
    def log_to_widget(self, widget, message):
        """线程安全的日志输出"""
        def _log():
            widget.config(state='normal')
            widget.insert(tk.END, message + "\n")
            widget.see(tk.END)
            widget.config(state='disabled')
        self.root.after(0, _log)
        
    def clear_log(self, widget):
        """清空日志"""
        widget.config(state='normal')
        widget.delete(1.0, tk.END)
        widget.config(state='disabled')

    # ============ 标签生成器功能 ============
    def run_label_generator(self):
        content = self.label_text.get("1.0", tk.END).strip()
        output_file = self.label_output_var.get()
        
        if not content:
            messagebox.showerror("错误", "请输入标签内容")
            return
        if not output_file:
            messagebox.showerror("错误", "请指定输出的PDF文件")
            return
            
        self.clear_log(self.label_log)
        
        def task():
            try:
                # 按空行分组
                groups = [g.strip() for g in content.split('\n\n') if g.strip()]
                self.log_to_widget(self.label_log, f"找到 {len(groups)} 组标签数据")
                
                self.log_to_widget(self.label_log, "开始生成PDF...")
                self.create_label_pdf(groups, output_file)
                
                self.log_to_widget(self.label_log, f"✓ PDF生成成功: {output_file}")
                self.root.after(0, lambda: messagebox.showinfo("完成", f"PDF生成成功!\n{output_file}"))
            except Exception as e:
                self.log_to_widget(self.label_log, f"✗ 错误: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
                
        threading.Thread(target=task, daemon=True).start()
        
    def create_label_pdf(self, groups, output_filename):
        """创建PDF文件"""
        base_width = 1000
        margin = 20
        
        # 设置中文字体
        font_name = 'Helvetica'
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    font_name = 'ChineseFont'
                    self.log_to_widget(self.label_log, f"加载字体: {os.path.basename(font_path)}")
                    break
                except:
                    continue
        
        # 创建临时canvas用于测量
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.close()
        temp_canvas = canvas.Canvas(temp_file.name, pagesize=(base_width, 1000))
        
        layouts = []
        for group in groups:
            lines = [line for line in group.strip().split('\n') if line.strip()]
            font_size, line_height, required_height = self.calculate_optimal_layout(
                temp_canvas, lines, font_name, base_width, margin
            )
            layouts.append({
                'lines': lines,
                'font_size': font_size,
                'line_height': line_height,
                'page_height': max(required_height, 200)
            })
        
        try:
            os.unlink(temp_file.name)
        except:
            pass
        
        c = None
        for i, layout in enumerate(layouts):
            page_size = (base_width, int(layout['page_height']))
            
            if c is None:
                c = canvas.Canvas(output_filename, pagesize=page_size)
            else:
                c.setPageSize(page_size)
                c.showPage()
            
            c.setFont(font_name, layout['font_size'])
            
            page_width, page_height = page_size
            start_y = page_height - margin - layout['font_size'] * 0.8
            start_x = margin
            
            for j, line in enumerate(layout['lines']):
                y_position = start_y - (j * layout['line_height'])
                c.drawString(start_x, y_position, line)
        
        if c:
            c.save()
            
    def calculate_optimal_layout(self, canvas_obj, lines, font_name, page_width, margin):
        """计算最优布局"""
        available_width = page_width - 2 * margin
        
        for font_size in range(80, 12, -2):
            line_height = font_size * 1.1
            
            max_width = 0
            for line in lines:
                if line.strip():
                    text_width = canvas_obj.stringWidth(line, font_name, font_size)
                    max_width = max(max_width, text_width)
            
            if max_width <= available_width * 0.95:
                total_text_height = len(lines) * line_height
                required_height = total_text_height + margin * 2 + font_size * 0.3
                return font_size, line_height, required_height
        
        font_size = 14
        line_height = font_size * 1.1
        total_text_height = len(lines) * line_height
        required_height = total_text_height + margin * 2 + font_size * 0.3
        return font_size, line_height, required_height

    # ============ 图片裁剪转PDF功能 ============
    def run_image_to_pdf(self):
        if not self.img_files:
            messagebox.showerror("错误", "请先选择图片文件")
            return
            
        output = self.img_output_var.get()
        if not output:
            messagebox.showerror("错误", "请指定输出位置")
            return
            
        mode = self.img_mode_var.get()
        self.clear_log(self.img_log)
        
        def task():
            try:
                self.log_to_widget(self.img_log, f"准备处理 {len(self.img_files)} 张图片")
                self.log_to_widget(self.img_log, f"模式: {'合并为一个PDF' if mode == 'merge' else '分别转换'}")
                
                if mode == "merge":
                    # 合并模式
                    output_file = output if output.lower().endswith('.pdf') else os.path.join(output, "merged.pdf")
                    self.images_to_single_pdf(self.img_files, output_file)
                    self.log_to_widget(self.img_log, f"✓ 合并完成: {output_file}")
                else:
                    # 分别转换模式
                    output_folder = output if os.path.isdir(output) or not output.lower().endswith('.pdf') else os.path.dirname(output)
                    os.makedirs(output_folder, exist_ok=True)
                    
                    processed = 0
                    for i, img_path in enumerate(self.img_files):
                        self.log_to_widget(self.img_log, f"处理 {i+1}/{len(self.img_files)}: {os.path.basename(img_path)}")
                        if self.image_to_pdf(img_path, output_folder):
                            processed += 1
                            
                    self.log_to_widget(self.img_log, f"✓ 完成! 成功处理 {processed}/{len(self.img_files)} 张图片")
                
                self.root.after(0, lambda: messagebox.showinfo("完成", "图片处理完成!"))
            except Exception as e:
                self.log_to_widget(self.img_log, f"✗ 错误: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
                
        threading.Thread(target=task, daemon=True).start()
        
    def crop_whitespace(self, image_path):
        """裁剪图片周围的空白区域"""
        img = Image.open(image_path)
        
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        white_threshold = 250
        
        # 找边界
        top, bottom, left, right = 0, height - 1, 0, width - 1
        
        for y in range(height):
            if any(pixels[x, y][c] < white_threshold for x in range(width) for c in range(3)):
                top = y
                break
                
        for y in range(height - 1, -1, -1):
            if any(pixels[x, y][c] < white_threshold for x in range(width) for c in range(3)):
                bottom = y
                break
                
        for x in range(width):
            if any(pixels[x, y][c] < white_threshold for y in range(height) for c in range(3)):
                left = x
                break
                
        for x in range(width - 1, -1, -1):
            if any(pixels[x, y][c] < white_threshold for y in range(height) for c in range(3)):
                right = x
                break
        
        if left < right and top < bottom:
            return img.crop((left, top, right + 1, bottom + 1))
        return img
        
    def crop_whitespace_from_img(self, img):
        """裁剪PIL Image对象的空白区域"""
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        white_threshold = 250
        
        top, bottom, left, right = 0, height - 1, 0, width - 1
        
        for y in range(height):
            if any(pixels[x, y][c] < white_threshold for x in range(width) for c in range(3)):
                top = y
                break
                
        for y in range(height - 1, -1, -1):
            if any(pixels[x, y][c] < white_threshold for x in range(width) for c in range(3)):
                bottom = y
                break
                
        for x in range(width):
            if any(pixels[x, y][c] < white_threshold for y in range(height) for c in range(3)):
                left = x
                break
                
        for x in range(width - 1, -1, -1):
            if any(pixels[x, y][c] < white_threshold for y in range(height) for c in range(3)):
                right = x
                break
        
        if left < right and top < bottom:
            return img.crop((left, top, right + 1, bottom + 1))
        return img
        
    def image_to_pdf(self, img_path, output_dir):
        """将单张图片转换为PDF"""
        temp_file_path = None
        try:
            cropped_img = self.crop_whitespace(img_path)
            
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            output_pdf = os.path.join(output_dir, f"{base_name}.pdf")
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # 保存图片到临时文件
            cropped_img.save(temp_file_path, 'PNG')
            
            # 创建PDF
            c = canvas.Canvas(output_pdf, pagesize=cropped_img.size)
            c.drawImage(temp_file_path, 0, 0, 
                      width=cropped_img.size[0], 
                      height=cropped_img.size[1])
            c.save()
            
            return True
        except Exception as e:
            self.log_to_widget(self.img_log, f"  处理失败: {e}")
            return False
        finally:
            # 确保删除临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
    def images_to_single_pdf(self, img_paths, output_pdf):
        """将多张图片合并为一个PDF"""
        c = None
        temp_files = []
        
        try:
            for i, img_path in enumerate(img_paths):
                self.log_to_widget(self.img_log, f"处理 {i+1}/{len(img_paths)}: {os.path.basename(img_path)}")
                
                try:
                    img = Image.open(img_path)
                    cropped_img = self.crop_whitespace_from_img(img)
                    
                    if c is None:
                        c = canvas.Canvas(output_pdf, pagesize=cropped_img.size)
                    else:
                        c.setPageSize(cropped_img.size)
                        c.showPage()
                    
                    # 创建临时文件
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_file_path = temp_file.name
                    temp_file.close()
                    temp_files.append(temp_file_path)
                    
                    # 保存图片到临时文件
                    cropped_img.save(temp_file_path, 'PNG')
                    c.drawImage(temp_file_path, 0, 0, 
                              width=cropped_img.size[0], 
                              height=cropped_img.size[1])
                        
                except Exception as e:
                    self.log_to_widget(self.img_log, f"  处理失败: {e}")
            
            if c:
                c.save()
        finally:
            # 清理所有临时文件
            for temp_file_path in temp_files:
                if os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass

    # ============ PDF空白裁剪功能 ============
    def run_pdf_crop(self):
        input_folder = self.pdf_input_var.get()
        output_folder = self.pdf_output_var.get()
        
        if not input_folder:
            messagebox.showerror("错误", "请选择PDF文件夹")
            return
        if not output_folder:
            messagebox.showerror("错误", "请指定输出文件夹")
            return
            
        self.clear_log(self.pdf_log)
        
        def task():
            try:
                self.log_to_widget(self.pdf_log, f"扫描文件夹: {input_folder}")
                pdf_files = self.find_pdf_files(input_folder)
                
                if not pdf_files:
                    self.log_to_widget(self.pdf_log, "未找到PDF文件")
                    return
                    
                self.log_to_widget(self.pdf_log, f"找到 {len(pdf_files)} 个PDF文件")
                
                os.makedirs(output_folder, exist_ok=True)
                processed = 0
                
                for i, pdf_path in enumerate(pdf_files):
                    rel_path = os.path.relpath(pdf_path, input_folder)
                    self.log_to_widget(self.pdf_log, f"处理 {i+1}/{len(pdf_files)}: {rel_path}")
                    
                    output_pdf_path = os.path.join(output_folder, rel_path)
                    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
                    
                    if self.crop_pdf_pages(pdf_path, output_pdf_path):
                        processed += 1
                        
                self.log_to_widget(self.pdf_log, f"✓ 完成! 成功处理 {processed}/{len(pdf_files)} 个PDF")
                self.root.after(0, lambda: messagebox.showinfo("完成", f"成功处理 {processed} 个PDF文件"))
            except Exception as e:
                self.log_to_widget(self.pdf_log, f"✗ 错误: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
                
        threading.Thread(target=task, daemon=True).start()
        
    def find_pdf_files(self, folder_path):
        """递归查找所有PDF文件"""
        pdf_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files
        
    def crop_pdf_pages(self, input_pdf_path, output_pdf_path):
        """裁剪PDF每一页的空白区域"""
        try:
            pdf_document = fitz.open(input_pdf_path)
            new_pdf = fitz.open()
            
            total_pages = len(pdf_document)
            
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img_stream = BytesIO(img_data)
                
                with Image.open(img_stream) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    pixels = img.load()
                    width, height = img.size
                    white_threshold = 240
                    
                    # 找边界
                    top, bottom, left, right = 0, height - 1, 0, width - 1
                    
                    for y in range(height):
                        if any(pixels[x, y][c] < white_threshold for x in range(width) for c in range(3)):
                            top = y
                            break
                            
                    for y in range(height - 1, -1, -1):
                        if any(pixels[x, y][c] < white_threshold for x in range(width) for c in range(3)):
                            bottom = y
                            break
                            
                    for x in range(width):
                        if any(pixels[x, y][c] < white_threshold for y in range(height) for c in range(3)):
                            left = x
                            break
                            
                    for x in range(width - 1, -1, -1):
                        if any(pixels[x, y][c] < white_threshold for y in range(height) for c in range(3)):
                            right = x
                            break
                    
                    if left < right and top < bottom:
                        cropped = img.crop((left, top, right + 1, bottom + 1))
                    else:
                        cropped = img
                    
                    if cropped.mode != 'RGB':
                        cropped = cropped.convert('RGB')
                    
                    output_stream = BytesIO()
                    cropped.save(output_stream, format='PNG', dpi=(300, 300))
                    output_stream.seek(0)
                    
                    img_rect = fitz.Rect(0, 0, cropped.width, cropped.height)
                    new_page = new_pdf.new_page(width=cropped.width, height=cropped.height)
                    new_page.insert_image(img_rect, stream=output_stream.getvalue())
            
            new_pdf.save(output_pdf_path)
            new_pdf.close()
            pdf_document.close()
            
            return True
            
        except Exception as e:
            self.log_to_widget(self.pdf_log, f"  处理失败: {e}")
            return False


def main():
    # 设置高DPI支持
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = ToolsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
