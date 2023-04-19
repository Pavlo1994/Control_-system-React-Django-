import time

from Flight.script.pixhawkController import PixhawkController
import math


class CommandHandler:

    def __init__(self, pixhawkController: PixhawkController):
        self.pixhawk = pixhawkController
        self.current_command = {}

    def execute_command(self, command):
        self.current_command = command
        if command["Command"] == "Takeoff":
            print("Setting Guided")
            self.pixhawk.set_mode("GUIDED")
            time.sleep(1)
            print("Arming")
            self.pixhawk.arm()
            time.sleep(1)
            print("Takeoff")
            self.pixhawk.takeoff(command["Details"]["Altitude"])
        elif command["Command"] == "Navigate":
            self.pixhawk.go_to_location(command["Details"]["Latitude"],
                                        command["Details"]["Longitude"],
                                        command["Details"]["Altitude"])
        elif self.current_command["Command"] == "Altitude":
            self.pixhawk.set_altitude(
                self.current_command["Details"]["Altitude"])
        elif command["Command"] == "Land":
            # TODO: Use CV for Landing
            self.pixhawk.set_mode("Land")
        elif command["Command"] == "RTL":
            self.pixhawk.set_mode("RTL")

    def is_current_command_completed(self):
        telemetry = self.pixhawk.get_telemetry(blocking=True)
        if self.current_command["Command"] == "Takeoff":
            target_alt = self.current_command["Details"]["Altitude"]
            if target_alt - 0.5 < telemetry['altitude'] < target_alt + 0.5:
                return True
        elif self.current_command["Command"] == "Navigate":
            # TODO: Refactor
            d_lat = self.current_command["Details"]["Latitude"] - telemetry["latitude"]
            d_lon = self.current_command["Details"]["Longitude"] - telemetry["longitude"]
            dist = math.sqrt((d_lat * d_lat) + (d_lon * d_lon)) * 1.113195e5
            if dist < 1:
                return True
        elif self.current_command["Command"] == "Land":
            # TODO: Use CV for Landing
            if -0.5 < telemetry['altitude'] < 0.5:
                return True
        elif self.current_command["Command"] == "RTL":
            if -0.5 < telemetry['altitude'] < 0.5:
                return True
        elif self.current_command["Command"] == "Altitude":
            target_alt = self.current_command["Details"]["Altitude"]
            if target_alt - 0.5 < telemetry['altitude'] < target_alt + 0.5:
                return True

        return False
