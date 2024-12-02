# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
from googletrans import Translator
import platform
from concurrent.futures import ThreadPoolExecutor

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
    if file_paths:
        file_list.delete(0, tk.END)
        for file_path in file_paths:
            file_list.insert(tk.END, file_path)

def select_output_dir():
    dir_path = filedialog.askdirectory()
    if dir_path:
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, dir_path)

def generate_srt_for_file(file_path, output_dir, language):
    messagebox.showinfo("信息", f"正在生成SRT文件: {os.path.basename(file_path)}，请稍候...")
    command = [
        "whisper", file_path,
        "--model", "medium",
        "--language", language,
        "--output_format", "srt",
        "--output_dir", output_dir
    ]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("成功", f"SRT文件生成成功: {os.path.basename(file_path)}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"生成SRT文件失败: {os.path.basename(file_path)} - {e}")

def generate_srt():
    file_paths = file_list.get(0, tk.END)
    output_dir = output_dir_entry.get()
    language = language_var.get()

    if not file_paths or not output_dir:
        messagebox.showerror("错误", "请选择文件和输出目录")
        return

    if len(file_paths) > 1:
        with ThreadPoolExecutor(max_workers=4) as executor:
            for file_path in file_paths:
                executor.submit(generate_srt_for_file, file_path, output_dir, language)
    else:
        for file_path in file_paths:
            generate_srt_for_file(file_path, output_dir, language)

def translate_srt(srt_file, target_language='zh-cn'):
    translator = Translator()
    translated_lines = []

    with open(srt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        if line.strip() and not line.strip().isdigit() and '-->' not in line:
            translated = translator.translate(line, dest=target_language).text
            translated_lines.append(translated + '\n')
        else:
            translated_lines.append(line)

    translated_srt_file = srt_file.replace('.srt', f'_{target_language}.srt')
    with open(translated_srt_file, 'w', encoding='utf-8') as file:
        file.writelines(translated_lines)

    return translated_srt_file

def merge_srt_with_video_for_file(file_path, output_dir):
    srt_file = os.path.join(output_dir, os.path.basename(file_path).replace('.mp4', '.srt'))

    if not os.path.exists(srt_file):
        generate_srt_for_file(file_path, output_dir, language_var.get())
        if not os.path.exists(srt_file):
            messagebox.showerror("错误", f"SRT文件生成失败，无法合成视频: {os.path.basename(file_path)}")
            return

    translated_srt_file = translate_srt(srt_file, target_language='zh-cn')

    messagebox.showinfo("信息", f"正在合成视频: {os.path.basename(file_path)}，请稍候...")
    output_file = os.path.join(output_dir, os.path.basename(file_path).replace('.mp4', '_merged.mp4'))
    command = [
        "ffmpeg", "-i", file_path, "-vf", f"subtitles={translated_srt_file}", output_file
    ]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("成功", f"视频合成成功: {os.path.basename(file_path)}")
        open_directory(output_dir)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"视频合成失败: {os.path.basename(file_path)} - {e}")

def merge_srt_with_video():
    file_paths = file_list.get(0, tk.END)
    output_dir = output_dir_entry.get()

    if not file_paths or not output_dir:
        messagebox.showerror("错误", "请选择文件和输出目录")
        return

    if len(file_paths) > 1:
        with ThreadPoolExecutor(max_workers=4) as executor:
            for file_path in file_paths:
                executor.submit(merge_srt_with_video_for_file, file_path, output_dir)
    else:
        for file_path in file_paths:
            merge_srt_with_video_for_file(file_path, output_dir)

def open_directory(path):
    selected_os = os_var.get()
    if selected_os == "Windows":
        os.startfile(path)
    elif selected_os == "macOS":
        subprocess.run(['open', path])
    else:  # Linux
        subprocess.run(['xdg-open', path])

app = tk.Tk()
app.title("Whisper SRT生成器")

# 设置窗口大小
window_width = 500
window_height = 600  # 增加窗口高度

# 获取屏幕尺寸以计算居中的位置
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()

# 计算居中位置
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))

# 设置窗口尺寸和位置
app.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# 文件选择
file_label = tk.Label(app, text="选择MP4文件:")
file_label.pack(pady=5)
file_list = tk.Listbox(app, selectmode=tk.MULTIPLE, width=50, height=10)
file_list.pack(pady=5)
file_button = tk.Button(app, text="浏览", command=select_files)
file_button.pack(pady=5)

# 输出目录选择
output_dir_label = tk.Label(app, text="选择输出目录:")
output_dir_label.pack(pady=5)
output_dir_entry = tk.Entry(app, width=50)
output_dir_entry.pack(pady=5)
output_dir_button = tk.Button(app, text="浏览", command=select_output_dir)
output_dir_button.pack(pady=5)

# 语言选择
language_label = tk.Label(app, text="选择语言:")
language_label.pack(pady=5)
language_var = tk.StringVar(value="Korean")
language_menu = tk.OptionMenu(app, language_var, "Korean", "Chinese", "Japanese")
language_menu.pack(pady=5)

# 操作系统选择
os_label = tk.Label(app, text="选择操作系统:")
os_label.pack(pady=5)
os_var = tk.StringVar(value="macOS")
os_menu = tk.OptionMenu(app, os_var, "macOS", "Windows")
os_menu.pack(pady=5)

# 生成按钮
generate_button = tk.Button(app, text="生成SRT", command=generate_srt)
generate_button.pack(pady=10)

# 合成按钮
merge_button = tk.Button(app, text="合成视频", command=merge_srt_with_video)
merge_button.pack(pady=5)

app.mainloop()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
