import os
import time
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class AmtbCrawler:
    def __init__(self):
        self.base_url = "https://ft.amtb.tw/"
        self.download_dir = Path("downloads")
        self.log_dir = Path("logs")
        self.stats_file = self.log_dir / "download_stats.log"
        self.progress_file = self.log_dir / "download_progress.json"
        self.setup_dirs()
        self.setup_logging()
        self.setup_driver()
        self.load_progress()

    def setup_dirs(self):
        """创建必要的目录结构"""
        self.download_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

    def setup_logging(self):
        """设置日志"""
        self.log_count = 0
        self.log_file_max_lines = 1000
        self.current_log_file = None
        self.create_new_log_file()

    def create_new_log_file(self):
        """创建新的日志文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"crawler_{timestamp}.log"
        
        if self.current_log_file:
            logging.getLogger().handlers = []
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.current_log_file = log_file
        self.log_count = 0

    def setup_driver(self):
        """设置Chrome浏览器"""
        try:
            print("正在配置 Chrome 选项...")
            options = webdriver.ChromeOptions()
            
            # 下载设置
            prefs = {
                "download.default_directory": "",
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "safebrowsing.disable_download_protection": True
            }
            options.add_experimental_option("prefs", prefs)
            
            # 添加其他必要的选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用日志
            
            print("正在初始化 ChromeDriver...")
            driver_path = Path(__file__).parent / "chromedriver.exe"
            if not driver_path.exists():
                print(f"错误：找不到本地 ChromeDriver: {driver_path}")
                print("请手动下载 ChromeDriver 并放置在 src 目录下")
                print("下载地址：https://googlechromelabs.github.io/chrome-for-testing/")
                raise Exception("找不到 ChromeDriver")
            
            service = Service(str(driver_path))
            
            print("正在启动 Chrome 浏览器...")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            print("Chrome 浏览器启动成功")
            
        except Exception as e:
            print(f"设置浏览器失败: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            raise

    def write_stats(self, lecture_no, total_count, downloaded_count, success_count, failed_count):
        """写入下载统计信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats = (
            f"{timestamp} - 讲座编号: {lecture_no}\n"
            f"  总文件数: {total_count}\n"
            f"  已下载: {downloaded_count}\n"
            f"  成功: {success_count}\n"
            f"  失败: {failed_count}\n"
            f"{'='*50}\n"
        )
        with open(self.stats_file, 'a', encoding='utf-8') as f:
            f.write(stats)

    def load_progress(self):
        """加载下载进度"""
        import json
        self.progress = {}
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
            except Exception as e:
                logging.error(f"加载进度文件失败: {str(e)}")

    def save_progress(self, lecture_no, status="completed", current_page=None):
        """保存下载进度"""
        import json
        try:
            self.progress[lecture_no] = {
                "status": status,
                "current_page": current_page,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存进度失败: {str(e)}")

    def process_lecture(self, lecture_no):
        """处理单个讲座编号"""
        if lecture_no in self.progress and self.progress[lecture_no]["status"] == "completed":
            logging.info(f"讲座 {lecture_no} 已下载完成，跳过")
            return

        resume_page = 0
        if lecture_no in self.progress and self.progress[lecture_no]["current_page"]:
            resume_page = self.progress[lecture_no]["current_page"]
            logging.info(f"检测到断点：第 {resume_page + 1} 页")

        total_count = 0
        downloaded_count = 0
        success_count = 0
        failed_count = 0
        
        try:
            # 创建讲座专属目录
            lecture_dir = self.download_dir / lecture_no
            lecture_dir.mkdir(exist_ok=True)
            
            # 使用绝对路径字符串，确保反斜杠正确
            download_path = str(lecture_dir.absolute()).replace('/', '\\')
            
            # 更新下载目录
            self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
            params = {
                'cmd': 'Page.setDownloadBehavior',
                'params': {
                    'behavior': 'allow',
                    'downloadPath': download_path
                }
            }
            self.driver.execute("send_command", params)
            
            logging.info(f"开始处理讲座编号: {lecture_no}")
            print(f"\n{'='*50}")
            print(f"开始处理讲座编号: {lecture_no}")
            print(f"{'='*50}")
            
            # 访问网页
            print("正在访问网页...")
            retry_count = 3
            for _ in range(retry_count):
                try:
                    self.driver.get(self.base_url)
                    # 增加页面加载等待时间
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "select#srange[name='srange']"))
                    )
                    break
                except TimeoutException:
                    print("页面加载超时，正在重试...")
                    time.sleep(3)
            else:
                raise Exception("页面加载失败")
            
            # 设置搜索选项
            print("正在设置搜索选项...")
            select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select#srange[name='srange']"))
            )
            select.click()
            option = select.find_element(By.CSS_SELECTOR, "option[value='sn']")
            option.click()
            time.sleep(1)
            
            # 输入讲座编号
            print(f"正在搜索讲座: {lecture_no}")
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#query[name='query']"))
            )
            search_input.clear()
            search_input.send_keys(lecture_no)
            time.sleep(1)
            
            # 选择繁体
            traditional_radio = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#lang_tw[type='radio'][value='zh_TW']"))
            )
            if not traditional_radio.is_selected():
                traditional_radio.click()
            time.sleep(1)
            
            # 执行搜索
            print("正在执行搜索...")
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#searchButton[type='button']"))
            )
            self.driver.execute_script("arguments[0].click();", search_button)
            time.sleep(3)
            
            # 获取结果数量
            result_text = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span#ctl00_CH_C_Label_ServerCostTime[style*='color:#C00000']"))
            ).text
            
            match = re.search(r'(\d+)\s*筆資料', result_text)
            if not match:
                print("未找到任何结果")
                # 记录统计
                self.write_stats(
                    lecture_no=lecture_no,
                    total_count=0,
                    downloaded_count=0,
                    success_count=0,
                    failed_count=0
                )
                self.save_progress(lecture_no, "completed")  # 标记为完成，避免重复处理
                return
            
            total_count = int(match.group(1))
            print(f"找到 {total_count} 个文件")
            
            if total_count == 0:
                print("没有可下载的文件")
                # 记录统计
                self.write_stats(
                    lecture_no=lecture_no,
                    total_count=0,
                    downloaded_count=0,
                    success_count=0,
                    failed_count=0
                )
                self.save_progress(lecture_no, "completed")  # 标记为完成，避免重复处理
                return
            
            # 设置每页显示数量为总文件数
            print(f"设置每页显示 {total_count} 个文件...")
            limit_select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select#limit[name='limit']"))
            )
            # 找到最接近但不小于 total_count 的选项
            options = [int(opt.get_attribute('value')) for opt in limit_select.find_elements(By.TAG_NAME, "option")]
            selected_limit = min([opt for opt in options if opt >= total_count], default=max(options))
            
            # 选择合适的显示数量
            for option in limit_select.find_elements(By.TAG_NAME, "option"):
                if int(option.get_attribute('value')) == selected_limit:
                    option.click()
                    break
            time.sleep(2)  # 等待页面刷新
            
            # 点击全选
            select_all = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#selectall[name='selectall']"))
            )
            if not select_all.is_selected():
                select_all.click()
            time.sleep(1)
            
            # 处理文件类型
            print("设置文件类型...")
            file_type_checkboxes = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "input[name='docstype[]']"
            )
            # 取消全选
            for checkbox in file_type_checkboxes:
                if checkbox.is_selected():
                    checkbox.click()
                    time.sleep(0.5)
            
            # 只选择 DOC
            doc_checkbox = self.driver.find_element(
                By.CSS_SELECTOR, 
                "input[name='docstype[]'][value='doc']"
            )
            if not doc_checkbox.is_selected():
                doc_checkbox.click()
            time.sleep(1)
            
            # 下载文件
            print(f"正在下载 {total_count} 个文件...")
            try:
                download_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input#zipdownloadbutton"))
                )
                download_button.click()
                
                # 等待下载开始和完成
                max_wait_time = 120  # 最长等待2分钟
                check_interval = 2  # 每2秒检查一次
                
                print("等待下载开始...")
                time.sleep(2)  # 先等待2秒确保下载开始
                
                # 检查下载目录中的文件
                def get_zip_files():
                    return list(lecture_dir.glob("*.zip"))
                
                def is_downloading():
                    for file in lecture_dir.glob("*"):
                        if file.suffix in ['.crdownload', '.tmp', '.download']:
                            return True
                    return False
                
                start_time = time.time()
                initial_zip_count = len(get_zip_files())
                
                while True:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    if elapsed_time > max_wait_time:
                        print(f"等待超时（{max_wait_time}秒），继续下一个讲座")
                        break
                    
                    # 检查是否有新的zip文件
                    current_zip_count = len(get_zip_files())
                    if current_zip_count > initial_zip_count:
                        print("检测到新的zip文件，下载完成")
                        break
                    
                    # 检查是否正在下载
                    if not is_downloading() and elapsed_time > 5:  # 改为至少等待5秒
                        print("没有检测到下载中的文件，可能已完成")
                        break
                    
                    # 打印等待时间
                    print(f"已等待 {int(elapsed_time)} 秒...")
                    time.sleep(check_interval)
                
                success_count = total_count
                downloaded_count = total_count
                
                # 标记为完成
                self.save_progress(lecture_no, "completed")
                print(f"讲座 {lecture_no} 下载完成")
                
            except Exception as e:
                print(f"下载出错: {str(e)}")
                failed_count = total_count
                self.save_progress(lecture_no, "error", 0)
                raise
            
            # 记录统计
            self.write_stats(
                lecture_no=lecture_no,
                total_count=total_count,
                downloaded_count=downloaded_count,
                success_count=success_count,
                failed_count=failed_count
            )
            
        except Exception as e:
            print(f"\n处理讲座 {lecture_no} 时出错: {str(e)}")
            logging.error(f"处理讲座 {lecture_no} 时出错: {str(e)}")
            # 记录统计
            self.write_stats(
                lecture_no=lecture_no,
                total_count=total_count,
                downloaded_count=downloaded_count,
                success_count=success_count,
                failed_count=failed_count
            )
            self.save_progress(lecture_no, "error", 0)  # 保存错误状态
            raise
            
    def close(self):
        """关闭浏览器"""
        self.driver.quit() 