# Cedar Grove Portable Air Quality Monitor

### _A portable CO2 and particulate air quality montor_

## Overview

The Portable Air Quality Monitor is a SCD-30 and PMSA003i -based ambient CO2 and particulate concentration measurement (Air Quality Index, AQI) device implemented using CircuitPython version 6.x. The monitor is tuned for the Adafruit PyBadge (https://www.adafruit.com/product/4200) and PyGamer (https://www.adafruit.com/product/4242) handheld gaming platforms. Features include graphical and numeric display of measured CO2 and AQI, qualitative descriptor, and user-configurable alarm setting. The PyBadge/PyGamer platform provides the color display, speaker for the audible alarm (https://www.adafruit.com/product/4227), and room for a LiPo rechargeable battery (https://www.adafruit.com/product/4237). The Adafruit Adafruit SCD-30 - NDIR CO2 Temperature and Humidity Sensor breakout (https://www.adafruit.com/product/4867) is connected to the PyBadge/PyGamer STEMMA connector.

The Indoor Air Quality Monitor bundle folder contains all the files and helpers needed for CircuitPython version 6.x.

Editable user-specified configuration parameters are stored in the _air_mon_config.py_ file. The configuration file specifies temperature units, alarm thresholds, and language.

The primary Portable Air Quality code module detects and adjusts automatically for display resolution including font size. The code was successfully tested on the EdgeBadge, PyPortal, PyPortal Pynt, PyPortal Titano, FunHouse, and Clue boards without requiring modification.

Forced calibration is initiated by pressing the START button on the PyBadge/PyGamer/EdgeBadge. Calibration is currently not supported on other boards.

![Image of Module](https://github.com/CedarGroveStudios/Portable_Air_Quality/blob/main/photos_and_graphics/co2_monitor_board_line-up.png)
