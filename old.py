'''
DONE : 예약대기
DONE : 시간 우선순위
DONE : 알림 기능

TODO : 다음 페이지 고려
TODO : 시간 초과하기 전에 로그인
TODO : 인원 선택
TODO : 모두할지 한장만 할지
TODO : 클래스화
'''
import time
import requests

import tkinter as tk
from tkinter import messagebox

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

SRT_ROOT_URL = r'https://etk.srail.kr/main.do'
DEPATURE = '평택지제'
DESTINATION = '동대구'
USER_ID = ''
USER_PASSWORD = ''
TARGET_DATE = '20240801'
TIME_AFTER = '14'
LIMIT_TIME_LOWER = '15:00'
LIMIT_TIME_UPPER = '17:30'
REFRESH_INTERVAL = 0.5
PRIORITY = 'asc'
RESERVATION_STATUS = False

def is_normal_on_sale(ticket: WebElement) -> bool:
    economy_col = ticket.find_elements(By.TAG_NAME, 'td')[6]
    if economy_col.text != '매진' and economy_col.text != '입석+좌석':
        return True
    else:
        return False
    
def is_special_on_sale(ticket: WebElement) -> bool:
    special_col = ticket.find_elements(By.TAG_NAME, 'td')[5]
    if special_col.text != '매진':
        return True
    else:
        return False

def can_reservasion(ticket: WebElement) -> bool:
    reservation_col = ticket.find_elements(By.TAG_NAME, 'td')[7]
    if reservation_col.text != '매진':
        return True
    else:
        return False
    
# def is_available_time(limit_time_lower: str, limit_time_upper: str, ticket_time: str) -> bool:
#     limit_hour_lower, limit_minute_lower = (int(time) for time in limit_time_lower.split(':'))
#     limit_hour_upper, limit_minute_upper = (int(time) for time in limit_time_upper.split(':'))    
#     ticket_hour, ticket_minute = (int(time) for time in ticket_time.split(':'))
#     if (limit_hour_lower <= ticket_hour <= limit_hour_upper):
#         if ticket_hour == limit_hour_lower:
#             if ticket_minute >= limit_minute_lower:
#                 return True
#             else:
#                 return False            
#         elif ticket_hour == limit_hour_upper:
#             if ticket_minute <= limit_minute_upper:
#                 return True
#             else:
#                 return False
#         else:
#             return True
#     else:
#         return False
    
def is_available_time(limit_time_lower: str, limit_time_upper: str, ticket_time: str) -> bool:
    limit_hour_lower, limit_minute_lower = (int(time) for time in limit_time_lower.split(':'))
    limit_hour_upper, limit_minute_upper = (int(time) for time in limit_time_upper.split(':'))    
    ticket_hour, ticket_minute = (int(time) for time in ticket_time.split(':'))
    if limit_hour_lower <= ticket_hour <= limit_hour_upper:
        if (ticket_hour == limit_hour_lower) & (ticket_minute < limit_minute_lower):
            return False            
        elif (ticket_hour == limit_hour_upper) & (ticket_minute > limit_minute_upper):
            return False
        else:
            return True
    else:
        return False
    
def do_reservation(
        tickets: list[WebElement], 
        ticket_type: str, 
        priority: str = 'asc'
        ) -> None:
    if priority == 'asc':
        best_ticket = tickets[0]
    elif priority == 'desc':
        best_ticket = tickets[-1]
    if ticket_type == 'special':
        idx = 5
    elif ticket_type == 'normal':
        idx = 6
    elif ticket_type == 'stage':
        idx = 7
    else:
        raise ValueError
    ticket_element = best_ticket.find_elements(By.TAG_NAME, 'td')[idx]
    final_reservation_button = ticket_element.find_element(By.TAG_NAME, 'a')
    final_reservation_button.click()
    try:
        driver.switch_to.alert.accept()
    except exceptions.NoAlertPresentException:
        pass

def book_ticket():
    messagebox.showinfo("알림", "예약완료")

    
# Enter main page
driver = webdriver.Chrome()
driver.implicitly_wait(1)
driver.get(SRT_ROOT_URL)

# Enter login page
driver.implicitly_wait(1)
login_button = driver.find_element(By.XPATH,'//*[@id="wrap"]/div[3]/div[1]/div/a[2]')
login_button.click()

# login
driver.implicitly_wait(1)
id_input_box = driver.find_element(By.ID, 'srchDvNm01')
id_input_box.send_keys(USER_ID)
driver.implicitly_wait(1)
pw_input_box = driver.find_element(By.ID, 'hmpgPwdCphd01')
pw_input_box.send_keys(USER_PASSWORD)
driver.implicitly_wait(1)
submit_button = driver.find_element(By.XPATH, '//*[@id="login-form"]/fieldset/div[1]/div[1]/div[2]/div/div[2]/input')
submit_button.click()

# Enter reservation page
driver.implicitly_wait(1)
ticket_button = driver.find_element(By.XPATH, '//*[@id="gnb"]')
ticket_button.click()
driver.implicitly_wait(1)
ticket_button.click()
driver.implicitly_wait(1)
ticket_reservation_button = driver.find_element(By.XPATH, '//*[@id="wrap"]/div[3]/div[2]/div/ul/li[1]/ul/li[1]/a')
ticket_reservation_button.click()

#input depature
driver.implicitly_wait(1)
depature_input_box = driver.find_element(By.XPATH,'//*[@id="dptRsStnCdNm"]')
depature_input_box.click()
depature_input_box.clear()
depature_input_box.send_keys(DEPATURE)
# input destination
driver.implicitly_wait(1)
destination_input_box = driver.find_element(By.XPATH, '//*[@id="arvRsStnCdNm"]')
destination_input_box.click()
destination_input_box.clear()
destination_input_box.send_keys(DESTINATION)


# //*[@id="NetFunnel_Loading_Popup"]

# Select time
time.sleep(5)
driver.implicitly_wait(1)
date_combobox = Select(driver.find_element(By.XPATH, '//*[@id="dptDt"]'))
date_combobox.select_by_value(TARGET_DATE)
time_combobox = Select(driver.find_element(By.XPATH, '//*[@id="dptTm"]'))
time_combobox.select_by_visible_text(TIME_AFTER)

# Enter time table page
time.sleep(5)
driver.implicitly_wait(5)
search_button = driver.find_element(By.XPATH, '//*[@id="search_top_tag"]/input')
search_button.click()

# time.sleep(240)

# WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="NetFunnel_Loading_Popup"]')))
# 명절용 로딩모달
# WebDriverWait(driver, 300).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="NetFunnel_Loading_Popup"]')))


# Refresh until the condition is satisfied
possible_normal_tickets = []
possible_special_tickets = []
stage_tickets = []
while not possible_normal_tickets and not stage_tickets:
    try:
        time.sleep(REFRESH_INTERVAL)
        driver.refresh()
        WebDriverWait(driver, 2).until(EC.alert_is_present())  # 알림창이 뜨기를 대기
        alert = Alert(driver)  # 알림창 객체 생성
        alert.accept()
        time_table = driver.find_element(By.XPATH, '//*[@id="result-form"]/fieldset/div[6]/table/tbody')
        tickets_list = time_table.find_elements(By.TAG_NAME, 'tr')
        
        for ticket in tickets_list:
            departure_time = ticket.find_element(By.TAG_NAME, 'em').text
            if not is_available_time(LIMIT_TIME_LOWER, LIMIT_TIME_UPPER, departure_time):
                continue
            if is_normal_on_sale(ticket):
                possible_normal_tickets.append(ticket)
            # 여기서 필요한 다른 조건들을 추가할 수 있습니다.
            # if is_special_on_sale(ticket):
            #     possible_special_tickets.append(ticket)
            if can_reservasion(ticket):
                stage_tickets.append(ticket)
            
        if possible_normal_tickets:
            driver.implicitly_wait(1)
            do_reservation(possible_normal_tickets, ticket_type='normal', priority='asc')
            try:
                result = driver.switch_to.alert
                result.accept()
            except:
                pass
            if driver.find_elements(By.ID, 'isFalseGotoMain'):
                print('RESERVATION SUCCESS')
                book_ticket()
                driver.close()
            else:
                print("잔여석 없음. 다시 검색")
                driver.back() # 뒤로가기
                driver.implicitly_wait(5)
                pass
            
        if stage_tickets:
            driver.implicitly_wait(1)
            do_reservation(stage_tickets, ticket_type='stage', priority='asc')
            try:
                result = driver.switch_to.alert
                result.accept()
            except:
                pass
            if driver.find_elements(By.ID, 'isFalseGotoMain'):
                print('RESERVATION SUCCESS')
                book_ticket()
                driver.close()
            else:
                print("잔여석 없음. 다시 검색")
                driver.back() # 뒤로가기
                driver.implicitly_wait(5)
                pass

    except :
        # 지정된 요소를 찾을 수 없을 때 여기가 실행됩니다.
        print("Trying to click on the search button again...")
        try:
            search_button = driver.find_element(By.XPATH, '//*[@id="search_top_tag"]/input')
            search_button.click()
        except:
            try:
                driver.execute_script("arguments[0].click()", search_button)
                print("click invisible botton")
            except:
                print("Search button not found. Check the page or XPATH.")