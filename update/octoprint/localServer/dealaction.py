#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging
import threading
import subprocess
import os

from time import sleep

from datasync import GetSyncData
from settings import settings
from settings import key_addr
from octoprint.settings import settings as octoSettings

from server.api import connection
from server.api import job
from server.api import files
from server.api import printer

from octoprint.util.firmwareInstall import InstallFirmware
from octoprint._version import get_versions

_instance=None
NO_CONTENT = ("", 204)

class DealAction():
	def __init__(self, qtManager=None):
		self._logger = logging.getLogger(__name__)
		self._qtManager = qtManager
		self._active = threading.Event()
		self._active.clear()
		self._worker = threading.Thread(target=self._work)
		self._worker.daemon = True
		self._worker.start()
		self.material_run = False
		self.material_init = True
		self.needtozero = True
		self.material_times=0 
		self._xyz_position = {"x":0, "y":0, "z":0}
		
	def _work(self):
		tool_map={"tool0":"tool0_actual","tool1":"tool1_actual"}
		
		while True:
			settings().set(["status","tool"],"null",force=True)
			self._active.wait()
			# brefore load reset
			if self.material_init is True:
				self.material_init = False
				if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
					printer.printerCommand(data= {"commands":settings().get_config()["material"]["init_action"]})	
			extrude_reverse=True
			while  self.material_run==True:
				sleep(1)
				tool = settings().get_config()["status"]["tool"]
				if tool != "null":
					toolTemp = GetSyncData(key=tool_map[tool])
					targetTemp = settings().get_config()["status"]["target_temp"][tool]
					if toolTemp != None and toolTemp >= targetTemp-2:
						printer.printerCommand(data= {"command":"G91"})
						if settings().get_config()["status"]["tool_step"]>0:
							self.material_times=0
							printer.printerCommand(data= {"command":"G1 E5 F150"})
							sleep(0.5)
						elif settings().get_config()["status"]["tool_step"]<0:
							if extrude_reverse:
								extrude_reverse=False
								printer.printerCommand(data= {"command":"G1 E10 F500"})
								printer.printerCommand(data= {"command":"G1 E-20 F900"})
								sleep(1)
								
							self.material_times+=1
							if self.material_times<15:
								printer.printerCommand(data= {"command":"G1 E-5 F300"})
								sleep(0.5)
							elif self.material_times<60:
								printer.printerCommand(data= {"command":"G1 E-10 F1200"})
							else:
								pass
				printer.printerCommand(data= {"commands":["G90","M105"]})
				
	def delayToDoSomething(self, secs=3, action=None, **kws):
		def delay(secs, action, **kws):
			sleep(secs)
			if action and callable(action):
				action(**kws)
		temp = threading.Thread(target=delay, args=(secs, action), kwargs=kws)
		temp.daemon = True
		temp.start()
		
	def executeSystemCommand(self, command):
		def commandExecutioner(command):
			self._logger.info("Executing system command: %s" % command)
			subprocess.Popen(command, shell=True)

		try:
			if isinstance(command, (list, tuple, set)):
				for c in command:
					commandExecutioner(c)
			else:
				commandExecutioner(command)
		except subprocess.CalledProcessError, e:
			self._logger.warn("Command failed with return code %i: %s" % (e.returncode, e.message))
		except Exception, ex:
			self._logger.exception("Command failed")
			
	def getMethodsMap(self):
		_funcs_dict = {}
		funcs_name = filter(lambda et:et.startswith("action"), dir(self))
		for func_name in funcs_name:
			func = getattr(self, func_name)
			if func and callable(func):
				_funcs_dict[func_name] = func
	
		return _funcs_dict
	
	def _serial_connect(self, payload={"port":"VIRTUAL","action":"connect"}):
		if isinstance(payload, dict):
			if payload["port"] in ["VIRTUAL","COM5","/dev/ttyACM0","/dev/ttyUSB0"]:
				port = payload["port"]
			else:
				port = "VIRTUAL"
			if payload["action"] in ["connect","disconnect"]:
				action = payload["action"]
			else:
				action = "connect"
		connection.connectionCommand(request={"command":action,"port":port,"baudrate":115200,"autoconnect":True})
	
	def print_ctrl(self,payload={"action":"pause","fileName":None}):
		result = False
		if payload["action"] in ["print","pause","cancel","recover","delete"]:
			action = payload["action"]
		else:
			action="pause"
		if action=="print":
			files.gcodeFileCommand(filename=payload["fileName"], target="local", request={"command":"select", "print":True})
			result = True
		elif action=="pause" and GetSyncData(key="state") is not None and GetSyncData(key="state") != "Operational":
			job.controlJob(request={"command":"pause"})
			result = True
		elif action=="cancel":
			job.controlJob(request={"command":"cancel"})
			result = True
		elif action=="recover":
			filename = octoSettings().get(["printerParameters","lastFileName"])
			files.gcodeFileCommand(filename=filename, target="local", request={"command":"select", "print":True, "recover":True})
			result = True
		elif action == "delete":
			if payload["fileName"] is not None:
				files.deleteGcodeFile(filename=payload["fileName"], target="local")
				result = True
		return result
						
	def set_temp(self, payload={"tool":"tool0","target_temp":0}):
		if payload["tool"] in ["tool0","tool1","bed","chamber"]:
			tool = payload["tool"]
		else:
			tool = "tool0"
			
		if tool in ["tool0","tool1"]:
			if payload["target_temp"] >= 170 and payload["target_temp"] <= 260:
				target_temp = payload["target_temp"]
			else:
				target_temp = 190
		elif tool is "bed":
			if payload["target_temp"] >= 50 and payload["target_temp"] <= 100:
				target_temp = payload["target_temp"]
			else:
				target_temp = 50
		elif tool is "chamber":
			if payload["target_temp"] >= 40 and payload["target_temp"] <= 80:
				target_temp = payload["target_temp"]
			else:
				target_temp = 50
				
		settings().set(["status", "target_temp", tool], target_temp, force=True)
			
	def tool_ctrl(self,payload={"witchE":"tool0","action":"stop"}):
		result = False
		if payload["witchE"] in ["tool0","tool1"]:
			witchE = payload["witchE"]
		else:
			witchE="tool0"
		if payload["action"] in ["stop","extrude","retreate","initAction"]:
			action = payload["action"]
		else:
			action = "stop"
		
		if action is "stop":
			self._active.clear()
			settings().set(["status","tool"],"null",force = True)
			self.material_run = False
			if GetSyncData(key="state") is not None:
				if GetSyncData(key="state") == "Operational":
					printer.printerToolCommand(request={"command":"target","targets":{"tool0":0}})
					printer.printerToolCommand(request={"command":"target","targets":{"tool1":0}})
					result = True
				elif GetSyncData(key="state") == "Paused":
					usedTools = octoSettings().get(["printerParameters", "usedTools"])
					for usedTool in usedTools:
						tool = "tool%s" %(str(usedTool[0]))
						printer.printerToolCommand(request={"command":"target","targets":{tool:170}})
					result = True
		elif action is "initAction":
			self.material_init = True
			result = False
		else:
			step={"extrude":5, "retreate":-5}
			settings().set(["status","tool_step"],step[action],force=True)
			if self.material_init is False:
				if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational": # add by evan, for avoid crash the nozzle when paused
					if self.needtozero is True:
						printer.printerCommand(data= {"commands":settings().get_config()["material"]["init_action"]})

			printer.printerToolCommand(request={"command":"target","targets":{witchE:settings().get_config()["status"]["target_temp"][witchE]}})
			printer.printerToolCommand(request={"command":"select","tool":witchE})
			settings().set(["status","tool"],witchE,force=True)
			self.material_run=True
			self.needtozero = False
			self._active.set()
			result = True
		return result	
					
	def level_bed(self,payload={"action":"failed", "value":0}):
		machineType = octoSettings().get(["printerParameters","machineType"])
		if machineType is 0:
			if payload["action"] in ["startNormal","startCompensate","startAdjust","startFine","succeedNormal","succeedCompensate","succeedAdjust","succeedMicro","failed"]:
				action = payload["action"]
			else:
				action="failed"
			if action=="startNormal":
				printer.printerCommand(data= {"command":"M12"})
			elif action == "startCompensate":
				printer.printerCommand(data= {"command":"M12 Z8"})
			elif action == "startAdjust":
				printer.printerCommand(data= {"command":"M206 P268 T1 F%s"%(8-self._xyz_position["z"])})
				printer.printerCommand(data= {"command":"M12"})
			elif action == "startFine":
				value = float(payload["value"])
				printer.printerCommand(data= {"command":"M206 P268 T1 I%s"%(value)})
				printer.printerCommand(data= {"command":"M12"})
			elif action =="succeedNormal":
				pass
			elif action == "succeedCompensate":
				self.move_xyz_axis("z", 8)
			elif action == "succeedAdjust":
				pass
			elif action == "succeedMicro":
				pass
			elif action =="failed":
				pass
		elif machineType is 1:
			if payload["action"] in ["bedLevelStartNormal","bedLevelFirst","bedLevelSecond","bedLevelThird","bedLevelDone","startCompensate","startAdjust","startFine","succeedCompensate","succeedAdjust","succeedMicro","failed"]:
				action = payload["action"]
			else:
				action="failed"
			if action=="bedLevelStartNormal":
				printer.printerCommand(data= {"command":"M11 S0"})
			elif action == "bedLevelFirst":
				printer.printerCommand(data= {"command":"M11 S1"})
			elif action == "bedLevelSecond":
				printer.printerCommand(data= {"command":"M11 S2"})
			elif action == "bedLevelThird":
				printer.printerCommand(data= {"command":"M11 S3"})
			elif action == "bedLevelDone":
				printer.printerCommand(data= {"command":"M11 S4"})
			elif action == "startCompensate":
				printer.printerCommand(data= {"command":"M262 S1"}) # turn on the light
				printer.printerCommand(data= {"command":"M12 Z12"})
			elif action == "startAdjust":
				printer.printerCommand(data= {"command":"M206 P268 T1 F%s"%(12-self._xyz_position["z"])})
				printer.printerCommand(data= {"command":"M12"})
				printer.printerCommand(data= {"command":"M262 S0"}) # turn off the light
			elif action == "startFine":
				value = float(payload["value"])
				printer.printerCommand(data= {"command":"M206 P268 T1 I%s"%(value)})
				printer.printerCommand(data= {"command":"M12"})
			elif action == "succeedCompensate":
				self.move_xyz_axis("z", 8)
			elif action == "succeedAdjust":
				pass
			elif action == "succeedMicro":
				pass			
			elif action == "failed":
				pass			

	def motor_reset(self,payload={"axes":["x","y","z"]}):
		printer.printerPrintheadCommand(request= {"command":"home","axes":payload["axes"]})
		
	def fan_ctrl(self,payload={"onoff":"off"}):
		if payload["onoff"] in ["off","on"]:
			onoff = payload["onoff"]
		else:
			onoff = "off"
		if onoff =="on":
			printer.printerCommand(data= {"command":"M106 S255"})
		elif onoff == "off":
			printer.printerCommand(data= {"command":"M106 S0"})
		return True
			
	def motor_disable(self,payload=None):
		if GetSyncData(key="state") is not None and GetSyncData(key="state")=="Operational":
			printer.printerCommand(data= {"command":"M84"})
			return True
		return False
			
	def water_cooling(self,payload={"onoff":"off"}):
		if payload["onoff"] in ["off","on"]:
			onoff = payload["onoff"]
		else:
			onoff = "off"
		if onoff == "on":
			printer.printerCommand(data= {"command":"M260 S1"})
		elif onoff == "off":
			printer.printerCommand(data= {"command":"M260 S0"})
		return True
			
	def bed_heat(self, payload={"onoff":"off"}):
		if payload["onoff"] in ["off","on"]:
			onoff = payload["onoff"]
		else:
			onoff = "off"
		target_temp = settings().get_config()["status"]["target_temp"]["bed"]
		if onoff == "on":
			printer.printerBedCommand(request={"command":"target","target":target_temp})
		elif onoff == "off":
			printer.printerBedCommand(request={"command":"target","target":0})
		return True
			
	def chamber_heat(self,payload={"onoff":"off"}):
		#if GetSyncData(key="state") is not None and GetSyncData(key="state")=="Operational":
		if payload["onoff"] in ["off","on"]:
			onoff = payload["onoff"]
		else:
			onoff = "off"
		target_temp = settings().get_config()["status"]["target_temp"]["chamber"]
		if onoff == "on":
			printer.printerToolCommand(request={"command":"target","targets":{"chamber":target_temp}})
		elif onoff == "off":
			printer.printerToolCommand(request={"command":"target","targets":{"chamber":0}})
		return True
		#return False

	def action_init(self,payload=None):
		self._qtManager.send(key_addr["addr_octoprint_version"], 0, get_versions()["version"])
		pass
		
	def action_serial_connect(self,payload={"port":"VIRTUAL","action":"connect"}):
		self.delayToDoSomething(secs=1,action=self._serial_connect,payload=payload)
		
	def action_print_ctrl(self,payload=None):
		self.needtozero = True
		cmd = payload["command"]
		fileName = payload["data"]
		if cmd in range(5):
			if self.print_ctrl(payload={"action":["print","pause","cancel","recover","delete"][cmd], "fileName":fileName}):
				self._qtManager.send(key_addr["addr_print_ctrl"], cmd, 0)
			
	def action_level_bed(self,payload=None):
		self.needtozero = True
		machineType = octoSettings().get(["printerParameters","machineType"])		
		if GetSyncData(key="state") is not None and GetSyncData(key="state")=="Operational":
			cmd = payload["command"]
			if machineType is 0:
				if cmd in range(7):
					action = ["startNormal","startCompensate","startAdjust","startFine","succeedNormal","succeedCompensate","succeedAdjust","succeedMicro","failed"]
					if payload["data"] is not None:
						value = float(payload["data"])
					else:
						value = 0
						
					self.level_bed(payload={"action": action[cmd], "value":value})
			elif machineType is 1:
				if cmd in range(12):
					action = ["bedLevelStartNormal","bedLevelFirst","bedLevelSecond","bedLevelThird","bedLevelDone","startCompensate","startAdjust","startFine","succeedCompensate","succeedAdjust","succeedMicro","failed"]
					if payload["data"] is not None:
						value = float(payload["data"])
					else:
						value = 0
					self.level_bed(payload={"action": action[cmd], "value":value})				

	def action_temp_select(self, payload=None):
		if self.material_run is False:
			cmd = payload["command"]
			if cmd in range(4):
				tool = ["tool0","tool1","bed","chamber"][cmd]
				target_temp = float(payload["data"])
				self.set_temp(payload={"tool":tool, "target_temp":target_temp})
				self._qtManager.send(key_addr["addr_temp_select"], cmd, target_temp)

	def action_material(self,payload=None):
		if GetSyncData(key="state") is not None and GetSyncData(key="state")!="Printing":
			cmd = payload["command"]
			tool = ord(payload["data"][0])
			if cmd in range(4) and tool in range(2):
				if self.tool_ctrl(payload={"witchE":["tool0","tool1"][tool],"action":["stop","extrude","retreate","initAction"][cmd]}):
					if cmd is 0:
						printer.printerCommand(data= {"command":"M106 S0"})
					elif cmd is 1 or cmd is 2:
						printer.printerCommand(data= {"command":"M106 S255"})
					self._qtManager.send(key_addr["addr_material"], cmd, chr(tool))

	def action_x_left_continuous(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			printer.printerPrintheadCommand(request= {"command":"jogInverted","x":1})
			#printer.printerCommand(data= {"commands":["G91","G1 X1 F600","G90"]})
			
	def action_x_right_continuous(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			printer.printerPrintheadCommand(request= {"command":"jogInverted","x":-1})
			#printer.printerCommand(data= {"commands":["G91","G1 X-1 F600","G90"]})
			
	def action_y_forward_continuous(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			printer.printerPrintheadCommand(request= {"command":"jogInverted","y":1})
			#printer.printerCommand(data= {"commands":["G91","G1 Y1 F600","G90"]})
			
	def action_y_backward_continuous(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			printer.printerPrintheadCommand(request= {"command":"jogInverted","y":-1})
			#printer.printerCommand(data= {"commands":["G91","G1 Y-1 F600","G90"]})
				
			
	def action_z_up_continuous(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			printer.printerPrintheadCommand(request= {"command":"jogInverted","z":1})
			#printer.printerCommand(data= {"commands":["G91","G1 Z-1 F600","G90"]})
			
	def action_z_down_continuous(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			printer.printerPrintheadCommand(request= {"command":"jogInverted","z":-1})
			#printer.printerCommand(data= {"commands":["G91","G1 Z1 F600","G90"]})
			
	def action_xyz_reset(self,payload=None):
		self.needtozero = True
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			cmd = payload["command"]
			if cmd in range(2):
				self.motor_reset(payload={"axes":[["x","y"],["z"]][cmd]})
				
	def action_switch(self,payload=None):
		self.needtozero = True
		machineType = octoSettings().get(["printerParameters","machineType"])
		cmd = payload["command"]
		value = ord(payload["data"][0])
		if machineType is 0:
			if cmd in range(5) and value in range(2):
				#if [self.fan_ctrl,self.motor_disable,self.bed_heat,self.chamber_heat,self.water_cooling,self.door_ctrl][cmd](payload={"onoff":["off","on"][value]}) == True:
				if [self.fan_ctrl,self.motor_disable,self.bed_heat,self.chamber_heat,self.water_cooling][cmd](payload={"onoff":["off","on"][value]}) == True:
					self._qtManager.send(key_addr["addr_switch"],cmd,chr(value))
		elif machineType is 1:
			if cmd in range(5) and value in range(2):
				if [self.fan_ctrl,self.motor_disable,self.bed_heat,self.chamber_heat,self.water_cooling][cmd](payload={"onoff":["off","on"][value]}) == True:
					self._qtManager.send(key_addr["addr_switch"],cmd,chr(value))

	def action_setings_reset(self,payload=None):
		pass
			
	def action_power_off(self,payload=None):
		if GetSyncData(key="state") is not None and GetSyncData(key="state") == "Operational":
			job.controlJobEx(request={"command":"powerOff"})
	def action_material_comfirm(self,payload=None):
		printer.printerCommand(data= {"command":"M15 S0"})
			
	def action_set_auto_power_off(self, payload=None):
		cmd = payload["command"]
		job.controlJobEx(request={"command":"autoPowerOff", "mode": cmd})
		
	def action_firmware_update(self, payload=None):
		fileName = "/home/fa/udisk/update/m3/Printer_3D.our"
		if os.path.exists(fileName):
			install = InstallFirmware(fileName)
			if install._state == install.STATE_FINISHED:
				self._qtManager.send(key_addr["addr_firmware_update"], 0, 0)
			else:
				self._qtManager.send(key_addr["addr_firmware_update"], 1, 0)
		else:
			self._qtManager.send(key_addr["addr_firmware_update"], 1, 0)

	def action_firmware_auto_update(self, payload=None):
		fileNameAuto = "/home/fa/qtEmbedded/bin/screen/icon/Printer_3D.our"
		if os.path.exists(fileNameAuto):
			install = InstallFirmware(fileNameAuto)
			if install._state == install.STATE_FINISHED:
				self._qtManager.send(key_addr["addr_firmware_auto_update"], 0, 0)
			else:
				self._qtManager.send(key_addr["addr_firmware_auto_update"], 1, 0)
		else:
			self._qtManager.send(key_addr["addr_firmware_auto_update"], 1, 0)

	def move_xyz_axis(self, axis, position):
		if position > 0:
			self._xyz_position[axis] = position
		else:
			self._xyz_position[axis] = 1
		printer.printerCommand(data= {"commands":["G90","G1 %s%s F600"%(axis.upper(), position)]})
				
	def action_move_xyz_axis(self, payload=None):
		self.needtozero = True
		cmd = payload["command"]
		axis = ["x", "y", "z"][cmd]
		amount = float(payload["data"])
		self.move_xyz_axis(axis, self._xyz_position[axis]+amount)
						
	def action_test01(self, payload=None):
		print "action_test01"
		
	def action_test02(self, payload=None):
		print "action_test02"
										
def ActionManager(qtManager = None):
	global _instance
	if _instance is None:
		print "_instance ActionManager"
		_instance=DealAction(qtManager)
	return _instance

if __name__=="__main__":
	am=ActionManager()
	acMaps=am.getMethodsMap()
	print "ok"
