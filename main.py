import os
import re
import csv
import glob

from time import ctime as time
from time import time as timestamp
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
    """main"""
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
        driver.switch_to.window(driver.window_handles[0])
        get_course_page_by_code(driver, course)
        driver.implicitly_wait(3)
        table_lst = driver.find_elements(By.CSS_SELECTOR, "#myTable0")
        if len(table_lst) > 0:
            download_course(driver, table_lst[0], course)
        close_windows(driver)


def download_course(driver, table, course):
    """For a given course table downloads all of the tests."""
    downloaded_exams = []
    for table_row in table.find_elements(By.CSS_SELECTOR, 'tbody>tr'):
        this_row = table_row.find_elements(By.CSS_SELECTOR, 'td')
        test = ingest_exam_row(this_row, course)
        if test not in downloaded_exams:
            download_exam(driver, this_row, test)
            downloaded_exams.append(test)
            # close_windows(driver)
            driver.switch_to.window(driver.window_handles[0])
    logger(f"Finished {course}")


def close_windows(driver):
    try:
        if len(driver.window_handles) > 1:
            driver.implicitly_wait(3)
        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
    except:
        logger("close_windows error (Oof)")


def ingest_exam_row(row, course):
    test = {
        "course": course,
        "year": re.sub("[^0-9]", "", row[5].text),
        "sem": row[6].text,
        "sitting": row[7].text
    }
    if 'א' in test['sem']:
        test['sem'] = 1
    elif 'ב' in test['sem']:
        test['sem'] = 2
    else:
        test['sem'] = 3
    return test


def download_exam(driver, this_row, test):
    """From a given table row, Downloads the tests"""
    cur_path = f"{getcwd()}/output/{test['course']}/{test['year']}/{test['sem']}"
    Path(cur_path).mkdir(parents=True, exist_ok=True)
    download_source = ""
    download_btn_cell = this_row[9].find_elements(
        By.CSS_SELECTOR, 'input[value="הורדה"]')
    if len(download_btn_cell) > 0:
        download_source = "table"
        driver.execute_script("arguments[0].click();", download_btn_cell[0])
        move_exam_to_folder(cur_path)
    else:
        download_source = "secondary page"
        secondary_page_download_btn = this_row[10].find_elements(
            By.CSS_SELECTOR, 'input[value="קבצים נוספים"]')
        driver.execute_script(
            "arguments[0].click();", secondary_page_download_btn[0])
        secondary_page_download(driver,cur_path)
    logger(
        f"Downloaded from {download_source}: {test['course']} - {test['year']} / {test['sem']} / {test['sitting']}")
    driver.switch_to.window(driver.window_handles[0])


def move_exam_to_folder(folder):
    """Moves the content of ./temp to 'folder'"""
    ready_to_move = False
    start = timestamp()
    while not ready_to_move:
        ready_to_move = True
        file_list = sorted(Path('temp').glob(f"*"))
        if len(file_list) < 1:
            ready_to_move = False
        for file in file_list:
            if file.suffix == '.part':
                ready_to_move = False
        if timestamp() - start > 10:
            break
    file_list = sorted(Path('temp').glob(f"*"))
    for file in file_list:
        file.rename(f"{folder}/{file.name}")

def secondary_page_download(driver,folder):
    """Downloads exam files from a secondary page"""
    window_before = driver.window_handles[0]
    window_after = driver.window_handles[len(driver.window_handles)-1]
    driver.switch_to.window(window_after)
    waitfor(driver, By.XPATH, "//h2[contains(text(),'אודות הקורס')]")
    download_btn = driver.find_elements( 
        By.XPATH, "//button[contains(text(),'קישור לקובץ')]")
    if len(download_btn) < 1: return False
    for btn in download_btn:
        driver.execute_script("arguments[0].click();", btn)
        move_exam_to_folder(folder)
    driver.close()
    driver.switch_to.window(window_before)


def get_course_page_by_code(driver, code):
    """Searches the exam bank page for course by course code"""
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
    """Reads 'db_file' and returns a list of course codes from it"""
    courses = []
    with open(db_file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for item in row:
                courses.append(str(item))
    return courses


def waitfor(driver, elem_type, elem_name):
    """Waits for page to load an element
    found by find_element(elem,type,elem_name)"""
    timeout = 10
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((elem_type, elem_name)))


def set_firefox_options():
    """Sets the firefox profile"""
    options = Options()
    options.profile = FirefoxProfile(f"{getcwd()}/firefox_profile/")
    options.set_preference("browser.download.dir", f"{getcwd()}/temp")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                            "Application/pdf, application/msword, \
                            application/vnd.openxmlformats-officedocument.wordprocessingml.document,\
                            application/vnd.ms-excel, \
                            application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    options.set_preference("browser.download.viewableInternally.enabledTypes","")
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("dom.disable_open_during_load", False)
    return options


def login(driver, username, password):
    """Logs in to MTA's SSO with username:password"""
    waitfor(driver, By.ID, "Ecom_User_ID")
    username_box = driver.find_element(By.ID, "Ecom_User_ID")
    pw_box = driver.find_element(By.ID, "Ecom_Password")
    login_btn = driver.find_element(By.ID, "loginButton2")
    username_box.send_keys(username)
    pw_box.send_keys(password)
    login_btn.click()
    logger("Logged in")


def goto_exam_bank_page(driver):
    """Open exam bank page"""
    waitfor(driver, By.XPATH, "//*[contains(text(),'מאגר בחינות')]")
    exam_bank_btn = driver.find_element(
        By.XPATH, "//*[contains(text(),'מאגר בחינות')]/..")
    driver.execute_script("arguments[0].click();", exam_bank_btn)
    logger("Got exam page")


def logger(message):
    """Log message to screen and to scrpr.log file"""
    message = f"{time()} - {message}"
    print(message)
    with open('scrpr.log', 'a') as log_file:
        log_file.write(f"{message}\n")


if __name__ == "__main__":
    main()
