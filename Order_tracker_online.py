import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime, timedelta

def configure_driver_logging():
    """配置WebDriver日志级别"""
    log = logging.getLogger("selenium.webdriver.remote.remote_connection")
    log.setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)

def close_popup_if_exists(driver):
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
    except Exception as e:
        print("没有弹窗需要关闭或关闭失败")
        driver.switch_to.default_content()

def process_single_query(row):
    """处理单条查询逻辑"""
    driver = None  # 初始化 driver 变量
    result = {"物流状态": "查询失败", "物流单号": "N/A", "订单金额": "N/A", "订单地址": "N/A"}
    
    try:
        # 临时保存并清除所有代理环境变量
        original_proxies = {
            'http_proxy': os.environ.pop('http_proxy', None),
            'https_proxy': os.environ.pop('https_proxy', None),
            'HTTP_PROXY': os.environ.pop('HTTP_PROXY', None),
            'HTTPS_PROXY': os.environ.pop('HTTPS_PROXY', None),
            'no_proxy': os.environ.pop('no_proxy', None),
            'NO_PROXY': os.environ.pop('NO_PROXY', None)
        }
        
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
        chrome_options.add_argument('--log-level=3')  # 只显示致命错误
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
        
        # 使用相对路径获取 ChromeDriver 路径
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        driver_path = os.path.join(current_dir, 'driver', 'chromedriver-win64', 'chromedriver.exe')
        
        print(f"当前目录: {current_dir}")
        print(f"Chrome驱动路径: {driver_path}")
        
        # 检查驱动文件是否存在
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

        url = "https://www.coachoutlet.com/track-order"

        try:
            driver.get(url)
            print(f"页面加载成功: {driver.title}")

            order_input = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "trackorder-form-number"))
            )
            order_input.clear()
            order_input.send_keys(row['单号'])
            print("订单号已输入")
            close_popup_if_exists(driver)

            email_input = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "trackorder-form-email"))
            )
            email_input.clear()
            email_input.send_keys(row['邮箱'])
            print("邮箱已输入")
            close_popup_if_exists(driver)

            zip_input = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "trackorder-form-zipcode"))
            )
            zip_input.clear()
            zip_input.send_keys(row['邮编'])
            print("邮编已输入")
            close_popup_if_exists(driver)

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

            total_price_div = driver.find_elements(By.CLASS_NAME, "order-total-price")
            if total_price_div:
                order_amount = total_price_div[0].text
                result["订单金额"] = order_amount
                print(f"订单金额已获取: {order_amount}")

            address_summary_div = driver.find_elements(By.CLASS_NAME, "address-summary")
            if address_summary_div:
                address_elements = address_summary_div[0].find_elements(By.TAG_NAME, "div")
                address_text = " ".join([element.text for element in address_elements if element.text.strip()])
                result["订单地址"] = address_text
                print(f"订单地址已获取: {address_text}")

            tracking_number_div = driver.find_elements(By.CLASS_NAME, "tracking-number")
            if tracking_number_div:
                result["物流状态"] = "查询成功-已发货"
                try:
                    tracking_number = tracking_number_div[0].find_element(By.TAG_NAME, "a").text
                    result["物流单号"] = tracking_number
                    print(f"物流单号已获取: {tracking_number}")
                    return result
                except Exception as e:
                    result["物流单号"] = "获取失败"
                    print(f"获取物流单号失败: {e}")
            else:
                result["物流状态"] = "查询成功-未发货"
                return result

        except Exception as e:
            result["物流状态"] = "查询失败"
            print(f"查询失败: {e}")
        finally:
            try:
                driver.quit()
            except:
                pass

    except Exception as e:
        result["物流状态"] = "查询失败"
        print(f"查询失败: {e}")
    finally:
        # 恢复代理环境变量
        for key, value in original_proxies.items():
            if value is not None:
                os.environ[key] = value
        # 安全地关闭driver
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")

    return result

def query_tracking_info(output_file):
    print(f"output_file: {output_file}")
    
    # 如果文件不存在，才创建新文件
    if not os.path.exists(output_file):
        # 创建一个空的DataFrame，包含所需的列
        empty_df = pd.DataFrame(columns=[
            '单号', '邮箱', '邮编', '物流状态', '物流单号', 
            '订单金额', '订单地址', '最近一次查询'
        ])
        try:
            # 尝试使用 utf-8 保存
            empty_df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"创建新文件: {output_file}")
        except Exception as e:
            print(f"创建文件失败: {e}")
            return
    
    # 读取现有文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'ansi']
    input_data = None
    
    for encoding in encodings:
        try:
            input_data = pd.read_csv(output_file, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取文件，共 {len(input_data)} 条记录")
            break
        except Exception as e:
            print(f"使用 {encoding} 编码读取失败: {e}")
            continue
    
    if input_data is None:
        print("所有编码方式都无法读取文件，请检查文件格式")
        return

    # 检查必要的列是否存在
    required_columns = ['单号', '邮箱', '邮编', '物流状态', '物流单号', '订单金额', '订单地址', '最近一次查询']
    missing_columns = [col for col in required_columns if col not in input_data.columns]
    if missing_columns:
        print(f"文件缺少必要的列: {missing_columns}")
        return

    current_time = datetime.now()
    
    # 添加统计变量
    successful_queries = 0
    failed_queries = 0
    total_time = 0
    query_times = []
    program_start_time = time.time()
    updated_records = 0

    # 筛选需要查询的订单
    orders_to_query = input_data[
        (input_data['物流状态'] != '查询成功-已发货') | 
        (pd.isna(input_data['物流状态']))
    ]

    total_records = len(input_data)
    shipped_records = input_data[input_data['物流状态'] == '查询成功-已发货'].shape[0]
    to_query_records = len(orders_to_query)

    print(f"\n统计信息:")
    print(f"总记录数: {total_records}")
    print(f"已发货记录数: {shipped_records}")
    print(f"待查询记录数: {to_query_records}\n")

    if to_query_records == 0:
        print("没有需要查询的订单")
        return

    # 只遍历需要查询的订单
    for index, row in orders_to_query.iterrows():
        max_retries = 3
        current_retry = 0
        query_success = False

        while current_retry < max_retries and not query_success:
            if current_retry > 0:
                print(f"\n第 {current_retry + 1} 次重试查询订单: {row['单号']}")
            else:
                print(f"\n开始查询订单: {row['单号']}")

            start_time = time.time()
            result = process_single_query(row)
            query_time = time.time() - start_time
            
            if result["物流状态"] != "查询失败":
                query_success = True
                query_times.append(query_time)
                total_time += query_time
                print(f"本次查询耗时: {query_time:.2f} 秒")

                # 更新逻辑
                needs_update = False
                update_message = []

                # 更新物流状态和单号
                if result["物流状态"] != row.get('物流状态', ''):
                    needs_update = True
                    update_message.append(f"物流状态从 {row.get('物流状态', 'N/A')} 更新为 {result['物流状态']}")
                    input_data.loc[index, "物流状态"] = result["物流状态"]
                    if result["物流单号"] != "N/A":
                        input_data.loc[index, "物流单号"] = result["物流单号"]

                # 更新订单金额
                if result["订单金额"] != "N/A":
                    if pd.isna(row.get('订单金额')) or result["订单金额"] != row.get('订单金额'):
                        needs_update = True
                        update_message.append(f"订单金额从 {row.get('订单金额', 'N/A')} 更新为 {result['订单金额']}")
                        input_data.loc[index, "订单金额"] = result["订单金额"]

                # 更新订单地址
                if result["订单地址"] != "N/A":
                    if pd.isna(row.get('订单地址')) or result["订单地址"] != row.get('订单地址'):
                        needs_update = True
                        update_message.append(f"订单地址从 {row.get('订单地址', 'N/A')} 更新为 {result['订单地址']}")
                        input_data.loc[index, "订单地址"] = result["订单地址"]

                # 更新最近一次查询时间
                input_data.loc[index, "最近一次查询"] = current_time.strftime('%Y-%m-%d %H:%M:%S')

                if needs_update:
                    updated_records += 1
                    print(f"订单 {row['单号']} 更新: {', '.join(update_message)}")
                    try:
                        # 使用成功读取时的编码保存
                        input_data.to_csv(output_file, index=False, encoding=encoding)
                        print("文件已更新")
                    except Exception as e:
                        print(f"保存文件失败: {e}")

                successful_queries += 1
            else:
                current_retry += 1
                if current_retry < max_retries:
                    print(f"查询失败，将进行第 {current_retry + 1} 次重试")
                    time.sleep(1)  # 重试前稍微等待
                else:
                    print(f"订单 {row['单号']} 已达到最大重试次数，仍然失败")
                    failed_queries += 1
                    # 更新最近一次查询时间
                    input_data.loc[index, "最近一次查询"] = current_time.strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        input_data.to_csv(output_file, index=False, encoding=encoding)
                    except Exception as e:
                        print(f"最终保存文件失败: {e}")

    # 最后保存文件时也使用相同的编码
    try:
        input_data.to_csv(output_file, index=False, encoding=encoding)
    except Exception as e:
        print(f"最终保存文件失败: {e}")
    
    # 计算程序总耗时
    program_total_time = time.time() - program_start_time
    
    # 计算统计信息
    if query_times:
        avg_time = total_time / len(query_times)
        min_time = min(query_times)
        max_time = max(query_times)
    else:
        avg_time = min_time = max_time = 0
    
    # 输出详细统计信息
    print("\n========== 查询任务统计 ==========")
    print(f"查询完成！成功: {successful_queries}, 失败: {failed_queries}")
    print(f"更新记录数: {updated_records}")
    print(f"程序总耗时: {program_total_time:.2f} 秒")
    print(f"查询总耗时: {total_time:.2f} 秒")
    print(f"平均查询耗时: {avg_time:.2f} 秒")
    print(f"最短查询耗时: {min_time:.2f} 秒")
    print(f"最长查询耗时: {max_time:.2f} 秒")
    print("==================================")
    print(f"结果已保存到 {output_file}")

# 主程序入口
if __name__ == "__main__":
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建输出文件的完整路径，改为 .csv 后缀
    output_file = os.path.join(script_dir, "output_with_tracking.csv")
    
    print(f"脚本目录: {script_dir}")
    
    query_tracking_info(output_file)
