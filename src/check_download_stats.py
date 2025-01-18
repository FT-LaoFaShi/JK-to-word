def check_download_stats(log_file):
    mismatched_records = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        current_record = {}
        for line in f:
            line = line.strip()
            
            # 检查新记录的开始
            if '讲座编号:' in line:
                # 处理前一条记录
                if current_record and (current_record['total'] != current_record['downloaded']):
                    mismatched_records.append(current_record.copy())
                
                # 开始新记录
                current_record = {
                    'time': line.split(' - ')[0].strip(),
                    'lecture_id': line.split('讲座编号: ')[1].strip(),
                    'total': 0,
                    'downloaded': 0
                }
            
            elif '总文件数:' in line:
                current_record['total'] = int(line.split('总文件数: ')[1])
            elif '已下载:' in line:
                current_record['downloaded'] = int(line.split('已下载: ')[1])
    
    # 处理最后一条记录
    if current_record and (current_record['total'] != current_record['downloaded']):
        mismatched_records.append(current_record)
    
    # 将结果写入新文件
    with open('logs/mismatched_downloads.log', 'w', encoding='utf-8') as f:
        f.write("下载数量不匹配的记录：\n")
        f.write("=" * 50 + "\n")
        for record in mismatched_records:
            f.write(f"时间: {record['time']}\n")
            f.write(f"讲座编号: {record['lecture_id']}\n")
            f.write(f"总文件数: {record['total']}\n")
            f.write(f"已下载: {record['downloaded']}\n")
            f.write("=" * 50 + "\n")

if __name__ == "__main__":
    check_download_stats('logs/download_stats.log') 