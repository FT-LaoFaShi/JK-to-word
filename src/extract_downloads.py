import os
import logging
from pathlib import Path
import shutil
import re

# 配置日志同时输出到文件和终端
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('check_empty_files.log'),
        logging.StreamHandler()
    ]
)

def is_empty_content(content):
    """检查内容是否为空"""
    # 移除HTML标签
    content_no_tags = re.sub(r'<[^>]+>', '', content)
    # 移除空白字符
    content_no_spaces = content_no_tags.strip()
    # 检查是否只包含基本的HTML结构但无实际内容
    basic_html = re.match(r'^<html[^>]*>.*?</html>$', content.strip(), re.DOTALL)
    
    return (not content_no_spaces) or (basic_html and not content_no_tags.strip())

def check_and_remove_files():
    extracted_dir = Path("extracted")
    backup_dir = Path("empty_files_backup")
    
    # 确保备份目录存在
    backup_dir.mkdir(exist_ok=True)
    
    file_count = 0
    empty_count = 0
    
    # 遍历extracted目录下的所有文件
    for file_path in extracted_dir.rglob("*"):
        if file_path.is_file():
            file_count += 1
            
            # 检查文件是否为空
            is_empty = False
            
            # 检查文件大小是否为0或很小
            if file_path.stat().st_size == 0:
                is_empty = True
            else:
                # 读取文件内容检查是否为空
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if is_empty_content(content):
                            is_empty = True
                except Exception as e:
                    logging.error(f"读取文件出错 {file_path}: {e}")
                    # 尝试用其他编码读取
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            content = f.read()
                            if is_empty_content(content):
                                is_empty = True
                    except Exception as e:
                        logging.error(f"GBK编码读取也失败 {file_path}: {e}")
                        continue
            
            if is_empty:
                logging.info(f"发现空文件: {file_path}")
                # 移动到备份目录而不是直接删除
                backup_path = backup_dir / file_path.relative_to(extracted_dir)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(backup_path))
                empty_count += 1
                
    logging.info(f"检查的文件总数: {file_count}")
    logging.info(f"已移动的空文件数: {empty_count}")
    logging.info(f"空文件已移动到: {backup_dir}")

if __name__ == "__main__":
    check_and_remove_files() 