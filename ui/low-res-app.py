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
        self.root.geometry('800x600')
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

        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600

        # Calculate center offset for alignment
        center_x = width // 2
        center_y = height // 2

        # Compact header (top bar)
        elm_version = self.current_data.get('ELM_VERSION', {}).get('value', 'N/A')
        run_time = self.current_data.get('RUN_TIME', {}).get('value', '0 second')
        run_time_sec = run_time.replace(" second", "").strip()
        try:
            run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time_sec)))
        except:
            run_time = "00:00:00"

        self.canvas.create_text(center_x, 12, text=f"ELM: {elm_version} | Time: {run_time}",
                                fill='#00FF00', font=('Arial', 9))

        # Main speed display (top center, compact)
        speed_val = float(self.current_data.get('SPEED', {}).get('value', '0').split()[0])
        self.canvas.create_text(center_x, 60, text=f"{int(speed_val)}",
                                fill='white', font=('Digital-7', 48, 'bold'))
        self.canvas.create_text(center_x, 90, text="KM/H",
                                fill='#888888', font=('Arial', 10))

        # Three compact gauges below speed (RPM, Load, Throttle)
        gauge_y = 160
        self.draw_compact_rpm_gauge(center_x - 160, gauge_y)
        self.draw_compact_engine_load(center_x, gauge_y)
        self.draw_compact_throttle(center_x + 160, gauge_y)

        # Temperature bars (compact, horizontal at bottom of gauges)
        temp_y = 250
        self.draw_compact_temp_bar(center_x - 100, temp_y, "COOL",
                                   self.current_data.get('COOLANT_TEMP', {}).get('value', '0'), 150)
        self.draw_compact_temp_bar(center_x + 100, temp_y, "INTK",
                                   self.current_data.get('INTAKE_TEMP', {}).get('value', '0'), 80)

        # Middle section - Equiv Ratio with visual indicator
        ratio_y = 330
        self.draw_equiv_ratio_indicator(center_x, ratio_y)

        # Bottom left - O2 Sensors (compact)
        self.draw_compact_o2_sensors(100, height - 120)

        # Bottom center - Cylinder indicators (compact)
        self.draw_compact_cylinder_indicators(center_x, height - 100)

        # Bottom right - Voltage indicators (compact with visual bars)
        self.draw_compact_voltage_bars(width - 100, height - 120)

        # Top corners - Barometric pressure (left)
        baro = self.current_data.get('BAROMETRIC_PRESSURE', {}).get('value', '0 kilopascal')
        baro_val = baro.split()[0]
        self.canvas.create_text(60, 30, text="BARO", fill='#666666', font=('Arial', 8))
        self.canvas.create_text(60, 45, text=f"{baro_val}kPa", fill='#00FFFF', font=('Arial', 9))

    def draw_compact_rpm_gauge(self, cx, cy):
        radius = 50
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
            self.canvas.create_arc(cx - radius + 3, cy - radius + 3,
                                   cx + radius - 3, cy + radius - 3,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=5, style=tk.ARC)

        # Draw RPM value
        self.canvas.create_text(cx, cy - 5, text=f"{int(rpm_val)}",
                                fill='white', font=('Digital-7', 18, 'bold'))
        self.canvas.create_text(cx, cy + 12, text="RPM",
                                fill='#888888', font=('Arial', 8))

    def draw_compact_engine_load(self, cx, cy):
        radius = 50
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
            self.canvas.create_arc(cx - radius + 3, cy - radius + 3,
                                   cx + radius - 3, cy + radius - 3,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=5, style=tk.ARC)

        # Draw load value
        self.canvas.create_text(cx, cy - 5, text=f"{int(load_val)}%",
                                fill='white', font=('Digital-7', 18, 'bold'))
        self.canvas.create_text(cx, cy + 12, text="LOAD",
                                fill='#888888', font=('Arial', 8))

    def draw_compact_throttle(self, cx, cy):
        radius = 50
        throttle_val = float(self.current_data.get('THROTTLE_POS', {}).get('value', '0').split()[0])

        # Draw outer circle
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                outline='#333333', width=2)

        # Draw arc based on throttle
        extent = (throttle_val / 100) * 270
        start_angle = 135
        color = '#00BFFF'

        if extent > 0:
            self.canvas.create_arc(cx - radius + 3, cy - radius + 3,
                                   cx + radius - 3, cy + radius - 3,
                                   start=start_angle, extent=-extent,
                                   outline=color, width=5, style=tk.ARC)

        # Draw throttle value
        self.canvas.create_text(cx, cy - 5, text=f"{int(throttle_val)}%",
                                fill='white', font=('Digital-7', 18, 'bold'))
        self.canvas.create_text(cx, cy + 12, text="THRTL",
                                fill='#888888', font=('Arial', 8))

    def draw_compact_temp_bar(self, x, y, label, temp_str, max_temp):
        temp_val = float(temp_str.split()[0])
        bar_width = 120
        bar_height = 12

        # Label
        self.canvas.create_text(x - bar_width // 2 - 25, y, text=label,
                                fill='#888888', font=('Arial', 8))

        # Draw bar outline
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=1)

        # Calculate fill width and color
        fill_width = (temp_val / max_temp) * bar_width
        if fill_width > bar_width:
            fill_width = bar_width

        # Color based on temperature
        if label == "COOL":
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

        # Draw temperature value
        self.canvas.create_text(x + bar_width // 2 + 25, y, text=f"{int(temp_val)}°",
                                fill='white', font=('Arial', 9))

    def draw_equiv_ratio_indicator(self, cx, cy):
        ratio = self.current_data.get('COMMANDED_EQUIV_RATIO', {}).get('value', '1.0')
        ratio_val = float(ratio.replace("ratio", "").strip())

        # Determine status
        if ratio_val >= 1.1:
            meaning = "LEAN"
            color = "#FF0000"
        elif 1.1 > ratio_val >= 1.02:
            meaning = "~LEAN"
            color = "#00FFFF"
        elif 1.01 > ratio_val >= 0.99:
            meaning = "STOICH"
            color = "#00FF00"
        elif 0.99 > ratio_val >= 0.95:
            meaning = "~RICH"
            color = "#00FFFF"
        else:
            meaning = "RICH"
            color = "#FF0000"

        # Draw visual indicator bar
        bar_width = 200
        bar_height = 20

        self.canvas.create_text(cx, cy - 25, text="AIR/FUEL RATIO",
                                fill='#888888', font=('Arial', 9, 'bold'))

        # Draw gradient bar from lean to rich
        self.canvas.create_rectangle(cx - bar_width // 2, cy - bar_height // 2,
                                     cx + bar_width // 2, cy + bar_height // 2,
                                     outline='#333333', width=1)

        # Draw segments
        segment_width = bar_width / 5
        colors = ['#FF0000', '#00FFFF', '#00FF00', '#00FFFF', '#FF0000']
        for i in range(5):
            seg_x = cx - bar_width // 2 + i * segment_width
            self.canvas.create_rectangle(seg_x, cy - bar_height // 2,
                                         seg_x + segment_width, cy + bar_height // 2,
                                         fill=colors[i], outline='#333333')

        # Draw indicator position
        # Map ratio from 0.85-1.15 to bar position
        ratio_normalized = (ratio_val - 0.85) / (1.15 - 0.85)
        ratio_normalized = max(0, min(1, ratio_normalized))
        indicator_x = cx - bar_width // 2 + ratio_normalized * bar_width

        # Draw triangle indicator
        tri_size = 8
        self.canvas.create_polygon(
            indicator_x, cy - bar_height // 2 - tri_size,
                         indicator_x - tri_size, cy - bar_height // 2,
                         indicator_x + tri_size, cy - bar_height // 2,
            fill='white', outline='black'
        )

        # Value and status
        self.canvas.create_text(cx, cy + 20, text=f"{round(ratio_val, 2)} - {meaning}",
                                fill=color, font=('Arial', 10, 'bold'))

    def draw_compact_o2_sensors(self, x, y):
        o2_b1s1 = float(self.current_data.get('O2_B1S1', {}).get('value', '0').split()[0])
        o2_b2s1 = float(self.current_data.get('O2_B2S1', {}).get('value', '0').split()[0])

        # Draw as horizontal bars
        bar_width = 60
        bar_height = 8

        # B1S1
        self.canvas.create_text(x - 35, y - 15, text="O2", fill='#888888', font=('Arial', 8))
        self.canvas.create_text(x - 35, y, text="B1S1", fill='#666666', font=('Arial', 7))

        self.canvas.create_rectangle(x, y - bar_height // 2, x + bar_width, y + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (o2_b1s1 / 1.0) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x, y - bar_height // 2, x + fill_w, y + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width + 20, y, text=f"{o2_b1s1:.2f}V",
                                fill='#00FF00', font=('Arial', 8))

        # B2S1
        y += 25
        self.canvas.create_text(x - 35, y, text="B2S1", fill='#666666', font=('Arial', 7))

        self.canvas.create_rectangle(x, y - bar_height // 2, x + bar_width, y + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (o2_b2s1 / 1.0) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x, y - bar_height // 2, x + fill_w, y + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width + 20, y, text=f"{o2_b2s1:.2f}V",
                                fill='#00FF00', font=('Arial', 8))

    def draw_compact_cylinder_indicators(self, cx, cy):
        self.canvas.create_text(cx, cy - 35, text="CYLINDER",
                                fill='#888888', font=('Arial', 9, 'bold'))

        cyl_spacing = 70

        for i, cyl_num in enumerate([1, 2]):
            x = cx - cyl_spacing // 2 + i * cyl_spacing

            # Get misfire data
            misfire_data = self.current_data.get(f'MONITOR_MISFIRE_CYLINDER_{cyl_num}', {}).get('value', '')
            is_passed = 'PASSED' in misfire_data

            # Draw compact piston indicator
            icon_color = '#00FF00' if is_passed else '#FF0000'

            # Small circle
            self.canvas.create_oval(x - 18, cy - 18, x + 18, cy + 18,
                                    fill=icon_color, outline='white', width=1)

            # Cylinder number
            self.canvas.create_text(x, cy, text=str(cyl_num),
                                    fill='black', font=('Arial', 16, 'bold'))

            # Status indicator (dot)
            status_color = '#00FF00' if is_passed else '#FF0000'
            self.canvas.create_oval(x - 3, cy + 25, x + 3, cy + 31,
                                    fill=status_color, outline=status_color)

    def draw_compact_voltage_bars(self, x, y):
        control_voltage = self.current_data.get('CONTROL_MODULE_VOLTAGE', {}).get('value', '0 volt')
        elm_voltage = self.current_data.get('ELM_VOLTAGE', {}).get('value', '0 volt')

        control_val = float(control_voltage.split()[0])
        elm_val = float(elm_voltage.split()[0])

        # Battery icon (simplified)
        self.canvas.create_text(x, y - 35, text="⚡", fill='#00FF00', font=('Arial', 16))

        bar_width = 50
        bar_height = 8
        max_voltage = 16

        # Control voltage bar
        self.canvas.create_text(x - bar_width // 2 - 20, y, text="CTL",
                                fill='#666666', font=('Arial', 7))
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (control_val / max_voltage) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                         x - bar_width // 2 + fill_w, y + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width // 2 + 18, y, text=f"{control_val:.1f}V",
                                fill='#00FF00', font=('Arial', 8))

        # ELM voltage bar
        y += 20
        self.canvas.create_text(x - bar_width // 2 - 20, y, text="ELM",
                                fill='#666666', font=('Arial', 7))
        self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                     x + bar_width // 2, y + bar_height // 2,
                                     outline='#333333', width=1)
        fill_w = (elm_val / max_voltage) * bar_width
        if fill_w > 0:
            self.canvas.create_rectangle(x - bar_width // 2, y - bar_height // 2,
                                         x - bar_width // 2 + fill_w, y + bar_height // 2,
                                         fill='#00FF00', outline='')
        self.canvas.create_text(x + bar_width // 2 + 18, y, text=f"{elm_val:.1f}V",
                                fill='#00FF00', font=('Arial', 8))

    def update_dashboard(self):
        """Check queue for new data and update dashboard"""
        try:
            while not self.data_queue.empty():
                self.current_data = self.data_queue.get_nowait()
                self.draw_dashboard()
        except queue.Empty:
            pass

        # Schedule next update (30 FPS)
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