import os
import re
import csv
import glob

from time import ctime as time
from os import getenv
from os import getcwd
from pathlib import Path
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def main():
    logger("Running!")
    load_dotenv()
    Path(f"{getcwd()}/temp/").mkdir(parents=True, exist_ok=True)
    log_file = open('scrpr.log', 'w')
    log_file.close()
    options = set_firefox_options()

    driver = webdriver.Firefox(options=options)
    driver.get("http://rishum.mta.ac.il/")
    username = getenv('MTA_USERNAME')
    password = getenv('MTA_PASSWORD')
    db_file = ('courses.csv')

    courses = ingest_courses(db_file)
    login(driver, username, password)
    goto_exam_bank_page(driver)
    for course in courses:
        get_course_page_by_code(driver, course)
        table = driver.find_elements(By.CSS_SELECTOR, "#myTable0")
        if len(table) < 1:
            continue
        download_course(driver, table, course)


def download_course(driver, table, course):
    downloaded_exams = []
    for table_row in table.find_elements(By.CSS_SELECTOR, 'tbody>tr'):
        this_row = table_row.find_elements(By.CSS_SELECTOR, 'td')
        test = {
            "year": this_row[5].text,
            "sem": this_row[6].text,
            "sitting": this_row[7].text
        }
        if test not in downloaded_exams:
            download_exam(driver, course, this_row, test)
            downloaded_exams.append(test)
    logger(f"Finished {course}")


def download_exam(driver, course, this_row, test):
    cur_year = re.sub("[^0-9]", "", test['year'])
    if 'א' in test['sem']:
        cur_sem = 1
    elif 'ב' in test['sem']:
        cur_sem = 2
    else:
        cur_sem = 3
    Path(f"{getcwd()}/output/{course}/{cur_year}/{cur_sem}").mkdir(parents=True, exist_ok=True)
    cur_path = f"{getcwd()}/output/{course}/{cur_year}/{cur_sem}"
    download_btn_cell = this_row[9].find_elements(
        By.CSS_SELECTOR, 'input[value="הורדה"]')
    if len(download_btn_cell) > 0:
        driver.execute_script("arguments[0].click();", download_btn_cell[0])
    else:
        window_before = driver.window_handles[0]
        secondary_page_download_btn = this_row[10].find_elements(
            By.CSS_SELECTOR, 'input[value="קבצים נוספים"]')
        driver.execute_script(
            "arguments[0].click();", secondary_page_download_btn[0])
        window_after = driver.window_handles[len(driver.window_handles)-1]
        driver.switch_to.window(window_after)
        waitfor(driver, By.XPATH, "//button[contains(text(),'קישור לקובץ')]")
        download_btn = driver.find_elements(
            By.XPATH, "//button[contains(text(),'קישור לקובץ')]")
        for btn in download_btn:
            driver.execute_script("arguments[0].click();", btn)
        driver.close()
        driver.switch_to.window(window_before)
        while len(driver.window_handles) > 1:
            driver.implicitly_wait(1)
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.implicitly_wait(1)
                if len(driver.window_handles) > 1:
                    driver.close()
    ready_to_move = False
    while not ready_to_move:
        download_file_name = glob.glob(f'{getcwd()}/temp/*.*')
        if len(download_file_name) > 0:
            extension = os.path.splitext(download_file_name[0])
            if '.part' not in extension[1]:
                ready_to_move = True
        driver.implicitly_wait(0.5)
    os.system(f"mv {getcwd()}/temp/* {cur_path}")
    logger(
        f"Downloaded {course} - {cur_year} / {test['sem']} / {test['sitting']}")
    driver.switch_to.window(driver.window_handles[0])


def get_course_page_by_code(driver, code):
    waitfor(driver, By.ID, "select2-R1C1-container")
    course_selection_dropdown = driver.find_element(
        By.ID, "select2-R1C1-container")
    course_selection_dropdown.click()
    course_selection_box = driver.find_element(
        By.CLASS_NAME, "select2-search__field")
    course_selection_box.send_keys(code)
    course_selection_box.send_keys(Keys.RETURN)
    course_search_btn = driver.find_element(
        By.XPATH, "//input[@value='חיפוש']")
    course_search_btn.click()
    waitfor(driver, By.ID,
            "myTable0_wrapper")
    row_amount_dropdown_arr = driver.find_elements(
        By.CSS_SELECTOR, "span[title='10']")
    if len(row_amount_dropdown_arr) > 0:
        row_amount_dropdown_arr[0].click()
        show_all_btn = driver.find_element(
            By.XPATH, "//li[contains(text(),'הכל')]")
        show_all_btn.click()
    logger(f"Got course nubmer {code}")


def ingest_courses(db_file):
    courses = []
    with open(db_file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for item in row:
                courses.append(str(item))
    return courses


def waitfor(driver, elem_type, elem_name):
    timeout = 10
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((elem_type, elem_name)))


def set_firefox_options():
    options = Options()
    options.profile = FirefoxProfile(f"{getcwd()}/firefox_profile/")
    options.set_preference("browser.download.dir", f"{getcwd()}/temp")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                            "Application/pdf, application/msword, \
                            application/vnd.openxmlformats-officedocument.wordprocessingml.document,\
                            application/vnd.ms-excel, \
                            application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    options.set_preference("browser.download.manager.showWhenStarting", False)
    return options


def login(driver, username, password):
    waitfor(driver, By.ID, "Ecom_User_ID")
    username_box = driver.find_element(By.ID, "Ecom_User_ID")
    pw_box = driver.find_element(By.ID, "Ecom_Password")
    login_btn = driver.find_element(By.ID, "loginButton2")
    username_box.send_keys(username)
    pw_box.send_keys(password)
    login_btn.click()
    logger("Logged in")


def goto_exam_bank_page(driver):
    waitfor(driver, By.XPATH, "//*[contains(text(),'מאגר בחינות')]")
    exam_bank_btn = driver.find_element(
        By.XPATH, "//*[contains(text(),'מאגר בחינות')]/..")
    driver.execute_script("arguments[0].click();", exam_bank_btn)
    logger("Got exam page")


def logger(message):
    message = f"{time()} - {message}"
    print(message)
    with open('scrpr.log', 'a') as log_file:
        log_file.write(message)


if __name__ == "__main__":
    main()
