from selenium import webdriver
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import pandas as pd
import gspread
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
from selenium.webdriver.common.by import By
import time
import re
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from datetime import date
import random


file_name = 'LI_run' + str(date.today()) + '.xls'
file_name_no_mail = 'LI_run_no_mail' + str(date.today()) + '.xls'

#-------------email and password input------------

email = input("Enter email: ")
password = input("Enter password: ")


# --------------drive upload function------------
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("mycreds.txt")
    return gauth


def upload_to_drive(file_path, folder_id=None):
    gauth = authenticate_drive()
    drive = GoogleDrive(gauth)
    file_name = file_path.split("/")[-1]
    file_drive = drive.CreateFile({'title': file_name, 'parents': [{'id': folder_id}] if folder_id else []})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()

    print(f"File uploaded to Google Drive successfully.")

# -------------email check--------------
def email_check(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return bool(match)
# ----------------log file setup--------------
log_name = str(date.today()) + 'error_log.log'
file_log = open(log_name, "w")
file_log.write('This is start of log')
file_log.close()
# ----------- setting up xls file for results------
home = pd.DataFrame()
with pd.ExcelWriter(file_name, engine="xlsxwriter", mode="w") as writer:
    home.to_excel(writer, sheet_name='HOME', index=False, header=True)

home = pd.DataFrame()
with pd.ExcelWriter(file_name_no_mail, engine="xlsxwriter", mode="w") as writer:
    home.to_excel(writer, sheet_name='HOME', index=False, header=True)

# ------------------getting keywords from google sheet---------------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
keyword_sheet = '1x3RQb1siUZKbDVxPg-_ZxWzRqzocy73n9WVer2dr5D4'
SHEET_NAME = 'Sheet1'
gc = gspread.service_account('trpworld-b494a2dd19c0.json')
spreadsheet = gc.open_by_key(keyword_sheet)
worksheet1 = spreadsheet.worksheet(SHEET_NAME)
rows = worksheet1.get_all_records()
df = pd.DataFrame(rows)
keywordss = df['Keywords'].tolist()
keywords = [element for element in keywordss if element]

# ---------------getting restricted keywords---------------------------
SHEET_NAME1 = 'Sheet1'
gc1 = gspread.service_account('trpworld-b494a2dd19c0.json')
res_sheet = gc1.open_by_key('1R5Jm8PEYsfgHfEwfceJdeMXc5-q2oy9Ba1-aDUKfiPI')
worksheet1 = res_sheet.worksheet(SHEET_NAME1)
rows = worksheet1.get_all_records()
df = pd.DataFrame(rows)
restricts = df['Keywords'].tolist()
restrict = [element for element in restricts if element]

# ----------starting the webdriver scraping process----------------------
today = datetime.now()

# driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()))
# driver = webdriver.Chrome()
# driver.get('chrome://settings/')
# driver.execute_script('chrome.settingsPrivate.setDefaultZoom(0.5);')
# driver.get("https://www.linkedin.com/login")
# driver.maximize_window()
# time.sleep(2)
# driver.find_element(By.XPATH, '//*[@id="username"]').send_keys('sahaybhagwan.ts@gmail.com')
# time.sleep(2)
# driver.find_element(By.XPATH, '//*[@id="password"]').send_keys('bhag#123')
# driver.find_element(By.XPATH, '//*[@id="organic-div"]/form/div[3]/button').click()
# time.sleep(3)
# driver.get('https://www.linkedin.com/search/results/content/?datePosted=%22past-week%22&keywords=looking%20for%20php%20developer&origin=FACETED_SEARCH&sid=b5F&sortBy=%22date_posted%22')
# time.sleep(3)
# -----------df for segregation----------
headers = ['Time Stamp', 'Post Time', 'Username', 'Link ID', 'Description']
df1 = pd.DataFrame(columns=headers)
df2 = pd.DataFrame(columns=headers)


for key in reversed(keywords):
    driver = uc.Chrome()
    # driver = webdriver.Chrome()
    driver.get('chrome://settings/')
    driver.execute_script('chrome.settingsPrivate.setDefaultZoom(0.5);')
    driver.get("https://www.linkedin.com/login")
    driver.maximize_window()
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="username"]').send_keys(email)
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(password)
    driver.find_element(By.XPATH, '//*[@id="organic-div"]/form/div[3]/button').click()
    time.sleep(3)
    driver.get(
        'https://www.linkedin.com/search/results/content/?datePosted=%22past-week%22&keywords=looking%20for%20php%20developer&origin=FACETED_SEARCH&sid=b5F&sortBy=%22date_posted%22')
    time.sleep(3)

    # driver.refresh()
    driver.switch_to.window(driver.window_handles[0])
    driver.find_element(By.XPATH, '//*[@id="global-nav-typeahead"]/input').clear()
    driver.find_element(By.XPATH, '//*[@id="global-nav-typeahead"]/input').send_keys(key)
    driver.find_element(By.XPATH, '//*[@id="global-nav-typeahead"]/input').send_keys(Keys.ENTER)
    time.sleep(3)

    for i in range(1, 50):
        actions = ActionChains(driver)
        actions.scroll_by_amount(0, 5000).perform()
        time.sleep(5)

    source = driver.page_source
    soup = BeautifulSoup(source, 'html.parser')
    names = []
    post_time = []
    link = []
    contents = []
    results = soup.findAll(class_="pt1 mb2 artdeco-card")
    for result in results:

        try:
            trial = result.find(class_="update-components-text relative update-components-update-v2__commentary")
            contents.append(trial.get_text().strip())
            trial = (result.find(class_='update-components-actor__name hoverable-link-text t-14 t-bold t-black'))
            name = trial.find(class_='visually-hidden')
            names.append(name.get_text().strip())
            trial = result.find(class_='update-components-text-view break-words')
            bulb = trial.get_text().strip()
            post_time.append(bulb[:len(bulb)//2])
            trial = result.a
            link.append(trial['href'])
        except:
            print('post content not found')

    try:
        time_stamp = len(contents)*[today.strftime('%d-%b-%Y,%H:%M:%S')]
        df = pd.DataFrame({'Time Stamp': time_stamp, 'Post Time': post_time, 'Username': names, 'Link ID': link, 'Description': contents})
        for ind in df.index:
            if any(ele in df['Description'][ind] for ele in restrict):
                df.drop(index=ind,inplace=True)
            else:
                continue
        df.reset_index(drop=True, inplace=True)
        print(df)
        for ind in df.index:
            if email_check(df['Description'][ind]):
                row_copy = df.iloc[ind]
                df1 = df1._append(row_copy, ignore_index=True)
            else:
                row_copy = df.iloc[ind]
                df2 = df2._append(row_copy, ignore_index=True)
        with pd.ExcelWriter(file_name, engine="openpyxl", mode="a") as writer:
            df1.to_excel(writer, sheet_name=key, index=False, header=True)
        with pd.ExcelWriter(file_name_no_mail, engine="openpyxl", mode="a") as writer:
            df2.to_excel(writer, sheet_name=key, index=False, header=True)
    except Exception as err:
        file_log = open(log_name, "a", encoding="utf-8")
        file_log.write(str(err))
        file_log.close()
        print('index might be out of range or some other error has occurred please check error_log file for more info')
    link.clear()
    names.clear()
    contents.clear()
    post_time.clear()
    time.sleep(random.randint(100, 300))
    time.sleep(5)
    driver.quit()



# -------------------uploading sheet----------------
folder_id = '13w3sdbuzlWkJc9t0uIUz4kuzsN214Bzt'
upload_to_drive(file_name, folder_id)
upload_to_drive(file_name_no_mail, folder_id)

# time.sleep(5)
# driver.quit()