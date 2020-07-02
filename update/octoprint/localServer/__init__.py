#!/usr/bin/env python
#-*- coding:utf-8 -*-

import threading
import sys
from time import sleep

from settings import settings
from octoprint.settings import settings as octoSettings
from dealaction import ActionManager
from datasync import DataSyncManager
from octoprint.server import printer
import events as Event

from util.gplQtPipe import QtPipeManager
from util.websocketClient import websocketClientManager
from octoprint.util import to_str

_instance = None


class localServer():	
	""" communicate to octoprint """
	def __init__(self, settingsManager=None, eventManager=None, qtManager=None):
		self._settingsManager  = settingsManager
		self._eventManager    = eventManager
		self._qtManager = qtManager
		self._thread_stop      = False
		self.work = threading.Thread(target=self._work)
		self.work.setDaemon(True)
		if octoSettings().get(["printerParameters", "phoneApp"]):
			self._wscm = websocketClientManager(eventManager = eventManager)
			self._wscm.start_loop()
		
	def _work(self):
		""" _work """
		
		self._eventManager.fire("action_init", payload=None)
		#self._eventManager.fire("action_serial_connect", payload={"port":"/dev/ttyACM0","action":"connect"})
		#self._eventManager.fire("action_serial_connect", payload={"port":"/dev/ttyUSB0","action":"connect"})
		#self._eventManager.fire("action_serial_connect", payload={"port":"VIRTUAL","action":"connect"})
		while not self._thread_stop:
			if sys.platform == "win32":
				sleep(1)
				continue
			else:
				sleep(0.01)
			addr,cmd,data = self._qtManager.receive()
			data=to_str(data, encoding='utf-8')
			print "addr:",addr,", cmd:",cmd,", data:",data
			if addr in self._settingsManager.action_map:
				self._eventManager.fire(self._settingsManager.action_map[addr],payload={"address":addr,"command":cmd,"data":data})
				pass
			else:
				pass
				
	def run(self):
		self.work.start()

def localServerManager():
	st = settings(init=True)
	qm = QtPipeManager()
	am = ActionManager(qtManager=qm)
	em = Event.eventManager()
	Event.CommandTrigger(am)
	sync = DataSyncManager(qtManager=qm, settingsManager=st, eventManager=em, printer=printer)

	global _instance
	if _instance is None:
		_instance = localServer(settingsManager=st, eventManager=em, qtManager=qm)
		_instance.run()
	return _instance

def main(): 
	localserver = localServerManager()
	
if __name__ == "__main__":
	import logging
	main()
	logger = logging.getLogger(__name__)
	logger.info("test serial info")
