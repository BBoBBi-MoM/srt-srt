import datetime
import os
from abc import ABC
from dataclasses import dataclass, field, fields
from enum import IntEnum
from typing import Generic, Iterator, Literal, TypeVar, get_args

import pandas as pd
from dotenv import load_dotenv
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select as SeleniumSelect

T = TypeVar("T")
VERY_HIGH: int = 4
HIGH: int = 3
MEDIUM: int = 2
LOW: int = 1
DISABLE: int = 0
SRT_LOGIN_PAGE_URL = r"https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000"
SRT_SELECT_SCHEDULE_PAGE_URL = r"https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000"
SRT_MAIN_URL = r"https://etk.srail.kr/main.do"
Region = Literal["수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미", "동대구", "서대구", "경주", "울산(통도사)", "울산", "부산"]


class Select(SeleniumSelect):
    @property
    def elem_options(self) -> list[WebElement]:
        return self.options

    @property
    def text_options(self) -> list[str]:
        return [elem.text for elem in self.options]


# class BaseColumn(ABC):
#     def __init__(self, col_elems: list[WebElement]):
#         self._col_elems = col_elems

#     @property
#     def text(self) -> list[str]:
#         return [elem.text for elem in self._col_elems]


# class TimeColumn(BaseColumn):
#     @property
#     def time(self) -> list[datetime.time]:
#         times = []
#         for text in self.text:
#             time_str = text.split("\n")[1]
#             time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()
#             times.append(time_obj)
#         return times


# class ClassColumn(BaseColumn):
#     @property
#     def is_available(self) -> list[bool]:
#         ...


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


@dataclass
class Passenger(Generic[T]):
    adult: T
    elder: T
    child: T
    severe_disabled: T
    mild_disabled: T

    def __iter__(self) -> Iterator[T]:
        return (getattr(self, f.name) for f in fields(self))


@dataclass
class PassengerSelect(Passenger[Select]):
    pass


@dataclass
class PassengerCount(Passenger[int]):
    adult: int = field(default=1)
    elder: int = field(default=0)
    child: int = field(default=0)
    severe_disabled: int = field(default=0)
    mild_disabled: int = field(default=0)


class SeatLocation(IntEnum):
    default = 0
    single_seat = 1
    window_seat = 2
    aisle_seat = 3


class SeatAttribute(IntEnum):
    default = 0
    normal = 1
    wheelchair = 2
    electric_wheelchair = 3


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


@dataclass
class ClassPriorityOptions:
    standard: int = HIGH
    first_class: int = LOW
    standard_standing: int = LOW
    first_class_standing: int = LOW
    allow_standing: bool = False

    def __post_init__(self):
        if not any([getattr(self, field.name) for field in fields(self)]):
            raise ValueError
        if self.allow_standing is False:
            self.standard_standing = DISABLE
            self.first_class_standing = DISABLE
        if self.standard == DISABLE:
            self.standard_standing = DISABLE
        if self.first_class == DISABLE:
            self.first_class_standing = DISABLE

    def __iter__(self):
        priorities = {field.name: getattr(self, field.name) for field in fields(self) if field.name not in
                      ['allow_standing', "time_ascendig", "best_time", "time_prefer"]}
        filtered_priorities = {name: value for name, value in priorities.items() if value != DISABLE}
        sorted_priorities = sorted(filtered_priorities.items(), key=lambda item: item[1], reverse=True)
        for name, _ in sorted_priorities:
            yield name


@dataclass
class TimePriorityOptions:
    min_datetime: datetime.datetime = datetime.datetime.now()
    max_datetime: datetime.datetime | None = None
    best_datetime: datetime.datetime | None = None
    prefer_time: bool = False
    ascendig: bool = True

    def __post_init__(self):
        if self.max_datetime is not None and self.min_datetime > self.max_datetime:
            raise ValueError
        if self.best_datetime is not None:
            if self.best_datetime < self.min_datetime:
                raise ValueError
            if self.max_datetime is not None:
                if self.best_datetime > self.max_datetime:
                    raise ValueError


class Ticket:
    DEP_IDX = 3
    FIRST_CLS_IDX = 5
    STANDARD_CLS_IDX = 6

    def __init__(self, table_elem: WebElement, class_priority_options: ClassPriorityOptions,
                 time_priority_options: TimePriorityOptions):
        self._class_priority_options = class_priority_options
        self._time_priority_options = time_priority_options
        self.min_time = time_priority_options.min_datetime
        self.max_time = time_priority_options.max_datetime
        self.best_time = time_priority_options.best_datetime

        _rows = [row_elem for row_elem in table_elem.find_elements(By.TAG_NAME, "tr")]
        _time_table_df = self._get_time_table_df(_rows)
        self._sorted_by_time_df = self._filter_by_time(_time_table_df)
        self._standard, self._standard_standing, self._first_class, self._first_class_standing = \
            self._split_by_class(self._sorted_by_time_df)

    def __bool__(self):
        return not (
            self._standard.empty and
            self._standard_standing.empty and
            self._first_class.empty and
            self._first_class_standing.empty
        )

    def _get_time_table_df(self, rows: list[WebElement]) -> pd.DataFrame:
        columns = {Ticket.DEP_IDX: []}
        if self._class_priority_options.standard:
            columns[Ticket.STANDARD_CLS_IDX] = []
        if self._class_priority_options.first_class:
            columns[Ticket.FIRST_CLS_IDX] = []

        for row in rows:
            row_elems = row.find_elements(By.TAG_NAME, "td")
            for idx in columns.keys():
                if idx == Ticket.DEP_IDX:
                    elem = row_elems[idx]
                    time_text = elem.text.split("\n")[1]
                    hour, minute = time_text.split(":")
                    new_time = self._time_priority_options.min_datetime.replace(hour=int(hour), minute=int(minute))
                    columns[idx].append(new_time)
                else:
                    columns[idx].append(row_elems[idx])
        time_table_df = pd.DataFrame(columns)
        return time_table_df

    def _filter_by_time(self, time_table_df: pd.DataFrame) -> pd.DataFrame:
        time_series = time_table_df.iloc[:, 0]
        time_filter = time_series >= self._time_priority_options.min_datetime
        _20_minutes = (datetime.datetime.now() + datetime.timedelta(minutes=20))
        _20_min_filter = time_series > _20_minutes
        time_filter = time_filter & _20_min_filter
        if self._time_priority_options.min_datetime is not None:
            max_time_filterd = time_series <= self._time_priority_options.max_datetime
            time_filter = time_filter & max_time_filterd
        time_table_df = time_table_df[time_filter]
        return time_table_df

    def _split_by_class(self, time_table_df: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
        status = time_table_df.iloc[:, 1:].map(lambda elem: elem.text)
        forbidon_statuses = ["좌석부족", "매진"]
        if self._class_priority_options.allow_standing is False:
            forbidon_statuses.append("입석+좌석")
        for fs in forbidon_statuses:
            status[status == fs] = False

        if self._class_priority_options.standard:
            standard = time_table_df[[Ticket.DEP_IDX, Ticket.STANDARD_CLS_IDX]
                                     ][status[Ticket.STANDARD_CLS_IDX].astype(bool)]
            if self._class_priority_options.allow_standing and self._class_priority_options.standard_standing:
                standard_standing = standard[status[Ticket.STANDARD_CLS_IDX] == "입석+좌석"]
                standard = standard[status[Ticket.STANDARD_CLS_IDX] != "입석+좌석"]
            else:
                standard_standing = pd.DataFrame()
        else:
            standard = pd.DataFrame()
            standard_standing = pd.DataFrame()

        if self._class_priority_options.first_class:
            first_class = time_table_df[[Ticket.DEP_IDX, Ticket.FIRST_CLS_IDX]
                                        ][status[Ticket.FIRST_CLS_IDX].astype(bool)]
            if self._class_priority_options.allow_standing and self._class_priority_options.first_class_standing:
                first_class_standing = first_class[status[Ticket.FIRST_CLS_IDX] == "입석+좌석"]
                first_class = first_class[status[Ticket.FIRST_CLS_IDX] != "입석+좌석"]
            else:
                first_class_standing = pd.DataFrame()
        else:
            first_class = pd.DataFrame()
            first_class_standing = pd.DataFrame()
        standard.columns = ['time', 'ticket']
        standard_standing.columns = ['time', 'ticket']
        first_class.columns = ['time', 'ticket']
        first_class_standing.columns = ['time', 'ticket']
        return standard, standard_standing, first_class, first_class_standing

    @property
    def standard(self) -> pd.DataFrame:
        return self._standard

    @property
    def standard_standing(self) -> pd.DataFrame:
        return self._standard_standing

    @property
    def first_class(self) -> pd.DataFrame:
        return self._first_class

    @property
    def first_class_standing(self) -> pd.DataFrame:
        return self._first_class_standing

    def sorted_by_priority(self) -> pd.DataFrame:
        if self._time_priority_options.prefer_time:  # 오직 시간만을
            all_df = pd.concat([self.standard, self.standard_standing, self.first_class, self.first_class_standing],
                               axis=0)
            if self._time_priority_options.best_datetime:  # 오직 베스트 타임과 가까울수록
                return self._sort_by_best_time(all_df)
            else:  # 객실 유형 무시하고 오름차순 or 내림차순으로만 정렬
                return all_df.sort_values("time", ascending=self._time_priority_options.ascendig)
        else:  # 객실 유형별로 시간정렬 한 후에 객실 유형 우선순위맞춰서 합쳐야함
            tickets_list: list[pd.DataFrame] = [getattr(self, p) for p in self._class_priority_options]
            if self._time_priority_options.best_datetime:
                for ticket in tickets_list:
                    ticket = self._sort_by_best_time(ticket)
                return pd.concat(tickets_list, axis=0)
            else:
                all_df = pd.concat(tickets_list, axis=0)
                all_df.sort_values("time", ascending=self._time_priority_options.ascendig) 
                return all_df

    def _sort_by_best_time(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df["time_diff"] = df["time"].apply(lambda t: t - self._time_priority_options.best_datetime)
        df = df.iloc[(df['time_diff'].abs()).argsort()]
        df = df.drop(columns=["time_diff"])
        return df


class AutoReserver:
    def __init__(self, driver: Chrome,
                 class_priority_options: ClassPriorityOptions, time_priority_options: TimePriorityOptions,
                 ):
        self._driver = driver
        _table_body_xpath = "//tbody"
        _tbody_elem = self._driver.find_element(By.XPATH, _table_body_xpath)
        self._tickets = Ticket(_tbody_elem, class_priority_options, time_priority_options)
        self._sorted_ticket = self._tickets.sorted_by_priority()
        ...

    def run(self):
        ...


if __name__ == "__main__":
    load_dotenv()
    ID = os.getenv("ID")
    if ID is None:
        raise OSError
    PW = os.getenv("PW")
    if PW is None:
        raise OSError

    driver_options = Options()
    # driver_options.add_argument("headless")
    driver = Chrome(options=driver_options)

    login_page = LoginPage(driver)
    login_page.login(ID, PW)

    departure: Region = "수서"
    destination: Region = "부산"
    min_datetime = datetime.datetime(2024, 7, 22, 21)
    best_datetime = min_datetime.replace(hour=22, minute=0)
    max_datetime = (min_datetime + datetime.timedelta(hours=5, minutes=40))
    passenger_cnt = PassengerCount()
    select_schedule_page = SelectSchedulePage(driver)
    select_schedule_page.enter_region(departure, destination)
    select_schedule_page.select_date_time(min_datetime)
    select_schedule_page.select_passenger(passenger_cnt)
    select_schedule_page.select_seat_type(SeatLocation.default, SeatAttribute.default)
    select_schedule_page.search()
    priority_options = ClassPriorityOptions(standard=LOW,
                                            first_class=VERY_HIGH,
                                            standard_standing=MEDIUM,
                                            first_class_standing=HIGH,
                                            allow_standing=True,
                                            )
    time_priority_options = TimePriorityOptions(
        min_datetime=min_datetime,
        max_datetime=max_datetime,
        best_datetime=best_datetime,
        prefer_time=False,
        ascendig=False)

    auto_reserver = AutoReserver(driver, class_priority_options=priority_options,
                                 time_priority_options=time_priority_options)  # , time_limit=max_time)

    # TODO: 입석옵션좀 고민해보자..
    input("Press Enter to close the browser and end the script...")
    print("Done")
