# Filament Motion Sensor Module
#
# Copyright (C) 2021 Joshua Wherrett <thejoshw.code@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from inspect import signature
from . import filament_switch_sensor

CHECK_RUNOUT_TIMEOUT = .250

class EncoderSensorCustom:
    def __init__(self, config):
        # Read config
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        switch_pin = config.get('switch_pin')
        self.extruder_name = config.get('extruder')
        self.detection_length = config.getfloat(
                'detection_length', 7., above=0.)
        # Configure pins
        buttons = self.printer.load_object(config, 'buttons')
        buttons.register_buttons([switch_pin], self.encoder_event)
        # Get printer objects
        self.gcode = self.printer.lookup_object('gcode')
        self.reactor = self.printer.get_reactor()
        self.runout_helper = filament_switch_sensor.RunoutHelper(config)
        self.olderVersionHelper = len(signature(self.runout_helper.note_filament_present).parameters) == 1
        self.extruder = None
        self.estimated_print_time = None
        # Initialise internal state
        self.filament_runout_pos = None
        self.resetMotionStats()
        self.gcode.register_mux_command(
            "QUERY_FILAMENT_MOTION", "SENSOR", self.name,
            self.cmd_QUERY_FILAMENT_MOTION,
            desc=self.cmd_QUERY_FILAMENT_MOTION_help)
        self.gcode.register_mux_command(
            "RESET_FILAMENT_MOTION_STATS", "SENSOR", self.name,
            self.cmd_RESET_FILAMENT_MOTION_STATS,
            desc=self.cmd_RESET_FILAMENT_MOTION_STATS_help)
        self.gcode.register_mux_command(
            "SET_FILAMENT_MOTION_DETECT_LENGTH", "SENSOR", self.name,
            self.cmd_SET_FILAMENT_MOTION_DETECT_LENGTH,
            desc=self.cmd_SET_FILAMENT_MOTION_DETECT_LENGTH_help)
        # Register commands and event handlers
        self.printer.register_event_handler('klippy:ready',
                self._handle_ready)
        self.printer.register_event_handler('idle_timeout:printing',
                self._handle_printing)
        self.printer.register_event_handler('idle_timeout:ready',
                self._handle_not_printing)
        self.printer.register_event_handler('idle_timeout:idle',
                self._handle_not_printing)

    def resetMotionStats(self):
        self.mstats = {
            "last_encoder_event" : {
                "extruder_position" : 0,
                "distance_between_events" : 0,
                "recorded" : False
            },
            "last_runout_event" : {
                "extruder_position" : 0,
                "max_permitted_extruder_position" : 0,
                "recorded" : False
            },
            "overall" : {
                "max_distance" : 0,
                "lastrunout_logged" : False
            }
        }   

    def cmd_QUERY_FILAMENT_MOTION(self, gcmd):
        msgs = []
        if self.mstats["last_encoder_event"]["recorded"] :
            msgs.append("LAST_ENCODER_EVENT_DISTANCE: %.2f" % (self.mstats["last_encoder_event"]["distance_between_events"]))
            msgs.append("MAX_DISTANCE: %.2f" % (self.mstats["overall"]["max_distance"]))
        if self.mstats["last_runout_event"]["recorded"] :
            msgs.append("LAST_RUNOUT_ACTUAL_POSITION: %.2f" % (self.mstats["last_runout_event"]["extruder_position"]))
            msgs.append("LAST_RUNOUT_MAX_PERMITTED_POSITION: %.2f" % (self.mstats["last_runout_event"]["max_permitted_extruder_position"]))
        if len(msgs) > 0 :
            gcmd.respond_info("\n".join(msgs)+"\n")
        else :
            gcmd.respond_info("No Data\n")
    cmd_QUERY_FILAMENT_MOTION_help = "Read Filament Motion Sensor Stats\n"

    def cmd_RESET_FILAMENT_MOTION_STATS(self, gcmd):
        self.resetMotionStats()
        gcmd.respond_info("Stats Reset")
    cmd_RESET_FILAMENT_MOTION_STATS_help = "Reset Filament Motion Sensor Stats\n"

    def cmd_SET_FILAMENT_MOTION_DETECT_LENGTH(self, gcmd):
        newVal = gcmd.get_float("VALUE")
        self.detection_length = newVal
        gcmd.respond_info("Value updated - this will only take effect until klipper reload")
    cmd_SET_FILAMENT_MOTION_DETECT_LENGTH_help = "Override the motion detect length for SENSOR temporarily until klipper reload with VALUE\n"

    def get_status(self, eventtime) :
        status =  self.runout_helper.get_status(eventtime)
        for statkey in self.mstats.keys() :
            for substatkey in self.mstats[statkey] :
                status[statkey + "_" + substatkey] = self.mstats[statkey][substatkey]
        return status
    
    def _handle_ready(self):
        self.extruder = self.printer.lookup_object(self.extruder_name)
        self.estimated_print_time = (
                self.printer.lookup_object('mcu').estimated_print_time)
        self._update_filament_runout_pos()
        self._extruder_pos_update_timer = self.reactor.register_timer(
                self._extruder_pos_update_event)
    def _handle_printing(self, print_time):
        self.reactor.update_timer(self._extruder_pos_update_timer,
                self.reactor.NOW)
    def _handle_not_printing(self, print_time):
        self.reactor.update_timer(self._extruder_pos_update_timer,
                self.reactor.NEVER)
    def _get_extruder_pos(self, eventtime=None):
        if eventtime is None:
            eventtime = self.reactor.monotonic()
        print_time = self.estimated_print_time(eventtime)
        return self.extruder.find_past_position(print_time)
    
    def _extruder_pos_update_event(self, eventtime):
        extruder_pos = self._get_extruder_pos(eventtime)
        filamentPresent = extruder_pos < self.filament_runout_pos
        if filamentPresent :
            self.mstats["overall"]["lastrunout_logged"] = False
        if not filamentPresent and not self.mstats["overall"]["lastrunout_logged"] :
            self.mstats["overall"]["lastrunout_logged"] = True
            self.mstats["last_runout_event"]["extruder_position"] = extruder_pos
            self.mstats["last_runout_event"]["max_permitted_extruder_position"] = self.filament_runout_pos
            self.mstats["last_runout_event"]["recorded"] = True
        # Pass values to helper
        if not self.olderVersionHelper :
            self.runout_helper.note_filament_present(eventtime, filamentPresent)
        else :
            self.runout_helper.note_filament_present(filamentPresent)
        return eventtime + CHECK_RUNOUT_TIMEOUT

    def _update_filament_runout_pos(self, eventtime=None):
        if eventtime is None:
            eventtime = self.reactor.monotonic()
        extruder_pos = self._get_extruder_pos(eventtime)
        prevPos = self.mstats["last_encoder_event"]["extruder_position"]
        if not self.mstats["last_encoder_event"]["recorded"] :
            prevPos = extruder_pos
        dist = extruder_pos - prevPos
        prevMaxDist = self.mstats["overall"]["max_distance"]
        self.mstats["last_encoder_event"]["extruder_position"] = extruder_pos
        self.mstats["last_encoder_event"]["distance_between_events"] = dist
        self.mstats["overall"]["max_distance"] = max(prevMaxDist, dist)
        self.mstats["last_encoder_event"]["recorded"] = True
        self.filament_runout_pos = (extruder_pos + self.detection_length)

    def encoder_event(self, eventtime, state):
        self.inputPinState = state
        if self.extruder is not None:
            self._update_filament_runout_pos(eventtime)
            # Check for filament insertion
            # Filament is always assumed to be present on an encoder event
            if not self.olderVersionHelper :
                self.runout_helper.note_filament_present(eventtime, True)
            else :
                self.runout_helper.note_filament_present(True)

def load_config_prefix(config):
    return EncoderSensorCustom(config)
    

