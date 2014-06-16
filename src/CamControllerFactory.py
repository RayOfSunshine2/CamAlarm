import MJPGCamController
import H264CamController
import H264NewCamController
import CamController
import inspect

ALARM_TYPES = {'NEVER':1,'ALWAYS':1,'STAY':1,'AWAY':1}

class CamControllerFactoryError(Exception):
    pass
        
class CamControllerFactory:

    @staticmethod
    def createCamController(maker,model,ip_address,port,user,password,alarm):
        alarm=alarm.upper()
        if alarm not in ALARM_TYPES:
            raise CamControllerFactoryError('Unrecognized Alarm Type: '+alarm)
        
        classes=CamController.CamController.__class__.__subclasses__(CamController.CamController)
        for cls in classes:
            for (sup_maker,sup_model) in cls.getSupportedModels():
                # returns first match, probably should make sure there isn't more than one
                if maker.upper()==sup_maker.upper() and model.upper()==sup_model.upper():
                    return cls(maker,model,ip_address,port,user,password,alarm)
            
        
                
        # if no supporting class found, the no supporting controller exists
        raise CamControllerFactoryError("Unexpected Maker/Model",maker,model,inspect.stack()[0][3])
