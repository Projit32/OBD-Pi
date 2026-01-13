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
        self.root.bind('<Escape>', lambda e: root.quit())

        # Queue for receiving data from OBD reader thread
        self.data_queue = queue.Queue(maxsize=1)

        # Load initial sample data

        self.current_data= {}

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

        width = self.canvas.winfo_width() or 1920
        height = self.canvas.winfo_height() or 1080

        # Header info (ELM Version and Runtime)
        elm_version = self.current_data.get('ELM_VERSION', {}).get('value', 'N/A')
        run_time = self.current_data.get('RUN_TIME', {}).get('value', '0 second')
        run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time.replace(" second","").strip())))
        self.canvas.create_text(width // 2, 40, text=f"ELM: {elm_version}  |  Runtime: {run_time}",
                                fill='#00FF00', font=('Digital-7', 24), tags='header')

        # Main speed display (center)
        speed_val = float(self.current_data.get('SPEED', {}).get('value', '0').split()[0])
        self.canvas.create_text(width // 2, height // 2 - 50, text=f"{int(speed_val)}",
                                fill='white', font=('Digital-7', 120, 'bold'), tags='speed')
        self.canvas.create_text(width // 2, height // 2 + 50, text="KM/H",
                                fill='#888888', font=('Arial', 24), tags='speed_unit')

        # RPM gauge (left side, below speed)
        rpm_x = width // 2 - 300
        rpm_y = height // 2 + 180
        self.draw_rpm_gauge(rpm_x, rpm_y)

        # Engine Load (circular gauge, right of RPM)
        load_x = width // 2
        load_y = height // 2 + 180
        self.draw_engine_load(load_x, load_y)

        # Throttle Position (circular gauge, right of Engine Load)
        throttle_x = width // 2 + 300
        throttle_y = height // 2 + 180
        self.draw_throttle_position(throttle_x, throttle_y)

        # Coolant temp bar (right side)
        self.draw_coolant_temp(width - 100, height // 2)

        # Intake temp bar (right side, next to coolant)
        self.draw_intake_temp(width - 200, height // 2)

        # Oxygen sensors (bottom left)
        self.draw_o2_sensors(150, height - 150)

        # Cylinder misfire indicators (bottom center)
        self.draw_cylinder_indicators(width // 2, height - 150)

        # Battery/voltage info (bottom right)
        self.draw_voltage_info(width - 200, height - 150)

        # Barometric pressure (top left)
        baro = self.current_data.get('BAROMETRIC_PRESSURE', {}).get('value', '0')
        self.canvas.create_text(160, 100, text=f"Barometric",
                                fill='#888888', font=('Arial', 14), tags='baro')
        self.canvas.create_text(160, 130, text=f"{baro}",
                                fill='#00FFFF', font=('Digital-7', 24))

        # Commanded Equiv Ratio (top right)
        ratio = self.current_data.get('COMMANDED_EQUIV_RATIO', {}).get('value', '0')
        self.canvas.create_text(width - 160, 100, text=f"Equiv Ratio",
                                fill='#888888', font=('Arial', 14), tags='ratio')
        ratio = float(ratio.replace("ratio", "").strip())
        meaning = "N/A"
        color = "#888888"

        if ratio >= 1.1:
            meaning = "LEAN"
            color = "#FF0000"

        elif 1.1 > ratio >= 1.02:
            meaning = "~LEAN"
            color = "#00FFFF"

        elif 1.01 > ratio >= 0.99:
            meaning = "STOICHIOMETRIC"
            color = "#00FF00"

        elif 0.99 > ratio >= 0.95:
            meaning = "~RICH"
            color = "#00FFFF"

        elif 0.95 > ratio >= 0.85:
            meaning = "RICH"
            color = "#FF0000"


        self.canvas.create_text(width - 160, 130, text=f"{round(ratio, 2)} ({meaning})",
                                fill=color, font=('Digital-7', 24))

    def draw_rpm_gauge(self, cx, cy):
        radius = 80
        rpm_val = float(self.current_data.get('RPM', {}).get('value', '0').split()[0])
        max_rpm = 8000

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=3)

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
            self.canvas.create_arc(cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=8, style=tk.ARC)

        # Draw RPM value
        self.canvas.create_text(cx, cy - 10, text=f"{int(rpm_val)}",
                                fill='white', font=('Digital-7', 32, 'bold'))
        self.canvas.create_text(cx, cy + 20, text="RPM",
                                fill='#888888', font=('Arial', 12))

    def draw_engine_load(self, cx, cy):
        radius = 80
        load_val = float(self.current_data.get('ENGINE_LOAD', {}).get('value', '0').split()[0])

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=3)

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
            self.canvas.create_arc(cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=8, style=tk.ARC)

        # Draw load value
        self.canvas.create_text(cx, cy - 10, text=f"{int(load_val)}%",
                                fill='white', font=('Digital-7', 28, 'bold'))
        self.canvas.create_text(cx, cy + 20, text="ENGINE LOAD",
                                fill='#888888', font=('Arial', 11))

    def draw_throttle_position(self, cx, cy):
        radius = 80
        throttle_val = float(self.current_data.get('THROTTLE_POS', {}).get('value', '0').split()[0])

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=3)

        # Draw arc based on throttle
        extent = (throttle_val / 100) * 270
        start_angle = 135

        color = '#00BFFF'  # Sky blue for throttle

        if extent > 0:
            self.canvas.create_arc(cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=8, style=tk.ARC)

        # Draw throttle value
        self.canvas.create_text(cx, cy - 10, text=f"{int(throttle_val)}%",
                                fill='white', font=('Digital-7', 28, 'bold'))
        self.canvas.create_text(cx, cy + 20, text="THROTTLE",
                                fill='#888888', font=('Arial', 11))

    def draw_coolant_temp(self, x, y):
        temp_val = float(self.current_data.get('COOLANT_TEMP', {}).get('value', '0').split()[0])
        max_temp = 150
        bar_height = 300
        bar_width = 30

        # Draw thermometer icon
        self.canvas.create_text(x, y - bar_height // 2 - 40, text="🌡️",
                                fill='white', font=('Arial', 24))
        self.canvas.create_text(x, y - bar_height // 2 - 70, text="COOLANT",
                                fill='#888888', font=('Arial', 12))

        # Draw bar outline
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=2)

        # Calculate fill height and color
        fill_height = (temp_val / max_temp) * bar_height
        if fill_height > bar_height:
            fill_height = bar_height

        if temp_val > 90:
            color = '#FF0000'
        elif temp_val > 75:
            color = '#FFFF00'
        else:
            color = '#00FF00'

        # Draw filled bar
        if fill_height > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y + bar_height // 2,
                                         x + bar_width // 2, y + bar_height // 2 - fill_height,
                                         fill=color, outline='')

        # Draw temperature value
        self.canvas.create_text(x, y + bar_height // 2 + 30, text=f"{int(temp_val)}°C",
                                fill='white', font=('Digital-7', 20))

    def draw_intake_temp(self, x, y):
        temp_val = float(self.current_data.get('INTAKE_TEMP', {}).get('value', '0').split()[0])
        max_temp = 80
        bar_height = 300
        bar_width = 30

        # Draw thermometer icon
        self.canvas.create_text(x, y - bar_height // 2 - 40, text="🌡️",
                                fill='white', font=('Arial', 24))
        self.canvas.create_text(x, y - bar_height // 2 - 70, text="INTAKE",
                                fill='#888888', font=('Arial', 12))

        # Draw bar outline
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=2)

        # Calculate fill height and color
        fill_height = (temp_val / max_temp) * bar_height
        if fill_height > bar_height:
            fill_height = bar_height

        if temp_val > 50:
            color = '#FF0000'
        elif temp_val > 35:
            color = '#FFFF00'
        else:
            color = '#00FF00'

        # Draw filled bar
        if fill_height > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y + bar_height // 2,
                                         x + bar_width // 2, y + bar_height // 2 - fill_height,
                                         fill=color, outline='')

        # Draw temperature value
        self.canvas.create_text(x, y + bar_height // 2 + 30, text=f"{int(temp_val)}°C",
                                fill='white', font=('Digital-7', 20))

    def draw_o2_sensors(self, x, y):
        o2_b1s1 = float(self.current_data.get('O2_B1S1', {}).get('value', '0').split()[0])
        o2_b2s1 = float(self.current_data.get('O2_B2S1', {}).get('value', '0').split()[0])

        # B1S1
        self.canvas.create_text(x, y - 40, text="O2 B1S1",
                                fill='#888888', font=('Arial', 11))
        self.canvas.create_text(x, y, text=f"{o2_b1s1:.3f}V",
                                fill='#00FF00', font=('Digital-7', 24))

        # B2S1
        self.canvas.create_text(x, y + 40, text="O2 B2S1",
                                fill='#888888', font=('Arial', 11))
        self.canvas.create_text(x, y + 80, text=f"{o2_b2s1:.3f}V",
                                fill='#00FF00', font=('Digital-7', 24))

    def draw_cylinder_indicators(self, cx, cy):
        # Header
        self.canvas.create_text(cx, cy - 80, text="CYLINDER MISFIRE",
                                fill='#888888', font=('Arial', 14, 'bold'))

        cyl_spacing = 150

        for i, cyl_num in enumerate([1, 2]):
            x = cx - cyl_spacing // 2 + i * cyl_spacing

            # Get misfire data
            misfire_data = self.current_data.get(f'MONITOR_MISFIRE_CYLINDER_{cyl_num}', {}).get('value', '')
            is_passed = 'PASSED' in misfire_data

            # Draw piston icon (simplified)
            icon_color = '#00FF00' if is_passed else '#FF0000'

            # Piston circle
            self.canvas.create_oval(x - 30, cy - 30, x + 30, cy + 30,
                                    fill=icon_color, outline='white', width=2)

            # Cylinder number
            self.canvas.create_text(x, cy, text=str(cyl_num),
                                    fill='black', font=('Arial', 24, 'bold'))

            # Status text
            status = "PASS" if is_passed else "FAIL"
            status_color = '#00FF00' if is_passed else '#FF0000'
            self.canvas.create_text(x, cy + 50, text=status,
                                    fill=status_color, font=('Arial', 12, 'bold'))

    def draw_voltage_info(self, x, y):
        control_voltage = self.current_data.get('CONTROL_MODULE_VOLTAGE', {}).get('value', '0')
        elm_voltage = self.current_data.get('ELM_VOLTAGE', {}).get('value', '0')

        # Battery icon
        self.canvas.create_text(x, y - 60, text="🔋",
                                fill='white', font=('Arial', 32))

        # Control voltage
        self.canvas.create_text(x, y, text="CONTROL MODULE",
                                fill='#888888', font=('Arial', 11))
        self.canvas.create_text(x, y + 25, text=control_voltage,
                                fill='#00FF00', font=('Digital-7', 20))

        # ELM voltage
        self.canvas.create_text(x, y + 50, text="ELM",
                                fill='#888888', font=('Arial', 11))
        self.canvas.create_text(x, y + 75, text=elm_voltage,
                                fill='#00FF00', font=('Digital-7', 20))

    def update_dashboard(self):
        """Check queue for new data and update dashboard"""
        try:
            # Get all available data from queue (non-blocking)
            while not self.data_queue.empty():
                self.current_data = self.data_queue.get_nowait()
                self.draw_dashboard()
        except queue.Empty:
            pass

        # Schedule next update (15 FPS)
        self.root.after(64, self.update_dashboard)

    def enqueue_data(self, data):
        """Thread-safe method to add data to queue"""
        self.data_queue.put(data)


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