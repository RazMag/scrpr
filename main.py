from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 

from os import getenv
from dotenv import load_dotenv


load_dotenv()

def main():
    print("Running!")
    u_name = getenv('MTA_USERNAME')
    pw = getenv('MTA_PASSWORD')

    driver = webdriver.Firefox()
    driver.get("http://rishum.mta.ac.il/")
    waitfor(driver,By.ID,"Ecom_User_ID")
    username_box = driver.find_element(By.ID,"Ecom_User_ID")
    pw_box = driver.find_element(By.ID,"Ecom_Password")
    login_btn = driver.find_element(By.ID,"loginButton2")

    username_box.send_keys(u_name)
    pw_box.send_keys(pw)
    login_btn.click()

    waitfor(driver,By.XPATH,"//*[contains(text(),'מאגר בחינות')]")
    exam_bank_btn = driver.find_element(By.XPATH,"//*[contains(text(),'מאגר בחינות')]")
    exam_bank_btn.click()
    

def waitfor(driver,elem_type,elem_name):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((elem_type,elem_name)))



if __name__ == "__main__":
    main()
