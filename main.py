from xxlimited import new
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from time import ctime as time
from os import getenv
from dotenv import load_dotenv
import csv


load_dotenv()


def main():
    print(f"{time()} - Running!")
    driver = webdriver.Firefox()
    driver.get("http://rishum.mta.ac.il/")
    u_name = getenv('MTA_USERNAME')
    pw = getenv('MTA_PASSWORD')
    courses = []
    with open('courses_testing.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for item in row:
                courses.append(str(item))
    login(driver, u_name, pw)
    goto_exam_bank_page(driver)
    downloaded_exams = []
    for course in courses:
        get_course_page_by_code(driver, course)
        table = driver.find_element(By.CSS_SELECTOR,"#myTable0")
        for table_row in table.find_elements(By.CSS_SELECTOR,'tbody>tr'):
            this_row = table_row.find_elements(By.CSS_SELECTOR,'td')
            test = {
                "year" : this_row[5].text,
                "sem" : this_row[6].text,
                "sitting" : this_row[7].text
            }
            #if test not in downloaded_exams:
                #TODO download this test

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
    row_amount_dropdown_arr = driver.find_elements(By.XPATH,
                                                   "//span[@title='10']")
    if len(row_amount_dropdown_arr) > 0:
        row_amount_dropdown_arr[0].click()
        show_all_btn = driver.find_element(
            By.XPATH, "//li[contains(text(),'הכל')]")
        show_all_btn.click()


def waitfor(driver, elem_type, elem_name):
    timeout = 10
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((elem_type, elem_name)))


def login(driver, u_name, pw):
    waitfor(driver, By.ID, "Ecom_User_ID")
    username_box = driver.find_element(By.ID, "Ecom_User_ID")
    pw_box = driver.find_element(By.ID, "Ecom_Password")
    login_btn = driver.find_element(By.ID, "loginButton2")
    username_box.send_keys(u_name)
    pw_box.send_keys(pw)
    login_btn.click()
    print(f"{time()} - Logged in")


def goto_exam_bank_page(driver):
    waitfor(driver, By.XPATH, "//*[contains(text(),'מאגר בחינות')]")
    exam_bank_btn = driver.find_element(
        By.XPATH, "//*[contains(text(),'מאגר בחינות')]/..")
    driver.execute_script("arguments[0].click();", exam_bank_btn)


if __name__ == "__main__":
    main()
