import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configure_chrome_driver():
    """配置Chrome驱动"""
    chrome_options = Options()
    
    # 基本配置
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--headless=new')
    
    # 禁用不必要的功能和日志
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-in-process-stack-traces')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    
    # 反自动化检测配置
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # 浏览器标头配置
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    
    # 添加请求头
    chrome_options.add_argument('--accept-language=zh,zh-CN;q=0.9')
    chrome_options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
    chrome_options.add_argument('--accept-encoding=gzip, deflate, br, zstd')
    
    # 使用相对路径获取ChromeDriver路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, '..', 'driver', 'chromedriver-win64', 'chromedriver.exe')
    
    if not os.path.exists(driver_path):
        raise FileNotFoundError(f"找不到Chrome驱动文件: {driver_path}")
        
    service = ChromeService(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 设置页面加载超时
    driver.set_page_load_timeout(30)
    
    # 执行 JavaScript 来修改 webdriver 标记
    stealth_js = '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        window.chrome = {
            runtime: {}
        };
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
    '''
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': stealth_js
    })
    
    return driver

def close_popup_if_exists(driver):
    """关闭弹窗"""
    try:
        iframe = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "attentive_creative"))
        )
        driver.switch_to.frame(iframe)
        
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.ID, "closeIconSvg"))
        )
        close_button = driver.find_element(By.ID, "closeIconSvg")
        close_button.click()
        print("弹窗关闭")
        driver.switch_to.default_content()
        time.sleep(0.5)
    except:
        print("没有弹窗需要关闭或关闭失败")
        driver.switch_to.default_content()

def query_single_order(driver, order_info):
    """查询单个订单"""
    result = {"物流状态": "查询失败", "物流单号": "N/A", "订单金额": "N/A", "订单地址": "N/A"}
    
    try:
        driver.get("https://www.coachoutlet.com/track-order")
        print(f"页面加载成功: {driver.title}")

        # 输入订单号
        order_input = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "trackorder-form-number"))
        )
        order_input.clear()
        order_input.send_keys(order_info['单号'])
        print("订单号已输入")
        close_popup_if_exists(driver)

        # 输入邮箱
        email_input = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "trackorder-form-email"))
        )
        email_input.clear()
        email_input.send_keys(order_info['邮箱'])
        print("邮箱已输入")
        close_popup_if_exists(driver)

        # 输入邮编
        zip_input = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "trackorder-form-zipcode"))
        )
        zip_input.clear()
        zip_input.send_keys(order_info['邮编'])
        print("邮编已输入")
        close_popup_if_exists(driver)

        # 提交表单
        submit_button = driver.find_element(
            By.CSS_SELECTOR, ".btn.btn-block.btn-primary.track-order-button"
        )
        submit_button.click()
        print("表单已提交")

        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CLASS_NAME, "order-total-price"))
            )
        except:
            try:
                error_message = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
                )
                print(f"查询出错: {error_message.text}")
                return result
            except:
                print("查询超时")
                return result

        driver.implicitly_wait(2)

        # 获取订单金额
        total_price_div = driver.find_elements(By.CLASS_NAME, "order-total-price")
        if total_price_div:
            order_amount = total_price_div[0].text
            result["订单金额"] = order_amount
            print(f"订单金额已获取: {order_amount}")

        # 获取订单地址
        address_summary_div = driver.find_elements(By.CLASS_NAME, "address-summary")
        if address_summary_div:
            address_elements = address_summary_div[0].find_elements(By.TAG_NAME, "div")
            address_text = " ".join([element.text for element in address_elements if element.text.strip()])
            result["订单地址"] = address_text
            print(f"订单地址已获取: {address_text}")

        # 获取物流信息
        tracking_number_div = driver.find_elements(By.CLASS_NAME, "tracking-number")
        if tracking_number_div:
            result["物流状态"] = "查询成功-已发货"
            try:
                tracking_number = tracking_number_div[0].find_element(By.TAG_NAME, "a").text
                result["物流单号"] = tracking_number
                print(f"物流单号已获取: {tracking_number}")
            except Exception as e:
                result["物流单号"] = "获取失败"
                print(f"获取物流单号失败: {e}")
        else:
            result["物流状态"] = "查询成功-未发货"

    except Exception as e:
        print(f"查询订单 {order_info['单号']} 时出错: {str(e)}")
        
    return result

def validate_data(df):
    """验证数据完整性"""
    error_messages = []
    
    # 检查每一行数据
    for index, row in df.iterrows():
        row_number = index + 1  # 实际行号（从1开始）
        
        # 检查邮箱
        if pd.isna(row['邮箱']) or str(row['邮箱']).strip() == '':
            error_messages.append(f"第{row_number}行: 邮箱未填写")
            
        # 检查单号
        if pd.isna(row['单号']) or str(row['单号']).strip() == '':
            error_messages.append(f"第{row_number}行: 单号未填写")
            
        # 检查邮编
        if pd.isna(row['邮编']) or str(row['邮编']).strip() == '':
            error_messages.append(f"第{row_number}行: 邮编未填写")
    
    if error_messages:
        error_text = "\\n".join(error_messages)
        raise ValueError(f"数据验证失败：\\n{error_text}\\n请按照要求填写后重新上传。")

def process_orders_file(file_path, progress_callback):
    """处理订单文件"""
    try:
        # 尝试不同的编码格式读取CSV文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'ansi']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"成功使用 {encoding} 编码读取文件")
                break
            except UnicodeDecodeError:
                continue
                
        if df is None:
            raise ValueError("无法读取文件，请确保文件编码为 UTF-8、GBK 或 GB2312")
        
        # 验证必要的列
        required_columns = ['单号', '邮箱', '邮编']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"文件格式错误：缺少必要的列（{', '.join(missing_columns)}）")
        
        # 验证数据完整性
        validate_data(df)
            
        # 添加结果列
        for col in ['物流状态', '物流单号', '订单金额', '订单地址', '最近一次查询']:
            if col not in df.columns:
                df[col] = None
                
        # 初始化浏览器
        driver = configure_chrome_driver()
        
        try:
            # 处理每个订单
            total_orders = len(df)
            successful = 0
            failed = 0
            start_time = time.time()
            processed_times = []  # 用于计算平均处理时间
            
            # 初始化进度信息
            progress_callback({
                'is_processing': True,
                'current': 0,
                'total': total_orders,
                'successful': 0,
                'failed': 0,
                'avg_time': 0,
                'estimated_remaining_time': 0,
                'percentage': 0
            })
            
            for index, row in df.iterrows():
                record_start_time = time.time()
                max_retries = 3
                current_retry = 0
                query_success = False
                
                while current_retry < max_retries and not query_success:
                    if current_retry > 0:
                        print(f"\n第 {current_retry + 1} 次重试查询订单: {row['单号']}")
                        time.sleep(2)  # 重试前等待
                    else:
                        print(f"\n开始查询订单: {row['单号']}")
                        
                    try:
                        result = query_single_order(driver, row)
                        
                        if result["物流状态"] != "查询失败":
                            query_success = True
                            # 更新结果
                            for key, value in result.items():
                                df.loc[index, key] = value
                            df.loc[index, '最近一次查询'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            successful += 1
                            
                            # 记录处理时间
                            record_time = time.time() - record_start_time
                            processed_times.append(record_time)
                            
                            # 计算预估剩余时间和更新进度
                            avg_time = sum(processed_times) / len(processed_times)
                            remaining_records = total_orders - (index + 1)
                            estimated_remaining_time = avg_time * remaining_records
                            percentage = ((index + 1) / total_orders) * 100
                            
                            # 更新进度信息
                            progress_callback({
                                'is_processing': True,
                                'current': index + 1,
                                'total': total_orders,
                                'successful': successful,
                                'failed': failed,
                                'avg_time': avg_time,
                                'estimated_remaining_time': estimated_remaining_time,
                                'percentage': percentage
                            })
                            
                            break
                        else:
                            current_retry += 1
                            
                    except Exception as e:
                        print(f"处理订单出错: {str(e)}")
                        current_retry += 1
                        
                if not query_success:
                    failed += 1
                    print(f"订单 {row['单号']} 查询失败")
                    
                    # 更新失败状态
                    progress_callback({
                        'is_processing': True,
                        'current': index + 1,
                        'total': total_orders,
                        'successful': successful,
                        'failed': failed,
                        'avg_time': sum(processed_times) / max(len(processed_times), 1),
                        'estimated_remaining_time': avg_time * remaining_records if processed_times else 0,
                        'percentage': ((index + 1) / total_orders) * 100
                    })
                    
            # 计算统计信息
            total_time = time.time() - start_time
            stats = {
                'total_orders': total_orders,
                'successful': successful,
                'failed': failed,
                'total_time': total_time,
                'avg_time': total_time / total_orders if total_orders > 0 else 0
            }
            
            # 保存结果
            output_filename = f'result_{int(time.time())}.csv'
            output_path = os.path.join(os.path.dirname(file_path), output_filename)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            # 更新最终状态
            progress_callback({
                'is_processing': False,
                'current': total_orders,
                'total': total_orders,
                'successful': successful,
                'failed': failed,
                'avg_time': stats['avg_time'],
                'estimated_remaining_time': 0,
                'percentage': 100
            })
            
            return output_filename, stats
            
        finally:
            driver.quit()
            
    except Exception as e:
        raise Exception(f"处理文件时出错: {str(e)}") 