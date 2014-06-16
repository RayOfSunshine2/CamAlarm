import urllib2
import urllib
from cookielib import LWPCookieJar
from bs4 import BeautifulSoup
import re

COOKIEFILE="cookies.lwp"

alarmComBaseURL="https://www.alarm.com/"
alarmComLanding="web/Default.aspx"
alarmComStatus="web/WirelessSignalingHome.aspx"

class AlarmDotComScraperError(Exception):
    pass

class AlarmDotComScraper:
    def __init__(self,user,password,event_log_path):
        self.user=user
        self.password=password
        self.event_log_path=event_log_path
        self.cj = LWPCookieJar(COOKIEFILE)  
    
    def getCurAlarmState(self):
        events=self.getLatestEvents()
        
        state_found=0 # assume we'll find no state change
        current_state="UNKNOWN"
        for event in events:
            #print event
            state=self.__getStateFromString(event[1])
            if state != "":
                #print "Found State:",state
                state_found=1
                current_state=state
        
        if not state_found:
            current_state=self.__getCurStateFromLog()
                
        self.addEventsToLog(events)
        return current_state
    
    def getLatestEvents(self):
        try:
            self.cj.load(None,True,True)
        except IOError:
            pass # Ignore the open error if the cookies file doesn't exist
        
        retry=False
        while True:
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
            response = opener.open(alarmComBaseURL+alarmComStatus)
            #response = opener.open("file:/home/tnorris/Desktop/Home.html")
            
            soup=BeautifulSoup(response.read())
            
            event_tab_heading=soup.find("th",text=re.compile(".*Last 5 Events.*"))
    
            # Assume if we can't find the event table on the 1st try we need to login
            # on the 2nd time (retry=True) assume there's an issue
            if (event_tab_heading is None):
                if retry:
                    raise AlarmDotComScraperError("Unable to locate Alarm Event Table Header")
                retry=True
                self.__login()
            else:
                break
        
        event_table=event_tab_heading.parent.parent

        if (event_table is None):
            raise AlarmDotComScraperError("Error locating Events in Table",soup)
    
        date_time_tags=event_table.find_all("div")
        event_tags=event_table.find_all("span")
        if len(date_time_tags)==0:
            raise AlarmDotComScraperError("Unable to locate time tags")

        if len(event_tags)==0:
            raise AlarmDotComScraperError("Unable to locate event tags")
            
        if len(event_tags) != len(date_time_tags):
            raise AlarmDotComScraperError("Mismatched length of events and times",len(event_tags),len(date_time_tags))
    
        date_times=[date_time_tags[i].string for i in reversed(range(len(date_time_tags)))]
        events=[event_tags[i].string for i in reversed(range(len(event_tags)))]
        return zip(date_times,events)
        
    def addEventsToLog(self,events):
        new_events=[]
        try:
            handle=open(self.event_log_path,"r")
            for i in range(len(events)): # assumes events are in oldest to newest order
                temp_line=self.__makeLine(events[i][0],events[i][1])
                found=0
                handle.seek(0)
                for line in handle:
                    line=line.strip()
                    if line==temp_line:
                        found=1
                        break
                
                if not found:
                    new_events.append(events[i])
                    
            handle.close()
        except IOError:
            new_events=events
            
        if len(new_events)>0:
            handle=open(self.event_log_path,"a")
            for i in range(len(new_events)):
                out_line=self.__makeLine(new_events[i][0],new_events[i][1])
                handle.write(out_line)
                handle.write("\n")
            handle.close()

    def __getCurStateFromLog(self):
        try:
            current_state="UNKNOWN"
            handle=open(self.event_log_path,"r")
            for line in handle:
                state=self.__getStateFromString(line)
                if state!="":
                    current_state=state
            handle.close()
        except IOError: # if no log exists, there's no state to find
            pass
        
        return current_state
    
    def __getStateFromString(self,string):
        state="" # return no state is none found
        if re.search(r"\bARMED\b",string, flags=re.IGNORECASE)>=0: # ARMED?
            if re.search(r"\bSTAY\b",string, flags=re.IGNORECASE)>=0: # STAY?
                state="STAY"
            elif re.search(r"\bAWAY\b",string, flags=re.IGNORECASE)>=0: # AWAY?
                state="AWAY"
            else:
                state="ARMED" # ARMED, but unknown type
        elif re.search(r"\bDISARMED\b",string, flags=re.IGNORECASE)>=0: # DISARMED?
            state="DISARMED"

        #print state_found,state
        return state
    
    def __makeLine(self,date_time,event):
        first_space=date_time.find(" ")
        date=date_time[:first_space]
        time=date_time[first_space+1:].swapcase()
        return "[{date} {time:>11}] {event}".format(date=date,time=time,event=event)
    
    def __login(self):
        formdata = {
                    "ctl00$ContentPlaceHolder_InnerCommon$loginform$txtUserName" : self.user,
                    "ctl00$ContentPlaceHolder_InnerCommon$loginform$txtPassword": self.password,
                    "IsFromNewSite": "1",
                    "JavaScriptTest":"1"}
        data_encoded = urllib.urlencode(formdata)
    
        # Actually login, response should contain status page
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        opener.open(alarmComBaseURL+alarmComLanding, data_encoded)
        self.cj.save(None,True,True)

    