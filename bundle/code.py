# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# air_mon_code.py
# 2021-09-25 v1.7.5 only compatible with CircuitPython v7.0.0

import time
import board
import busio
import os
import gc
import displayio
import neopixel
import random
from analogio import AnalogIn
from digitalio import DigitalInOut
from simpleio import tone
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
from cedargrove_unit_converter.temperature import celsius_to_fahrenheit
from cedargrove_unit_converter.air_quality.co2_air_quality import co2_ppm_to_quality
from cedargrove_unit_converter.air_quality.aqi_air_quality import concentration_to_aqi

from air_mon_config import *

SCREEN_TITLE = 'Air Quality'

# Import translator for alt language
exec(
    'from cedargrove_unit_converter.air_quality.interpreter.english_to_'
    + ALT_LANGUAGE.lower()
    + ' import interpret'
)

board_type = board.board_id
print('Board:', board_type)
if ('pygamer' == board_type) or ('pybadge' == board_type):
    import air_mon_buttons.buttons_pybadge as air_mon_panel

    has_speaker = True
    has_battery_mon = True
    battery_mon = AnalogIn(board.A6)
    trend_points = 32
elif 'pyportal' == board_type:
    import air_mon_buttons.buttons_pyportal as air_mon_panel

    has_speaker = True
    has_battery_mon = False
    trend_points = 32
elif 'funhouse' == board_type:
    import air_mon_buttons.buttons_funhouse as air_mon_panel

    has_speaker = False
    has_battery_mon = False
    trend_points = 32
else:
    print('--- Incompatible board ---')

panel = air_mon_panel.Buttons()

i2c = busio.I2C(board.SCL, board.SDA, frequency=95000)

try:
    import adafruit_scd30

    scd = adafruit_scd30.SCD30(i2c)
    co2_sensor_exists = True
except:
    print('')
    print('-- SCD30 I2C SENSOR --')
    print('--  NOT CONNECTED   --')
    co2_sensor_exists = False

try:
    from adafruit_pm25.i2c import PM25_I2C

    pm25 = PM25_I2C(i2c)
    aqi_sensor_exists = True
except:
    print('')
    print('-- PM25 I2C SENSOR --')
    print('--  NOT CONNECTED  --')
    aqi_sensor_exists = False

if not aqi_sensor_exists:
    try:
        # Connect the sensor TX pin to the D3 3-pin connector
        uart = busio.UART(None, board.D3, baudrate=9600)
        from adafruit_pm25.uart import PM25_UART

        pm25 = PM25_UART(uart, None)
        pm25.read()
        aqi_sensor_exists = True
    except RuntimeError as err:
        print('')
        print('-- PM25 UART SENSOR --')
        print(err)
        print('--  NOT CONNECTED   --')
        aqi_sensor_exists = False


display = board.DISPLAY
display.brightness = BRIGHTNESS
WIDTH = display.width
HEIGHT = display.height

if WIDTH > 160:
    font_0 = bitmap_font.load_font('/fonts/OpenSans-12.bdf')
    font_1 = bitmap_font.load_font('/fonts/Helvetica-Bold-36.bdf')
else:
    font_0 = bitmap_font.load_font('/fonts/OpenSans-9.bdf')
    font_1 = bitmap_font.load_font('/fonts/OpenSans-16.bdf')

if SOUND and hasattr(board, 'SPEAKER_ENABLE'):
    speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
    speaker_enable.switch_to_output(value=True)

if hasattr(board, 'NEOPIXEL'):
    has_neopixel = True
    pixels = neopixel.NeoPixel(board.NEOPIXEL, 5, pixel_order=neopixel.GRB)
    pixels.brightness = 0.05
    pixels.fill(0x000000)
else:
    has_neopixel = False


# - Helpers -


def sample_aq_sensor():
    # Sample PM2.5 sensor over 2.3 seconds
    aq_reading = 0
    aq_samples = []
    time_start = time.monotonic()
    while time.monotonic() - time_start <= 2.3:
        try:
            aqdata = pm25.read()
            aq_samples.append(aqdata['pm25 env'])
        except RuntimeError:
            print('Unable to read from sensor, retrying...')
            continue
        time.sleep(1)

    for sample in range(len(aq_samples)):
        aq_reading += aq_samples[sample]
    aq_reading = aq_reading / len(aq_samples)
    aq_samples.clear()
    return aq_reading


def play_tone(freq=440, duration=0.01):
    # Play tones through the integral speaker.
    if SOUND and has_speaker:
        tone(board.A0, freq, duration)
    return


def flash_status(text='', duration=0.05):
    # Flash a status message once.
    status_label.color = WHITE
    status_label.text = text
    time.sleep(duration)
    status_label.color = BLACK
    time.sleep(duration)
    status_label.text = ''
    return


def update_co2_image_frame(blocking=False, wait_time=3):
    """Acquire SCD-30 data and update the display. Return sensor health flag.
    When blocking = True, wait until the sensor is ready, up
    to 3 seconds. When blocking = False, immediately
    return when sensor data not available."""
    sensor_data_valid = True
    if co2_sensor_exists:
        t0 = time.monotonic()
        while (
            blocking
            and (not scd.data_available)
            and (t0 - time.monotonic() < wait_time)
        ):
            watchdog.fill = RED
            flash_status(interpret(TRANSLATE, 'WARMUP'), 0.5)

        if scd.data_available:
            watchdog.fill = YELLOW
            # Get CO2 sensor data
            sensor_co2 = round(scd.CO2)
            (
                sensor_data_valid,
                sensor_co2,
                co2_qual_label.color,
                label,
            ) = co2_ppm_to_quality(sensor_co2)
            sensor_co2_norm = sensor_co2 / 6000
            sensor_rh = round(scd.relative_humidity)
            sensor_temp = round(scd.temperature)
            if TEMP_UNIT == 'F':
                sensor_temp = round(celsius_to_fahrenheit(sensor_temp))

            if sensor_co2 < 6000:
                co2_pointer.fill = GRAY
                co2_pointer.y = HEIGHT - int(sensor_co2_norm * HEIGHT) - 3
                co2_pointer_shadow.y = co2_pointer.y
            else:
                co2_pointer.fill = CO2_ALARM[1]
                co2_poointer_shadow.y = co2_pointer.y = 0
                flash_status(interpret(TRANSLATE, 'OVERRANGE'), 0.75)

            co2_qual_label.text = interpret(TRANSLATE, label)
            co2_value.text = str(sensor_co2)
            co2_humid_value.text = str(sensor_rh)
            co2_temp_value.text = str(sensor_temp)
            co2_alarm_value.text = str(CO2_ALARM[0])

            # Trend chart
            for i in range(0, len(co2_trend_chart)):
                co2_trend_group[len(co2_trend_chart) - i - 1].y = (
                    HEIGHT - int(co2_trend_chart[i] * HEIGHT) + 1 - 3
                )
                co2_trend_group[len(co2_trend_chart) - i - 1].fill = GRAY
            co2_trend_chart.pop(0)
            co2_trend_chart.append(sensor_co2_norm)
    return sensor_data_valid


def update_aqi_image_frame(blocking=False, wait_time=3):
    """Acquire PM25 data and update the display. Return sensor health flag.
    When blocking = True, wait until the sensor is ready, up
    to 3 seconds. When blocking = False, immediately
    return when sensor data not available."""
    sensor_data_valid = True
    if aqi_sensor_exists:
        sensor_pm25 = sample_aq_sensor()  # Get aqi sensor data
        flag, sensor_aqi, aqi_qual_label.color, label = concentration_to_aqi(
            sensor_pm25
        )
        sensor_aqi_norm = sensor_aqi / 500

        if sensor_aqi < 500:
            aqi_pointer.fill = PURPLE
            aqi_pointer.y = HEIGHT - int(sensor_aqi_norm * HEIGHT) - 3
            aqi_pointer_shadow.y = aqi_pointer.y
        else:
            aqi_pointer.fill = RED
            aqi_pointer_shadow.y = aqi_pointer.y = 0
            flash_status(interpret(TRANSLATE, 'OVERRANGE'), 0.75)

        aqi_qual_label.text = interpret(TRANSLATE, label)
        aqi_value.text = str(sensor_aqi)

        # Trend chart
        for i in range(0, len(aqi_trend_chart)):
            aqi_trend_group[len(aqi_trend_chart) - i - 1].y = (
                HEIGHT - int(aqi_trend_chart[i] * HEIGHT) + 1 - 3
            )
            aqi_trend_group[len(aqi_trend_chart) - i - 1].fill = PURPLE
        aqi_trend_chart.pop(0)
        aqi_trend_chart.append(sensor_aqi_norm)
    return sensor_data_valid


play_tone(880, 0.1)

# Define the display groups
image_group = displayio.Group()
co2_trend_group = displayio.Group()
aqi_trend_group = displayio.Group()
reference_group = displayio.Group()

co2_trend_chart = []
point_width = int((WIDTH - 28) / trend_points)
for i in range(0, WIDTH - 28, point_width):
    point = Rect(
        x=(WIDTH - 28) - i,
        y=(HEIGHT - 6),
        width=point_width,
        height=HEIGHT * 2,
        fill=None,
        outline=None,
        stroke=0,
    )
    co2_trend_chart.insert(0, HEIGHT)
    co2_trend_group.append(point)
image_group.append(co2_trend_group)

aqi_trend_chart = []
point_width = int((WIDTH - 28) / trend_points)
for i in range(0, WIDTH - 28, point_width):
    point = Rect(
        x=(WIDTH - 28) - i,
        y=(HEIGHT - 6),
        width=point_width,
        height=point_width,
        fill=None,
        outline=None,
        stroke=0,
    )
    aqi_trend_chart.insert(0, HEIGHT)
    aqi_trend_group.append(point)
image_group.append(aqi_trend_group)

if aqi_sensor_exists:
    aqi_good_scale = Rect(
        x=WIDTH - 10,
        y=HEIGHT - int((50 / 500) * HEIGHT),
        width=10,
        height=int(((50 - 0) / 500) * HEIGHT) + 3,
        fill=GREEN,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(aqi_good_scale)

    aqi_moderate_scale = Rect(
        x=WIDTH - 10,
        y=HEIGHT - int((100 / 500) * HEIGHT),
        width=10,
        height=int(((100 - 50) / 500) * HEIGHT) + 3,
        fill=YELLOW,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(aqi_moderate_scale)

    aqi_sens_unhealthy_scale = Rect(
        x=WIDTH - 10,
        y=HEIGHT - int((150 / 500) * HEIGHT),
        width=10,
        height=int(((150 - 100) / 500) * HEIGHT) + 3,
        fill=ORANGE,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(aqi_sens_unhealthy_scale)

    aqi_unhealthy_scale = Rect(
        x=WIDTH - 10,
        y=HEIGHT - int((200 / 500) * HEIGHT),
        width=10,
        height=int(((200 - 150) / 500) * HEIGHT) + 3,
        fill=RED,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(aqi_unhealthy_scale)

    aqi_very_unhealthy_scale = Rect(
        x=WIDTH - 10,
        y=HEIGHT - int((300 / 500) * HEIGHT),
        width=10,
        height=int(((300 - 200) / 500) * HEIGHT) + 3,
        fill=PURPLE,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(aqi_very_unhealthy_scale)

    aqi_hazardous_scale = Rect(
        x=WIDTH - 10,
        y=HEIGHT - int((500 / 500) * HEIGHT),
        width=10,
        height=int(((500 - 300) / 500) * HEIGHT) + 3,
        fill=MAROON,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(aqi_hazardous_scale)

if co2_sensor_exists:
    co2_good_scale = Rect(
        x=WIDTH - 22,
        y=HEIGHT - int((1000 / 6000) * HEIGHT),
        width=10,
        height=int(((1000 - 0) / 6000) * HEIGHT) + 3,
        fill=GREEN,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(co2_good_scale)

    co2_poor_scale = Rect(
        x=WIDTH - 22,
        y=HEIGHT - int((2000 / 6000) * HEIGHT),
        width=10,
        height=int(((2000 - 1000) / 6000) * HEIGHT) + 3,
        fill=YELLOW,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(co2_poor_scale)

    co2_warning_scale = Rect(
        x=WIDTH - 22,
        y=HEIGHT - int((5000 / 6000) * HEIGHT),
        width=10,
        height=int(((5000 - 2000) / 6000) * HEIGHT) + 3,
        fill=ORANGE,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(co2_warning_scale)

    co2_danger_scale = Rect(
        x=WIDTH - 22,
        y=HEIGHT - int((6000 / 6000) * HEIGHT),
        width=10,
        height=int(((6000 - 5000) / 6000) * HEIGHT) + 3,
        fill=RED,
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(co2_danger_scale)

    co2_alarm_pointer_shadow = Rect(
        x=WIDTH - 25, y=0, width=12, height=4, fill=RED, outline=BLACK, stroke=1
    )
    co2_alarm_pointer_shadow.y = HEIGHT - int((CO2_ALARM[0] / 6000) * HEIGHT)
    reference_group.append(co2_alarm_pointer_shadow)

    co2_alarm_pointer = Rect(
        x=WIDTH - 25,
        y=HEIGHT - int((CO2_ALARM[0] / 6000) * HEIGHT),
        width=12,
        height=3,
        fill=CO2_ALARM[1],
        outline=BLACK,
        stroke=1,
    )
    reference_group.append(co2_alarm_pointer)
    image_group.append(reference_group)

co2_pointer_shadow = Rect(
    x=WIDTH - 25, y=HEIGHT + 2, width=12, height=6, fill=None, outline=BLACK, stroke=1
)
image_group.append(co2_pointer_shadow)

co2_pointer = Rect(
    x=WIDTH - 25, y=HEIGHT + 2, width=12, height=5, fill=None, outline=BLACK, stroke=1
)
image_group.append(co2_pointer)

aqi_pointer_shadow = Rect(
    x=WIDTH - 12, y=HEIGHT + 2, width=11, height=6, fill=None, outline=BLACK, stroke=1
)
image_group.append(aqi_pointer_shadow)

aqi_pointer = Rect(
    x=WIDTH - 12, y=HEIGHT + 2, width=11, height=5, fill=CYAN, outline=BLACK, stroke=1
)
image_group.append(aqi_pointer)

watchdog = Rect(x=1, y=1, width=10, height=10, fill=None, outline=YELLOW, stroke=1)
image_group.append(watchdog)

title_label = Label(font_0, text=interpret(TRANSLATE, SCREEN_TITLE), color=CYAN)
title_label.anchor_point = (0.5, 0)
title_label.anchored_position = ((WIDTH - 20) // 2, 0)
image_group.append(title_label)

status_label = Label(font_0, text=' ', color=None)
status_label.anchor_point = (0.5, 0.5)
status_label.anchored_position = ((WIDTH - 20) // 2, (HEIGHT // 2) + 27)
image_group.append(status_label)

co2_alarm_label = Label(
    font_0, text=interpret(TRANSLATE, CO2_ALARM[2]), color=CO2_ALARM[1]
)
co2_alarm_label.anchor_point = (0, 0)
co2_alarm_label.anchored_position = (5, HEIGHT - 14)
image_group.append(co2_alarm_label)

co2_alarm_value = Label(
    font_0, text=str(CO2_ALARM[0]) if co2_sensor_exists else '----', color=CO2_ALARM[1]
)
co2_alarm_value.anchor_point = (0, 0)
co2_alarm_value.anchored_position = (5, HEIGHT - 28)
image_group.append(co2_alarm_value)

co2_temp_label = Label(font_0, text='°' + TEMP_UNIT, color=CYAN)
co2_temp_label.anchor_point = (0.5, 0)
co2_temp_label.anchored_position = ((WIDTH - 20) // 2, HEIGHT - 14)
image_group.append(co2_temp_label)

co2_temp_value = Label(font_0, text=' ' if co2_sensor_exists else '--', color=CYAN)
co2_temp_value.anchor_point = (0.5, 0)
co2_temp_value.anchored_position = ((WIDTH - 20) // 2, HEIGHT - 28)
image_group.append(co2_temp_value)

co2_humid_label = Label(font_0, text='RH', color=CYAN)
co2_humid_label.anchor_point = (1, 0)
co2_humid_label.anchored_position = (WIDTH - 40, HEIGHT - 14)
image_group.append(co2_humid_label)

co2_humid_value = Label(font_0, text=' ' if co2_sensor_exists else '--', color=CYAN)
co2_humid_value.anchor_point = (1, 0)
co2_humid_value.anchored_position = (WIDTH - 40, HEIGHT - 28)
image_group.append(co2_humid_value)

co2_qual_label = Label(font_0, text=' ', color=None)
co2_qual_label.anchor_point = (0.5, 0.5)
co2_qual_label.anchored_position = ((WIDTH - 20) // 4, HEIGHT // 4)
image_group.append(co2_qual_label)

co2_label = Label(font_0, text='PPM CO2', color=BLUE)
co2_label.anchor_point = (0.5, 0)
co2_label.anchored_position = ((WIDTH - 20) // 4, 4 + (HEIGHT // 2))
image_group.append(co2_label)

co2_value = Label(font_1, text=' ' if co2_sensor_exists else '---', color=WHITE)
co2_value.anchor_point = (0.5, 1.0)
co2_value.anchored_position = ((WIDTH - 20) // 4, HEIGHT // 2)
image_group.append(co2_value)

aqi_qual_label = Label(font_0, text=' ', color=None)
aqi_qual_label.anchor_point = (0.5, 0.5)
aqi_qual_label.anchored_position = (((WIDTH - 26) // 4) * 3, HEIGHT // 4)
image_group.append(aqi_qual_label)

aqi_label = Label(font_0, text='AQI-US', color=BLUE)
aqi_label.anchor_point = (0.5, 0)
aqi_label.anchored_position = (((WIDTH - 26) // 4) * 3, 4 + (HEIGHT // 2))
image_group.append(aqi_label)

aqi_value = Label(font_1, text=' ' if aqi_sensor_exists else '---', color=WHITE)
aqi_value.anchor_point = (0.5, 1.0)
aqi_value.anchored_position = (((WIDTH - 26) // 4) * 3, (HEIGHT // 2))
image_group.append(aqi_value)

# Add panel class group
if panel.button_display_group:
    image_group.append(panel.button_display_group)

# - PRIMARY PROCESS SETUP -
display.show(image_group)
if co2_sensor_exists:
    scd.reset()
    scd.measurement_interval = SENSOR_INTERVAL
    sensor_valid = update_co2_image_frame(blocking=True)
else:
    flash_status(interpret(TRANSLATE, 'NO CO2 SENSOR'), 2.0)

if aqi_sensor_exists:
    update_aqi_image_frame(blocking=True)
else:
    flash_status(interpret(TRANSLATE, 'NO AQI SENSOR'), 2.0)

play_tone(440, 0.1)
play_tone(880, 0.1)

# - PRIMARY PROCESS LOOP -
t0 = time.monotonic()  # Sensor interval timer
while True:
    gc.collect()
    button_pressed, hold_time = panel.read_buttons()
    if button_pressed == 'calibrate':  # Recalibrate CO2 sensor
        if hold_time >= 1.0:
            if co2_sensor_exists:
                flash_status(interpret(TRANSLATE, 'CALIBRATE'), 0.5)
                scd.forced_recalibration_reference = 400
                print('recal ref:', scd.forced_recalibration_reference)
            else:
                flash_status(interpret(TRANSLATE, 'NO CO2 SENSOR'), 0.5)
            play_tone(440, 0.1)  # A4
    if button_pressed == 'temperature':  # Toggle temperature units
        if hold_time >= 1.0:
            flash_status(interpret(TRANSLATE, 'TEMPERATURE'), 0.5)
            if TEMP_UNIT == 'F':
                TEMP_UNIT = 'C'
            else:
                TEMP_UNIT = 'F'
            co2_temp_label.text = '°' + TEMP_UNIT
            play_tone(440, 0.1)
    if button_pressed == 'language':  # Toggle language
        if hold_time >= 1.0:
            flash_status(interpret(TRANSLATE, 'LANGUAGE'), 0.5)
            TRANSLATE = not TRANSLATE
            title_label.text = interpret(TRANSLATE, SCREEN_TITLE)
            co2_alarm_label.text = interpret(TRANSLATE, CO2_ALARM[2])
            play_tone(440, 0.1)
            if TRANSLATE:
                flash_status(interpret(True, 'ENGLISH'), 0.5)
            else:
                flash_status('ENGLISH', 0.5)

    if time.monotonic() - SENSOR_INTERVAL > t0:
        # Acquire sensors
        sensor_valid = update_co2_image_frame()
        update_aqi_image_frame()
        t0 = time.monotonic()
    else:
        watchdog.fill = BLUE
        watchdog.x = int(((time.monotonic() - t0) / SENSOR_INTERVAL) * 10) - 10
        watchdog.y = watchdog.x

    # Test CO2 alarm threshold
    if co2_sensor_exists:
        if co2_value.text != ' ' and float(co2_value.text) >= CO2_ALARM[0]:
            flash_status(interpret(TRANSLATE, 'ALARM'), 0.75)
            if has_neopixel:
                pixels.fill(RED)
            play_tone(880, 0.015)  # A5
            if has_neopixel:
                pixels.fill(BLACK)

    if has_battery_mon:
        # Low battery or invalid CO2 sensor data warning
        battery_volts = round(battery_mon.value * 6.6 / 0xFFF0, 2)
        if (not sensor_valid) and battery_volts < 3.3:
            play_tone(880, 0.030)  # A5
            flash_status(interpret(TRANSLATE, 'LOW BATTERY'), 1)
            flash_status(str(battery_volts) + ' volts', 1)
