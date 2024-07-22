import datetime
from dataclasses import dataclass, field, fields
from enum import IntEnum
from typing import Generic, Iterator, Literal, TypeVar

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select as SeleniumSelect

T = TypeVar("T")

VERY_HIGH: int = 4
HIGH: int = 3
MEDIUM: int = 2
LOW: int = 1
DISABLE: int = 0

Region = Literal["수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미", "동대구", "서대구", "경주", "울산(통도사)", "울산", "부산"]


class Select(SeleniumSelect):
    @property
    def elem_options(self) -> list[WebElement]:
        return self.options

    @property
    def text_options(self) -> list[str]:
        return [elem.text for elem in self.options]


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
    default = 1
    wheelchair = 2
    electric_wheelchair = 3


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

    def is_empty(self):
        return (
            self.standard.empty and
            self.standard_standing.empty and
            self.first_class.empty and
            self.first_class_standing.empty
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
        if self._time_priority_options.max_datetime is not None:
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
        if not standard.empty:
            standard.columns = ['time', 'ticket']
        if not standard_standing.empty:
            standard_standing.columns = ['time', 'ticket']
        if not first_class.empty:
            first_class.columns = ['time', 'ticket']
        if not first_class_standing.empty:
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
                return pd.concat(tickets_list, axis=0).drop(columns=["time_diff"])
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
