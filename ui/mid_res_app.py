import tkinter as tk
import json
import queue
import threading
import time


class OBD2Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("OBD2 Dashboard")
        self.root.configure(bg='black')
        self.root.geometry('1280x720')
        self.root.bind('<Escape>', lambda e: root.quit())

        # Queue for receiving data from OBD reader thread
        self.data_queue = queue.Queue(maxsize=1)

        # Load initial sample data with fallback
        self.current_data = {}

        # Main canvas
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind resize event
        self.canvas.bind('<Configure>', self.on_resize)

        self.draw_dashboard()
        self.root.after(500, lambda: self.root.wm_attributes('-fullscreen', 'true'))

        # Start update loop
        self.update_dashboard()

    def on_resize(self, event):
        self.draw_dashboard()

    def draw_dashboard(self):
        self.canvas.delete('all')

        width = self.canvas.winfo_width() or 1280
        height = self.canvas.winfo_height() or 720

        # Calculate center
        center_x = width // 2
        center_y = height // 2

        # Header
        elm_version = self.current_data.get('ELM_VERSION', {}).get('value', 'N/A')
        run_time = self.current_data.get('RUN_TIME', {}).get('value', '0 second')
        run_time_sec = run_time.replace(" second", "").strip()
        try:
            run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time_sec)))
        except:
            run_time = "00:00:00"

        self.canvas.create_text(center_x, 20, text=f"ELM: {elm_version}  |  Runtime: {run_time}",
                                fill='#00FF00', font=('Arial', 14))

        # Main speed display (top center)
        speed_val = float(self.current_data.get('SPEED', {}).get('value', '0').split()[0])
        self.canvas.create_text(center_x, 100, text=f"{int(speed_val)}",
                                fill='white', font=('Digital-7', 80, 'bold'))
        self.canvas.create_text(center_x, 155, text="KM/H",
                                fill='#888888', font=('Arial', 16))

        # Three main gauges (RPM, Load, Throttle)
        gauge_y = 280
        self.draw_rpm_gauge(center_x - 220, gauge_y)
        self.draw_engine_load(center_x, gauge_y)
        self.draw_throttle_position(center_x + 220, gauge_y)

        # Temperature bars (side by side, below gauges)
        temp_y = 420
        self.draw_temp_bar_horizontal(center_x - 180, temp_y, "COOLANT",
                                      self.current_data.get('COOLANT_TEMP', {}).get('value', '0'), 150)
        self.draw_temp_bar_horizontal(center_x + 180, temp_y, "INTAKE",
                                      self.current_data.get('INTAKE_TEMP', {}).get('value', '0'), 80)

        # Air/Fuel Ratio indicator (center, below temps)
        ratio_y = 500
        self.draw_equiv_ratio_indicator(center_x, ratio_y)

        # Bottom section
        bottom_y = height - 100

        # Bottom left - O2 Sensors
        self.draw_o2_sensors_compact(150, bottom_y)

        # Bottom center - Cylinder indicators
        self.draw_cylinder_indicators(center_x, bottom_y)

        # Bottom right - Voltage info
        self.draw_voltage_bars(width - 150, bottom_y)

        # Top corners info
        # Barometric pressure (top left)
        baro = self.current_data.get('BAROMETRIC_PRESSURE', {}).get('value', '0 kilopascal')
        baro_val = baro.split()[0]
        self.canvas.create_text(80, 50, text="BAROMETRIC", fill='#888888', font=('Arial', 10))
        self.canvas.create_text(80, 70, text=f"{baro_val} kPa", fill='#00FFFF', font=('Digital-7', 16))

    def draw_rpm_gauge(self, cx, cy):
        radius = 65
        rpm_val = float(self.current_data.get('RPM', {}).get('value', '0').split()[0])
        max_rpm = 8000

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=2)

        # Draw arc based on RPM
        extent = (rpm_val / max_rpm) * 270
        start_angle = 135

        # Determine color based on RPM
        if rpm_val < 3500:
            color = '#00FF00'
        elif rpm_val < 6000:
            color = '#FFFF00'
        else:
            color = '#FF0000'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 4, cy - radius + 4,
                                   cx + radius - 4, cy + radius - 4,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=6, style=tk.ARC)

        # Draw RPM value
        self.canvas.create_text(cx, cy - 8, text=f"{int(rpm_val)}",
                                fill='white', font=('Digital-7', 24, 'bold'))
        self.canvas.create_text(cx, cy + 15, text="RPM",
                                fill='#888888', font=('Arial', 10))

    def draw_engine_load(self, cx, cy):
        radius = 65
        load_val = float(self.current_data.get('ENGINE_LOAD', {}).get('value', '0').split()[0])

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=2)

        # Draw arc based on load
        extent = (load_val / 100) * 270
        start_angle = 135

        if load_val < 50:
            color = '#00FF00'
        elif load_val < 75:
            color = '#FFFF00'
        else:
            color = '#FF9900'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 4, cy - radius + 4,
                                   cx + radius - 4, cy + radius - 4,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=6, style=tk.ARC)

        # Draw load value
        self.canvas.create_text(cx, cy - 8, text=f"{int(load_val)}%",
                                fill='white', font=('Digital-7', 24, 'bold'))
        self.canvas.create_text(cx, cy + 15, text="ENGINE LOAD",
                                fill='#888888', font=('Arial', 10))

    def draw_throttle_position(self, cx, cy):
        radius = 65
        throttle_val = float(self.current_data.get('THROTTLE_POS', {}).get('value', '0').split()[0])

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=2)

        # Draw arc based on throttle
        extent = (throttle_val / 100) * 270
        start_angle = 135
        color = '#00BFFF'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 4, cy - radius + 4,
                                   cx + radius - 4, cy + radius - 4,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=6, style=tk.ARC)

        # Draw throttle value
        self.canvas.create_text(cx, cy - 8, text=f"{int(throttle_val)}%",
                                fill='white', font=('Digital-7', 24, 'bold'))
        self.canvas.create_text(cx, cy + 15, text="THROTTLE",
                                fill='#888888', font=('Arial', 10))

    def draw_temp_bar_horizontal(self, x, y, label, temp_str, max_temp):
        temp_val = float(temp_str.split()[0])
        bar_width = 180
        bar_height = 18

        # Label above
        self.canvas.create_text(x, y - 25, text=label,
                                fill='#888888', font=('Arial', 11, 'bold'))

        # Draw bar outline
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=2)

        # Calculate fill width and color
        fill_width = (temp_val / max_temp) * bar_width
        if fill_width > bar_width:
            fill_width = bar_width

        # Color based on temperature
        if label == "COOLANT":
            if temp_val > 90:
                color = '#FF0000'
            elif temp_val > 75:
                color = '#FFFF00'
            else:
                color = '#00FF00'
        else:  # INTAKE
            if temp_val > 50:
                color = '#FF0000'
            elif temp_val > 35:
                color = '#FFFF00'
            else:
                color = '#00FF00'

        # Draw filled bar
        if fill_width > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                         x - bar_width // 2 + fill_width, y + bar_height // 2,
                                         fill=color, outline='')

        # Draw temperature value below
        self.canvas.create_text(x, y + 25, text=f"{int(temp_val)}°C",
                                fill='white', font=('Digital-7', 16))

    def draw_equiv_ratio_indicator(self, cx, cy):
        ratio = self.current_data.get('COMMANDED_EQUIV_RATIO', {}).get('value', '1.0')
        ratio_val = float(ratio.replace("ratio", "").strip())

        # Determine status
        if ratio_val >= 1.1:
            color = "#FF0000"
        elif 1.1 > ratio_val >= 1.02:
            color = "#00FFFF"
        elif 1.01 > ratio_val >= 0.99:
            color = "#00FF00"
        elif 0.99 > ratio_val >= 0.95:
            color = "#00FFFF"
        else:
            color = "#FF0000"

        # Draw visual indicator bar
        bar_width = 300
        bar_height = 25

        self.canvas.create_text(cx, cy - 30, text="AIR/FUEL RATIO",
                                fill='#888888', font=('Arial', 12, 'bold'))

        # Draw gradient bar from lean to rich
        self.canvas.create_rectangle(cx - bar_width // 2, cy - bar_height // 2,
                                     cx + bar_width // 2, cy + bar_height // 2,
                                     outline='#333333', width=2)

        # Draw segments with labels
        segment_width = bar_width / 5
        colors = ['#FF0000', '#00FFFF', '#00FF00', '#00FFFF', '#FF0000']
        labels = ['LEAN', '~LEAN', 'STOICH', '~RICH', 'RICH']

        for i in range(5):
            seg_x = cx - bar_width // 2 + i * segment_width
            self.canvas.create_rectangle(seg_x, cy - bar_height // 2,
                                         seg_x + segment_width, cy + bar_height // 2,
                                         fill=colors[i], outline='#333333')
            # Add segment labels
            self.canvas.create_text(seg_x + segment_width // 2, cy,
                                    text=labels[i], fill='black',
                                    font=('Arial', 7, 'bold'))

        # Draw indicator position
        ratio_normalized = (ratio_val - 0.85) / (1.15 - 0.85)
        ratio_normalized = max(0, min(1, ratio_normalized))
        indicator_x = cx - bar_width // 2 + ratio_normalized * bar_width

        # Draw triangle indicator
        tri_size = 10
        self.canvas.create_polygon(
            indicator_x, cy - bar_height // 2 - tri_size,
                         indicator_x - tri_size, cy - bar_height // 2,
                         indicator_x + tri_size, cy - bar_height // 2,
            fill='white', outline='black', width=2
        )

        # Value and status below
        self.canvas.create_text(cx, cy + 30, text=f"{round(ratio_val, 3)}",
                                fill=color, font=('Digital-7', 14, 'bold'))

    def draw_o2_sensors_compact(self, x, y):
        o2_b1s1 = float(self.current_data.get('O2_B1S1', {}).get('value', '0').split()[0])
        o2_b2s1 = float(self.current_data.get('O2_B2S1', {}).get('value', '0').split()[0])

        # Header
        self.canvas.create_text(x, y - 45, text="O2 SENSORS",
                                fill='#888888', font=('Arial', 11, 'bold'))

        bar_width = 80
        bar_height = 12

        # B1S1
        self.canvas.create_text(x - 45, y - 15, text="B1S1",
                                fill='#888888', font=('Arial', 9))

        self.canvas.create_rectangle(x, y - 15 - bar_height // 2,
                                     x + bar_width, y - 15 + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (o2_b1s1 / 1.0) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x, y - 15 - bar_height // 2,
                                         x + fill_w, y - 15 + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width + 30, y - 15, text=f"{o2_b1s1:.3f}V",
                                fill='#00FF00', font=('Digital-7', 12))

        # B2S1
        self.canvas.create_text(x - 45, y + 15, text="B2S1",
                                fill='#888888', font=('Arial', 9))

        self.canvas.create_rectangle(x, y + 15 - bar_height // 2,
                                     x + bar_width, y + 15 + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (o2_b2s1 / 1.0) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x, y + 15 - bar_height // 2,
                                         x + fill_w, y + 15 + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width + 30, y + 15, text=f"{o2_b2s1:.3f}V",
                                fill='#00FF00', font=('Digital-7', 12))

    def draw_cylinder_indicators(self, cx, cy):
        self.canvas.create_text(cx, cy - 50, text="CYLINDER MISFIRE",
                                fill='#888888', font=('Arial', 12, 'bold'))

        cyl_spacing = 100

        for i, cyl_num in enumerate([1, 2]):
            x = cx - cyl_spacing // 2 + i * cyl_spacing

            # Get misfire data
            misfire_data = self.current_data.get(f'MONITOR_MISFIRE_CYLINDER_{cyl_num}', {}).get('value', '')
            is_passed = 'PASSED' in misfire_data

            # Draw piston indicator
            icon_color = '#00FF00' if is_passed else '#FF0000'

            # Circle
            self.canvas.create_oval(x - 25, cy - 25, x + 25, cy + 25,
                                    fill=icon_color, outline='white', width=2)

            # Cylinder number
            self.canvas.create_text(x, cy, text=str(cyl_num),
                                    fill='black', font=('Arial', 20, 'bold'))

            # Status text
            status = "PASS" if is_passed else "FAIL"
            status_color = '#00FF00' if is_passed else '#FF0000'
            self.canvas.create_text(x, cy + 40, text=status,
                                    fill=status_color, font=('Arial', 11, 'bold'))

    def draw_voltage_bars(self, x, y):
        control_voltage = self.current_data.get('CONTROL_MODULE_VOLTAGE', {}).get('value', '0 volt')
        elm_voltage = self.current_data.get('ELM_VOLTAGE', {}).get('value', '0 volt')

        control_val = float(control_voltage.split()[0])
        elm_val = float(elm_voltage.split()[0])

        # Header
        self.canvas.create_text(x, y - 45, text="VOLTAGE",
                                fill='#888888', font=('Arial', 11, 'bold'))

        bar_width = 70
        bar_height = 12
        max_voltage = 16

        # Control voltage bar
        self.canvas.create_text(x - bar_width // 2 - 35, y - 15, text="CTRL",
                                fill='#888888', font=('Arial', 9))
        self.canvas.create_rectangle(x - bar_width // 2, y - 15 - bar_height // 2,
                                     x + bar_width // 2, y - 15 + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (control_val / max_voltage) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y - 15 - bar_height // 2,
                                         x - bar_width // 2 + fill_w, y - 15 + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width // 2 + 25, y - 15, text=f"{control_val:.1f}V",
                                fill='#00FF00', font=('Digital-7', 12))

        # ELM voltage bar
        self.canvas.create_text(x - bar_width // 2 - 35, y + 15, text="ELM",
                                fill='#888888', font=('Arial', 9))
        self.canvas.create_rectangle(x - bar_width // 2, y + 15 - bar_height // 2,
                                     x + bar_width // 2, y + 15 + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (elm_val / max_voltage) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y + 15 - bar_height // 2,
                                         x - bar_width // 2 + fill_w, y + 15 + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width // 2 + 25, y + 15, text=f"{elm_val:.1f}V",
                                fill='#00FF00', font=('Digital-7', 12))

    def update_dashboard(self):
        """Check queue for new data and update dashboard"""
        try:
            while not self.data_queue.empty():
                self.current_data = self.data_queue.get_nowait()
                self.draw_dashboard()
        except queue.Empty:
            pass

        # Schedule next update (15 FPS)
        self.root.after(64, self.update_dashboard)

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
       with open("./sample.json", "r") as logs:
           data = json.load(logs)
       count = 0
       while True:
           # Simulate reading OBD data (replace with actual OBD reading)
           simulated_data = data[count]
           count += 1
           if count == len(data):
               count = 0

           dashboard.enqueue_data(simulated_data)
           time.sleep(0.11)


   # Start OBD reader thread (replace with your actual OBD reader)
   reader_thread = threading.Thread(target=obd_reader_thread, args=(dashboard,), daemon=True)
   reader_thread.start()

   root.mainloop()