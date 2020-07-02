#-*- coding=gbk -*-
__author__ = "_guess_"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import sys
import os
import yaml
import logging
import re
import uuid

APPNAME="LocalServer"

instance = None

def settings(init=False, configfile=None, basedir=None):
	global instance
	if instance is None:
		if init:
			instance = Settings(configfile, basedir)
		else:
			raise ValueError("Settings not initialized yet")
	return instance

default_settings = {
    "printerParameters":{
            "platform":{"x":155,"y":155,"z":160},
            "invertAxes":{"x":1,"y":1,"z":-1},
            "movementSpeed":{"x": 6000,"y": 6000,"z": 1200,"e": 300},
            "step":1
            },
    "bed_level":{
            "finished":["G1 Z140 F1500"]
            },
    "material":{
            "init_action":["G21","G90","G28","G1 X127 Y127 Z100 F1900"],
            },
    "status":{
            "error":False,
            "target_temp":{
                    "tool0":190,
                    "tool1":190,
                    "bed":50,
                    "chamber":50,
                    },
            "tool":"tool0",
            "tool_step":1,
            "fan":"disable",
            "water_cooling":"disable",
            "chamber":"disable",
            "motor_disable":False
            },
}

key_actions = {
        "action_print_ctrl":0x01,
        "action_level_bed":0x02,
        "action_material":0x03,
        "action_x_left_continuous":0x04,
        "action_x_right_continuous":0x05,
        "action_y_forward_continuous":0x06,
        "action_y_backward_continuous":0x07,
        "action_z_up_continuous":0x08,
        "action_z_down_continuous":0x09,
        "action_xyz_reset":0x0A,
        "action_switch":0x0B,
        "action_setings_reset":0x0C,
        "action_temp_select":0x0D,
        "action_power_off":0x0E,
        "action_set_auto_power_off":0x0F,
        "action_firmware_update":0x10,
        "action_move_xyz_axis":0x11,
        "action_material_comfirm":0x12, # add by evan, for matrial-confirm
        "action_firmware_auto_update":0x16,
}

key_addr = {
        # WR
        "addr_print_ctrl":0x01,
        "addr_level_bed":0x02,
        "addr_material":0x03,
        "addr_x_left_continuous":0x04,
        "addr_x_right_continuous":0x05,
        "addr_y_forward_continuous":0x06,
        "addr_y_backward_continuous":0x07,
        "addr_z_up_continuous":0x08,
        "addr_z_down_continuous":0x09,
        "addr_xyz_reset":0x0A,
        "addr_switch":0x0B,
        "addr_settings_reset":0x0C,
        "addr_temp_select":0x0D,
        "addr_power_off":0x0E,
        "addr_set_auto_power_off":0x0F,
        "addr_firmware_update":0x10,
        "addr_move_xyz_axis":0x11,
        "addr_firmware_auto_update":0x16,
        # WO
        "addr_printer_state":0x20,
        "addr_temp_actual":0x21,
        "addr_temp_target":0x22,
        "addr_print_file_name":0x24,
        "addr_print_file_size":0x25,
        "addr_progress_completion":0x26,
        "addr_print_time":0x27,
        "addr_exception_abort":0x28,
        "addr_level_bed_state":0x29,
        "addr_material_blocked0":0x2A,
        "addr_request_power_off":0x2B,
        "addr_print_job_aborted":0x2C,
        "addr_about_information": 0x2D,
        "addr_material_lost0":0x2F, # add by evan, for material-lost
        "addr_material_blocked1":0x30,
        "addr_material_lost1":0x31,
        "addr_handle_tip":0x32, # add by evan, for pause-tip
        "addr_remaining_material":0x33, # add by evan, for remaining-material
        "addr_show_error_message":0x40, # add by evan, for show error message
        "addr_connecting_state":0x41, # add by evan, for process the problem while the machine is in the state of connecting
}

	
valid_boolean_trues = [True, "true", "yes", "y", "1"]

class Settings(object):

	def __init__(self, configfile=None, basedir=None):
		self._logger = logging.getLogger(__name__)

		self.settings_dir = None

		self._config = None
		self._dirty = False
		self.action_map = {}
		
		#if self.action_map is None:
		self._getkeyvalue(key_actions)		
		
		
		self._init_settings_dir(basedir)

		if configfile is not None:
			self._configfile = configfile
		else:
			self._configfile = os.path.join(self.settings_dir, "localsvrconfig.yaml")
	
		self.load(migrate=True)
			
	def _getkeyvalue(self,key_action):
		if isinstance(key_action,dict):
			for key in key_action:
				if isinstance(key_action[key],dict):
					self._getkeyvalue(key_action[key])
				else:
					self.action_map[key_action[key]]=key
					
	def _init_settings_dir(self, basedir):
		if basedir is not None:
			self.settings_dir = basedir
		else:
			self.settings_dir = _resolveSettingsDir(APPNAME)

		if not os.path.isdir(self.settings_dir):
			os.makedirs(self.settings_dir)

	def get_config(self):
		return self._config

	#~~ load and save

	def load(self, migrate=False):
		if os.path.exists(self._configfile) and os.path.isfile(self._configfile):
			with open(self._configfile, "r") as f:
				self._config = yaml.safe_load(f)
		# chamged from else to handle cases where the file exists, but is empty / 0 bytes
		if not self._config:
			self._config = {}

		if migrate:
			self._migrateConfig()

	def _migrateConfig(self):
		if not self._config:
			self._config=default_settings
			self.save(force=True)
			self._logger.info("save default config")
			return	
		

	def save(self, force=False):
		if not self._dirty and not force:
			return

		with open(self._configfile, "wb") as configFile:
			yaml.safe_dump(self._config, configFile, default_flow_style=False, indent="    ", allow_unicode=True)
			self._dirty = False
		self.load()

	#~~ getter

	def get(self, path, asdict=False):
		if len(path) == 0:
			return None

		config = self._config
		defaults = default_settings

		while len(path) > 1:
			key = path.pop(0)
			if key in config.keys() and key in defaults.keys():
				config = config[key]
				defaults = defaults[key]
			elif key in defaults.keys():
				config = {}
				defaults = defaults[key]
			else:
				return None

		k = path.pop(0)
		if not isinstance(k, (list, tuple)):
			keys = [k]
		else:
			keys = k

		if asdict:
			results = {}
		else:
			results = []
		for key in keys:
			if key in config.keys():
				value = config[key]
			elif key in defaults:
				value = defaults[key]
			else:
				value = None

			if asdict:
				results[key] = value
			else:
				results.append(value)

		if not isinstance(k, (list, tuple)):
			if asdict:
				return results.values().pop()
			else:
				return results.pop()
		else:
			return results

	#~~ setter		
	def set(self, path, value, force=False):
		if len(path) == 0:
			return

		config = self._config
		defaults = default_settings

		while len(path) > 1:
			key = path.pop(0)
			if key in config.keys() and key in defaults.keys():
				config = config[key]
				defaults = defaults[key]
			elif key in defaults.keys():
				config[key] = {}
				config = config[key]
				defaults = defaults[key]
			else:
				return

		key = path.pop(0)
		if not force and key in defaults.keys() and key in config.keys() and defaults[key] == value:
			del config[key]
			self._dirty = True
		elif force or (not key in config.keys() and defaults[key] != value) or (key in config.keys() and config[key] != value):
			if value is None:
				del config[key]
			else:
				config[key] = value
			self._dirty = True

def _resolveSettingsDir(applicationName):
	if sys.platform == "darwin":
		from AppKit import NSSearchPathForDirectoriesInDomains
		return os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], applicationName)
	elif sys.platform == "win32":
		return os.path.join(os.environ["APPDATA"], applicationName)
	else:
		return os.path.expanduser(os.path.join("~", "." + applicationName.lower()))
