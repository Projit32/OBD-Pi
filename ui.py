import tkinter as tk
from tkinter import font
import math
import json


class OBDDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("OBD Dashboard")
        self.root.configure(bg='black')
        self.root.geometry("1200x700")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.end_fullscreen)
        self.root.bind("<F11>", self.end_fullscreen)

        # Main canvas
        self.canvas = tk.Canvas(root, width=1200, height=700, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Fonts
        self.speed_font = font.Font(family="Digital-7", size=80, weight="bold")
        self.label_font = font.Font(family="Arial", size=12, weight="bold")
        self.value_font = font.Font(family="Arial", size=14, weight="bold")
        self.small_font = font.Font(family="Arial", size=10)

        self.draw_static_elements()
        self.setup_update_handlers()

    def draw_static_elements(self):
        """Draw static UI elements"""
        # Title area
        self.canvas.create_text(600, 30, text="VEHICLE DIAGNOSTICS",
                                fill='#00ffff', font=('Arial', 20, 'bold'))

        # ELM Version label
        self.elm_label = self.canvas.create_text(150, 70, text="ELM Version:",
                                                 fill='#888888', font=self.small_font, anchor='w')
        self.elm_value = self.canvas.create_text(150, 90, text="",
                                                 fill='#00ff00', font=self.label_font, anchor='w')

        # Run Time label
        self.runtime_label = self.canvas.create_text(400, 70, text="Run Time:",
                                                     fill='#888888', font=self.small_font, anchor='w')
        self.runtime_value = self.canvas.create_text(400, 90, text="",
                                                     fill='#00ff00', font=self.label_font, anchor='w')

        # Speed display (center)
        self.canvas.create_text(600, 200, text="SPEED",
                                fill='#666666', font=self.label_font)
        self.speed_text = self.canvas.create_text(600, 280, text="0",
                                                  fill='#00ffff', font=self.speed_font)
        self.canvas.create_text(600, 340, text="km/h",
                                fill='#666666', font=self.label_font)

        # RPM Gauge (left side)
        self.draw_rpm_gauge_static()

        # Coolant Temperature Bar (right side)
        self.draw_coolant_bar_static()

        # Intake Temperature Bar (left of coolant)
        self.draw_intake_bar_static()

        # Misfire indicators
        self.draw_misfire_indicators()

        # Other parameters
        self.draw_other_params()

    def draw_rpm_gauge_static(self):
        """Draw static parts of RPM gauge"""
        cx, cy, r = 250, 480, 120

        # Outer circle
        self.canvas.create_oval(cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10,
                                outline='#333333', width=3)

        # RPM Label
        self.canvas.create_text(cx, cy - 150, text="RPM x1000",
                                fill='#888888', font=self.label_font)

        # Draw scale marks and numbers
        for i in range(0, 9):
            angle = 225 - (i * 270 / 8)
            rad = math.radians(angle)

            # Scale marks
            x1 = cx + (r - 15) * math.cos(rad)
            y1 = cy - (r - 15) * math.sin(rad)
            x2 = cx + r * math.cos(rad)
            y2 = cy - r * math.sin(rad)

            # Color code
            if i <= 3.5:
                color = '#00ff00'
            elif i <= 6:
                color = '#ffff00'
            else:
                color = '#ff0000'

            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

            # Numbers
            x3 = cx + (r - 35) * math.cos(rad)
            y3 = cy - (r - 35) * math.sin(rad)
            self.canvas.create_text(x3, y3, text=str(i), fill=color,
                                    font=self.small_font)

        # RPM value text
        self.rpm_value_text = self.canvas.create_text(cx, cy + 40, text="0",
                                                      fill='#00ffff',
                                                      font=('Arial', 18, 'bold'))

    def draw_coolant_bar_static(self):
        """Draw static parts of coolant temperature bar"""
        x, y, w, h = 1050, 150, 40, 300

        # Draw thermometer icon
        self.draw_thermometer_icon(x + w / 2, y - 65, '#ff6666')

        # Border
        self.canvas.create_rectangle(x, y, x + w, y + h, outline='#333333', width=3)

        # Label
        self.canvas.create_text(x + w / 2, y - 23, text="COOLANT",
                                fill='#888888', font=self.small_font)
        self.canvas.create_text(x + w / 2, y - 8, text="TEMP °C",
                                fill='#888888', font=self.small_font)

        # Temperature marks
        temps = [120, 100, 80, 60, 40, 20, 0]
        for i, temp in enumerate(temps):
            y_pos = y + (i * h / 6)
            self.canvas.create_line(x + w, y_pos, x + w + 10, y_pos, fill='#666666', width=2)
            self.canvas.create_text(x + w + 30, y_pos, text=str(temp),
                                    fill='#666666', font=self.small_font)

        # Value display
        self.coolant_value_text = self.canvas.create_text(x + w / 2, y + h + 25, text="0°C",
                                                          fill='#00ffff',
                                                          font=self.label_font)

    def draw_intake_bar_static(self):
        """Draw static parts of intake temperature bar"""
        x, y, w, h = 960, 150, 40, 300

        # Draw thermometer icon
        self.draw_thermometer_icon(x + w / 2, y - 65, '#66ff66')

        # Border
        self.canvas.create_rectangle(x, y, x + w, y + h, outline='#333333', width=3)

        # Label
        self.canvas.create_text(x + w / 2, y - 23, text="INTAKE",
                                fill='#888888', font=self.small_font)
        self.canvas.create_text(x + w / 2, y - 8, text="TEMP °C",
                                fill='#888888', font=self.small_font)

        # Temperature marks
        temps = [80, 70, 60, 50, 40, 30, 20, 10, 0]
        for i, temp in enumerate(temps):
            y_pos = y + (i * h / 8)
            self.canvas.create_line(x - 10, y_pos, x, y_pos, fill='#666666', width=2)
            self.canvas.create_text(x - 30, y_pos, text=str(temp),
                                    fill='#666666', font=self.small_font)

        # Value display
        self.intake_value_text = self.canvas.create_text(x + w / 2, y + h + 25, text="0°C",
                                                         fill='#00ffff',
                                                         font=self.label_font)

    def draw_thermometer_icon(self, x, y, color):
        """Draw a thermometer icon"""
        # Bulb
        self.canvas.create_oval(x - 8, y + 15, x + 8, y + 31, fill=color, outline=color)
        # Tube
        self.canvas.create_rectangle(x - 4, y, x + 4, y + 20, fill=color, outline=color)
        # Top cap
        self.canvas.create_oval(x - 4, y - 2, x + 4, y + 2, fill=color, outline=color)

    def draw_battery_icon(self, x, y, color):
        """Draw a battery icon"""
        # Battery body
        self.canvas.create_rectangle(x - 12, y - 8, x + 12, y + 12, outline=color, width=2)
        # Battery terminal
        self.canvas.create_rectangle(x - 4, y - 12, x + 4, y - 8, fill=color, outline=color)
        # Plus sign
        self.canvas.create_line(x - 3, y + 2, x + 3, y + 2, fill=color, width=2)
        self.canvas.create_line(x, y - 1, x, y + 5, fill=color, width=2)

    def draw_piston_icon(self, x, y, color):
        """Draw a piston icon"""
        # Piston head
        self.canvas.create_rectangle(x - 10, y - 5, x + 10, y + 5, fill=color, outline=color)
        # Piston rod
        self.canvas.create_rectangle(x - 3, y + 5, x + 3, y + 15, fill=color, outline=color)
        # Connecting point
        self.canvas.create_oval(x - 4, y + 13, x + 4, y + 21, fill=color, outline=color)

    def draw_misfire_indicators(self):
        """Draw misfire indicator icons"""
        # Center the cylinders under the header
        header_x = 535  # Center position for the header
        y_pos = 550
        spacing = 100
        x_start = header_x - spacing / 2  # Start position for first cylinder

        # Header text centered
        self.canvas.create_text(header_x, y_pos - 40, text="CYLINDER MISFIRES",
                                fill='#888888', font=self.label_font)

        # Cylinder 1
        self.cyl1_piston = self.draw_piston_icon(x_start, y_pos - 10, '#666666')
        self.canvas.create_text(x_start, y_pos + 25, text="CYL 1",
                                fill='#666666', font=self.small_font)
        self.cyl1_status = self.canvas.create_text(x_start, y_pos + 45, text="",
                                                   fill='#00ff00', font=self.small_font)

        # Cylinder 2
        x2 = x_start + spacing
        self.cyl2_piston = self.draw_piston_icon(x2, y_pos - 10, '#666666')
        self.canvas.create_text(x2, y_pos + 25, text="CYL 2",
                                fill='#666666', font=self.small_font)
        self.cyl2_status = self.canvas.create_text(x2, y_pos + 45, text="",
                                                   fill='#00ff00', font=self.small_font)

        # Store positions for later updates
        self.cyl1_pos = (x_start, y_pos - 10)
        self.cyl2_pos = (x2, y_pos - 10)

    def draw_other_params(self):
        """Draw other parameter displays"""
        params = [
            ("ENGINE LOAD", 70, 180),
            ("THROTTLE POS", 70, 240),
            ("O2 B1S1", 70, 300),
            ("O2 B2S1", 70, 360),
            ("BAROMETRIC", 750, 480),
            ("CONTROL V", 750, 530),
            ("ELM VOLTAGE", 750, 580),
            ("CMD EQUIV", 750, 630),
        ]

        self.param_values = {}
        self.param_bars = {}

        for label, x, y in params:
            self.canvas.create_text(x, y, text=label, fill='#888888',
                                    font=self.small_font, anchor='w')
            self.param_values[label] = self.canvas.create_text(x, y + 20, text="0",
                                                               fill='#00ffff',
                                                               font=self.value_font,
                                                               anchor='w')

            # Add bars for percentage values
            if "LOAD" in label or "THROTTLE" in label:
                bar_x = x + 150
                self.param_bars[label] = self.canvas.create_rectangle(
                    bar_x, y + 5, bar_x, y + 25, fill='', outline='#333333', width=2
                )

            # Add battery icons for voltage
            if "VOLTAGE" in label or "CONTROL V" in label:
                self.draw_battery_icon(x - 30, y + 12, '#666666')

    def setup_update_handlers(self):
        """Setup dictionary of update handlers using lambda functions"""
        self.update_handlers = {
            'SPEED': lambda val: self.canvas.itemconfig(self.speed_text, text=f"{int(val)}"),

            'RPM': lambda val: self.update_rpm_gauge(val),

            'ELM_VERSION': lambda val: self.canvas.itemconfig(self.elm_value, text=val),

            'RUN_TIME': lambda val: self.canvas.itemconfig(
                self.runtime_value,
                text=f"{int(val // 60)}m {int(val % 60)}s"
            ),

            'COOLANT_TEMP': lambda val: self.update_coolant_bar(val),

            'INTAKE_TEMP': lambda val: self.update_intake_bar(val),

            'MONITOR_MISFIRE_CYLINDER_1': lambda val: self.update_misfire_indicator(
                1, "PASSED" in str(val)
            ),

            'MONITOR_MISFIRE_CYLINDER_2': lambda val: self.update_misfire_indicator(
                2, "PASSED" in str(val)
            ),

            'ENGINE_LOAD': lambda val: (
                self.canvas.itemconfig(self.param_values["ENGINE LOAD"], text=f"{val:.1f}%"),
                self.update_bar("ENGINE LOAD", val, 100)
            ),

            'THROTTLE_POS': lambda val: (
                self.canvas.itemconfig(self.param_values["THROTTLE POS"], text=f"{val:.1f}%"),
                self.update_bar("THROTTLE POS", val, 100)
            ),

            'O2_B1S1': lambda val: self.canvas.itemconfig(
                self.param_values["O2 B1S1"],
                text=f"{val:.3f}V"
            ),

            'O2_B2S1': lambda val: self.canvas.itemconfig(
                self.param_values["O2 B2S1"],
                text=f"{val:.3f}V"
            ),

            'BAROMETRIC_PRESSURE': lambda val: self.canvas.itemconfig(
                self.param_values["BAROMETRIC"],
                text=f"{val:.0f}kPa"
            ),

            'CONTROL_MODULE_VOLTAGE': lambda val: self.canvas.itemconfig(
                self.param_values["CONTROL V"],
                text=f"{val:.2f}V"
            ),

            'ELM_VOLTAGE': lambda val: self.canvas.itemconfig(
                self.param_values["ELM VOLTAGE"],
                text=f"{val:.1f}V"
            ),

            'COMMANDED_EQUIV_RATIO': lambda val: self.canvas.itemconfig(
                self.param_values["CMD EQUIV"],
                text=f"{val:.3f}"
            ),
        }

    def update_sensor(self, sensor_name, sensor_value):
        """
        Update a single sensor value

        Args:
            sensor_name: Name of the sensor (e.g., 'SPEED', 'RPM')
            sensor_value: Numeric value or string value of the sensor
        """
        handler = self.update_handlers.get(sensor_name)
        if handler:
            handler(sensor_value)

    def update_from_sensor(self, sensor_data_tuple):
        """
        Update dashboard from JSON data (convenience method)

        Args:
            sensor_data_tuple: (Sensor Name and value -> {actual_value, unit_of_measurement})
        """
        sensor_name, sensor_data = sensor_data_tuple

        if sensor_name in self.update_handlers:
            # Extract numeric value from the value string
            value_str = sensor_data.get("value", "")

            # For string values like ELM_VERSION
            if sensor_name == "ELM_VERSION":
                self.update_sensor(sensor_name, value_str)
            # For misfire monitors
            elif "MONITOR_MISFIRE" in sensor_name:
                self.update_sensor(sensor_name, value_str)
            # For numeric values
            else:
                try:
                    value = float(value_str.split()[0])
                    self.update_sensor(sensor_name, value)
                except (ValueError, IndexError):
                    pass

    def update_rpm_gauge(self, rpm):
        """Update RPM gauge needle"""
        cx, cy, r = 250, 480, 100

        # Delete old needle
        self.canvas.delete("rpm_needle")

        # Calculate angle (0 RPM = 225°, 8000 RPM = -45°)
        rpm_percent = min(rpm / 8000, 1.0)
        angle = 225 - (rpm_percent * 270)
        rad = math.radians(angle)

        # Needle endpoint
        x = cx + r * math.cos(rad)
        y = cy - r * math.sin(rad)

        # Needle color
        if rpm <= 3500:
            color = '#00ff00'
        elif rpm <= 6000:
            color = '#ffff00'
        else:
            color = '#ff0000'

        # Draw needle
        self.canvas.create_line(cx, cy, x, y, fill=color, width=4,
                                tags="rpm_needle")
        self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill=color,
                                outline=color, tags="rpm_needle")

        # Update value
        self.canvas.itemconfig(self.rpm_value_text, text=f"{int(rpm)}")

    def update_coolant_bar(self, temp):
        """Update coolant temperature bar"""
        x, y, w, h = 1050, 150, 40, 300

        # Delete old bar
        self.canvas.delete("coolant_bar")

        # Calculate fill height (0-120°C range)
        fill_percent = min(temp / 120, 1.0)
        fill_height = h * fill_percent

        # Color based on temperature - red above 90°C
        if temp < 60:
            color = '#00ffff'  # Cold - cyan
        elif temp < 80:
            color = '#00ff00'  # Normal - green
        elif temp <= 90:
            color = '#ffff00'  # Warm - yellow
        else:
            color = '#ff0000'  # Hot - red (above 90°C)

        # Draw filled bar from bottom
        self.canvas.create_rectangle(x + 2, y + h - fill_height + 2, x + w - 2, y + h - 2,
                                     fill=color, outline='', tags="coolant_bar")

        # Update value
        self.canvas.itemconfig(self.coolant_value_text,
                               text=f"{int(temp)}°C", fill=color)

    def update_intake_bar(self, temp):
        """Update intake temperature bar"""
        x, y, w, h = 960, 150, 40, 300

        # Delete old bar
        self.canvas.delete("intake_bar")

        # Calculate fill height (0-80°C range)
        fill_percent = min(temp / 80, 1.0)
        fill_height = h * fill_percent

        # Color based on temperature - red above 50°C
        if temp < 30:
            color = '#00ffff'  # Cold - cyan
        elif temp < 40:
            color = '#00ff00'  # Normal - green
        elif temp <= 50:
            color = '#ffff00'  # Warm - yellow
        else:
            color = '#ff0000'  # Hot - red (above 50°C)

        # Draw filled bar from bottom
        self.canvas.create_rectangle(x + 2, y + h - fill_height + 2, x + w - 2, y + h - 2,
                                     fill=color, outline='', tags="intake_bar")

        # Update value
        self.canvas.itemconfig(self.intake_value_text,
                               text=f"{int(temp)}°C", fill=color)

    def update_misfire_indicator(self, cylinder, passed):
        """Update misfire indicator with piston icon"""
        if cylinder == 1:
            x, y = self.cyl1_pos
            status = self.cyl1_status
        else:
            x, y = self.cyl2_pos
            status = self.cyl2_status

        if passed:
            color = '#00ff00'
            status_text = "PASSED"
        else:
            color = '#ff0000'
            status_text = "FAILED"

        # Delete old piston
        self.canvas.delete(f"piston_{cylinder}")

        # Draw new piston with updated color
        self.draw_piston_icon(x, y, color)
        self.canvas.addtag_withtag(f"piston_{cylinder}", "all")

        self.canvas.itemconfig(status, text=status_text, fill=color)

    def update_bar(self, param, value, max_value):
        """Update horizontal bar indicators"""
        if param not in self.param_bars:
            return

        bar_x = 220 if param in ["ENGINE LOAD", "THROTTLE POS"] else 1000
        width = int((value / max_value) * 80)

        # Color based on value
        if value < 50:
            color = '#00ff00'
        elif value < 75:
            color = '#ffff00'
        else:
            color = '#ff0000'

        coords = self.canvas.coords(self.param_bars[param])
        self.canvas.coords(self.param_bars[param],
                           coords[0], coords[1],
                           coords[0] + width, coords[3])
        self.canvas.itemconfig(self.param_bars[param], fill=color, outline=color)

    def end_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)
        return "break"  # Prevents default Tkinter behavior


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    dashboard = OBDDashboard(root)


    with open("./sample.json", "r") as file:
        data = json.load(file)
        for key in data.keys():
            dashboard.update_from_sensor((key, data.get(key)))
    root.mainloop()

