# Manager for sending and verifying route commands
import logging

from qr import QrTypes, QrHandler
from telemetryHandler import TelemetryHandler
from route import RouteTypes
from waypoint import Waypoint
from flaskClientSocket import FlaskClientSocket
from loggingHandler import setup_logging

setup_logging()

# Boolean to email flight plan or send flight plan to drone to execute
TASK_2_EMAIL_DAY = True

# Weight of drone used to filter Task 2 routes with weight limits
VEHICLE_WEIGHT = 0


class CommandManager:

    def __init__(self,
                 qr_handler: QrHandler,
                 telemetry_handler: TelemetryHandler):
        self.qr_handler = qr_handler
        self.telemetry_handler = telemetry_handler
        self.route = []
        self.updated_route = []
        self.current_command = None
        self.backup_command = None
        self.sent_command = None
        self.sent_message = ""
        self.socket = FlaskClientSocket(1, 8080)

        # TODO: Without Flight/CommunicationRouter, socket connection fails
        # Requires button on website on whether to flight is initialized or not
        # self.socket.connect()

    def connect_to_socket(self):
        """Start socket connection

        :return: True if successful connection, else False
        """
        return self.socket.connect()

    def send_command(self, message):
        """Send message to Flight

        :param message: (str) message to send
        :return: True if successful send, else False
        """
        status = self.socket.send_message(message)
        self.sent_message = message if status else self.sent_message
        return status

    def send_last_message(self):
        """Send last recorded message

        :return: True if successful send, else False
        """
        return self.socket.send_message(self.sent_message)

    def send_initial_route(self):
        pass

    def send_updated_route(self):
        pass

    def process_qr(self, qr_type: QrTypes) -> None:
        """Process QR data and sending initial/updated route to Flight
        Assumes QR data is validated

        :param qr_type: QrTypes enum for which QR data to process
        :return:
        """
        qr_response = self.qr_handler.get_qr(str(qr_type.value),
                                             waypoints_as_dicts=False)
        if not qr_response['success']:
            return
        qr_data = qr_response['qr_data']

        if qr_type == QrTypes.Task_1_Initial_Qr:
            wp_str = ";".join([f"{wp.name, wp.latitude, wp.longitude}"
                               for wp in qr_data])
            self.socket.send_message(f"QR1:{wp_str}")

        elif qr_type == QrTypes.Task_1_Update_Qr:
            # Maybe BoundaryHandler class should calculate detour?
            route_update = self.calculate_detour(qr_data.boundaries,
                                                 qr_data.rejoin_waypoint)
            wp_upd_str = f"{route_update}"
            message = f"QR2:{wp_upd_str}"
            self.socket.send_message(message)

        elif qr_type == QrTypes.Task_2_Qr:
            flight_plan_route = qr_data.routes

            # Filter inaccessible routes
            routes = [route for route in qr_data.routes
                      if route.max_vehicle_weight > VEHICLE_WEIGHT]

            if TASK_2_EMAIL_DAY:
                # Optimization algorithm
                # flight_plan_route = calculate_flight_plan(routes)

                # Save to csv

                # Send email with route plan
                pass
            else:
                # Read flight plan from file

                # Send flight plan to Flight
                # TODO: Update into Flight readable format
                routes_str = ";".join([f"{route.name}, "
                                       f"{route.starting_waypoint}, "
                                       f"{route.end_waypoint}"
                                       for route in flight_plan_route])
                self.socket.send_message(f"QR3:{routes_str}")

    def verify_routes(self, route_type: RouteTypes, routes) -> bool:
        """Validate routes with saved routes

        :param route_type: (RouteTypes) for which Task and initial or updated
        :param routes: Routes to validate with
        :return: True if same routes, else False
        """
        if route_type == RouteTypes.Task_1_Initial_Route:
            return self.route == routes
        elif route_type == RouteTypes.Task_1_Update_Route:
            pass
        elif route_type == RouteTypes.Task_2_Route:
            pass

    def get_sent_command(self) -> str:
        """Retrieve last sent command message

        :return: (str) command message
        """
        return self.sent_command

    def calculate_detour(self, boundaries: list[Waypoint],
                         rejoin_waypoint: Waypoint):
        """Calculate detour from current position to rejoin waypoint

        :param boundaries: boundary of enclosed by waypoints to avoid
        :param rejoin_waypoint: waypoint to end at
        :return:
        """
        # TODO: Finish detour
        logging.info(f"Calculating detour to {rejoin_waypoint.name}")
        detour_start = self.telemetry_handler.get_recent_data()
        detour_end = rejoin_waypoint
        return boundaries, detour_start, detour_end