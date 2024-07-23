from selenium.webdriver import Chrome
import datetime
from ..page_object import pages
from ..page_object.pages import LoginPage, SelectSchedulePage, TimeTablePage, TicketingPage
from ..page_object.custom_types import (PriorityOptions, SeatOptions, PassengerCount, Region)


class AutoReserver:
    def __init__(self,
                 driver: Chrome,
                 ):

        self._login_page = LoginPage(driver, pages.SRT_LOGIN_PAGE_URL)
        self._select_schedule_page = SelectSchedulePage(driver, pages.SRT_SELECT_SCHEDULE_PAGE_URL)
        self._time_table_page = TimeTablePage(driver)
        self._ticketing_page = TicketingPage(driver, pages.SRT_TICKETING_PAGE_URL)

    def run(self,
            _id_: str,
            pw: str,
            departure: Region,
            destination: Region,
            min_datetime: datetime.datetime,
            max_datetime: datetime.datetime,
            passenger_count: PassengerCount,
            seat_options: SeatOptions,
            priority_options: PriorityOptions,
            best_datetime: datetime.datetime | None = None
            ):
        self._login_page.login(_id_, pw)
        self._select_schedule_page.enter_region(departure, destination)
        self._select_schedule_page.select_date_time(min_datetime)
        self._select_schedule_page.select_passenger(passenger_count)
        self._select_schedule_page.select_seat_type(seat_options.seat_location, seat_options.seat_attribute)
        self._select_schedule_page.search()
        self._time_table_page.run(class_priority_options=priority_options.class_priority_option,
                                  time_priority_options=priority_options.time_priority_option)
        is_success = self._ticketing_page.validate()
