from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time
import requests
import json
from urllib.parse import urlparse

class SendContact:
    def __init__(self):
        self.logger = self.setup_logger()
        self.service = ChromeService(executable_path=ChromeDriverManager().install())
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--ignore-ssl-errors")
        self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.options)

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def wait_and_fill_input(self, by, value, data):
        try:
            input_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((by, value))
            )
            input_field.clear()
            input_field.send_keys(data)
        except Exception as e:
            self.logger.error(f"An error occurred while waiting for the element: {e}")
            return 'error'

    def wait_and_fill_textarea(self, form, data):
        try:
            textarea_element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
            )
            textarea_element.clear()
            textarea_element.send_keys(data)
        except Exception as e:
            self.logger.error(f"An error occurred while waiting for and filling the textarea element: {e}")
            return 'error'

    def select_option_in_form(self, form, prefecture):
        try:
            select_elements = form.find_all('select')

            for select_element in select_elements:
                options = select_element.find_all('option')

                found_prefecture = any('県' in option.text for option in options)

                if found_prefecture:
                    Select(self.driver.find_element(By.NAME, select_element['name'])).select_by_visible_text(prefecture)
                else:
                    Select(self.driver.find_element(By.NAME, select_element['name'])).select_by_index(len(options) - 1)

        except Exception as e:
            self.logger.error(f"An error occurred while selecting options in form: {e}")

    def select_check_radio_in_form(self, form):
        try:
            elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input[type="checkbox"], input[type="radio"]'))
            )

            for element in elements:
                element.click()
        except Exception as e:
            self.logger.error(f"An error occurred while selecting options in form: {e}")
            return 'error'
        
    def is_submission_successful(self):
        page_html_after_submit = self.driver.page_source
        soup_after_submit = BeautifulSoup(page_html_after_submit, 'html.parser')
        success_message = soup_after_submit.find(string="送信されました") or soup_after_submit.find(string="成功しました") or soup_after_submit.find(string="successful") or soup_after_submit.find(string="contacting us") or soup_after_submit.find(string="お問い合わせありがとうございました") or soup_after_submit.find(string="メッセージは送信されました") or soup_after_submit.find(string="has been sent") or soup_after_submit.find(string="お問い合わせをいただきまして誠にありがとうございました") or soup_after_submit.find(string="ありがとうございました")
        if success_message:
            return True
        return False

    
    def click_submit_button(self, form, check_name, check_type, url):
        send_result = 'failure'
        submit_button_xpath = "//button[@type='submit'] | //input[@type='submit']"

        try:
            wait = WebDriverWait(self.driver, 20)
            submit_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
            )
            time.sleep(20)
            submit_button.click()
            time.sleep(5)
        
            if self.is_submission_successful():
                return 'success'
            else:
                return 'failure'

        except Exception as e:
            self.logger.error(f"Error clicking the submit button: {e}")

        return send_result
    
    def click_submit_button_first_check(self, form, check_name, check_type, url):
        send_result = 'failure'
        submit_button_xpath = "//button[@type='submit'] | //input[@type='submit']"

        try:
            elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
            )
            time.sleep(20)
            elements[0].click()
            time.sleep(5)
            if "global-coms.biz/contact_us" in url:
                print("intarget")
                print(url)
                send_result = 'success'
            elif "dx-lab.biz/contact" in url:
                sub_elements = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
                )
                time.sleep(20)
                sub_elements[0].click()
                send_result = 'success'
            else:
                send_result = 'failure'
            page_html_after_submit = self.driver.page_source
            if send_result == 'failure':
                soup_after_submit = BeautifulSoup(page_html_after_submit, 'html.parser')
                check_state_exists = soup_after_submit.find('input', {'name': check_name, 'type': check_type}) is not None
                check_change_exists = soup_after_submit.find('input', {'name': check_name, 'type': 'hidden'}) is not None
                if check_state_exists:
                    send_result = 'failure'
                elif check_change_exists:
                    submit_button_xpath = "//button[@type='submit'] | //input[@type='submit']"
                    if self.is_submission_successful():
                        return 'success'

                    try:
                        wait = WebDriverWait(self.driver, 20)
                        submit_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
                        )
                        submit_button.click()
                        time.sleep(20)
                        page_html_after_submit = self.driver.page_source
                        soup_after_submit = BeautifulSoup(page_html_after_submit, 'html.parser')
                        check_state_exists = soup_after_submit.find('input', {'name': check_name}) is not None
                        send_result = 'success' if not check_state_exists else 'failure'
                    except Exception as e:
                        self.logger.error(f"Error clicking the resubmit button: {e}")

                else:
                    send_result = 'success'

        except Exception as e:
            self.logger.error(f"Error clicking the submit button: {e}")

        return send_result
    
    def click_submit_button_recheck(self, form, check_name, check_type, url):
        send_result = 'failure'
        submit_button_xpath = "//button[@type='submit'] | //input[@type='submit']"

        try:
            elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
            )
            time.sleep(20)
            elements[0].click()
            time.sleep(5)
            page_html_after_submit = self.driver.page_source
            if send_result == 'failure':
                soup_after_submit = BeautifulSoup(page_html_after_submit, 'html.parser')
                check_state_exists = soup_after_submit.find('input', {'name': check_name, 'type': check_type}) is not None
                check_change_exists = soup_after_submit.find('input', {'name': check_name, 'type': 'hidden'}) is not None
                if check_state_exists:
                    send_result = 'failure'
                elif check_change_exists:
                    submit_button_xpath = "//button[@type='submit'] | //input[@type='submit']"
                    if self.is_submission_successful():
                        return 'success'

                    try:
                        wait = WebDriverWait(self.driver, 20)
                        submit_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
                        )
                        submit_button.click()
                        time.sleep(20)
                        page_html_after_submit = self.driver.page_source
                        soup_after_submit = BeautifulSoup(page_html_after_submit, 'html.parser')
                        check_state_exists = soup_after_submit.find('input', {'name': check_name}) is not None
                        send_result = 'success' if not check_state_exists else 'failure'
                    except Exception as e:
                        self.logger.error(f"Error clicking the resubmit button: {e}")

                else:
                    send_result = 'success'

        except Exception as e:
            self.logger.error(f"Error clicking the submit button: {e}")

        return send_result

    def send_data(self, url, contact_form, profile_data, retry_count=0, api_key=None):
        MAX_RETRIES = 1
        try:
            self.driver.maximize_window()
            self.driver.get(url)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            keywords = ["氏名", "電話番号", "メールアドレス", "お名前", "住所", "お問合せ", "ご連絡先", "お問い合わせ", "質問"]
            target_form = None
           
            for form in soup.find_all('form'):
                form_text = form.get_text().lower()
                if any(keyword in form_text for keyword in keywords):
                    target_form = form
                    break

            if target_form:
                for key, key_values in contact_form.items():
                    key_value = key_values[0]
                    check_name = key_value['name']
                    check_type = key_value['type']

                    if '詳細' in key or '文' in key or '内容' in key or 'text' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['お問い合わせ詳細'])
                    elif '都道府県' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['都道府県'])
                    elif '建物名' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['建物名'])
                    elif '市区町村' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['市区町村'])
                    elif '町域' in key or '番地' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['町域・番地'])
                    elif 'メール' in key or 'mail' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['メールアドレス'])
                    elif '確認' in key or 'もう一度' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['メールアドレス'])
                    elif '業種' in key or '業界' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['業種・業界'])
                    elif '部署' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['部署名'])
                    elif '役職' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['役職名'])
                    elif '役費' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['役費'])
                    elif '従業員数' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['従業員数'])
                    elif 'サイト' in key or 'url' in key or 'URL' in key or 'ホームページ' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['Webサイト'])
                    elif ('会社' in key or '法人' in key or '企業' in key or '御社' in key or '貴社' in key) and '名' in key and 'ヨミ' not in key and 'フリ' not in key and 'ふり' not in key and 'カナ' not in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['会社名'])
                    elif ('会社' in key or '法人' in key or '企業' in key or '御社' in key or '貴社' in key) and '名' in key and ('ヨミ' in key or 'フリ' in key or 'カナ' in key or 'ふり' in key):
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['会社名（ヨミ）'])
                    elif ('会社' not in key) and ('法人' not in key)  and '企業' not in key and ('ヨミ' in key or 'フリ' in key or 'カナ' in key or 'ふり' in key):
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['姓（ヨミ）'] + ' ' + profile_data['名（ヨミ）']))
                        else:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['姓（ヨミ）'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['名（ヨミ）'])
                    elif ('担当者' in key or '名前' in key or '氏名' in key or '姓名' in key or 'name' in key) and 'ヨミ' not in key and 'フリ' not in key and 'ふり' not in key and 'カナ' not in key:
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['姓'] + ' ' + profile_data['名']))
                        else:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['姓'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['名'])
                    elif ('担当者' in key or '名前' in key or '氏名' in key or '姓名' in key) and ('ヨミ' in key or 'フリ' in key or 'カナ' in key or 'ふり' in key):
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['姓（ヨミ）'] + ' ' + profile_data['名（ヨミ）']))
                        else:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['姓（ヨミ）'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['名（ヨミ）'])
                    elif (('姓' in key or '氏' in key ) and '名' not in key ) and 'ヨミ' not in key and 'フリ' not in key and 'ふり' not in key and 'カナ' not in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['姓'])
                    elif (('姓' in key or '氏' in key ) and '名' not in key ) and ('ヨミ' in key or 'フリ' in key or 'カナ' in key or 'ふり' in key):
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['姓（ヨミ）'])
                    elif ('姓' not in key and '氏' not in key and '名' in key ) and 'ヨミ' not in key and 'フリ' not in key and 'ふり' not in key and 'カナ' not in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['名'])
                    elif ('姓' not in key and '氏' not in key and '名' in key ) and ('ヨミ' in key or 'フリ' in key or 'カナ' in key or 'ふり' in key):
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['名（ヨミ）'])
                    elif 'フリカナ' in key:
                        self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['姓（ヨミ）'] + ' ' + profile_data['名（ヨミ）']))
                    elif '電話番号' in key or 'TEL' in key or 'ご連絡先' in key:
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['電話番号1'] + profile_data['電話番号2'] + profile_data['電話番号3']))
                        elif number_element == 2:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['電話番号1'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['電話番号2'] + profile_data['電話番号3']))
                        elif number_element == 3:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['電話番号1'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['電話番号2'])
                            key_value = key_values[2]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['電話番号3'])
                    elif '郵便番号' in key:
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号'])
                        elif number_element == 2:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号1'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号2'])
                    elif '住所' in key and '社名' in key:
                        number_element = len(key_values)
                        if number_element == 2:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['都道府県'] + profile_data['市区町村']))
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['会社名'])
                        else:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['都道府県'] + profile_data['市区町村']))
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), (profile_data['町域・番地'] + profile_data['建物名']))
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['会社名'])
                    elif '住所' in key:
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['都道府県'])
                        else:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['都道府県'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['市区町村'])
                    elif '〒' in key:
                        number_element = len(key_values)
                        if number_element == 1:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号'])
                        elif number_element == 2:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号1'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号2'])
                        elif number_element == 3:
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号1'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['郵便番号2'])
                            key_value = key_values[1]
                            self.wait_and_fill_input(By.NAME, key_value.get('name'), profile_data['市区町村'])

                self.select_option_in_form(target_form, profile_data['都道府県'])
                self.wait_and_fill_textarea(target_form, profile_data['お問い合わせ詳細'])
                self.select_check_radio_in_form(target_form)
                send_result = self.click_submit_button(target_form, check_name, check_type, url)
                if send_result != 'success':
                    if retry_count < MAX_RETRIES:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc
                        if ':' in domain:
                            domain = domain.split(':')[0]
                        data = {
                                'api_key': api_key,
                                'url': domain,
                            }
                        try:
                            # Make API call
                            api_url = "https://autofill.robosell.jp/api/get_url_data"

                            response = requests.get(
                                url=api_url,
                                params=data
                            )
                            if response.status_code == 200:
                                new_data = response.json()
                                if new_data:
                                    element_pairs = json.loads(new_data['data']['element_pairs'])
                                    content = new_data['data']['content']
                                    input_to_modal = {pair['inputField']: pair['modalButton'] for pair in element_pairs}

                                    # Then modify the form filling logic
                                    for key, key_values in contact_form.items():
                                        key_value = key_values[0]
                                        form_field_name = key_value['name']
                                        
                                        # Check if this form field name exists in our new data mapping
                                        if form_field_name in input_to_modal:
                                            modal_button = input_to_modal[form_field_name]
                                            
                                            # Map modal_button to the correct profile_data key
                                            profile_key = {
                                                # Company related
                                                'company': '会社名',
                                                'company_hira': '会社名（ヨミ）',
                                                
                                                # Name related
                                                'last_name': '姓',
                                                'first_name': '名',
                                                'full_name': '姓名',
                                                'last_hira': '姓（ヨミ）',
                                                'first_hira': '名（ヨミ）',
                                                'full_hira': '姓名（ヨミ）',
                                                
                                                # Department and position
                                                'department': '部署名',
                                                'business': '業種・業界',
                                                'job': '役職名',
                                                'service_fee': '役費',
                                                
                                                # Address related
                                                'post': '郵便番号',
                                                'post1': '郵便番号1',
                                                'post2': '郵便番号2',
                                                'address': '都道府県',
                                                'full_address': '住所',
                                                'city': '市区町村',
                                                'street': '町域・番地',
                                                'building': '建物名',
                                                
                                                # Contact information
                                                'tel': '電話番号',
                                                'tel1': '電話番号1',
                                                'tel2': '電話番号2',
                                                'tel3': '電話番号3',
                                                'email': 'メールアドレス',
                                                'website': 'Webサイト',
                                                
                                                # Other
                                                'employee': '従業員数',
                                                'content': 'お問い合わせ詳細',
                                                'memo': 'メモ'
                                            }.get(modal_button)
                                            
                                            if profile_key and profile_key in profile_data:
                                                self.wait_and_fill_input(By.NAME, form_field_name, profile_data[profile_key])
                                    
                                    self.select_option_in_form(target_form, profile_data['都道府県'])
                                    self.wait_and_fill_textarea(target_form, profile_data['お問い合わせ詳細'])
                                    self.select_check_radio_in_form(target_form)  
                                    if content == '2次確認ボタンの出現':
                                        send_result = self.click_submit_button_recheck(target_form, check_name, check_type, url)
                                    else:
                                        send_result = self.click_submit_button_first_check(target_form, check_name, check_type, url)     
                        except Exception as api_error:
                            self.logger.error(f"API call failed: {api_error}")

            else:
                self.logger.warning("No matching form found on the page")
                send_result = 'failure'
            return send_result

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            send_result = 'error'
            pass

        finally:
            self.driver.quit()


        return send_result

    