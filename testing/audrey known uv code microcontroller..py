#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
import board
import analogio
import digitalio
#user settings - placeholders
#need to verify volts per uvi and uv minimum with uv sensor
skin_type = 1
sample_interval = 5.0
#vout for guva = 0.2*uvi+0.6
#for the breakout board, multiply the output voltage by 10 and it is the uv index
zero_voltage = 0.0
#volts_per_uvi = 0.1
uv_minimum = 0.0

#skin type thresholds
#could put skin type in warning system or input in set-up
#automatically assumed 1 for now
skin_thresholds = {
    1: (849000, 2200000),
    2: (1150000, 2500000),
    3: (1430000, 2790000),
    4: (1950000, 3300000)
}
first_threshold, second_threshold = (skin_thresholds[skin_type])

#sensor configuration
#uv_sensor = analogio.AnalogIn(board.A1)
#def get_voltage(sensor):
    #return sensor.value * 3.3 / 65535
def read_uv_index():
    #voltage = get_voltage(uv_sensor)
    #uv_index = (voltage - zero_voltage) / volts_per_uvi
    uv_index = 40.0
    return max(0.0, uv_index)

#alert output
red_output = digitalio.DigitalInOut(board.D5)
red_output.direction = digitalio.Direction.OUTPUT
green_output = digitalio.DigitalInOut(board.D7)
green_output.direction = digitalio.Direction.OUTPUT
blue_output = digitalio.DigitalInOut(board.D9)
blue_output.direction = digitalio.Direction.OUTPUT
alert_level = 0

#alert timing settings
alert_interval = 30.0  # seconds between alerts
alert_duration = 2.0    # seconds alert stays active
next_alert_time = 0.0
pulse_end_time = 0.0

def activate_alert(level, current_time):
    global alert_level
    global next_alert_time
    global pulse_end_time
    alert_level = level
    # No alert needed
    if level == 0:
        red_output.value = False
        green_output.value = False
        blue_output.value = False
        pulse_end_time = 0.0
        next_alert_time = current_time
        return
    # Turn off alert after pulse duration
    if current_time >= pulse_end_time:
        red_output.value = False
        green_output.value = False
        blue_output.value = False
    # Activate alert when next alert time is reached
    if current_time >= next_alert_time:
        if level == 1:
            red_output.value = False
            green_output.value = True
            blue_output.value = False
        elif level == 2:
            red_output.value = False
            green_output.value = False
            blue_output.value = True
        elif level == 3:
            red_output.value = True
            green_output.value = False
            blue_output.value = False
        pulse_end_time = current_time + alert_duration
        next_alert_time = current_time + alert_interval

#exposure and dose calculations
cumulative_dose = 0.0
exposure_time = 0.0
previous_time = time.monotonic()
def calculate_dose(uv_index, elapsed_time):
    intensity = 18.9 * uv_index
    dose_increment = (intensity ** (4/3)) * elapsed_time
    return dose_increment
def update_exposure(uv_index):
    global cumulative_dose
    global exposure_time
    global previous_time
    current_time = time.monotonic()
    elapsed_time = current_time - previous_time
    previous_time = current_time
    if uv_index > uv_minimum:
        exposure_time += elapsed_time
        cumulative_dose += calculate_dose(uv_index, elapsed_time)

#alert threshold checking
def check_alerts():
    if cumulative_dose >= second_threshold:
        return 3
    elif cumulative_dose >= first_threshold:
        return 2
    elif cumulative_dose >= first_threshold * 0.75:
        return 1
    else:
        return 0

#main
def main():
    global previous_time
    last_sample = time.monotonic()
    level = 0
    start_time = time.time()
    while time.time() - start_time < 5:
        red_output.value = True
        green_output.value = True
        blue_output.value = True
        time.sleep(0.05)
    red_output.value = False
    green_output.value = False
    blue_output.value = False
    while True:
        current_time = time.monotonic()
        # Take UV measurement every 20 seconds
        if current_time - last_sample >= sample_interval:
            uv_index = read_uv_index()
            update_exposure(uv_index)
            level = check_alerts()
            last_sample = current_time
        # Check alert timing continuously
        activate_alert(level, current_time)
        time.sleep(0.05)

#run program
main()

