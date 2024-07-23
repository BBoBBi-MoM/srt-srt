import datetime
import time
from abc import ABC
from dataclasses import fields
from typing import get_args

from custom_types import (ClassPriorityOptions, Passenger, PassengerCount,
                          PassengerSelect, Region, SeatAttribute, SeatLocation,
                          Select, Ticket, TimePriorityOptions)
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SRT_LOGIN_PAGE_URL = r"https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000"
SRT_SELECT_SCHEDULE_PAGE_URL = r"https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000"
SRT_TICKETING_PAGE_URL = r"https://etk.srail.kr/hpg/hra/02/selectReservationList.do?pageId=TK0102010000"
SRT_MAIN_URL = r"https://etk.srail.kr/main.do"
POP_UP_VISIBLE_EXPLICIT_WAIT_TIME = 3
POP_UP_INVISIBLE_EXPLICIT_WAIT_TIME = 10


class BasePage(ABC):
    def __init__(self, driver: Chrome):
        self._driver = driver
        self._driver.implicitly_wait(10)

    def is_alert_present(self) -> bool:
        try:
            _ = self._driver.switch_to.alert
            return True
        except Exception:
            return False

    def _get_select(self, xpath: str):
        elem = self._driver.find_element(By.XPATH, xpath)
        return Select(elem)


class LoginPage(BasePage):
    def __init__(self, driver: Chrome, url: str = SRT_LOGIN_PAGE_URL):
        BasePage.__init__(self, driver)
        self._url = url
        _id_input_box_xpath = "//*[@id='srchDvNm01']"
        self._id_input_box = self._driver.find_element(By.XPATH, _id_input_box_xpath)
        _pw_input_box_xpath = "//*[@id='hmpgPwdCphd01']"
        self._pw_input_box = self._driver.find_element(By.XPATH, _pw_input_box_xpath)
        _confirm_button_xpath = "/html/body/div/div[4]/div/div[2]/form/fieldset/div[1]/div[1]/div[2]/div/div[2]/input"
        self._confirm_button = self._driver.find_element(By.XPATH, _confirm_button_xpath)

    def login(self, account_id: str, pw: str):
        self._driver.get(self._url)
        if len(account_id) != 10 or not account_id.isdigit():
            raise ValueError
        self._pw_input_box.send_keys(pw)
        self._id_input_box.send_keys(account_id)
        self._confirm_button.click()
        if self.is_alert_present():
            alert_msg = self._driver.switch_to.alert.text
            raise ValueError(alert_msg)
        else:
            print("로그인 성공")


class SelectSchedulePage(BasePage):
    def __init__(self, driver: Chrome, url: str = SRT_SELECT_SCHEDULE_PAGE_URL):
        BasePage.__init__(self, driver)
        self._url = url
        _dep_input_box_xpath = "//*[@id='dptRsStnCdNm']"
        self._dep_input_box = self._driver.find_element(By.XPATH, _dep_input_box_xpath)
        self._dep_input_box.clear()
        _dst_input_box_xpath = "//*[@id='arvRsStnCdNm']"
        self._dst_input_box = self._driver.find_element(By.XPATH, _dst_input_box_xpath)
        self._dst_input_box.clear()

        _date_select_xpath = "//*[@id='dptDt']"
        self._date_select = self._get_select(_date_select_xpath)
        _time_select_xpath = "//*[@id='dptTm']"
        self._time_select = self._get_select(_time_select_xpath)

        _adult_select_xpath = "//select[@name='psgInfoPerPrnb1']"
        _children_select_xpath = "//select[@name='psgInfoPerPrnb5']"
        _elder_select_xpath = "//select[@name='psgInfoPerPrnb4']"
        _severe_select_xpath = "//select[@title='중증장애인 인원수 선택']"
        _mild_select_xpath = "//select[@title='경증장애인 인원수 선택']"
        self._passenger_selects = PassengerSelect(self._get_select(_adult_select_xpath),
                                                  self._get_select(_children_select_xpath),
                                                  self._get_select(_elder_select_xpath),
                                                  self._get_select(_severe_select_xpath),
                                                  self._get_select(_mild_select_xpath),
                                                  )

        _seat_location_xpath = "//select[@title='좌석위치 선택']"
        _seat_attr_xpath = "//select[@title='좌석속성 선택']"
        self.seat_loc_select = self._get_select(_seat_location_xpath)
        self.seat_attr_select = self._get_select(_seat_attr_xpath)

        _search_button_xpath = "//input[@value='조회하기']"
        self._search_button = self._driver.find_element(By.XPATH, _search_button_xpath)

    def enter_region(self, dep: Region, dst: Region):
        self._driver.get(self._url)
        if dep not in get_args(Region) or dst not in get_args(Region):
            ValueError("지역 이상함;")
        self._dep_input_box.send_keys(dep)
        self._dst_input_box.send_keys(dst)

    def select_date_time(self, date_time: datetime.datetime):
        if datetime.datetime.today().date() > date_time.date():
            raise ValueError
        date_list = [datetime.datetime.strptime(date_string.split('(')[0], '%Y/%m/%d').date()
                     for date_string in self._date_select.text_options]
        date_idx = date_list.index(date_time.date())
        self._date_select.select_by_index(date_idx)
        dep_time = date_time.hour
        dep_time = dep_time if dep_time % 2 == 0 else dep_time - 1
        time_list = self._time_select.text_options
        time_idx = time_list.index(f"{dep_time:02d}")
        self._time_select.select_by_index(time_idx)

    def select_passenger(self, pessanger_count: PassengerCount) -> None:
        for f in fields(Passenger):
            cnt: int = getattr(pessanger_count, f.name)
            if cnt > 9:
                raise ValueError
            select: Select = getattr(self._passenger_selects, f.name)
            select.select_by_index(cnt)

    def select_seat_type(self, location: SeatLocation = SeatLocation.default,
                         attribute: SeatAttribute = SeatAttribute.default):
        self.seat_loc_select.select_by_index(location.value)
        self.seat_attr_select.select_by_index(attribute.value)

    def search(self):
        self._search_button.click()
        popup_xpath = "//*[@id=\"NetFunnel_Loading_Popup\"]"
        try:
            # 요소가 나타날 때까지 대기
            popup_xpath = "//*[@id=\"NetFunnel_Loading_Popup\"]"
            WebDriverWait(self._driver, POP_UP_VISIBLE_EXPLICIT_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, popup_xpath))
            )
            # 요소가 사라질 때까지 대기
            WebDriverWait(self._driver, POP_UP_INVISIBLE_EXPLICIT_WAIT_TIME).until(
                EC.invisibility_of_element((By.XPATH, popup_xpath))
            )
        except BaseException:
            pass


class TimeTablePage(BasePage):
    def __init__(self, driver: Chrome):
        self._driver = driver
        self._table_body_xpath = "//tbody"
        self._ticking_page = TicketingPage(self._driver)

    def run(self, refresh_cycle_sec: float = 0.5, class_priority_options: ClassPriorityOptions, time_priority_options: TimePriorityOptions):
        while True:
            tickets = self._get_tickets(class_priority_options, time_priority_options)
            if tickets.is_empty():
                self._driver.refresh()
                time.sleep(refresh_cycle_sec)
            else:
                sorted_ticket = tickets.sorted_by_priority()
                best_ticket: WebElement = sorted_ticket["ticket"].iloc[0]
                reservation_button = best_ticket.find_element(By.TAG_NAME, "a")
                reservation_button.click()
                if self.is_alert_present():
                    alert = self._driver.switch_to.alert
                    alert.accept()
                if self._ticking_page.validate():
                    break

    def _get_tickets(self, class_priority_options: ClassPriorityOptions, time_priority_options: TimePriorityOptions) -> Ticket:
        try:
            table_elem = self._driver.find_element(By.XPATH, self._table_body_xpath)
        except NoSuchElementException:
            search_button = self._driver.find_element(By.XPATH, "//*[@id=\"search_top_tag\"]/input")
            search_button.click()
            try:
                popup_xpath = "//*[@id=\"NetFunnel_Loading_Popup\"]"
                WebDriverWait(self._driver, POP_UP_VISIBLE_EXPLICIT_WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, popup_xpath))
                )
                WebDriverWait(self._driver, POP_UP_INVISIBLE_EXPLICIT_WAIT_TIME).until(
                    EC.invisibility_of_element((By.XPATH, popup_xpath))
                )
            except BaseException:
                pass
            table_elem = self._driver.find_element(By.XPATH, self._table_body_xpath)
        tickets = Ticket(table_elem, class_priority_options, time_priority_options)
        return tickets


class TicketingPage(BasePage):
    def __init__(self, driver: Chrome, url: str = SRT_TICKETING_PAGE_URL):
        BasePage.__init__(self, driver)
        self._url = url

    def validate(self):
        self._driver.get(self._url)
        try:
            self._driver.find_element(By.XPATH, "//*[@id=\"list-form\"]/fieldset/div[2]")
            return False
        except NoSuchElementException:
            return True
