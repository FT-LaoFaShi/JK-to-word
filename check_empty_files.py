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
    """检查并移动空文件和空文件夹"""
    extracted_dir = Path("extracted")
    if not extracted_dir.exists():
        logging.error("extracted目录不存在")
        return
        
    backup_dir = Path("empty_files_backup")
    backup_dir.mkdir(exist_ok=True)
    
    empty_file_count = 0
    empty_dir_count = 0
    file_count = 0
    dir_count = 0
    
    # 先检查文件
    for file_path in extracted_dir.rglob("*"):
        if file_path.is_file():
            file_count += 1
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
                    # 尝试用其他编码读取
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            content = f.read()
                            if is_empty_content(content):
                                is_empty = True
                    except Exception as e2:
                        logging.error(f"无法读取文件 {file_path}: {e2}")
                        continue
            
            if is_empty:
                logging.info(f"发现空文件: {file_path}")
                # 移动到备份目录
                backup_path = backup_dir / file_path.relative_to(extracted_dir)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(backup_path))
                empty_file_count += 1
    
    # 然后检查空文件夹(从最深层开始)
    for dirpath, dirnames, filenames in os.walk(str(extracted_dir), topdown=False):
        dir_path = Path(dirpath)
        dir_count += 1
        
        # 检查文件夹是否为空
        if not any(dir_path.iterdir()):
            logging.info(f"发现空文件夹: {dir_path}")
            # 移动空文件夹到备份目录
            backup_path = backup_dir / dir_path.relative_to(extracted_dir)
            try:
                if dir_path != extracted_dir:  # 不移动根目录
                    shutil.move(str(dir_path), str(backup_path))
                    empty_dir_count += 1
            except Exception as e:
                logging.error(f"移动文件夹失败 {dir_path}: {e}")
                
    # 输出统计信息
    logging.info(f"\n检查完成:")
    logging.info(f"检查的文件总数: {file_count}")
    logging.info(f"检查的文件夹总数: {dir_count}")
    logging.info(f"发现的空文件数: {empty_file_count}")
    logging.info(f"发现的空文件夹数: {empty_dir_count}")
    logging.info(f"空文件和文件夹已移动到: {backup_dir}")

if __name__ == "__main__":
    check_and_remove_files()