import tkinter as tk
import json
import queue
import threading
import time
import random
import math


class OBD2Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("OBD2 Dashboard")
        self.root.configure(bg='black')
        self.root.geometry('1920x1080')
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: root.quit())

        # Queue for receiving data from OBD reader thread
        self.data_queue = queue.Queue(maxsize=1)

        # Load initial sample data with fallback
        try:
            with open('../sample.json', 'r') as f:
                self.current_data = json.load(f)
        except:
            self.current_data = self.get_default_data()

        # Main canvas
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind resize event
        self.canvas.bind('<Configure>', self.on_resize)

        self.draw_dashboard()

        # Start update loop
        self.update_dashboard()

    def get_default_data(self):
        """Provide default data structure"""
        return {
            "SPEED": {"value": "0 kilometer_per_hour"},
            "RPM": {"value": "0 revolutions_per_minute"},
            "COOLANT_TEMP": {"value": "0 degree_Celsius"},
            "ENGINE_LOAD": {"value": "0 percent"},
            "THROTTLE_POS": {"value": "0 percent"},
            "INTAKE_TEMP": {"value": "0 degree_Celsius"},
            "O2_B1S1": {"value": "0 volt"},
            "O2_B2S1": {"value": "0 volt"},
            "ELM_VERSION": {"value": "N/A"},
            "RUN_TIME": {"value": "0 second"},
            "BAROMETRIC_PRESSURE": {"value": "0 kilopascal"},
            "CONTROL_MODULE_VOLTAGE": {"value": "0 volt"},
            "ELM_VOLTAGE": {"value": "0 volt"},
            "COMMANDED_EQUIV_RATIO": {"value": "1.0 ratio"},
            "MONITOR_MISFIRE_CYLINDER_1": {"value": "PASSED"},
            "MONITOR_MISFIRE_CYLINDER_2": {"value": "PASSED"}
        }

    def on_resize(self, event):
        self.draw_dashboard()

    def draw_dashboard(self):
        self.canvas.delete('all')

        width = self.canvas.winfo_width() or 1920
        height = self.canvas.winfo_height() or 1080
        center_x = width // 2
        center_y = height // 2

        # Header bar
        self.canvas.create_rectangle(0, 0, width, 60, fill='#0d0d0d', outline='')
        self.canvas.create_line(0, 60, width, 60, fill='#00ffff', width=2)

        self.canvas.create_text(center_x, 30, text=f"◆ OBD-II DIAGNOSTICS SYSTEM ◆",
                                fill='#00ffff', font=('Arial', 18, 'bold'))

        # ELM Version
        elm_version = self.current_data.get('ELM_VERSION', {}).get('value', 'N/A')
        self.canvas.create_text(150, 30, text=f"ELM: {elm_version}",
                                fill='#888888', font=('Courier', 12))

        # Runtime
        run_time = self.current_data.get('RUN_TIME', {}).get('value', '0 second')
        run_time_sec = run_time.replace(" second", "").strip()
        try:
            run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time_sec)))
        except:
            run_time = "00:00:00"
        self.canvas.create_text(width - 150, 30, text=f"⏱ {run_time}",
                                fill='#888888', font=('Courier', 12))

        # Main speed display (top center)
        speed_val = float(self.current_data.get('SPEED', {}).get('value', '0').split()[0])
        speed_color = self.get_speed_color(speed_val)

        self.draw_bordered_panel(center_x, 180, 400, 180, '#00ffff')
        self.canvas.create_text(center_x, 150, text=f"{int(speed_val)}",
                                fill=speed_color, font=('Digital-7', 100, 'bold'))
        self.canvas.create_text(center_x, 220, text="KM/H",
                                fill='#888888', font=('Arial', 20))

        # Three main circular gauges
        gauge_y = 450
        self.draw_enhanced_rpm_gauge(center_x - 400, gauge_y)
        self.draw_enhanced_engine_load(center_x, gauge_y)
        self.draw_enhanced_throttle(center_x + 400, gauge_y)

        # Temperature displays (below gauges)
        temp_y = 680
        self.draw_vertical_temp_gauge(center_x - 400, temp_y, "COOLANT",
                                      self.current_data.get('COOLANT_TEMP', {}).get('value', '0'), 150)
        self.draw_vertical_temp_gauge(center_x, temp_y, "INTAKE",
                                      self.current_data.get('INTAKE_TEMP', {}).get('value', '0'), 80)

        # Air/Fuel Ratio (replaces one temp gauge)
        self.draw_afr_gauge(center_x + 400, temp_y)

        # Bottom section - data cards
        bottom_y = height - 150

        # Left card - O2 Sensors
        self.draw_data_card(250, bottom_y, "OXYGEN SENSORS")
        self.draw_o2_waveform(250, bottom_y + 20)

        # Center card - Cylinder Status
        self.draw_data_card(center_x, bottom_y, "CYLINDER STATUS")
        self.draw_cylinder_status(center_x, bottom_y + 20)

        # Right card - System Voltage
        self.draw_data_card(width - 250, bottom_y, "SYSTEM VOLTAGE")
        self.draw_voltage_meters(width - 250, bottom_y + 20)

        # Corner indicators
        # Top left - Barometric Pressure
        baro = self.current_data.get('BAROMETRIC_PRESSURE', {}).get('value', '0 kilopascal')
        baro_val = baro.split()[0]
        self.draw_corner_info(150, 120, "BAROMETRIC", f"{baro_val} kPa", '#00ffff')

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

    def draw_bordered_panel(self, x, y, w, h, border_color):
        """Draw a panel with border only"""
        self.canvas.create_rectangle(x - w // 2, y - h // 2,
                                     x + w // 2, y + h // 2,
                                     outline=border_color, width=2)

    def draw_enhanced_rpm_gauge(self, cx, cy):
        """Enhanced RPM gauge with tick marks"""
        radius = 100
        rpm_val = float(self.current_data.get('RPM', {}).get('value', '0').split()[0])
        max_rpm = 8000

        # Title
        self.canvas.create_text(cx, cy - 150, text="RPM",
                                fill='#888888', font=('Arial', 14, 'bold'))

        # Draw tick marks
        for i in range(0, 9):
            angle = 135 + (i * 270 / 8)
            rad = math.radians(angle)
            x1 = cx + (radius - 10) * math.cos(rad)
            y1 = cy - (radius - 10) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy - radius * math.sin(rad)

            tick_color = '#00ff00' if i < 4 else '#ffff00' if i < 7 else '#ff0000'
            self.canvas.create_line(x1, y1, x2, y2, fill=tick_color, width=3)

            # RPM labels
            label_x = cx + (radius + 25) * math.cos(rad)
            label_y = cy - (radius + 25) * math.sin(rad)
            self.canvas.create_text(label_x, label_y, text=str(i * 1000),
                                    fill='#666666', font=('Arial', 10))

        # Outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=3)

        # Arc indicator
        extent = (rpm_val / max_rpm) * 270
        start_angle = 135

        if rpm_val < 3500:
            color = '#00ff00'
        elif rpm_val < 6000:
            color = '#ffff00'
        else:
            color = '#ff0000'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 8, cy - radius + 8,
                                   cx + radius - 8, cy + radius - 8,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=12, style=tk.ARC)

        # Center display
        self.canvas.create_oval(cx - 55, cy - 55, cx + 55, cy + 55,
                                outline=color, width=2)
        self.canvas.create_text(cx, cy - 15, text=f"{int(rpm_val)}",
                                fill='white', font=('Digital-7', 32, 'bold'))
        self.canvas.create_text(cx, cy + 15, text="rpm",
                                fill='#666666', font=('Arial', 10))

    def draw_enhanced_engine_load(self, cx, cy):
        """Enhanced engine load gauge"""
        radius = 100
        load_val = float(self.current_data.get('ENGINE_LOAD', {}).get('value', '0').split()[0])

        # Title
        self.canvas.create_text(cx, cy - 150, text="ENGINE LOAD",
                                fill='#888888', font=('Arial', 14, 'bold'))

        # Draw tick marks
        for i in range(0, 11):
            angle = 135 + (i * 270 / 10)
            rad = math.radians(angle)
            x1 = cx + (radius - 10) * math.cos(rad)
            y1 = cy - (radius - 10) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy - radius * math.sin(rad)

            tick_color = '#00ff00' if i < 5 else '#ffff00' if i < 8 else '#ff9900'
            self.canvas.create_line(x1, y1, x2, y2, fill=tick_color, width=2)

            # Percentage labels every 25%
            if i % 3 == 0:
                label_x = cx + (radius + 25) * math.cos(rad)
                label_y = cy - (radius + 25) * math.sin(rad)
                self.canvas.create_text(label_x, label_y, text=f"{i * 10}%",
                                        fill='#666666', font=('Arial', 10))

        # Outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=3)

        # Arc indicator
        extent = (load_val / 100) * 270
        start_angle = 135

        if load_val < 50:
            color = '#00ff00'
        elif load_val < 75:
            color = '#ffff00'
        else:
            color = '#ff9900'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 8, cy - radius + 8,
                                   cx + radius - 8, cy + radius - 8,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=12, style=tk.ARC)

        # Center display
        self.canvas.create_oval(cx - 55, cy - 55, cx + 55, cy + 55,
                                outline=color, width=2)
        self.canvas.create_text(cx, cy - 15, text=f"{int(load_val)}",
                                fill='white', font=('Digital-7', 32, 'bold'))
        self.canvas.create_text(cx, cy + 15, text="%",
                                fill='#666666', font=('Arial', 10))

    def draw_enhanced_throttle(self, cx, cy):
        """Enhanced throttle position gauge"""
        radius = 100
        throttle_val = float(self.current_data.get('THROTTLE_POS', {}).get('value', '0').split()[0])

        # Title
        self.canvas.create_text(cx, cy - 150, text="THROTTLE POSITION",
                                fill='#888888', font=('Arial', 14, 'bold'))

        # Draw tick marks
        for i in range(0, 11):
            angle = 135 + (i * 270 / 10)
            rad = math.radians(angle)
            x1 = cx + (radius - 10) * math.cos(rad)
            y1 = cy - (radius - 10) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy - radius * math.sin(rad)

            self.canvas.create_line(x1, y1, x2, y2, fill='#00bfff', width=2)

            # Percentage labels
            if i % 3 == 0:
                label_x = cx + (radius + 25) * math.cos(rad)
                label_y = cy - (radius + 25) * math.sin(rad)
                self.canvas.create_text(label_x, label_y, text=f"{i * 10}%",
                                        fill='#666666', font=('Arial', 10))

        # Outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=3)

        # Arc indicator
        extent = (throttle_val / 100) * 270
        start_angle = 135
        color = '#00bfff'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 8, cy - radius + 8,
                                   cx + radius - 8, cy + radius - 8,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=12, style=tk.ARC)

        # Center display
        self.canvas.create_oval(cx - 55, cy - 55, cx + 55, cy + 55,
                                outline=color, width=2)
        self.canvas.create_text(cx, cy - 15, text=f"{int(throttle_val)}",
                                fill='white', font=('Digital-7', 32, 'bold'))
        self.canvas.create_text(cx, cy + 15, text="%",
                                fill='#666666', font=('Arial', 10))

    def draw_vertical_temp_gauge(self, x, y, label, temp_str, max_temp):
        """Draw vertical thermometer-style temperature gauge"""
        temp_val = float(temp_str.split()[0])

        # Title
        self.canvas.create_text(x, y - 100, text=label,
                                fill='#888888', font=('Arial', 12, 'bold'))

        # Thermometer body
        bar_width = 40
        bar_height = 120

        # Background
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=2)

        # Scale marks
        for i in range(5):
            mark_y = y - bar_height // 2 + (i * bar_height / 4)
            self.canvas.create_line(x + bar_width // 2, mark_y,
                                    x + bar_width // 2 + 5, mark_y,
                                    fill='#666666', width=1)
            temp_mark = int(max_temp - (i * max_temp / 4))
            self.canvas.create_text(x + bar_width // 2 + 20, mark_y,
                                    text=f"{temp_mark}°", fill='#666666',
                                    font=('Arial', 9))

        # Fill
        fill_height = (temp_val / max_temp) * bar_height
        if fill_height > bar_height:
            fill_height = bar_height

        # Color
        if label == "COOLANT":
            if temp_val > 90:
                color = '#ff0000'
            elif temp_val > 75:
                color = '#ffff00'
            else:
                color = '#00ff00'
        else:
            if temp_val > 50:
                color = '#ff0000'
            elif temp_val > 35:
                color = '#ffff00'
            else:
                color = '#00ff00'

        if fill_height > 0:
            self.canvas.create_rectangle(x - bar_width // 2 + 2, y + bar_height // 2 - 2,
                                         x + bar_width // 2 - 2, y + bar_height // 2 - fill_height,
                                         fill=color, outline='')

        # Value display
        self.canvas.create_text(x, y + bar_height // 2 + 30, text=f"{int(temp_val)}°C",
                                fill=color, font=('Digital-7', 24, 'bold'))

    def draw_afr_gauge(self, x, y):
        """Draw air/fuel ratio as a gauge"""
        ratio = self.current_data.get('COMMANDED_EQUIV_RATIO', {}).get('value', '1.0')
        ratio_val = float(ratio.replace("ratio", "").strip())

        # Title
        self.canvas.create_text(x, y - 100, text="AIR/FUEL RATIO",
                                fill='#888888', font=('Arial', 12, 'bold'))

        # Horizontal bar gauge
        bar_width = 200
        bar_height = 30

        # Draw segments
        segment_width = bar_width / 5
        colors = ['#ff0000', '#ffaa00', '#00ff00', '#ffaa00', '#ff0000']
        labels = ['LEAN', '', 'STOICH', '', 'RICH']

        for i in range(5):
            seg_x = x - bar_width // 2 + i * segment_width
            self.canvas.create_rectangle(seg_x, y - bar_height // 2,
                                         seg_x + segment_width, y + bar_height // 2,
                                         fill=colors[i], outline='#333333', width=1)
            if labels[i]:
                self.canvas.create_text(seg_x + segment_width // 2, y,
                                        text=labels[i], fill='black',
                                        font=('Arial', 9, 'bold'))

        # Border
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#666666', width=2)

        # Indicator needle
        ratio_normalized = (ratio_val - 0.85) / (1.15 - 0.85)
        ratio_normalized = max(0, min(1, ratio_normalized))
        indicator_x = x - bar_width // 2 + ratio_normalized * bar_width

        self.canvas.create_polygon(
            indicator_x, y - bar_height // 2 - 15,
                         indicator_x - 8, y - bar_height // 2,
                         indicator_x + 8, y - bar_height // 2,
            fill='white', outline='black', width=2
        )
        self.canvas.create_line(indicator_x, y - bar_height // 2,
                                indicator_x, y + bar_height // 2,
                                fill='white', width=3)

        # Value display
        self.canvas.create_text(x, y + bar_height // 2 + 30,
                                text=f"λ = {ratio_val:.3f}",
                                fill='#00ffff', font=('Digital-7', 20, 'bold'))

    def draw_data_card(self, x, y, title):
        """Draw card header"""
        self.canvas.create_text(x, y - 60, text=title,
                                fill='#00ffff', font=('Arial', 13, 'bold'))
        self.canvas.create_rectangle(x - 140, y - 70, x + 140, y + 70,
                                     outline='#333333', width=2)

    def draw_o2_waveform(self, x, y):
        """Draw O2 sensors with bar graphs"""
        o2_b1s1 = float(self.current_data.get('O2_B1S1', {}).get('value', '0').split()[0])
        o2_b2s1 = float(self.current_data.get('O2_B2S1', {}).get('value', '0').split()[0])

        for i, (label, value) in enumerate([("BANK 1 SENSOR 1", o2_b1s1), ("BANK 2 SENSOR 1", o2_b2s1)]):
            y_pos = y - 20 + i * 50

            # Label
            self.canvas.create_text(x - 80, y_pos, text=label,
                                    fill='#888888', font=('Arial', 10))

            # Vertical bar
            bar_height = 30
            bar_width = 15
            fill_h = (value / 1.0) * bar_height

            # Background
            self.canvas.create_rectangle(x + 30, y_pos - bar_height // 2,
                                         x + 30 + bar_width, y_pos + bar_height // 2,
                                         outline='#333333', width=1)

            # Fill
            if fill_h > 0:
                self.canvas.create_rectangle(x + 30, y_pos + bar_height // 2,
                                             x + 30 + bar_width, y_pos + bar_height // 2 - fill_h,
                                             fill='#00ff00', outline='')

            # Value
            self.canvas.create_text(x + 85, y_pos, text=f"{value:.3f} V",
                                    fill='#00ff00', font=('Digital-7', 14, 'bold'))

    def draw_cylinder_status(self, cx, cy):
        """Draw cylinder status indicators"""
        cyl_spacing = 100

        for i, cyl_num in enumerate([1, 2]):
            x = cx - cyl_spacing // 2 + i * cyl_spacing

            misfire_data = self.current_data.get(f'MONITOR_MISFIRE_CYLINDER_{cyl_num}', {}).get('value', '')
            is_passed = 'PASSED' in misfire_data

            icon_color = '#00ff00' if is_passed else '#ff0000'

            # Cylinder representation
            self.canvas.create_rectangle(x - 25, cy - 35, x + 25, cy + 35,
                                         fill=icon_color, outline='white', width=3)

            # Number
            self.canvas.create_text(x, cy, text=str(cyl_num),
                                    fill='black', font=('Arial', 28, 'bold'))

            # Status
            status = "PASS" if is_passed else "FAIL"
            self.canvas.create_text(x, cy + 50, text=status,
                                    fill=icon_color, font=('Arial', 12, 'bold'))

    def draw_voltage_meters(self, x, y):
        """Draw voltage meters"""
        control_voltage = self.current_data.get('CONTROL_MODULE_VOLTAGE', {}).get('value', '0 volt')
        elm_voltage = self.current_data.get('ELM_VOLTAGE', {}).get('value', '0 volt')

        control_val = float(control_voltage.split()[0])
        elm_val = float(elm_voltage.split()[0])

        for i, (label, value) in enumerate([("CONTROL MODULE", control_val), ("ELM INTERFACE", elm_val)]):
            y_pos = y - 20 + i * 50

            # Label
            self.canvas.create_text(x - 70, y_pos, text=label,
                                    fill='#888888', font=('Arial', 10))

            # Horizontal bar
            bar_width = 100
            bar_height = 15
            max_voltage = 16

            # Background
            self.canvas.create_rectangle(x + 10, y_pos - bar_height // 2,
                                         x + 10 + bar_width, y_pos + bar_height // 2,
                                         outline='#333333', width=1)

            # Fill
            fill_w = (value / max_voltage) * bar_width
            color = '#00ff00' if value > 12.5 else '#ffff00' if value > 11.5 else '#ff0000'

            if fill_w > 0:
                self.canvas.create_rectangle(x + 10, y_pos - bar_height // 2,
                                             x + 10 + fill_w, y_pos + bar_height // 2,
                                             fill=color, outline='')

            # Value
            self.canvas.create_text(x + 10 + bar_width + 35, y_pos,
                                    text=f"{value:.1f} V",
                                    fill=color, font=('Digital-7', 14, 'bold'))

    def draw_corner_info(self, x, y, label, value, color):
        """Draw corner information panel"""
        self.canvas.create_rectangle(x - 100, y - 40, x + 100, y + 40,
                                     outline='#333333', width=2)
        self.canvas.create_text(x, y - 15, text=label,
                                fill='#888888', font=('Arial', 11, 'bold'))
        self.canvas.create_text(x, y + 15, text=value,
                                fill=color, font=('Digital-7', 18, 'bold'))

    def update_dashboard(self):
        """Check queue for new data and update dashboard"""
        try:
            while not self.data_queue.empty():
                self.current_data = self.data_queue.get_nowait()
                self.draw_dashboard()
        except queue.Empty:
            pass

        self.root.after(16, self.update_dashboard)

    def enqueue_data(self, data):
        """Thread-safe method to add data to queue"""
        try:
            self.data_queue.put(data, block=False)
        except queue.Full:
            pass


# Example OBD reader thread function
def obd_reader_thread(dashboard):
    """Simulated OBD reader that sends data to dashboard"""
    while True:
        simulated_data = {
            "SPEED": {"value": f"{random.randint(0, 140)} kilometer_per_hour"},
            "RPM": {"value": f"{random.randint(1500, 8000)} revolutions_per_minute"},
            "COOLANT_TEMP": {"value": f"{random.randint(70, 120)} degree_Celsius"},
            "ENGINE_LOAD": {"value": f"{random.uniform(20, 90)} percent"},
            "THROTTLE_POS": {"value": f"{random.uniform(10, 90)} percent"},
            "INTAKE_TEMP": {"value": f"{random.randint(15, 65)} degree_Celsius"},
            "O2_B1S1": {"value": f"{random.uniform(0.1, 0.9)} volt"},
            "O2_B2S1": {"value": f"{random.uniform(0.1, 0.9)} volt"},
            "ELM_VERSION": {"value": "ELM327 v1.5"},
            "RUN_TIME": {"value": f"{random.randint(0, 10000)} second"},
            "BAROMETRIC_PRESSURE": {"value": f"{random.randint(90, 105)} kilopascal"},
            "CONTROL_MODULE_VOLTAGE": {"value": f"{random.uniform(13, 15):.3f} volt"},
            "ELM_VOLTAGE": {"value": f"{random.uniform(12, 14):.1f} volt"},
            "COMMANDED_EQUIV_RATIO": {"value": f"{random.uniform(0.8, 1.2):.6f} ratio"},
            "MONITOR_MISFIRE_CYLINDER_1": {"value": random.choice(["FAILED", "PASSED"])},
            "MONITOR_MISFIRE_CYLINDER_2": {"value": random.choice(["FAILED", "PASSED"])}
        }

        dashboard.enqueue_data(simulated_data)
        time.sleep(0.15)


if __name__ == "__main__":
    root = tk.Tk()
    dashboard = OBD2Dashboard(root)

    # Start OBD reader thread
    reader_thread = threading.Thread(target=obd_reader_thread, args=(dashboard,), daemon=True)
    reader_thread.start()

    root.mainloop()