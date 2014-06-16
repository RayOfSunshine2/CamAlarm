import urllib
import inspect
import CamController

urllib.FancyURLopener.prompt_user_passwd = lambda *a, **k: (None, None) # Disable urlopen's password prompt (Dumb!)

class MJPGCamController(CamController.CamController):
    def __init__(self,maker,model,ip_address,port,user,password,alarm):
        self.maker=maker
        self.model=model
        self.ip_address=ip_address
        self.port=port
        self.user=user
        self.password=password
        self.alarm=alarm
        self.base_url="http://" + self.ip_address + ":" + self.port + "/"
        
        if not self.isAdmin():
            raise CamController.CamControllerError("Configured User must be an admin",inspect.stack()[0][3])
        
        self.cam_name=self.__getStatus()['alias']
            
    @staticmethod
    def getSupportedModels():
        return [('FOSCAM',"FI8910W"),('FOSCAM',"FI8910E"),('FOSCAM',"FI8918W"),('FOSCAM',"FI8918E"),('FOSCAM',"FI8903W"),
                    ('FOSCAM',"FI8904W"),('FOSCAM',"FI8905W"),('FOSCAM',"FI8905E"),('FOSCAM',"FI8908W"),('FOSCAM',"FI8916W")]

    def isAdmin(self):
        url= self.base_url + "check_user.cgi?user=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        return int(self.__sendURL(url)['pri'])==3
         
    def getCamName(self):
        return self.cam_name
    
    def isMailAlarmEnabled(self):
        return bool(int(self.__getParams()['alarm_mail']))
    
    def isFTPAlarmEnabled(self):
        return bool(int(self.__getParams()['alarm_upload_interval']))

    def testMail(self):
        url= self.base_url + "test_mail.cgi?user=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        return int(self.__sendURL(url)['result'])
            
    def testFTP(self):
        url= self.base_url + "test_ftp.cgi?user=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        return int(self.__sendURL(url)['result'])

    def isAlarmEnabled(self):
        return bool(int(self.__getParams()['alarm_motion_armed']))
    
    def enableMotionAlarm(self):
        return self.__setMotionAlarm(1)
    
    def disableMotionAlarm(self):
        return self.__setMotionAlarm(0)
        
    def __getStatus(self):
        url=self.base_url + "get_status.cgi?user=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        return self.__sendURL(url)
    
    def __getParams(self):
        url= self.base_url + "get_params.cgi?user=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        return self.__sendURL(url)

    def __setMotionAlarm(self,status):
        url=self.base_url + "set_alarm.cgi?motion_armed="+`status`+"&user=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        result=urllib.urlopen(url).read()
        result=result.strip()
        if result != "ok.":
            raise CamController.CamControllerError(result,inspect.stack()[0][3])
        return
        
    def __sendURL(self,url):
        try:
            f=urllib.urlopen(url)

            if f.getcode()!=200:
                raise CamController.CamControllerError("Bad HTTP Response from Camera",f.getcode(),inspect.stack()[0][3])
    
            lines=[]
            for line in f:            
                lines.append(line.strip())
            f.close()
            
            if lines[0].find("var") < 0:
                raise CamController.CamControllerError("".join(lines),inspect.stack()[0][3])
        except IOError as e:
            raise CamController.CamControllerError(e.args)

        return self.__parseLines(lines)
        
    def __parseLines(self,lines):
        variables = {}
        for line in lines:
            (key,value) = line.split("=")
            variables[key[4:].strip()]=value[:-1].strip("'")
    
        return variables