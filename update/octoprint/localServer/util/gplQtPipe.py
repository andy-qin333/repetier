#-*- coding:utf-8 -*-
#!/usr/bin/env python

__license__ = "GPL (General Public License)"
__author__  = "Bruce <Bruce.zhang@ouring.com.cn>"
__date__    = "2016-08-1 (version 0.1)"

import os
import sys
import stat
import signal
import time
import Queue
import select
import logging
import threading
from octoprint.util import to_str

_instance = None

class gplQtPipe():
	""" 
	process to process communication
	notes: this class must be use under linux!
	"""
	def __init__(self, sendQueneSize=10, recviveQueneSize=10, enable_logger=False):
		
		self._logger = logging.getLogger(__name__)
		if enable_logger:
			logging.basicConfig(level=logging.DEBUG)
		else:
			logging.basicConfig()
			
		self._readfifo = "/tmp/qt2octo"
		self._writefifo = "/tmp/octo2qt"

		self._write_quene = Queue.Queue(sendQueneSize)
		self._write_mutex = threading.Lock()
		self._write_sem = threading.Semaphore(0)
		self._sender = threading.Thread(target=self._send)

		self._read_quene = Queue.Queue(recviveQueneSize)
		self._read_mutex = threading.Lock()
		self._read_sem = threading.Semaphore(0)
		self._receiver = threading.Thread(target=self._receive)
		
		self._header_len = 3
		
		self._start_rsloop()

	def _log(self, msg, level="DEBUG"):
		if self._logger:
			if level == "DEBUG":
				self._logger.debug(msg)
			elif level == "INFO":
				self._logger.info(msg)
			elif level == "ERROR":
				self._logger.error(msg)

	def _start_rsloop(self):
		if sys.platform == "win32":
			return
		self._receiver.setDaemon(True)
		self._sender.setDaemon(True)
		self._receiver.start()
		self._sender.start()
		
	def _mkfifo(self):
		if not (os.path.exists(self._readfifo) and stat.S_ISFIFO(os.stat(self._readfifo)[stat.ST_MODE])):
			try:
				os.mkfifo(self._readfifo)
			except AttributeError, e:
				self._logger.error(AttributeError(e))
				raise AttributeError(e)
		if not (os.path.exists(self._writefifo) and stat.S_ISFIFO(os.stat(self._writefifo)[stat.ST_MODE])):
			try:
				os.mkfifo(self._writefifo)
			except AttributeError, e:
				self._logger.error(AttributeError(e))
				raise AttributeError(e)
		
	def _receive(self):
		while True:
			self._mkfifo()
			rfd = os.open(self._readfifo, os.O_RDONLY) #do not use os.O_NONBLOCK
			while True:
				try:
					packetHeader = os.read(rfd, self._header_len)
					bytesNum = ord(packetHeader[2])
					if (bytesNum > 0):
						packetData = os.read(rfd, bytesNum)
						data = packetHeader+packetData
					else:
						data = packetHeader
					
					with self._read_mutex:
						self._read_quene.put(data, False)
					self._read_sem.release()
				except IndexError, e:
					self._logger.error(IndexError(e))
					break
				except:
					break
			
			os.close(rfd)
			
	def receive(self):
		packet = None
		self._read_sem.acquire()
		with self._read_mutex:
			packet = self._read_quene.get(True)
		addr = ord(packet[0])
		cmd = ord(packet[1])
		if ord(packet[2]) > 0:
			data = packet[self._header_len:]
		else:
			data = None
		data=to_str(data)
		return addr,cmd,data
					
	def _send(self):
		while True:
			self._mkfifo()
			wfd = os.open(self._writefifo, os.O_WRONLY)
			while True:
				self._write_sem.acquire()
				with self._write_mutex:
					data = self._write_quene.get(True)
				try:
					os.write(wfd, data)
				except OSError, e:
					self._logger.error(OSError(e))
					break
				except:
					break
			os.close(wfd)
			
	def send(self, addr, cmd, data):
		data = to_str(data)
		if sys.platform == "win32":
			return
		
		_data = str(data)
		str_send = "{0}{1}{2}{3}".format(chr(addr), chr(cmd), chr(len(_data)), _data)
		with self._write_mutex:
			if not self._write_quene.full():
				self._write_quene.put(str_send, False)
			else:
				self._log("Send FIFO Quene is full!", "INFO")
				return
		self._write_sem.release()
		

def QtPipeManager(sendQueneSize=64, recviveQueneSize=64, enable_logger=False):
	global _instance
	if _instance is None:
		try:
			_instance = gplQtPipe(sendQueneSize, recviveQueneSize, enable_logger)
		except:
			print "There are some unexpected error, can't init pipe"
			_instance = None
	return _instance

	
def debugQtPipe():
	pipe = QtPipeManager(enable_logger=True)
	def doSend():
		data = 0
		while True:
			try:
				time.sleep(1)
			except:
				break
				
	def doReceive():
		while True:
			try:
				addr,cmd,data = pipe.receive()
				data = to_str(data)
				print "addr:",addr,", cmd:", cmd,", data:",data
			except:
				break
	
	sender = threading.Thread(target=doSend)
	receiver = threading.Thread(target=doReceive)
	
	sender.daemon = True
	receiver.daemon = True
	
	sender.start()
	receiver.start()
			
	
if __name__ == "__main__":
	pid = debugQtPipe()
	while True:
		try:
			time.sleep(3)
		except KeyboardInterrupt:
			break
		
