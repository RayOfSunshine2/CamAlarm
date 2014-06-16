import urllib
import inspect
import CamController

urllib.FancyURLopener.prompt_user_passwd = lambda *a, **k: (None, None) # Disable urlopen's password prompt (Dumb!)

class H264CamController(CamController.CamController):
    def __init__(self,maker,model,ip_address,port,user,password,alarm):
        self.maker=maker
        self.model=model
        self.ip_address=ip_address
        self.port=port
        self.user=user
        self.password=password
        self.alarm=alarm
        
        if not self.isAdmin():
            raise CamController.CamControllerError("Configured User must be an admin",inspect.stack()[0][3])

        self.base_url="http://" + self.user + ":" + self.password + "@" + self.ip_address + ":" + self.port + "/web/cgi-bin/hi3510/"
        url = self.base_url + "param.cgi?cmd=getosd&-chn=1&-region=1"
        self.cam_name=self.__sendURL(url)['name']
    
    @staticmethod
    def getSupportedModels():
        return [('FOSCAM','FI8601W'),('FOSCAM','FI8602W'),('FOSCAM','FI8608W'),('FOSCAM','FI8620'),('FOSCAM','FI9820W')]
    
    def isAdmin(self):
        return self.user == 'admin'
        
    def getCamName(self):
        return self.cam_name
    
    def isMailAlarmEnabled(self):
        url=self.base_url+"param.cgi?cmd=getmdalarm&-aname=emailsnap"
        if self.__sendURL(url)['md_emailsnap_switch']=='on':
            return True
        else:
            return False
    
    def isFTPAlarmEnabled(self):
        url=self.base_url+"param.cgi?cmd=getmdalarm&-aname=ftprec&cmd=getmdalarm&-aname=ftpsnap"
        result=self.__sendURL(url)
        if result['md_ftprec_switch']=='on' or result['md_ftpsnap_switch']=='on':
            return True
        else:
            return False

    def testMail(self):
        return 0
    
    def testFTP(self):
        return 0
    
    def isAlarmEnabled(self):
        return True
    
    def enableMotionAlarm(self):
        return self.__setMotionAlarm(1)
    
    def disableMotionAlarm(self):
        return self.__setMotionAlarm(0)
        
    def __setMotionAlarm(self,status):
        pass

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
            if key.find("var") >= 0:
                variables[key[4:].strip()]=value[:-1].strip('"')
            else:
                variables[key.strip()]=value[:-1].strip('"')
    
        return variables