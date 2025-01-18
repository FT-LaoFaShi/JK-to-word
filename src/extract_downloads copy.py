import os
import logging
from pathlib import Path
import shutil

# 配置日志同时输出到文件和终端
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('folder_file_check.log'),
        logging.StreamHandler()
    ]
)

def check_and_remove_files():
    logging.info("开始检查文件...")
    
    # 创建备份目录
    backup_dir = Path('mismatched_files_backup')
    backup_dir.mkdir(exist_ok=True)
    
    # 获取extracted目录下的所有文件夹
    extracted_dir = Path('extracted')
    if not extracted_dir.exists():
        logging.error("extracted目录不存在")
        return
        
    logging.info(f"找到extracted目录: {extracted_dir}")
    
    # 记录检查的文件夹总数
    folder_count = 0
    mismatch_count = 0
        
    for folder in sorted(extracted_dir.iterdir()):
        if not folder.is_dir():
            continue
            
        folder_count += 1
        folder_num = folder.name  # 例如 "01-001"
        folder_parts = folder_num.split('-')  # ['01', '001']
        
        # 获取文件夹中的所有.doc文件
        doc_files = list(folder.glob('*.doc'))
        if not doc_files:
            continue
            
        has_mismatch = False
        # 检查不匹配的文件
        for doc_path in doc_files:
            try:
                # 获取文件名的前两组数字
                doc_parts = doc_path.name.split('_')[0].split('-')  # 先分割掉语言标识等后缀
                if len(doc_parts) >= 2:  # 确保至少有两部分
                    if doc_parts[:2] != folder_parts:  # 比较前两组数字
                        # 格式化输出: "文件夹编号 - 文件名"
                        logging.info(f"{folder_num:>12} - {doc_path.name}")
                        
                        # 移动不匹配的文件到备份目录
                        backup_folder = backup_dir / folder_num
                        backup_folder.mkdir(exist_ok=True)
                        shutil.move(str(doc_path), str(backup_folder / doc_path.name))
                        
                        has_mismatch = True
                        mismatch_count += 1
            except Exception as e:
                logging.error(f"处理文件 {doc_path.name} 时出错: {str(e)}")
                
        # 只有当有不匹配的文件时才添加分隔符
        if has_mismatch:
            logging.info("=" * 50)
    
    # 输出统计信息
    logging.info(f"\n检查完成:")
    logging.info(f"检查的文件夹总数: {folder_count}")
    logging.info(f"已移动的不匹配文件数: {mismatch_count}")
    logging.info(f"不匹配的文件已移动到: {backup_dir}")

if __name__ == "__main__":
    check_and_remove_files() 