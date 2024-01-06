from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--headless")

url = "https://store.exertissupplies.co.uk/"

driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
driver.get(url)

try:
    logged_in_body = driver.find_element(By.CSS_SELECTOR, "body.ex-loggedin")
except NoSuchElementException:
    try:
        shopping_tools_wrapper = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".shopping-tools-wrapper .account-btn"))
        )
        
        ActionChains(driver).move_to_element(shopping_tools_wrapper).perform()

        login_form = shopping_tools_wrapper.find_element(By.CSS_SELECTOR, "form.auth-form.login-form")
        email_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.login-email input[name='email']"))
        )

        email_input.send_keys("paul@digitalmps.co.uk")

        password_input = login_form.find_element("css selector", "div.login-password input[name='password']")
        password_input.send_keys("##Megan23")

        login_form.submit()

        time.sleep(3)

    except NoSuchElementException:
        pass

df = pd.read_csv('product_data.csv')

batch_size = 100

try:
    existing_data_df = pd.read_csv('extracted_data.csv')
    existing_product_codes = set(existing_data_df['product_code'])
except FileNotFoundError:
    existing_product_codes = set()

total_no_results_count = 0

def fetch_product_data(product_code):
    search_input = driver.find_element("css selector", "input.ajax-search-control")
    search_input.clear()
    search_input.send_keys(product_code)
    time.sleep(2)

    try:
        result_container = driver.find_element("css selector", ".ajax-results")
        first_result = result_container.find_element("tag name", "a")
        first_result.click()

        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        try:
            product_code = soup.find("div", class_="prod-code").find('span').get_text().strip()
        except AttributeError:
            product_code = ''

        try:
            product_category = soup.find("div", class_="prod-category").find('a').get_text().strip()
        except AttributeError:
            product_category = ''

        try:
            product_name = soup.find("h1", class_="product-name").get_text().strip()
        except AttributeError:
            product_name = ''

        try:
            product_manufacturer_name = soup.find("div", class_="manufacturer-name").find('span').get_text().strip()
        except AttributeError:
            product_manufacturer_name = ''

        try:
            filter_container = soup.find("div", class_="filter-container")
            product_price = filter_container.find("span", class_="has-price").get_text().strip()
            product_price = re.sub(r'[^0-9.]', '', product_price)
        except AttributeError:
            product_price = ''

        try:
            product_stock = soup.find("strong", class_="live-stock-content").find('strong').get_text().strip()
        except AttributeError:
            product_stock = ''

        return {
            "product_code": product_code.replace('Product Code: ', ''),
            "product_category": product_category,
            "product_name": product_name,
            "product_price": product_price,
            "product_stock": product_stock,
            "product_manufacturer_name": product_manufacturer_name.replace('Manufacturer ', ''),
        }

    except NoSuchElementException:
        return None

with ThreadPoolExecutor(max_workers=5) as executor:
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i + batch_size]

        extracted_data = []
        no_results_count = 0

        results = executor.map(fetch_product_data, batch_df['product_code'])

        for result in results:
            if result is not None:
                extracted_data.append(result)
            else:
                no_results_count += 1
                total_no_results_count += 1

        result_df = pd.DataFrame(extracted_data, columns=['product_code', 'product_category', 'product_name', 'product_price', 'product_stock', 'product_manufacturer_name'])
        result_df.to_csv('extracted_data.csv', mode='a', header=(not existing_product_codes), index=False)

        existing_product_codes.update(result_df['product_code'])

        extracted_data = []

        print(f"Inserted {len(result_df)} records in {i + batch_size} batch. (Total No result found: {total_no_results_count})")

driver.quit()