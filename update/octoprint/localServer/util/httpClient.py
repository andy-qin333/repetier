#-*- coding:utf-8 -*-

import logging
import httplib2
import json
import urllib
import urllib2

_instance = None

########################################################################
class httpClient():
    """"""

    #----------------------------------------------------------------------
    def __init__(self, addr="139.224.211.75:8080", enable_log=False):
        """Constructor"""
        self._url = "http://" + str(addr)
        self._http = httplib2.Http(timeout=3)
        if enable_log:
            self._logger = logging.getLogger(__name__)
            
    #----------------------------------------------------------------------
    def _httpRequest(self, path="/", method="GET", data=None, dataType="json", callback=None):
        if path:
            url = self._url + str(path)
        else:
            url = self._url
        
        if dataType == "json":
            data = json.dumps(data)
        else:
            data = urllib.urlencode(data)
            
        headers = {'Content-Type': 'application/{0}; charset=UTF-8'.format(dataType)}
            
        try:
            response, content = self._http.request(uri=url, method=method, body=data, headers=headers)
        except:
            response, content = None, None
            
        if callback:
            return callback(response, content)
        else:
            return response, content
    
    def httpGet(self, path='/', data=None, dataType="json", callback=None):
        """ httpGet """
        return self._httpRequest(path, "GET", data, dataType)
    
    def httpPost(self, path='/', data=None, dataType="json"):
        """ httpPost """
        return self._httpRequest(path, "POST", data, dataType)
    
    def downloadFile(self, path, callback):
        exec_callback = False
        filelength = 0
        url = self._url + str(path)
        response = urllib2.urlopen(url=url)
        headers = response.headers
        if headers:
            if "x-zip-compressed" in headers["content-type"]:
                exec_callback = True
            if "file-length" in headers.keys():
                filelength = int(headers["file-length"])
            if "model-name" in headers.keys():
                modelname = headers["model-name"]
        content = ""
        size = 0
        while True:
            buff = response.read(2048)
            content += buff
            size += len(buff)
            if exec_callback:
                progress = float(size)/float(filelength)*100.0
                if callback(progress, modelname):
                    return None, None
            if len(buff) == 0:
                break
        return headers, content

#----------------------------------------------------------------------
def httpClientManager(addr="139.224.211.75:8080", enable_log=False):
    global _instance
    if _instance is None:
        try:
            _instance = httpClient(addr, enable_log)
        except:
            print "There are some unexpected error, can't init http client"
            _instance = None
    return _instance

def save_file(dstFile, data):
    with open(dstFile, 'wb') as fdst:
        fdst.write(data)

if __name__=="__main__":
    hcm = httpClientManager(addr="139.224.211.75:8080")
    hcm.downloadFile(path="https://www.baidu.com/img/bd_logo1.png")

        
        
    
    