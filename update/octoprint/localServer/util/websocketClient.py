#-*- coding:utf-8 -*-

import logging

import os
import websocket
import Queue
import threading
import json
import subprocess
from time import sleep
from copy import deepcopy
from octoprint.settings import settings as octoSettings
import octoprint.filemanager
from httpClient import httpClientManager
from octoprint.server import fileManager
from octoprint.filemanager.destinations import FileDestinations

_instance = None

printer_state={
    "work_status":1,
    "print_status":0,
    "box_status":0,
    "surp_time":0,
    "printed_time":0,
    "model_name":"",
    "model_id":"local",
    "print_progress":0,
    "down_progress":0,
    "nozzle_temp":0,
    "nozzle_temp_total":0,
    "hotbed_temp":0,
    "hotbed_temp_total":0,
    "print_user":"",
    "app_push_msg":False,
}

FILE_LOCATION_SERVER = 0
FILE_LOCATION_LOCAL = 1

BOX_STATUS_IDLE = 0
BOX_STATUS_DOWNLOADING = 1
BOX_STATUS_SLICING = 2

PRINT_STATUS_IDLE = 0
PRINT_STATUS_PRINTING = 2
PRINT_STATUS_PAUSED = 3

CODE_FAILED = 0
CODE_SUCCEED = 1

########################################################################
class websocketClient():
    """websocketClient"""
    
    def __init__(self, addr="139.224.211.75:8080", eventManager=None, enable_log=False, receiveQueueSize=5, sendQueueSize=5):
        self._serialNumber = octoSettings().get(["printerParameters", "serialNumber"])
        self._url = "ws://{0}/socket.do?code={1}&type=0".format(addr, str(self._serialNumber))
        self._addr = addr
        try:
            self._wsc = websocket.WebSocketApp(self._url,
                                               on_open=self._on_open, 
                                               on_message=self._on_message, 
                                               on_error=self._on_error, 
                                               on_close=self._on_close, 
                                               on_ping=self._on_ping,
                                               on_pong=self._on_pong)
        except:
            self._wsc = None
            print "There are some unexpected error, cannot open websocket"
        
        self._httpClient = httpClientManager(addr=addr)
        self._eventManager = eventManager
        
        self._recevie_quene = Queue.Queue(receiveQueueSize)
        self._recevie_mutex = threading.Lock()
        self._recevie_sem = threading.Semaphore(0)
        self._monitor = threading.Thread(target = self.monitor)
        
        self._send_queue = Queue.Queue(sendQueueSize)
        self._send_mutex = threading.Lock()
        self._send_sem = threading.Semaphore(0)
        self._sender = threading.Thread(target=self._send)
        
        self._timer = None
        
        self._looper = threading.Thread(target=self._loop)
        
        self._isWebActived = False
        self._basedir = octoSettings().getBaseFolder("uploads")
        
        self._print_user = None
        self._print_model_id = "local"
        self._print_model_name = ""
        self._cancel_down = False
        
        if enable_log:
            self._logger = logging.getLogger(__name__)
            
    #----------------------------------------------------------------------
    def _on_open(self, wsc):
        self._isWebActived = True
        self.start_timer()
        print "on_open"
        pass
    
    #----------------------------------------------------------------------
    def _on_message(self, wsc, message):
        with self._recevie_mutex:
            if message and not self._recevie_quene.full():
                self._recevie_quene.put(message, False)
                self._recevie_sem.release()
    
    #----------------------------------------------------------------------
    def _on_error(self, wsc, error):
        print "on_error:",error
        pass
    
    #----------------------------------------------------------------------
    def _on_close(self, wsc):
        print "on_close"
        self._isWebActived = False
        sleep(5)
        try:
            self._wsc = websocket.WebSocketApp(self._url,
                                               on_open=self._on_open, 
                                               on_message=self._on_message, 
                                               on_error=self._on_error, 
                                               on_close=self._on_close, 
                                               on_ping=self._on_ping,
                                               on_pong=self._on_pong)
        except:
            print "There are some unexpected error, cannot open websocket"
        self._wsc.run_forever(ping_interval=5, ping_timeout=5)
    
    #----------------------------------------------------------------------
    def _on_ping(self, wsc):
        print "on_ping"
        
    def _on_pong(self, wsc, ss):
        print "on_pong"
        if printer_state["app_push_msg"] is True:
            print "push_msg"
            printer_state["app_push_msg"] = False
            reply = {
                "data":{
                    "user":str(self._print_user),
                    "device_code":self._serialNumber,
                    "model_id":self._print_model_id,
                    "val":100,
                },
                "event":"PRINT_BACK",
                "code":CODE_SUCCEED,
                "msg":""
            }
            self.send(json.dumps(reply))
            
        reply = {
            "event":"BEAT",
            "msg":"",
            "code":CODE_SUCCEED,
            "data":printer_state["print_status"]
        }
        self.send(json.dumps(reply))
        self.start_timer()
            
    def start_timer(self):
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(10, self._time_out)
        self._timer.start()
                
    def _time_out(self):
        print "time out"
        self._timer = None
        self._wsc.close()
            
    #----------------------------------------------------------------------
    def receive(self):
        message = ""
        self._recevie_sem.acquire()
        with self._recevie_mutex:
            message = self._recevie_quene.get(True)
        return message
    
    #----------------------------------------------------------------------
    def _send(self):
        while True:
            self._send_sem.acquire()
            with self._send_mutex:
                data = self._send_queue.get(True)
            try:
                self._wsc.send(data)
            except:
                pass

    #----------------------------------------------------------------------
    def send(self, data):
        with self._send_mutex:
            if not self._send_queue.full():
                self._send_queue.put(data, False)
            else:
                return
        self._send_sem.release()
      
    #----------------------------------------------------------------------
    def monitor(self):
        while True:
            message = self.receive()
            data = json.loads(message)
            if "ctrl" in data.keys():
                ctrl = data["ctrl"]
                if ctrl == "PRINT":
                    self.ctrl_print(data)
                elif ctrl == "PAUSE":
                    self.ctrl_pause(data)
                elif ctrl == "CANCEL":
                    self.ctrl_cancel(data)
                elif ctrl == "GET_CURRENT_STATUS":
                    self.ctrl_get_current_status(data)
                elif ctrl == "GET_PRINT_MODEL_LIST":
                    self.ctrl_get_print_model_list(data)
                elif ctrl == "SLICE":
                    self.ctrl_slice(data)
                elif ctrl == "CANCEL_DOWN":
                    self.ctrl_cancel_down(data)
                elif ctrl == "OPEN_VIDEO":
                    self.ctrl_open_video(data)
                elif ctrl == "CLOSE_VIDEO":
                    self.ctrl_close_video(data)
                            
    #----------------------------------------------------------------------
    def get_valid_filenames(self):
        result=[]
        files = os.listdir(self._basedir)
        for file in files:
            _, extension = os.path.splitext(file)
            if extension in [".gcode",".3dt"]:
                fileDetail={
                    "name":file,
                    "model_id":file,
                    "size":os.path.getsize(os.path.join(self._basedir, file)),
                }
                result.append(fileDetail)
        return result
    
    #----------------------------------------------------------------------
    def is_file_exist(self, filename):
        filepath = os.path.join(self._basedir, filename)
        return os.path.isfile(filepath)
        
    #----------------------------------------------------------------------
    def startDownloadThread(self, body, callback=None):
        if printer_state["box_status"] != BOX_STATUS_DOWNLOADING: # printer is not downloading file
            printer_state["box_status"] = BOX_STATUS_DOWNLOADING
            downloader = threading.Thread(target=self.download_file,args=(body, callback))
            downloader.setDaemon(True)
            downloader.start()
            
            reply = {
                "data":{
                    "user":body["user"],
                    "device_code":self._serialNumber,
                    "progress":0
                },
                "event":"DOWNLOAD_BACK",
                "code":CODE_SUCCEED,
                "msg":""
            }
            self.send(json.dumps(reply))
        
    #----------------------------------------------------------------------            
    def download_file(self, body, callback):
        path = "/api/file/download.do?device_code={0}&model_id={1}&user={2}".format(body["device_code"], body["model_id"], body["user"])
        printer_state["down_progress"] = 0
        headers, content = self._httpClient.downloadFile(path, callback)
        if headers:
            if "json" in headers["content-type"]:
                content = json.loads(content)
                if content["code"] == 1:
                    if content["data"] == "slice":
                        printer_state["box_status"] = BOX_STATUS_SLICING
                elif content["code"] == 0:
                    printer_state["box_status"] = BOX_STATUS_IDLE
            elif "x-zip-compressed" in headers["content-type"]:
                printer_state["box_status"] = BOX_STATUS_IDLE
                model_name = fileManager.add_server_file(FileDestinations.LOCAL, content, body["model_id"], headers["model-version"], headers["model-name"]+".gcode")
                if model_name:
                    self._print_user = body["user"]
                    self._print_model_id = body["model_id"]
                    self._eventManager.fire("action_print_ctrl", payload={"command":0,"data":model_name})
        else:
            printer_state["box_status"] = BOX_STATUS_IDLE
    
    def download_progress(self, progress, filename):
        self._print_model_name = filename
        printer_state["down_progress"] = progress
        if self._cancel_down == True:
            self._cancel_down = False
            return True
        else:
            return False
            
    #----------------------------------------------------------------------
    def start_loop(self):
        self._sender.setDaemon(True)
        self._sender.start()
        self._monitor.setDaemon(True)
        self._monitor.start()
        self._looper.setDaemon(True)
        self._looper.start()
        
    #----------------------------------------------------------------------
    def _loop(self):
        self._wsc.run_forever(ping_interval=5, ping_timeout=5)
            
    #----------------------------------------------------------------------
    def ctrl_print(self, data):
        if data is None:
            return
        
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        if "model_id" in data.keys() and data["model_id"] is not None:
            model_id = data["model_id"]
        else:
            return
        
        if "local" in data.keys() and data["local"] is not None:
            file_location = data["local"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
                "device_code":self._serialNumber,
                "model_id":model_id,
                "val":0
            },
            "event":"PRINT_BACK",
            "code":CODE_FAILED,
            "msg":""
        }
        
        if printer_state["print_status"] == PRINT_STATUS_PAUSED:
            if self._print_user == user:
                self._eventManager.fire("action_print_ctrl", payload={"command":1,"data":None})
                reply["code"] = CODE_SUCCEED
        else:
            if file_location == FILE_LOCATION_LOCAL: #local file
                if self.is_file_exist(model_id):
                    self._print_user = user
                    self._print_model_id = "local"
                    self._eventManager.fire("action_print_ctrl", payload={"command":0,"data":model_id})
                    reply["code"] = CODE_SUCCEED
                else:
                    reply["msg"] = "File not found!"
            else: # server file
                body={
                    "model_id":model_id,
                    "device_code":self._serialNumber,
                    "user":user
                }
                model_name = fileManager.find_server_file(FileDestinations.LOCAL, model_id, data["model_version"])
                self._print_model_id = model_id
                if model_name:
                    self._print_user = user
                    self._print_model_name = model_name
                    reply["code"] = CODE_SUCCEED
                    self._eventManager.fire("action_print_ctrl", payload={"command":0,"data":model_name})
                else:
                    self._print_user = user
                    self._print_model_name = ""
                    reply["code"] = CODE_SUCCEED
                    self.startDownloadThread(body=body, callback=self.download_progress)
        self.send(json.dumps(reply))
                
    #----------------------------------------------------------------------
    def ctrl_pause(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
                "device_code":self._serialNumber,
            },
            "event":"PAUSE_BACK",
            "code":CODE_FAILED,
            "msg":""
        }
        
        if self._print_user == user:
            self._eventManager.fire("action_print_ctrl", payload={"command":1,"data":None})
            reply["code"] = CODE_SUCCEED
        else:
            reply["msg"] = "The printer is occupied by other user!"
        self.send(json.dumps(reply))
        
    #----------------------------------------------------------------------
    def ctrl_cancel(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
                "device_code":self._serialNumber,
            },
            "event":"CANCEL_BACK",
            "code":CODE_FAILED,
            "msg":""
        }
        
        if self._print_user == user:
            self._eventManager.fire("action_print_ctrl", payload={"command":2,"data":None})
            reply["code"] = CODE_SUCCEED
        else:
            reply["msg"] = "The printer is occupied by other user!"            
        self.send(json.dumps(reply))
        
    #----------------------------------------------------------------------
    def ctrl_get_current_status(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
                "device_code":self._serialNumber,
                "work_status":printer_state["work_status"],
                "print_status":printer_state["print_status"],
                "box_status":printer_state["box_status"],
                "surp_time":printer_state["surp_time"],
                "printed_time":printer_state["printed_time"],
                "model_name":printer_state["model_name"],
                "model_id":printer_state["model_id"],
                "print_progress":printer_state["print_progress"],
                "down_progress":printer_state["down_progress"],
                "nozzle_temp":printer_state["nozzle_temp"],
                "nozzle_temp_total":printer_state["nozzle_temp_total"],
                "hotbed_temp":printer_state["hotbed_temp"],
                "hotbed_temp_total":printer_state["hotbed_temp_total"],
                "print_user":printer_state["print_user"],
            },
            "event":"GET_CURRENT_STATUS_BACK",
            "code":CODE_SUCCEED,
            "msg":""
        }

        if reply["data"]["print_status"] == PRINT_STATUS_IDLE:
            if reply["data"]["box_status"] == BOX_STATUS_DOWNLOADING:
                reply["data"]["model_name"] = self._print_model_name
                reply["data"]["model_id"] = self._print_model_id
                reply["data"]["print_user"] = self._print_user
            else:
                reply["data"]["model_name"] = ""
                reply["data"]["model_id"] = ""
                reply["data"]["print_user"] = ""
                reply["data"]["print_progress"] = 0
                reply["data"]["down_progress"] = 0
        else:
            reply["data"]["model_id"] = self._print_model_id
            reply["data"]["print_user"] = self._print_user
        self.send(json.dumps(reply))
        
    #----------------------------------------------------------------------
    def ctrl_get_print_model_list(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else: return
        
        reply = {
            "data":{
                "user":str(user),
                "device_code":self._serialNumber,
                "list":"",
            },
            "event":"GET_PRINT_MODEL_LIST_BACK",
            "code":CODE_FAILED,
            "msg":""
        }
        reply["code"] = CODE_SUCCEED
        filelist = self.get_valid_filenames()
        reply["data"]["list"] = filelist
        self.send(json.dumps(reply))
        
    #----------------------------------------------------------------------
    def ctrl_slice(self, data):
        print "ctrl_slice"
        if "data" in data.keys() and "status" in data["data"].keys() and data["data"]["status"] is not None:
            status = data["data"]["status"]
        else: return
        
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else: return
        
        if "model_id" in data["data"].keys() and data["data"]["model_id"] is not None:
            model_id = data["data"]["model_id"]
        else: return
        
        if status == 0: # slicing, watting
            printer_state["box_status"] = BOX_STATUS_SLICING
        elif status == 1: # sliced, then to download
            body={
                "model_id":model_id,
                "device_code":self._serialNumber,
                "user":user
            }
            self._print_user = user
            self._print_model_name = ""
            self.startDownloadThread(body=body, callback=self.download_progress)
        
    #----------------------------------------------------------------------
    def ctrl_download(self, data):
        body = {
            "deviceCode": self._serialNumber,
            "model_id": data["model_id"],
            "user":data["user"]
        }
        self.startDownloadThread(body=body, callback=self.download_progress)
        
    #----------------------------------------------------------------------
    def ctrl_cancel_down(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
                "device_code":self._serialNumber,
            },
            "event":"CANCEL_DOWN_BACK",
            "code":CODE_FAILED,
            "msg":""
        }

        if self._print_user == user:
            self._cancel_down = True
            reply["code"] = CODE_SUCCEED
        else:
            self._cancel_down = False
            reply["msg"] = "The printer is occupied by other user!"
        self.send(json.dumps(reply))
        
    #----------------------------------------------------------------------
    def ctrl_open_video(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
                "id":self._serialNumber,
            },
            "event":"OPEN_VIDEO_BACK",
            "code":CODE_FAILED,
            "msg":""
        }
        try:
            if os.path.exists("/dev/video0"):
                #if not is_webcam_started():
                subprocess.Popen(["sudo", "/usr/local/mjpg-streamer/start.sh"])
                reply["code"] = CODE_SUCCEED
            else:
                reply["msg"] = "no webcam found"
        except:
            reply["msg"] = "open webcam failed"
        self.send(json.dumps(reply))
    
    #----------------------------------------------------------------------
    def ctrl_close_video(self, data):
        if "user" in data.keys() and data["user"] is not None:
            user = data["user"]
        else:
            return
        
        reply = {
            "data":{
                "user":str(user),
            },
            "event":"CLOSE_VIDEO_BACK",
            "code":CODE_FAILED,
            "msg":""
        }
        try:
            if os.path.exists("/dev/video0"):
                subprocess.Popen(["sudo","killall", "-9", "mjpg_streamer"])
                reply["code"] = CODE_SUCCEED
            else:
                reply["msg"] = "no webcam found"
        except:
            reply["msg"] = "close webcam failed"
            pass
        self.send(json.dumps(reply))
        
    def is_webcam_started(self):
        tmpfile = "/tmp/mjpg_streamer.lock"
        os.system("ps -e | grep mjpg_streamer > " + tmpfile)
        if os.path.getsize(tmpfile) <= 0:
            return False
        return True
        
                
def websocketClientManager(addr="139.224.211.75:8080", enable_log=True, eventManager=None):
    global _instance
    if _instance is None:
        try:
            _instance = websocketClient(addr=addr, eventManager=eventManager, enable_log=enable_log)
        except:
            print "There are some unexpected error, can't init websocket client"
            _instance = None
    return _instance

if __name__=="__main__":
    wscm = websocketClientManager()
    #wscm = websocketClientManager()
    #wscm.start_loop()
    
    
        