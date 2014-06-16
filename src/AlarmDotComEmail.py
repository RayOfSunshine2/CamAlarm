import re
import poplib
import email.utils
import email.header
import time

pop_server = "pop.gmail.com"

class AlarmDotComEmailError(Exception):
    pass

class AlarmDotComEmail:
    def __init__(self,user,password,event_log_path):
        self.user=user
        self.password=password
        self.event_log_path=event_log_path
    
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
        pop = poplib.POP3_SSL(pop_server)
        pop.user(self.user)
        pop.pass_(self.password)
        
        date_times=[]
        events=[]
        for i in range(1,len(pop.list()[1])+1):
            message=pop.retr(i)
            message="\n".join(message[1])
            message=email.message_from_string(message)
            date_time=time.strftime("%Y/%m/%d %I:%M:%S %p",email.utils.parsedate(message['date']))
            event=email.header.decode_header(message['subject'])[0][0]
            
            date_times.append(date_time)
            events.append(event)
        
        pop.quit()
        
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
        my_time=date_time[first_space+1:].swapcase()
        return "[{date} {time:>11}] {event}".format(date=date,time=my_time,event=event)
    