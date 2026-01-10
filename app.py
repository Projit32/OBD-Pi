import obd
import json
import tkinter as tk
import threading
import queue
import time
from ui import OBDDashboard

class OBDDataReader:
    def __init__(self, data_queue):
        """Initialize OBD reader with a queue for data sharing"""
        self.data_queue = data_queue
        self.connection = None
        self.running = False

        # Load commands from JSON
        with open("./commands.json", "r") as file:
            self.commands_file = json.load(file)

    def connect(self):
        """Establish connection to OBD interface"""
        try:
            self.connection = obd.OBD()
            if self.connection.is_connected():
                print(f"Connected to: {self.connection.port_name()}")
                return True
            else:
                print("Failed to connect to OBD2 interface!")
                return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def fetch_data(self):
        """Fetch sensor data and put it in the queue"""
        for cmd in self.commands_file.keys():
            try:
                response = self.connection.query(obd.commands[cmd])
                if not response.is_null():
                    if response.value is not None:
                        sensor_data= {
                            "value": str(response.value),
                            "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
                        }
                        self.data_queue.put((cmd, sensor_data))
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
        self.dashboard = OBDDashboard(self.root)
        self.data_queue = queue.Queue()
        self.reader = OBDDataReader(self.data_queue)
        self.reader_thread = None

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_reader_thread(self):
        """Start the OBD reader in a separate thread"""
        self.reader_thread = threading.Thread(target=self.reader.run, daemon=True)
        self.reader_thread.start()
        print("OBD reader thread started")

    def update_ui(self):
        """Update UI with data from queue"""
        try:
            # Get all available data from queue (non-blocking)
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                self.dashboard.update_from_sensor(data)
        except queue.Empty:
            pass

        # Schedule next update (every 50ms for smooth UI)
        self.root.after(5, self.update_ui)

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

            # Start UI update loop
            self.root.after(100, self.update_ui)

            # Start Tkinter main loop
            self.root.mainloop()
        else:
            print("Failed to connect to OBD interface. Exiting...")
            # Optionally, you can still start the UI with sample data
            # self.root.mainloop()


if __name__ == "__main__":
    app = IntegratedDashboard()
    app.run()