import urllib
import inspect
import CamController
import xml.etree.ElementTree as ET

urllib.FancyURLopener.prompt_user_passwd = lambda *a, **k: (None, None) # Disable urlopen's password prompt (Dumb!)

class H264NewCamController(CamController.CamController):
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
        
        self.cam_name=self.__getCamName()
            
    @staticmethod
    def getSupportedModels():
        return [('FOSCAM',"FI9821W")]

    def isAdmin(self):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=logIn&usrName="+urllib.quote(self.user)+"&groupId=0&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        result=self.__sendURL(url)
        return int(result['logInResult'])==0 and int(result['privilege'])==2
         
    def getCamName(self):
        return self.cam_name
    
    def isMailAlarmEnabled(self):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=getMotionDetectConfig&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        return bool(int(self.__sendURL(url)['linkage'])&2)
    
    def isFTPAlarmEnabled(self):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=getMotionDetectConfig&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        return bool(int(self.__sendURL(url)['linkage'])&4)

    def testMail(self):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=getSMTPConfig&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        result=self.__sendURL(url)
        
        if int(result['isEnable'])==0:
            return True
        
        for key in result:
            if result[key] is None:
                return False

        url = self.base_url + "/cgi-bin/CGIProxy.fcgi?cmd=smtpTest" + \
        "&smtpServer=" + result['server'] + "&port=" + result['port'] + "&tls=" + result['tls'] + "&isNeedAuth=" + result['isNeedAuth'] + \
        "&user=" + result['user'] + "&password=" + result['password'] + \
        "&usr=" + urllib.quote(self.user) + "&pwd=" + urllib.quote(self.password)
        return int(self.__sendURL(url)['testResult'])
    
    def testFTP(self):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=getFtpConfig&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        result=self.__sendURL(url)

        url2 = self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=testFtpServer" + \
        "&ftpAddr=" + urllib.quote(result['ftpAddr']) + "&ftpPort=" + result['ftpPort'] + "&mode=" + result['mode'] +"&fptUserName=" + result['userName'] + \
        "&ftpPassword=" + result['password'] + "&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        return int(self.__sendURL(url2)['testResult'])

    def isAlarmEnabled(self):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=getMotionDetectConfig&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        return bool(int(self.__sendURL(url)['isEnable']))
    
    def enableMotionAlarm(self):
        return self.__setMotionAlarm(1)
    
    def disableMotionAlarm(self):
        return self.__setMotionAlarm(0)
        
    def __getCamName(self):
        url=self.base_url + "/cgi-bin/CGIProxy.fcgi?cmd=getDevName&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        return self.__sendURL(url)['devName']
    
    def __setMotionAlarm(self,status):
        url= self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=getMotionDetectConfig&usr="+urllib.quote(self.user)+"&pwd="+urllib.quote(self.password)
        result=self.__sendURL(url)

        url=self.base_url + "cgi-bin/CGIProxy.fcgi?cmd=setMotionDetectConfig&isEnable=" + str(status) + "&linkage=" + result['linkage'] + \
        "&snapInterval=" +result['snapInterval'] + "&sensitivity=" + result['sensitivity'] + "&triggerInterval="+ result['triggerInterval'] + \
        "&schedule0="+ result['schedule0'] + "&schedule1="+ result['schedule1'] + "&schedule2="+ result['schedule2'] + \
        "&schedule3="+ result['schedule3'] + "&schedule4="+ result['schedule4'] + "&schedule5="+ result['schedule5'] + \
        "&schedule6="+ result['schedule6'] + "&area0="+ result['area0'] + "&area1="+ result['area1'] + "&area2="+ result['area2'] + \
        "&area3="+ result['area3'] + "&area4="+ result['area4'] + "&area5="+ result['area5'] + "&area6="+ result['area6'] + \
        "&area7="+ result['area7'] + "&area8="+ result['area8'] + "&area9="+ result['area9'] + \
        "&usr="+urllib.quote(self.user)+ "&pwd="+urllib.quote(self.password)
        result=self.__sendURL(url)
        
        return
        
    def __sendURL(self,url):
        try:
            f=urllib.urlopen(url)

            if f.getcode()!=200:
                raise CamController.CamControllerError("Bad HTTP Response from Camera",f.getcode(),url,inspect.stack()[0][3])
    
            lines=[]
            for line in f:            
                lines.append(line.strip())
            f.close()
        except IOError as e:
            raise CamController.CamControllerError(e.args)
        
        if lines[0] == "<CGI Result>":
            raise CamController.CamControllerError("Bad Result from Camera",inspect.stack()[0][3])

        result=self.__parseLines(lines)
        
        if int(result['result'])!=0:
            raise CamController.CamControllerError("Non-Zero Response from Camera",result,inspect.stack()[0][3])
        
        return result
        
    def __parseLines(self,lines):
        variables = {}
        result = ET.fromstringlist(lines)
        
        for element in list(result):
            variables[element.tag]=element.text
                
        return variables