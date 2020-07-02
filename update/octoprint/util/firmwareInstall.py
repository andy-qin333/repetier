from __future__ import absolute_import

import serial
import os, threading, logging, time, struct
import re

from octoprint.settings import settings
from octoprint.server import printer

IAP_INFO_ADDR_OFFSET=0x7800
APP_PROG_ADDR_OFFSET=0x8000

class InstallFirmware():
    STATE_NONE = 0
    STATE_CONNECTING = 1
    STATE_IAP_MODE = 2
    STATE_WRITE_APP = 3
    STATE_CHECK_APP = 4
    STATE_FINISHED = 6
    STATE_ERROR = 7
    
    def __init__(self, filename=None, configname=None, port=None, progressCallback=None):
        self._logger = logging.getLogger(__name__)
        self._serial = None
        self._state = self.STATE_NONE
        if port is None:
            port = settings().get(["serial", "port"])
            if port is None:
                port = "/dev/ttyAMA3"
        if filename is None or os.path.exists(filename) is False:
            self._logger.warn("has no firmware file!")
            self.changeState(self.STATE_ERROR)
            return

        self._filename = filename
        self._configName = None
        if configname is not None and os.path.exists(configname):
            self._configName = configname
        self._port = port
        self._handle = None

        self._thread = threading.Thread(target=self.run, args=(progressCallback,))
        self._thread.start()
        self._thread.join()
        
    def __del__(self):
        self.close()
        if self._handle:
            self._handle.close()

    def run(self, progressCallback=None):
        #write parameter to eeprom of m3 board
        if self._configName is not None:
            command_list = []
            self._handle = open(self._configName, "rb")
            regex_e2 = re.compile("addr:(\d+)\stype:(\d).*\s(\d+\.?\d*)\s.*")
            while (True):
                line = self._handle.readline()
                if line is not "":
                    match_e2 = re.match(regex_e2, line)
                    if match_e2 is not None:
                        addr = match_e2.group(1)
                        types = match_e2.group(2)
                        valueType = ["F","S","S","S"][int(types)-1]
                        value = match_e2.group(3)
                        cmd = "M206 P{0} T{1} {2}{3}".format(addr,types,valueType,value)
                        command_list.append(cmd)
                        print cmd
                else:
                    self._handle.close()
                    break
            if command_list is not None:
                printer.commands(command_list)
        
        # disconnect serial of printer, because the update firmware need the same serial port
        try: printer.disconnect()
        except: pass
        time.sleep(0.5)
        
        try: self.connect(self._port)
        except serial.SerialException:
            self._logger.error('Failed to find machine for firmware upgrade!')
            self.changeState(self.STATE_ERROR)
            return

        if self._serial != None:
            self._logger.info("Uploading firmware...")
            
        self.sendCommand("M0")
        self._state = self.STATE_CONNECTING
                    
        while True:
            line = self._serial.readline()
            if line == "":
                self.changeState(self.STATE_ERROR)
                
            if self._state == self.STATE_CONNECTING:
                if "send M100 to start IAP interface" in line or "APP program area is not valid" in line:
                    self._handle = open(self._filename, "rb")
                    startAddress = 0
                    self.sendCommand("M100")
                    self.changeState(self.STATE_IAP_MODE)
            
            elif self._state == self.STATE_IAP_MODE:
                if "unknown command" in line:
                    self.sendCommand("M100")
                elif "max packet length:" in line:
                    regex_length = re.compile(".*max\packet\slength:\s(\d+)bytes.*")
                    match_length = re.match(regex_length, line)
                    if match_length is not None:
                        packetLength = int(match_length.group(1))
                    else:
                        packetLength = 2*1024
                        
                    startAddress = IAP_INFO_ADDR_OFFSET
                    srcData = self.readFirmware(64)
                    dataLen = len(srcData)
                    self.sendCommand("M101 S%s P%s" %(startAddress, dataLen))
                    self.changeState(self.STATE_WRITE_APP)
                    
            elif self._state == self.STATE_WRITE_APP:
                if "please send the data" in line:
                    self.sendData(srcData)
                elif "program successful" in line:
                    self.sendCommand("M102 S%s P%s" %(startAddress, dataLen))
                    self.changeState(self.STATE_CHECK_APP)
                elif "data receive timeout" in line:
                    self.sendData(srcData)
                    
            elif self._state == self.STATE_CHECK_APP:
                if "ok" in line:
                    dstData = self.readData(dataLen)
                    if set(srcData) == set(dstData):
                        if startAddress == IAP_INFO_ADDR_OFFSET:
                            startAddress = APP_PROG_ADDR_OFFSET
                        else:
                            startAddress += dataLen
                            
                        srcData = self.readFirmware(packetLength)
                        dataLen = len(srcData)
                        if dataLen != 0:
                            self.sendCommand("M101 S%s P%s" %(startAddress, dataLen))
                            self.changeState(self.STATE_WRITE_APP)
                        else:
                            self.changeState(self.STATE_FINISHED)
                    else:
                        self.changeState(self.STATE_ERROR)
                 
            if self._state == self.STATE_ERROR:
                if self._handle:
                    self._handle.close()
                return
                
            elif self._state == self.STATE_FINISHED:
                self.sendCommand("M0")
                self._handle.close()
                time.sleep(2)
                printer.connect(port=self._port, baudrate=115200)
                return
            
        #printer.connect(port=self._port, baudrate=settings().get(["serial", "baudrate"]))
        
    def connect(self, port = 'COM22', speed = 115200):
        if self._serial != None:
            self.close()
        try:
            self._serial = serial.Serial(str(port), 115200, timeout=5,writeTimeout=10000, parity=serial.PARITY_NONE)
        except serial.SerialException as e:
            raise e
    
    def close(self):
        if self._serial != None:
            self._serial.close()
            self._serial = None
            
    def sendCommand(self, cmd):
        self._serial.write(cmd+'\n')
        
    def sendData(self, data):
        for c in data:
            self._serial.write(c)
            
    def readData(self, size):
        return self._serial.read(size)
        
    def changeState(self, state):
        self._state = state

    def onProgress(self, value, max):
        print value, max
        
    def readFirmware(self, size):
        if self._handle is not None:
            data = self._handle.read(size)
            return data
        else:
            return None

if __name__ == "__main__":
    InstallFirmware("C:/Users/Administrator/Desktop/firmware/Printer_3D.our", "C:/Users/Administrator/Desktop/firmware/EEPROM.txt", "COM3")
    import time
    time.sleep(1)
