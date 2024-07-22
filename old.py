import datetime
import os
from dataclasses import dataclass, field, fields
from enum import IntEnum
from typing import Generic, Iterator, Literal, TypeVar, get_args

import pandas as pd
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time







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
    destination: Region = "대전"
    min_datetime = datetime.datetime(2024, 7, 22, 5)
    # min_datetime = datetime.datetime.now()
    max_datetime = (min_datetime + datetime.timedelta(hours=3))
    # best_datetime = min_datetime.replace(hour=22, minute=0)
    # max_datetime = (min_datetime + datetime.timedelta(hours=5, minutes=40))
    passenger_cnt = PassengerCount()
    select_schedule_page = SelectSchedulePage(driver)
    select_schedule_page.enter_region(departure, destination)
    select_schedule_page.select_date_time(min_datetime)
    select_schedule_page.select_passenger(passenger_cnt)
    select_schedule_page.select_seat_type(SeatLocation.default, SeatAttribute.default)
    select_schedule_page.search()
    priority_options = ClassPriorityOptions(standard=MEDIUM,
                                            first_class=HIGH,
                                            standard_standing=DISABLE,
                                            first_class_standing=DISABLE,
                                            allow_standing=False,
                                            )
    time_priority_options = TimePriorityOptions(
        min_datetime=min_datetime,
        max_datetime=max_datetime,
        # best_datetime=best_datetime,
        prefer_time=False,
        ascendig=False)

    auto_reserver = AutoReserver(driver, class_priority_options=priority_options,
                                 time_priority_options=time_priority_options)  # , time_limit=max_time)
    ticketing_page = TicketingPage(driver)
    auto_reserver.run()
    is_success = ticketing_page.validate()
    print(is_success)

    # TODO: 
    input("Press Enter to close the browser and end the script...")
    print("Done")
