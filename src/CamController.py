import abc
abstractstaticmethod = abc.abstractmethod

TIME_OUT = 30

class CamControllerError(Exception):
    pass
        
class CamController(object):
    __metaclass__ = abc.ABCMeta
    
    @staticmethod
    def getSupportedModels():
        pass
                
    @abc.abstractmethod    
    def isAdmin(self):
        pass

    @abc.abstractmethod    
    def getCamName(self):
        pass
    
    @abc.abstractmethod    
    def isMailAlarmEnabled(self):
        pass
    
    @abc.abstractmethod    
    def isFTPAlarmEnabled(self):
        pass

    @abc.abstractmethod    
    def testMail(self):
        pass
            
    @abc.abstractmethod    
    def testFTP(self):
        pass
    
    @abc.abstractmethod
    def isAlarmEnabled(self):
        pass
    
    @abc.abstractmethod    
    def enableMotionAlarm(self):
        pass
    
    def disableMotionAlarm(self):
        pass
