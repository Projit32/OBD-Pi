import tkinter as tk
import json
import threading
import time
import obd
from datetime import datetime, timedelta
from ui.pi_display_app import OBD2Dashboard

class OBDDataReader:
    def __init__(self, callback):
        """Initialize OBD reader with a callback for data sharing"""
        self.callback = callback
        self.connection = None
        self.running = False
        self.current_value = {}
        self.obd_delay = 0.07
        self.start_time = time.time()
        # Load commands from JSON
        with open("running.json", "r") as file:
            commands_file = json.load(file)
            self.running_commands = [obd.commands[key] for key in commands_file]

        with open("occasional.json", "r") as file:
            commands_file = json.load(file)
            self.occasional_commands = [obd.commands[key] for key in commands_file]

        self.all_commands = self.occasional_commands + self.running_commands

    def watch_running_commands(self):
        for cmd in self.running_commands:
            self.connection.watch(cmd)

    def watch_occasional_commands(self):
        self.connection.stop()
        for cmd in self.occasional_commands:
            self.connection.watch(cmd)

        print("Watch ||  Total commands : ", self.connection.__commands, " (", len(self.connection.__commands),")")
        self.connection.start()

    def unwatch_occasional_commands(self):
        self.connection.stop()
        for cmd in self.occasional_commands:
            self.connection.unwatch(cmd)
        print("Unwatch || Total commands : ", self.connection.__commands, " (", len(self.connection.__commands),")")

        self.connection.start()

    def connect(self):
        """Establish connection to OBD interface"""
        try:
            self.connection = obd.OBD()
            if self.connection.is_connected():
                print(f"Connected to: {self.connection.port_name()}")
                response = self.connection.query(obd.commands["ELM_VERSION"])
                if not response.is_null() and response.value is not None:
                    self.current_value["ELM_VERSION"] = {
                        "value": str(response.value),
                        "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
                    }
                    print("ELM VERSION : ", self.current_value["ELM_VERSION"]["value"])

                self.connection.close()

                self.connection = obd.Async(delay_cmds=self.obd_delay)
                if self.connection.is_connected():
                    print(f"Async Connection established with: {self.connection.port_name()}")
                    return True
                else:
                    print("Failed to Async Connect to OBD2 interface!")
                    return False
            else:
                print("Failed to connect to OBD2 interface!")
                return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def fetch_data(self):
        """Fetch sensor data and put it in the callback"""

        time_delta = round(float(time.time() - self.start_time), 1)
        self.current_value["RUN_TIME"] = {
            "value": f"{time_delta} second",
            "unit": "second"
        }

        for cmd in self.all_commands:
            try:
                response = self.connection.query(cmd)
                if not response.is_null() and response.value is not None:
                    self.current_value[cmd.name]= {
                        "value": str(response.value),
                        "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
                    }
                    print(cmd.name,response.value)
                    self.callback(self.current_value)
                    time.sleep(self.obd_delay)
            except Exception as e:
                print("ERROR fetching sensor data ",e)
                pass  # Silently skip errors for individual sensors


    def run(self):
        """Main loop for reading OBD data"""
        # Watch all commands
        self.watch_running_commands()
        self.watch_occasional_commands()

        self.connection.start()

        initial_sleep = 2*(len(self.occasional_commands)+len(self.running_commands))*self.obd_delay
        # Wait for first full cycle
        print(f"Commands has been loaded to be watched. Waiting for 2 full cycle to complete... [{initial_sleep} sec]")
        time.sleep(initial_sleep)
        self.unwatch_occasional_commands()
        self.running = True

        is_occasional_on = False
        occasional_end_time = datetime.now()

        while self.running:
            try:
                self.fetch_data()
                if not is_occasional_on and datetime.now().second % 20 == 0:
                    is_occasional_on = True
                    print("Turning occasional on :")
                    self.watch_occasional_commands()
                    occasional_end_time = datetime.now() + timedelta(seconds=(self.obd_delay*len(self.all_commands))*2)
                    print("Stop Time for occasional ", occasional_end_time)

                if is_occasional_on and datetime.now() >= occasional_end_time:
                    self.unwatch_occasional_commands()
                    is_occasional_on = False
                    print("Turning off occasional")

            except Exception as e:
                print(f"Error reading data: {e}")
                time.sleep(1)

    def stop(self):
        """Stop the reading loop and close connection"""
        self.running = False
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("OBD connection closed")


class IntegratedDashboard:
    def __init__(self):
        """Initialize the integrated dashboard with threading"""
        self.root = tk.Tk()
        self.reader_thread = None

        # Create dashboard after binding resize
        self.dashboard = OBD2Dashboard(self.root)
        self.reader = OBDDataReader(self.dashboard.enqueue_data)

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_reader_thread(self):
        """Start the OBD reader in a separate thread"""
        self.reader_thread = threading.Thread(target=self.reader.run, daemon=True)
        self.reader_thread.start()
        print("OBD reader thread started")

    def on_closing(self):
        """Handle window close event"""
        print("Shutting down...")
        self.reader.stop()
        if self.reader_thread:
            self.reader_thread.join(timeout=2)
        self.root.destroy()

    def run(self):
        """Start the application"""
        print("Starting OBD Dashboard...")

        # Connect to OBD
        if self.reader.connect():
            # Start reader thread
            self.start_reader_thread()

            # Start Tkinter main loop
            self.root.update_idletasks()  # Force window to fully render
            self.root.mainloop()
        else:
            print("Failed to connect to OBD interface. Exiting...")
            # Optionally, you can still start the UI with sample data
            # self.root.mainloop()

if __name__ == "__main__":
     app = IntegratedDashboard()
     app.run()