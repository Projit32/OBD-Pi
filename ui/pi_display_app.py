import tkinter as tk
import json
import queue
import threading
import time


class OBD2Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("OBD2")
        self.root.configure(bg='black')
        self.root.geometry('480x320')
        # self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: root.quit())

        # Queue for receiving data from OBD reader thread
        self.data_queue = queue.Queue(maxsize=1)

        # Load initial sample data with fallback
        self.current_data = {}

        # Main canvas
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.draw_dashboard()

        self.root.after(500, lambda: self.root.wm_attributes('-fullscreen', 'true'))

        # Start update loop
        self.update_dashboard()


    def draw_dashboard(self):
        self.canvas.delete('all')

        width = 480
        height = 320

        # Header bar
        self.canvas.create_rectangle(0, 0, width, 20, fill='#1a1a1a', outline='')

        # Left header - ELM info
        elm_version = self.current_data.get('ELM_VERSION', {}).get('value', 'N/A')
        self.canvas.create_text(60, 10, text=f"ELM: {elm_version}",
                                fill='#00ffff', font=('Arial', 8))

        # Center header - Title
        self.canvas.create_text(width // 2, 10, text="OBD-II DASHBOARD",
                                fill='#00ff00', font=('Arial', 9, 'bold'))

        # Right header - Runtime
        run_time = self.current_data.get('RUN_TIME', {}).get('value', '0 second')
        run_time_sec = run_time.replace(" second", "").strip()
        try:
            run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time_sec)))
        except:
            run_time = "00:00:00"
        self.canvas.create_text(width - 40, 10, text=run_time,
                                fill='#00ffff', font=('Arial', 8))

        # === LEFT COLUMN ===
        # Speed display (large)
        speed_val = float(self.current_data.get('SPEED', {}).get('value', '0').split()[0])
        speed_color = self.get_speed_color(speed_val)

        self.canvas.create_rectangle(10, 30, 150, 120, fill='#1a1a1a', outline='#333333', width=1)
        self.canvas.create_text(80, 65, text=f"{int(speed_val)}",
                                fill=speed_color, font=('Digital-7', 40, 'bold'))
        self.canvas.create_text(80, 100, text="KM/H",
                                fill='#888888', font=('Arial', 9))

        # RPM with bar
        y_left = 130
        rpm_val = float(self.current_data.get('RPM', {}).get('value', '0').split()[0])
        self.draw_mini_row(10, y_left, "RPM", rpm_val, 8000, 130)

        # Engine Load
        y_left += 30
        load_val = float(self.current_data.get('ENGINE_LOAD', {}).get('value', '0').split()[0])
        self.draw_mini_row(10, y_left, "LOAD", load_val, 100, 130)

        # Throttle
        y_left += 30
        throttle_val = float(self.current_data.get('THROTTLE_POS', {}).get('value', '0').split()[0])
        self.draw_mini_row(10, y_left, "THRT", throttle_val, 100, 130)

        # Bottom left - Cylinder status
        y_left += 35
        self.canvas.create_text(25, y_left, text="CYL", fill='#888888', font=('Arial', 7))

        cyl1_data = self.current_data.get('MONITOR_MISFIRE_CYLINDER_1', {}).get('value', '')
        cyl2_data = self.current_data.get('MONITOR_MISFIRE_CYLINDER_2', {}).get('value', '')
        cyl1_ok = 'PASSED' in cyl1_data
        cyl2_ok = 'PASSED' in cyl2_data

        c1_color = '#00ff00' if cyl1_ok else '#ff0000'
        self.canvas.create_rectangle(45, y_left - 8, 65, y_left + 8, fill=c1_color, outline='')
        self.canvas.create_text(55, y_left, text="1", fill='black', font=('Arial', 10, 'bold'))

        c2_color = '#00ff00' if cyl2_ok else '#ff0000'
        self.canvas.create_rectangle(75, y_left - 8, 95, y_left + 8, fill=c2_color, outline='')
        self.canvas.create_text(85, y_left, text="2", fill='black', font=('Arial', 10, 'bold'))

        # === CENTER COLUMN ===
        # Temperature section
        y_center = 30
        self.canvas.create_text(240, y_center, text="🌡️ TEMPERATURE",
                                fill='#00ffff', font=('Arial', 8, 'bold'))

        y_center += 20

        # Coolant temp with bar
        coolant_val = float(self.current_data.get('COOLANT_TEMP', {}).get('value', '0').split()[0])
        self.draw_temp_bar(170, y_center, "COOL", coolant_val, 150, 130)

        y_center += 30

        # Intake temp with bar
        intake_val = float(self.current_data.get('INTAKE_TEMP', {}).get('value', '0').split()[0])
        self.draw_temp_bar(170, y_center, "INTK", intake_val, 80, 130)

        y_center += 40

        # Air/Fuel Ratio
        self.canvas.create_text(240, y_center, text="AIR/FUEL RATIO",
                                fill='#00ffff', font=('Arial', 8, 'bold'))
        y_center += 20

        ratio = self.current_data.get('COMMANDED_EQUIV_RATIO', {}).get('value', '1.0')
        ratio_val = float(ratio.replace("ratio", "").strip())
        self.draw_afr_bar(170, y_center, ratio_val, 140)

        y_center += 30

        # O2 Sensors
        self.canvas.create_text(240, y_center, text="O2 SENSORS",
                                fill='#00ffff', font=('Arial', 8, 'bold'))
        y_center += 15

        o2_b1s1 = float(self.current_data.get('O2_B1S1', {}).get('value', '0').split()[0])
        o2_b2s1 = float(self.current_data.get('O2_B2S1', {}).get('value', '0').split()[0])

        self.canvas.create_text(195, y_center, text="B1S1", fill='#888888', font=('Arial', 7))
        self.canvas.create_text(195, y_center + 12, text=f"{o2_b1s1:.2f}V",
                                fill='#00ff00', font=('Arial', 8, 'bold'))

        self.canvas.create_text(285, y_center, text="B2S1", fill='#888888', font=('Arial', 7))
        self.canvas.create_text(285, y_center + 12, text=f"{o2_b2s1:.2f}V",
                                fill='#00ff00', font=('Arial', 8, 'bold'))

        # === RIGHT COLUMN ===
        # Voltage section
        y_right = 30
        self.canvas.create_text(400, y_right, text="VOLTAGE ⚡️",
                                fill='#00ffff', font=('Arial', 8, 'bold'))

        y_right += 20

        control_voltage = self.current_data.get('CONTROL_MODULE_VOLTAGE', {}).get('value', '0 volt')
        control_val = float(control_voltage.split()[0])

        self.canvas.create_text(340, y_right, text="CTRL", fill='#888888', font=('Arial', 7))
        self.draw_voltage_bar(360, y_right, control_val, 16, 80)

        y_right += 25

        elm_voltage = self.current_data.get('ELM_VOLTAGE', {}).get('value', '0 volt')
        elm_val = float(elm_voltage.split()[0])

        self.canvas.create_text(340, y_right, text="ELM", fill='#888888', font=('Arial', 7))
        self.draw_voltage_bar(360, y_right, elm_val, 16, 80)

        # Barometric pressure
        y_right += 35
        self.canvas.create_text(400, y_right, text="BAROMETRIC",
                                fill='#00ffff', font=('Arial', 8, 'bold'))
        y_right += 15

        baro = self.current_data.get('BAROMETRIC_PRESSURE', {}).get('value', '0 kilopascal')
        baro_val = baro.split()[0]

        self.canvas.create_text(400, y_right, text=f"{baro_val}",
                                fill='#00ff00', font=('Digital-7', 16))
        self.canvas.create_text(400, y_right + 15, text="kPa",
                                fill='#888888', font=('Arial', 7))

    def get_speed_color(self, speed):
        """Get color based on speed"""
        if speed < 60:
            return '#00ff00'
        elif speed < 100:
            return '#ffff00'
        elif speed < 130:
            return '#ff9900'
        else:
            return '#ff0000'

    def draw_mini_row(self, x, y, label, value, max_val, bar_width):
        """Draw a compact row with label, bar, and value"""
        # Label
        self.canvas.create_text(x + 20, y, text=label,
                                fill='#888888', font=('Arial', 7, 'bold'))

        # Bar
        bar_height = 10
        bar_x = x + 45

        # Background
        self.canvas.create_rectangle(bar_x, y - bar_height // 2,
                                     bar_x + bar_width - 50, y + bar_height // 2,
                                     fill='#0a0a0a', outline='#333333', width=1)

        # Fill
        fill_width = (value / max_val) * (bar_width - 50)
        if fill_width > bar_width - 50:
            fill_width = bar_width - 50

        # Determine color
        if label == "RPM":
            if value < 3500:
                color = '#00ff00'
            elif value < 6000:
                color = '#ffff00'
            else:
                color = '#ff0000'
        else:
            if value < 50:
                color = '#00ff00'
            elif value < 75:
                color = '#ffff00'
            else:
                color = '#ff9900'

        if fill_width > 0:
            self.canvas.create_rectangle(bar_x, y - bar_height // 2,
                                         bar_x + fill_width, y + bar_height // 2,
                                         fill=color, outline='')

        # Value
        self.canvas.create_text(x + bar_width, y, text=f"{int(value)}",
                                fill=color, font=('Arial', 8, 'bold'))

    def draw_temp_bar(self, x, y, label, value, max_val, bar_width):
        """Draw temperature bar"""
        # Label
        self.canvas.create_text(x + 20, y, text=label,
                                fill='#888888', font=('Arial', 7, 'bold'))

        # Bar
        bar_height = 10
        bar_x = x + 45

        # Background
        self.canvas.create_rectangle(bar_x, y - bar_height // 2,
                                     bar_x + bar_width - 50, y + bar_height // 2,
                                     fill='#0a0a0a', outline='#333333', width=1)

        # Fill
        fill_width = (value / max_val) * (bar_width - 50)
        if fill_width > bar_width - 50:
            fill_width = bar_width - 50

        # Color
        if label == "COOL":
            if value > 90:
                color = '#ff0000'
            elif value > 75:
                color = '#ffff00'
            else:
                color = '#00ff00'
        else:
            if value > 50:
                color = '#ff0000'
            elif value > 35:
                color = '#ffff00'
            else:
                color = '#00ff00'

        if fill_width > 0:
            self.canvas.create_rectangle(bar_x, y - bar_height // 2,
                                         bar_x + fill_width, y + bar_height // 2,
                                         fill=color, outline='')

        # Value
        self.canvas.create_text(x + bar_width + 10, y, text=f"{int(value)}°",
                                fill=color, font=('Arial', 8, 'bold'))

    def draw_afr_bar(self, x, y, ratio_val, bar_width):
        """Draw air/fuel ratio bar"""
        bar_height = 14
        bar_x = x + 20

        # Draw 5 segments
        segment_width = (bar_width - 20) / 5
        colors = ['#ff0000', '#00ffff', '#00ff00', '#00ffff', '#ff0000']

        for i in range(5):
            seg_x = bar_x + i * segment_width
            self.canvas.create_rectangle(seg_x, y - bar_height // 2,
                                         seg_x + segment_width, y + bar_height // 2,
                                         fill=colors[i], outline='#000000', width=1)

        # Indicator triangle
        ratio_normalized = (ratio_val - 0.85) / (1.15 - 0.85)
        ratio_normalized = max(0, min(1, ratio_normalized))
        indicator_x = bar_x + ratio_normalized * (bar_width - 20)

        self.canvas.create_polygon(
            indicator_x, y - bar_height // 2 - 6,
                         indicator_x - 5, y - bar_height // 2,
                         indicator_x + 5, y - bar_height // 2,
            fill='white', outline='black', width=1
        )

        # Status
        if ratio_val >= 1.1:
            meaning = "L"
            color = "#ff0000"
        elif ratio_val >= 1.02:
            meaning = "~L"
            color = "#00ffff"
        elif ratio_val >= 0.99:
            meaning = "OK"
            color = "#00ff00"
        elif ratio_val >= 0.95:
            meaning = "~R"
            color = "#00ffff"
        else:
            meaning = "R"
            color = "#ff0000"

        # Value display below bar
        self.canvas.create_text(x + bar_width // 2, y + 15,
                                text=f"{ratio_val:.2f} {meaning}",
                                fill=color, font=('Arial', 8, 'bold'))

    def draw_voltage_bar(self, x, y, value, max_val, bar_width):
        """Draw voltage bar"""
        bar_height = 8

        # Background
        self.canvas.create_rectangle(x, y - bar_height // 2,
                                     x + bar_width, y + bar_height // 2,
                                     fill='#0a0a0a', outline='#333333', width=1)

        # Fill
        fill_width = (value / max_val) * bar_width
        if fill_width > bar_width:
            fill_width = bar_width

        color = '#00ff00' if value > 12.5 else '#ffff00' if value > 11.5 else '#ff0000'

        if fill_width > 0:
            self.canvas.create_rectangle(x, y - bar_height // 2,
                                         x + fill_width, y + bar_height // 2,
                                         fill=color, outline='')

        # Value
        self.canvas.create_text(x + bar_width + 20, y, text=f"{value:.1f}V",
                                fill=color, font=('Arial', 8, 'bold'))

    def update_dashboard(self):
        """Check queue for new data and update dashboard"""
        try:
            while not self.data_queue.empty():
                self.current_data = self.data_queue.get_nowait()
                self.draw_dashboard()
        except queue.Empty:
            pass

        self.root.after(32, self.update_dashboard)

    def enqueue_data(self, data):
        """Thread-safe method to add data to queue"""
        try:
            self.data_queue.put(data, block=False)
        except queue.Full:
            pass

if __name__ == "__main__":

   root = tk.Tk()
   dashboard = OBD2Dashboard(root)

   # Example OBD reader thread function
   def obd_reader_thread(dashboard):
       """Simulated OBD reader that sends data to dashboard"""
       with open("./new-sample.json", "r") as logs:
           data = json.load(logs)
       count = 0
       while True:
           # Simulate reading OBD data (replace with actual OBD reading)
           simulated_data = data[count]
           count += 1
           if count == len(data):
               count = 0

           dashboard.enqueue_data(simulated_data)
           time.sleep(0.32)


   # Start OBD reader thread (replace with your actual OBD reader)
   reader_thread = threading.Thread(target=obd_reader_thread, args=(dashboard,), daemon=True)
   reader_thread.start()

   root.mainloop()