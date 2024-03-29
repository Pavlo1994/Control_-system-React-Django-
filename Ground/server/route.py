from enum import Enum

import utils
from waypoint import WAYPOINT_LST


class RouteTypes(Enum):
    Task_1_Initial_Route = 1
    Task_1_Update_Route = 2
    Task_2_Route = 3


class Route:

    updated_qr_3 = "Route number 1: 2 pers; Lima; Quebec; 15 kg;\
 obstacle 2 m to NE; $112\
Route number 2: 6 pers; Delta; Charlie; 5 kg; nil; $50\
Route number 3: 4 pers; Alpha; Zulu; 15 kg; other comment; $150"

    def __init__(self, number: int = 0, num_passengers: int = 0,
                 start_waypoint_name: str = "Origin",
                 end_waypoint_name: str = "Origin",
                 max_vehicle_weight: float = 0,
                 remarks: str = "", reward: float = 0.0):
        self.number = number
        self.num_passengers = num_passengers
        self.start_waypoint_name = start_waypoint_name
        self.end_waypoint_name = end_waypoint_name
        self.max_vehicle_weight = max_vehicle_weight
        self.remarks = remarks
        self.reward = reward

        self.start_waypoint = WAYPOINT_LST.get_wp_by_name(start_waypoint_name)
        self.end_waypoint = WAYPOINT_LST.get_wp_by_name(end_waypoint_name)

        self.distance = utils.calculate_distance(self.start_waypoint,
                                                 self.end_waypoint)

    def to_dict(self):
        """Converts Route object to dictionary

        :return: Dictionary with Route details
        """
        return {
            "number": self.number,
            "num_passengers": self.num_passengers,
            "start_waypoint": self.start_waypoint.to_dict(),
            "end_waypoint": self.end_waypoint.to_dict(),
            "max_vehicle_weight": self.max_vehicle_weight,
            "remarks": self.remarks,
            "reward": self.reward
        }

    def __str__(self):
        return f"[{self.start_waypoint_name}, {self.end_waypoint_name}, " \
               f"{self.reward}]"

    def __repr__(self) -> str:
        return f"[{self.start_waypoint_name}, {self.end_waypoint_name}, " \
               f"{self.reward}]"
