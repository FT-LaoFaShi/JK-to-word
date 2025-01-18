import os
import logging
from pathlib import Path

def check_folder_file_numbers():
    # 配置日志
    logging.basicConfig(
        filename='folder_file_check.log',
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )
    
    # 获取extracted目录下的所有文件夹
    extracted_dir = Path('extracted')
    if not extracted_dir.exists():
        logging.error("extracted目录不存在")
        return
        
    folders = [f for f in extracted_dir.iterdir() if f.is_dir()]
    
    for folder in folders:
        folder_name = folder.name
        # 获取文件夹编号 (例如 01-001 中的 001)
        try:
            folder_num = folder_name.split('-')[1]
        except IndexError:
            logging.error(f"文件夹名称格式错误: {folder_name}")
            continue
            
        # 获取该文件夹下的所有.doc文件
        files = list(folder.glob('*.doc'))
        
        # 检查每个文件的编号是否与文件夹匹配
        matched_files = []
        unmatched_files = []
        
        for file in files:
            file_name = file.name
            try:
                # 获取文件编号 (例如 01-001-0001_zh_TW.doc 中的 001)
                file_num = file_name.split('-')[1]
                if file_num == folder_num:
                    matched_files.append(file_name)
                else:
                    unmatched_files.append(file_name)
            except IndexError:
                logging.error(f"文件名称格式错误: {file_name}")
                continue
        
        # 记录结果
        logging.info(f"\n文件夹: {folder_name}")
        logging.info(f"文件总数: {len(files)}")
        logging.info(f"匹配的文件数: {len(matched_files)}")
        if matched_files:
            logging.info("匹配的文件:")
            for f in matched_files:
                logging.info(f"  - {f}")
                
        if unmatched_files:
            logging.info("不匹配的文件:")
            for f in unmatched_files:
                logging.info(f"  - {f}")
        
        logging.info("-" * 50)

if __name__ == "__main__":
    check_folder_file_numbers()