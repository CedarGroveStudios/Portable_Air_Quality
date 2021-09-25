# air_mon_config.py
# Initial start-up configuration

from air_mon_colors import *

ALT_LANGUAGE = "FRANCAIS"  # DEUTSCH, FRANCAIS, or PIRATE
TRANSLATE = False  # Start with alternate language
TEMP_UNIT     = "F"   # "F" for Fahrenheit, "C" for Celsius
BRIGHTNESS    = 1.0  # 0.0 to 1.0; 0.75 typical
SENSOR_INTERVAL = 10  # Measurement interval (2 to 1800 seconds)
SOUND = True  # Use sound cues if speaker exists

CO2_ALARM = [2500, RED, "Alarm"]  # CO2 concentration; parts-per-million (PPM)
