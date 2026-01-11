import tkinter as tk
import json
import threading
import time
import obd
from ui.mid_res_app import OBD2Dashboard

class OBDDataReader:
    def __init__(self, callback):
        """Initialize OBD reader with a callback for data sharing"""
        self.callback = callback
        self.connection = None
        self.running = False
        self.current_value = {}

        # Load commands from JSON
        with open("./commands.json", "r") as file:
            self.commands_file = json.load(file)

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
                return True
            else:
                print("Failed to connect to OBD2 interface!")
                return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def fetch_data(self):
        """Fetch sensor data and put it in the callback"""

        for cmd in self.commands_file.keys():
            try:
                response = self.connection.query(obd.commands[cmd])
                if not response.is_null():
                    if response.value is not None:
                        self.current_value[cmd]= {
                            "value": str(response.value),
                            "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
                        }
                        print(self.current_value[cmd])
                        self.callback(self.current_value)
            except Exception as e:
                pass  # Silently skip errors for individual sensors


    def run(self):
        """Main loop for reading OBD data"""
        self.running = True

        while self.running:
            try:
                self.fetch_data()
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
            self.root.mainloop()
        else:
            print("Failed to connect to OBD interface. Exiting...")
            # Optionally, you can still start the UI with sample data
            # self.root.mainloop()

if __name__ == "__main__":
     app = IntegratedDashboard()
     app.run()