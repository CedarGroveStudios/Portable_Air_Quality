# Cedar Grove Portable Air Quality Monitor

### _A portable CO2 and particulate air quality montor_
### _for CircuitPython v7.0.0_

## Overview

The Portable Air Quality Monitor is a SCD-30 and PMSA003i -based ambient CO2 and particulate concentration measurement (Air Quality Index, AQI) device implemented using CircuitPython version 6.x. The monitor is tuned for the Adafruit PyBadge (https://www.adafruit.com/product/4200) and PyGamer (https://www.adafruit.com/product/4242) handheld gaming platforms. Features include graphical and numeric display of measured CO2 and AQI, qualitative descriptor, and user-configurable CO2 alarm setting. The PyBadge/PyGamer platform provides the color display, speaker for the audible alarm (https://www.adafruit.com/product/4227), and room for a LiPo rechargeable battery (https://www.adafruit.com/product/4237). The Adafruit Adafruit SCD-30 - NDIR CO2 Temperature and Humidity Sensor breakout (https://www.adafruit.com/product/4867) and Adafruit PMSA003I Air Quality Breakout (https://www.adafruit.com/product/4632) are connected to the PyBadge/PyGamer STEMMA connector.

The Portable Air Quality Monitor _bundle_ folder contains all the files and helpers needed for CircuitPython version 7.0.0.

Editable user-specified configuration parameters are stored in the _air_mon_config.py_ file. The configuration file specifies start-up temperature units, alarm thresholds, and language. Currently, only English and German language translations are supported, but more are planned.

The primary Portable Air Quality code module detects and adjusts automatically for display resolution including font size. The code was successfully tested on the PyBadge, PyGamer, EdgeBadge,  and PyPortal without requiring modification. Testing with the PyPortal Pynt, PyPortal Titano, and FunHouse are planned. Because of limited memory, the CLUE board will not be supported.

Forced CO2 sensor calibration is initiated by pressing and holding the START button on the PyBadge/PyGamer/EdgeBadge for one second. Forced calibration is initiated by touching and holding the middle portion of the PyPortal touchscreen or pressing and holding the FunHouse center button.

Pressing and holding the PyBadge SELECT button changes temperature units. For other boards, touch and hold the lower portion of the PyPortal touchscreen or the FunHouse lower button.

The PyBadge A button toggles between languages. To switch languages on the PyPortal, touch and hold the upper portion of the touchscreen. Press and hold the FunHouse top button to switch languages.

Thank you to @effiksmusic for the German translation.

![Image of Module](https://github.com/CedarGroveStudios/Portable_Air_Quality/blob/main/photos_and_graphics/DSC06364.JPG)
