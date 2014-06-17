#!/usr/bin/python

from CamControllerFactory import CamControllerFactory
from AlarmDotComEmail import AlarmDotComEmail
import xml.etree.ElementTree as ET
import sys
import os
import datetime

CONFIG_FILE = "CamAlarm.xml"
TS_FILE = "CamAlarm.dat"

def log_info(message):
    now=str(datetime.datetime.now())
    print "["+now+"] "+message

def log_error(message):
    now=str(datetime.datetime.now())
    sys.stderr.write("["+now+"] "+message)    

def read_last_ts(cams):
    last_tests = {}
    try:
        f=open(TS_FILE,"r")
        for line in f:
            delim_pos=line.find(":")
            if delim_pos<0:
                continue
            last_tests[line[:delim_pos].strip()]=int(line[delim_pos+1:].strip())
        f.close()
    except IOError:
        pass # If file doesn't exist, assume all tests were never done
    
    for cam in cams:
        if cam.getCamName() not in last_tests:
            last_tests[cam.getCamName()]=0
    
    return last_tests

def write_last_ts(last_tests):
    f=open(TS_FILE,"w")
    for cam in last_tests.keys():
        f.write(cam+":"+str(last_tests[cam])+"\n")
    f.close()

def hrs_since_epoch():
    return int((datetime.datetime.now()-datetime.datetime.fromtimestamp(0)).total_seconds()/3600)
     
if __name__ == "__main__":
    #log_info("CamAlarm Started")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    tree = ET.parse(CONFIG_FILE)
    root=tree.getroot()
    
    test_freq = int(root.find('test_freq').text)
    max_retries = int(root.find('max_retries').text)
    cams_element = root.find('cams')
    cams = []
    for cam_element in cams_element.findall('cam'):
        maker=cam_element.find('maker').text
        model=cam_element.find('model').text
        ip_address=cam_element.find('ip_address').text
        port=cam_element.find('port').text
        user=cam_element.find('user').text
        password=cam_element.find('password').text
        alarm=cam_element.find('alarm').text
        cams.append(CamControllerFactory.createCamController(maker,model, ip_address, port, user, password,alarm,max_retries))
    
    alarm_element = root.find('alarm')
    alarm_user = alarm_element.find('user').text
    alarm_password =alarm_element.find('password').text
    alarm_log_file = alarm_element.find('log_file').text
                
    alarmChecker = AlarmDotComEmail(alarm_user,alarm_password,alarm_log_file)

    alarm_state = alarmChecker.getCurAlarmState()
    #alarm_state = "DISARMED"
    
    last_tests = read_last_ts(cams)
    current_hour = hrs_since_epoch()

    for cam in cams:
        if (current_hour - last_tests[cam.getCamName()])>=test_freq:
            log_info("Test Timer Expired for "+cam.getCamName())
            if cam.isFTPAlarmEnabled():
                result=cam.testFTP()
                if result != 0:
                    log_error("Warning: FTP Alarm is enabled on "+cam.getCamName()+", but failing ("+str(result)+")\n")
            
            if cam.isMailAlarmEnabled():
                result=cam.testMail()
                if result != 0:
                    log_error("Warning: Mail Alarm is enabled on "+cam.getCamName()+", but failing ("+str(result)+")\n")
            
            last_tests[cam.getCamName()]=current_hour

        if cam.isAlarmEnabled():
            if cam.alarm=="NEVER":
                log_info("NEVER ON - Disabling Motion Alarm for "+cam.getCamName())
                cam.disableMotionAlarm()
                continue
            if alarm_state=="DISARMED":
                log_info("Alarm Disarmed - Disabling Motion Alarm for "+cam.getCamName())
                cam.disableMotionAlarm()
                continue
            if alarm_state == "STAY" and cam.alarm == "AWAY":
                log_info("Alarm Enabled ("+alarm_state+") - Disabling Motion Alarm ("+cam.alarm+") for "+cam.getCamName())
                cam.disableMotionAlarm()
                continue
        else:
            if cam.alarm=="ALWAYS":
                log_info("ALWAYS ON - Enabling Motion Alarm for "+cam.getCamName())
                cam.enableMotionAlarm()
                continue
            if alarm_state=="UNKNOWN" and cam.alarm != "NEVER":
                log_info("Alarm State (UNKNOWN) - Enabling Motion Alarm for "+cam.getCamName())
                cam.enableMotionAlarm()
                continue
            if alarm_state=="STAY" and cam.alarm=="STAY":
                log_info("Alarm State ("+alarm_state+") - Enabling Motion Alarm for "+cam.getCamName())
                cam.enableMotionAlarm()
                continue
            if alarm_state=="AWAY" and (cam.alarm=="STAY" or cam.alarm=="AWAY"):
                log_info("Alarm State (AWAY) - Enabling Motion Alarm for "+cam.getCamName())
                cam.enableMotionAlarm()
                continue
    
    write_last_ts(last_tests)
    #log_info("CamAlarm Complete")
