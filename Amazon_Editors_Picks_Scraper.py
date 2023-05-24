from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import pandas as pd
import time
import csv
import sys
import numpy as np
import re
import calendar

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--user-data-dir=C:\\Users\\abdel\\AppData\\Local\\Google\\Chrome\\User Data")
    #chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 1, "profile.managed_default_content_settings.images": 1, "profile.default_content_setting_values.cookies": 1}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver

def scrape_AmazonEditorsPicks(path):

    start = time.time()
    # initialize the web driver
    driver = initialize_bot()
    # signing in
    print('-'*75)
    print('Signing In ...')
    try:
        driver.get('https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&')
        username = wait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='ap_email']")))
        username.send_keys('type the account username here')
        button = wait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='continue']")))
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)        
        password = wait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='ap_password']")))
        password.send_keys('type the account password here')
        button = wait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='signInSubmit']")))
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)
    except Exception as err:
        print('Failed to sign in to Amazon due to the below error:')
        print(str(err))
        sys.exit()

    print('-'*75)
    print('Scraping AmazonEditorsPicks.com ...')
    print('-'*75)


    # initializing the dataframe
    data = pd.DataFrame()
    months = list(calendar.month_name[1:])
    name = 'AmazonEditorsPicks_data.xlsx'
    # getting the books under each category
    links, categories = [], {}
    nbooks = 0
    homepage = "https://www.amazon.com/b?ie=UTF8&node=17143709011"
    exclude = ["Cookbooks, food & wine", "Children's books"]
    driver.get(homepage)

    # scraping books category urls
    sections = wait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[class='a-button-text bxc-button-text ']")))
    for sec in sections:
        try:
            cat = sec.get_attribute('textContent').strip()
            skip = False
            for elem in exclude:
                if elem in cat: 
                    skip = True
                    break
            if skip: continue
            link = sec.get_attribute('href')
            if '/b/' in link:
                categories[cat] = link
        except Exception as err:
            continue
                    
    # scraping books urls
    nbooks = 0
    for cat, link in categories.items():
        try:
            driver.get(link)
            url = wait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='a-link-normal']"))).get_attribute('href')
            driver.get(url)
            while True:           
                # scraping books urls
                titles = wait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h2[class='a-size-mini a-spacing-none a-color-base s-line-clamp-2']")))
                for title in titles:
                    try:
                        url = wait(title, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')
                        links.append((url, cat))
                        nbooks += 1
                        print(f'Scraping the url for book {nbooks}')
                    except:
                        pass

                # checking the next page
                try:
                    url = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='s-pagination-item s-pagination-next s-pagination-button s-pagination-separator']"))).get_attribute('href')
                    driver.get(url)
                except:
                    break
        except:
            print(f'Error in getting the books urls from category link: {link}')
            pass

    scraped = []
    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    print('-'*75)
    n = len(links)
    for i, elem in enumerate(links):
        try:
            link = elem[0]
            cat = elem[1]
            if link in scraped: continue
            driver.get(link)           
            details = {}
            print(f'Scraping the info for book {i+1}\{n}')

            # title and title link
            title_link, title = '', ''              
            try:
                title_link = link
                title = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='productTitle']"))).get_attribute('textContent').replace('\n', '').strip().title() 
            except:
                print(f'Warning: failed to scrape the title for book: {link}')                             
            details['Title'] = title
            details['Title Link'] = title_link    
            
            # Author and author link
            author, author_link = '', ''
            try:
                spans = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.author")))
                if len(spans) > 1:
                    spans = spans[:-1]
                for span in spans:
                    try:
                        a = wait(span, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        author += a.get_attribute('textContent').replace('\n', '').strip().title() + ', '
                        author_link += a.get_attribute('href') + ', '
                    except:
                        pass
                author = author[:-2]
                author_link = author_link[:-2]
            except:
                pass
                    
            details['Author'] = author            
            details['Author Link'] = author_link            
            details['Category'] = cat            

            # other info
            try:
                try:
                    # all formats except audio
                    tag = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='detailBulletsWrapper_feature_div']")))
                    lis = wait(tag, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                    for li in lis:
                        try:
                            text = li.get_attribute('textContent').replace('\u200e', '').replace('\n', '').replace('\u200f', '')
                            if ':' not in text: continue
                            elif 'ASIN' in text:
                                details['ASIN'] = text.split(':')[-1].strip()
                            elif 'Publisher' in text:
                                details['Publisher'] = text.split(':')[-1].strip().split('(')[0].strip()
                                if '(' in text:
                                    details['Publication date'] = text.split(':')[-1].strip().split('(')[-1].strip()[:-1]
                            elif 'Language' in text and 'Language' not in details:
                                details['Language'] = text.split(':')[-1].strip()
                            elif 'File size' in text:
                                details['File size'] = text.split(':')[-1].strip()        
                                details['Format'] = 'Kindle'
                            elif 'Paperback' in text or 'Hardcover' in text:
                                details['Format'] = text.split(':')[0].strip()
                                details['Number of Pages'] = text.split(':')[-1].split()[0]
                            elif 'ISBN-10' in text:
                                details['ISBN-10'] = text.split(':')[-1].strip()                            
                            elif 'ISBN-13' in text:
                                details['ISBN-13'] = text.split(':')[-1].strip()
                            elif 'Reading age' in text:
                                details['Reading Age'] = text.split(':')[-1].split()[0]                            
                            elif 'Lexile measure' in text:
                                details['Lexile'] = text.split(':')[-1].strip()                            
                            elif 'Item Weight' in text:
                                details['Weight'] = text.split(':')[-1].strip()                            
                            elif 'Dimensions' in text:
                                details['Dimensions'] = text.split(':')[-1].strip()                              
                            elif 'Publication date' in text:
                                details['Publication date'] = text.split(':')[-1].strip()                            
                            elif 'Best Sellers Rank' in text:
                                details['Best Sellers Rank'] = text.split(':')[-1].strip().split('(')[0].replace('#', '').replace(',', '').strip()
                            elif 'Customer Reviews' in text:
                                try:
                                    details['Rating'] = wait(li, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id='acrPopover']"))).get_attribute('title').split()[0]
                                except:
                                    pass
                                try:
                                    details['Number of Ratings'] = wait(li, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id='acrCustomerReviewText']"))).get_attribute('textContent').split()[0].replace(',', '')
                                except:
                                    pass
                        except:
                            pass

                        if 'Publication date' not in details:
                            try:
                                text = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='productSubtitle']"))).get_attribute('textContent')
                                for month in months:
                                    if month in text:
                                        details['Publication date'] = text.split('–')[-1].strip()
                                        break
                            except:
                                pass


                except:
                    # audio books
                    tag = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//table[@class='a-keyvalue a-vertical-stripes a-span6']")))
                    trs = wait(tag, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
                    for tr in trs:
                        th = wait(tr, 2).until(EC.presence_of_element_located((By.TAG_NAME, "th"))).get_attribute('textContent')
                        td = wait(tr, 2).until(EC.presence_of_element_located((By.TAG_NAME, "td"))).get_attribute('textContent').strip()
                        try:
                            if 'Listening Length' in th:
                                details['Listening Length'] = td
                            elif 'Release Date' in th:
                                details['Publication date'] = td 
                            elif 'Publisher' in th:
                                details['Publisher'] = td 
                            elif 'Type' in th:
                                details['Format'] = td   
                            elif 'Version' in th:
                                details['Version'] = td   
                            elif 'Language' in th:
                                details['Language'] = td 
                            elif 'ASIN' in th:
                                details['ASIN'] = td 
                            elif 'Best Sellers Rank' in th:
                                details['Best Sellers Rank'] = td.split('(')[0].replace('#', '').replace(',', '').strip()
                        except:
                            pass
                    try:
                        # reading age
                        text = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@class='a-section cr-childrens-books']"))).get_attribute('textContent')
                        age = int(re.findall("\d+", text)[0]) 
                        details['Reading Age'] = age
                    except:
                        pass

                    try:
                        details['Rating'] = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id='acrPopover']"))).get_attribute('title').split()[0]
                    except:
                        pass
                    try:
                        details['Number of Ratings'] = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id='acrCustomerReviewText']"))).get_attribute('textContent').split()[0].replace(',', '')
                    except:
                        pass
            except:
                pass

            # price
            price = ''            
            try:
                text = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@class='a-button a-button-selected a-spacing-mini a-button-toggle format']"))).get_attribute('textContent').replace('\n', '').strip() 
                price = float(re.findall("[0-9]+[.][0-9]+", text)[0])
                if 'Format' not in details:
                    details['Format'] = text.split('$')[0].strip()
            except:
                pass                             
            details['Price'] = price   
            
            # appending the output to the datafame        
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except:
            pass

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'AmazonEditorsPicks.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":

    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_AmazonEditorsPicks(path)

