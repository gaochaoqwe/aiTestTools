"""
通用文件操作工具函数
"""
import os
import shutil

def safe_makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remove_file_if_exists(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)

def copy_file(src, dst):
    shutil.copy2(src, dst)
