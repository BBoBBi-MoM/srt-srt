import datetime
from ..page_object.custom_types import PassengerOptions, PriorityOptions, Region, RegionOptions, SeatOptions
from typing import TypedDict, cast


class Context(TypedDict):
    departure: Region
    destination: Region
    min_time: datetime.datetime
    max_time: datetime.datetime
    best_time: datetime.datetime
    adult_count: int


class ReserverOptions:
    def __init__(self,
                 region_options: RegionOptions,
                 passenger_count: PassengerOptions,
                 seat_options: SeatOptions,
                 priority_options: PriorityOptions,
                 ):
        self._region_options = region_options
        self._passenger_count = passenger_count
        self._seat_options = seat_options
        self._priority_options = priority_options

    @classmethod
    def from_request(cls, **context):
        region_options = RegionOptions(departure=context["departure"],
                                       destination=context["destination"],
                                       )
        passenser_options = PassengerOptions(adult=context["adult_count"],
                                             elder=context["elder_count"],
                                             child=context["child_count"],
                                             severe_disabled=context["severe_disabled_count"],
                                             mild_disabled=context["mild_disabled_count"]
                                             )
