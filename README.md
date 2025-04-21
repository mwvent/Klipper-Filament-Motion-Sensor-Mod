A modified Filament Motion Sensor module for Klipper 3D Printers. The vanilla module provides little to no information to help you set the best detection length so I updated it with status keeping and runtime detection length overrides.

Adds the follwing new commands

QUERY_FILAMENT_MOTION SENSOR=<your sensor name>
Returns a few stats on filament distance between encoder events, also if a runout event happens it will return the stats for that helping find the right value for your config.

RESET_FILAMENT_MOTION_STATS SENSOR=<your sensor name>
Rests the stats for query

SET_FILAMENT_MOTION_DETECT_LENGTH SENSOR=<your sensor name> VALUE=<new length>
Temporarily overrides the motion detect length in the printer config. This value is not saved to the config but provides a way of testing new values mid print without restarting Klipper.


To install just drop the .py file in your klipper/klippy/extras folder and in the printer cfg file use filament_motion_sensor_custom in place of filament_motion_sensor. Restart klipper
