A modified Filament Motion Sensor module for Klipper 3D Printers. The vanilla module provides little to no information to help you set the best detection length so I updated it with status keeping and runtime detection length overrides.

Adds the follwing new commands

QUERY_FILAMENT_MOTION SENSOR=<your sensor name>
Returns a few stats on filament distance between encoder events, also if a runout event happens it will return the stats for that helping find the right value for your config.
Stats that may be returned are -
  No Data: If no events have yet been recorded
  LAST_ENCODER_EVENT_DISTANCE:  The difference between the E position at the time of the last Filament Motion Encoder event and the position before that
  MAX_DISTANCE: The maximum value seen of LAST_ENCODER_EVENT_DISTANCE since the last stats or Klipper reset
  LAST_RUNOUT_ACTUAL_POSITION: The position of the extuder when the last Filament Runout Detection happened
  LAST_RUNOUT_MAX_PERMITTED_POSITION: Filament Runout is determined by the extruder position reaching a higher value than this one without the filament montion encoder responding, the difference between this and last_runout_event_extruder_position can inform what detection distance is needed if things were in fact operating okay

RESET_FILAMENT_MOTION_STATS SENSOR=<your sensor name>
Rests the stats for query

SET_FILAMENT_MOTION_DETECT_LENGTH SENSOR=<your sensor name> VALUE=<new length>
Temporarily overrides the motion detect length in the printer config. This value is not saved to the config but provides a way of testing new values mid print without restarting Klipper.

The following data will also be availible via the Klipper API
filament_detected
enabled
last_encoder_event_extruder_position - The E position at the time of the last Filament Motion Encoder event
last_encoder_event_distance_between_events - The difference between the E position at the time of the last Filament Motion Encoder event and the position before that
last_encoder_event_recorded - False if no encoder event is yet logged since last stats or Klipper reset
last_runout_event_extruder_position - The position of the extuder when the last Filament Runout Detection happened
last_runout_event_max_permitted_extruder_position - Filament Runout is determined by the extruder position reaching a higher value than this one without the filament montion encoder responding, the difference between this and last_runout_event_extruder_position can inform what detection distance is needed if things were in fact operating okay
last_runout_event_recorded - False if no runout has been logged since last stats or Klipper reset
overall_max_distance - The maximum value seen of last_encoder_event_distance_between_events since the last stats or Klipper reset
overall_lastrunout_logged - Used internally by the module

To install just drop the .py file in your klipper/klippy/extras folder and in the printer cfg file use filament_motion_sensor_custom in place of filament_motion_sensor. Restart klipper
