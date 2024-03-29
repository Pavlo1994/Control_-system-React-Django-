from waypoint import WAYPOINT_LST, Waypoint
from utils import calculate_distance


class FlightPlan:
    # Tunable Parameters
    drone_speed = 18.06  # metres / seconds
    time_to_takeoff = 16.0  # seconds
    time_to_land = 60.0  # seconds
    time_to_load = 10.0  # seconds
    max_time_on_battery = 1500.0  # seconds
    max_time_in_air = 3300.0 # seconds
    time_to_swap_battery = 250 # seconds

    # User configured RTL location
    origin = WAYPOINT_LST.get_wp_by_name("Alpha")

    # Static Memory Storage start: {end : {value}}
    dist_store = {}

    def __init__(self, reward: float = 0.0, distance: float = 0.0, waypoints: list = []) -> None:
        """Initialize FlightPlan object

        param reward: reward earned from initial route in flight plan (float)
        param distance: distance travelled completing initial route in flight plan (float)
        param waypoints: list of waypoints traveled (list)
        """
        self.reward_collected = reward
        self.distance_travelled = distance
        self.waypoints = waypoints
        # time accumulated completing the routes
        self.time_accumulated = self.distance_travelled / self.drone_speed
        # ratio based on distance time and reward earned
        self.ratio = 0
        # signal to add a stop at origin for battery swap
        self.origin_head = None
        # store flight instructions
        self.instructions = []
        # store route numbers
        self.route_plan = []
        # store battery swap waypoint index -> From right to left
        self.battery_swap_indexes = []

    def add_route_tail_wp_only(self, start_wp: Waypoint, end_wp: Waypoint) -> None:
        """Add a full route to the waypoints list

        param start_wp: starting waypoint to start route (Waypoint)
        param end_wp: ending waypoint to complete route (Waypoint)
        """
        self.waypoints = self.waypoints + [start_wp, end_wp]

    def add_route_tail(self, start_wp: Waypoint, end_wp: Waypoint, reward: float = None, without_start: bool = False) \
            -> None:
        """Add a full route to the waypoint list, accounting for distance traveled and time accumulated, if
        without_start flag is set, only end waypoint will be added

        param start_wp: starting waypoint to start route (Waypoint)
        param end_wp: ending waypoint to complete route (Waypoint)
        param reward: reward earned for completing route (float)
        param without_start: optional parameter to signal only add end_wp (bool)
        """

        dist = FlightPlan.calculate_distance(start_wp, end_wp)
        self.distance_travelled += dist
        self.update_time(dist / self.drone_speed)

        if without_start:
            self.waypoints = self.waypoints + [end_wp]
        else:
            self.waypoints = self.waypoints + [start_wp, end_wp]

        if reward:
            self.reward_collected += reward

    def add_route_head(self, reward: float, distance: float, waypoint: Waypoint) -> None:
        """Add a waypoint to the head of the waypoints list, accounting for distance traveled and any reward earned.
        If origin_head is signaled, perform a battery_swap

        param reward: value earned for completing a route (float)
        param distance: distance travelled completing a route (float)
        param waypoint: waypoint to be added to the head of the waypoints list (Waypoint)
        """
        self.distance_travelled += distance
        self.update_time(distance / self.drone_speed)
        self.waypoints = [waypoint] + self.waypoints
        self.reward_collected += reward

        if self.origin_head:
            self.origin_head = None
            if waypoint != FlightPlan.origin:
                self.battery_swap()
            else:
                # halt for battery swap at location
                self.update_time(FlightPlan.time_to_swap_battery)
                self.battery_swap_indexes.append(len(self.waypoints) - 1)

    def takeoff(self) -> None:
        """Increment time accumulated based on set time to takeoff"""
        self.update_time(self.time_to_takeoff)

    def land(self) -> None:
        """Increment time accumulated based on set time to land"""
        self.update_time(self.time_to_land)

    def load(self) -> None:
        """Increment time accumulated based on set time to load"""
        self.update_time(self.time_to_load)

    def update_time(self, add_time: float) -> None:
        """Increment time accumulated with given new time

        param add_time: value to be added to time_accumulated (float)
        """
        self.time_accumulated += add_time

    def complete_route(self) -> None:
        """Increment time accumulated with completing route procedures"""
        self.land()
        self.load()
        self.takeoff()

    def append_at_next_head(self) -> None:
        """Signal to add a stop at origin before next waypoint added to waypoints list head"""
        self.origin_head = FlightPlan.origin

    def battery_swap(self) -> None:
        """Add a stop at origin for a battery swap, updating distance from origin to head waypoint"""
        dist_to_origin = calculate_distance(self.waypoints[0], FlightPlan.origin)
        self.add_route_head(0.0, dist_to_origin, FlightPlan.origin)
        self.update_time(FlightPlan.time_to_swap_battery)
        self.battery_swap_indexes.append(len(self.waypoints) - 1)

    def generate_email(self) -> dict:
        """Generate an email with the planned route order

        :return: Dictionary containing email subject and body (Dict)
        """
        route_join = ";".join(map(str, self.route_plan))
        email_body = f"TMAV;{route_join}"
        return {
            "Subject" : "TMAV Flight Plan",
            "Body" : email_body
        }

    def reformat_battery_indexes(self):
        for i in range(len(self.battery_swap_indexes)):
            self.battery_swap_indexes[i] = len(self.waypoints) - self.battery_swap_indexes[i] - 1
        self.battery_swap_indexes.append(len(self.waypoints) - 1)

    # Static Methods
    @staticmethod
    def rtl_swap_battery(waypoint : Waypoint, acc_time : float) -> bool:
        if waypoint == FlightPlan.origin and acc_time > 0.7 * FlightPlan.time_to_swap_battery:
            return True
        return False

    @staticmethod
    def is_low_battery(acc_time: float, est_distance: float, next_wp: Waypoint) -> bool:
        """Determine if there is enough battery to complete a route, then travel to origin
        from the end of the route

        param acc_time: current amount of time accumulated on battery (float)
        param est_distance: estimated distance to complete route (float)
        param next_wp: waypoint at the end of the route (Waypoint)
        :return: True if battery is low
        """

        dist_to_origin = FlightPlan.calculate_distance(next_wp, FlightPlan.origin)

        time_to_next_wp = est_distance / FlightPlan.drone_speed
        time_to_origin_from_next_wp = dist_to_origin / FlightPlan.drone_speed

        # Calculate time to next wp, then to origin including land, load, takeoff
        acc_time_update = acc_time + time_to_next_wp + FlightPlan.time_to_land \
            + FlightPlan.time_to_load + FlightPlan.time_to_takeoff + time_to_origin_from_next_wp

        # Determine if going to next waypoint and then to origin will take more battery then currently have
        return acc_time_update > FlightPlan.max_time_on_battery

    @staticmethod
    def get_time_from_origin(next_wp: Waypoint) -> float:
        """Calculate the time required to travel from origin to the next waypoint

        param next_wp: the next waypoint to be travelled to (Waypoint)
        :return: the time required to travel
        """
        
        return FlightPlan.calculate_distance(FlightPlan.origin, next_wp) / FlightPlan.drone_speed
    
    @staticmethod
    def calculate_distance(start_wp: Waypoint, end_wp: Waypoint) -> float:
        """ Wrappers around calculate distance function to check if a stored data 
        value exist before calling function

        :param start_wp: Waypoint Object
        :param end_wp: Waypoint Object
        :return: Calculated distance between start and end
        """
        if start_wp.name in FlightPlan.dist_store:
            if end_wp.name in FlightPlan.dist_store[start_wp.name]:
                return FlightPlan.dist_store[start_wp.name][end_wp.name]
        
        elif end_wp.name in FlightPlan.dist_store:
            if start_wp.name in FlightPlan.dist_store[end_wp.name]:
                return FlightPlan.dist_store[end_wp.name][start_wp.name]
            
        computed_dist = calculate_distance(start_wp, end_wp)
        FlightPlan.dist_store[start_wp.name] = {end_wp.name : computed_dist}

        return computed_dist
