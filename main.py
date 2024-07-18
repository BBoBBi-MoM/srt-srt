import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Literal, get_args, Iterator
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select as SeleniumSelect
from abc import ABC
from selenium.webdriver import Chrome
import os
from dotenv import load_dotenv
import pandas as pd


SRT_LOGIN_PAGE_URL = r"https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000"
SRT_SELECT_SCHEDULE_PAGE_URL = r"https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000"
SRT_MAIN_URL = r"https://etk.srail.kr/main.do"
Region = Literal["수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미", "동대구", "서대구", "경주", "울산(통도사)", "울산", "부산"]


@dataclass
class PassengerCount:
    adult: int = 0
    elder: int = 0
    child: int = 0
    severe_disabled: int = 0
    mild_disabled: int = 0

    def __iter__(self) -> Iterator[int]:
        return iter([self.adult, self.elder, self.child, self.severe_disabled, self.mild_disabled])


class SeatLocation(Enum):
    default: int = 0
    single_seat: int = 1
    window_seat: int = 2
    aisle_seat: int = 3


class SeatAttr(Enum):
    default: int = 0
    normal: int = 1
    wheelchair: int = 2
    electric_wheelchair: int = 3


class Select(SeleniumSelect):
    @property
    def elem_options(self) -> list[WebElement]:
        return self.options

    @property
    def text_options(self) -> list[str]:
        return [elem.text for elem in self.options]


class BasePage(ABC):
    def __init__(self, driver: Chrome, url: str):
        self._driver = driver
        self._driver.implicitly_wait(10)
        self._driver.get(url)

    @property
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
        BasePage.__init__(self, driver, url)
        _id_input_box_xpath = "//*[@id='srchDvNm01']"
        self._id_input_box = self._driver.find_element(By.XPATH, _id_input_box_xpath)
        _pw_input_box_xpath = "//*[@id='hmpgPwdCphd01']"
        self._pw_input_box = self._driver.find_element(By.XPATH, _pw_input_box_xpath)
        _confirm_button_xpath = "/html/body/div/div[4]/div/div[2]/form/fieldset/div[1]/div[1]/div[2]/div/div[2]/input"
        self._confirm_button = self._driver.find_element(By.XPATH, _confirm_button_xpath)

    def login(self, account_id: str, pw: str):
        if len(account_id) != 10 or not account_id.isdigit():
            raise ValueError
        self._pw_input_box.send_keys(pw)
        self._id_input_box.send_keys(account_id)
        self._confirm_button.click()
        if self.is_alert_present:
            alert_msg = self._driver.switch_to.alert.text
            raise ValueError(alert_msg)
        else:
            print("로그인 성공")


class SelectSchedulePage(BasePage):
    def __init__(self, driver: Chrome, url: str = SRT_SELECT_SCHEDULE_PAGE_URL):
        BasePage.__init__(self, driver, url)
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
        self._passenger_selects = {
            "adult": self._get_select(_adult_select_xpath),
            "child": self._get_select(_children_select_xpath),
            "elder": self._get_select(_elder_select_xpath),
            "severe_disabled": self._get_select(_severe_select_xpath),
            "mild_disabled": self._get_select(_mild_select_xpath),
        }

        _seat_location_xpath = "//select[@title='좌석위치 선택']"
        _seat_attr_xpath = "//select[@title='좌석속성 선택']"
        self.seat_loc_select = self._get_select(_seat_location_xpath)
        self.seat_attr_select = self._get_select(_seat_attr_xpath)

        _search_button_xpath = "//input[@value='조회하기']"
        self._search_button = self._driver.find_element(By.XPATH, _search_button_xpath)

    def enter_region(self, dep: Region, dst: Region):
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

    def select_passenger(self, person_count: PassengerCount):
        for key, count in zip(self._passenger_selects.keys(), person_count):
            if count > 9:
                raise ValueError(f"{key} count cannot be more than 9.")
            self._passenger_selects[key].select_by_index(count)

    def select_seat_type(self, location: SeatLocation = SeatLocation.default,
                         attribute: SeatAttr = SeatAttr.default):
        self.seat_loc_select.select_by_index(location.value)
        self.seat_attr_select.select_by_index(attribute.value)

    def search(self):
        self._search_button.click()

class TableColumn:
    ...


class AutoReserver:
    DEP_IDX = 3
    FIRST_CLS_IDX = 5
    NORMAL_CLS_IDX = 6

    def __init__(self, driver: Chrome, allow_stand: bool = True):
        self._driver = driver
        # _dep_col_xpath = "/html/body/div/div[4]/div/div[3]/div[1]/form/fieldset/div[6]/table/colgroup/col[4]"
        # self.dep_col_elems = self._driver.find_elements(By.XPATH, _dep_col_xpath)
        # _first_cls_col_xpath = "/html/body/div/div[4]/div/div[3]/div[1]/form/fieldset/div[6]/table/colgroup/col[6]"
        # self.first_cls_col_elems = self._driver.find_elements(By.XPATH, _first_cls_col_xpath)
        # _normal_cls_col_xpath = "/html/body/div/div[4]/div/div[3]/div[1]/form/fieldset/div[6]/table/colgroup/col[7]"
        # self.normal_col_cls_elems = self._driver.find_elements(By.XPATH, _normal_cls_col_xpath)
        _table_body_xpath = "//tbody"
        self._tbody_elem = self._driver.find_element(By.XPATH, _table_body_xpath)
        self._row_elems = [row_elem for row_elem in self._tbody_elem.find_elements(By.TAG_NAME, "tr")]

        ...


    def _get_table(self) -> pd.DataFrame:
        table_elem = self._driver.find_element(By.XPATH, self._table_xpath)
        ...
        


if __name__ == "__main__":
    load_dotenv()
    ID = os.getenv("ID")
    PW = os.getenv("PW")

    driver = Chrome()
    login_page = LoginPage(driver)
    login_page.login(ID, PW)

    DEPARTURE: Region = "수서"
    DESTINATION: Region = "부산"
    DATETIME = datetime.datetime(2024, 7, 19, 15, 30)
    PASSENGER_COUNT = PassengerCount(adult=1, elder=3, child=3)
    select_schedule_page = SelectSchedulePage(driver)
    select_schedule_page.enter_region(DEPARTURE, DESTINATION)
    select_schedule_page.select_date_time(DATETIME)
    select_schedule_page.select_passenger(PASSENGER_COUNT)
    select_schedule_page.select_seat_type(SeatLocation.window_seat, SeatAttr.default)
    select_schedule_page.search()
    auto_reserver = AutoReserver(driver)
    df = auto_reserver._get_table()
    

    # TODO:
    input("Press Enter to close the browser and end the script...")
    print("Done")


