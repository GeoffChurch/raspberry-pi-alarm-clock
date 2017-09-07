#! /usr/bin/python3

import daemon

import datetime
from functools import total_ordering
import os
import pickle
import subprocess
import sys
import time
import traceback

@total_ordering
class Time():
    def __init__(self, day=0, hour=0, minute=0):
        self._minutes = ((24 * 60 * day) + (60 * hour) + minute) % (7 * 24 * 60)

    def day(self):
        return self._minutes // (24 * 60)

    def hour(self):
        return (self._minutes % (24 * 60)) // 60

    def minute(self):
        return self._minutes % 60

    def __sub__(self, other):
        return Time(minute=self._minutes - other._minutes)

    def __eq__(self, other):
        return self._minutes == other._minutes

    def __lt__(self, other):
        return self._minutes <= other._minutes

day_stoi = {e : i for i, e in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"])}

alarms = [ # TODO read from file at each interval
    Time(day=day_stoi["Mo"], hour=8, minute=0),
    Time(day=day_stoi["Tu"], hour=8, minute=0),
    Time(day=day_stoi["We"], hour=8, minute=0),
    Time(day=day_stoi["Th"], hour=8, minute=0),
    Time(day=day_stoi["Fr"], hour=8, minute=0),
]

def say(utterance):
    print(utterance)
    subprocess.call(['bash','-c', "espeak \"{}\" --stdout | aplay -D sysdefault:CARD=Device".format(utterance)])

def formatDatetime(d):
    def formatInteger(i):
        i = str(i)
        return i + ("th" if i in {11, 12, 13} else {'1' : "st", '2' : "nd", '3' : "rd"}.get(i[-1], "th"))
    return d.strftime("{}{} %p{} on %A, %B {}, %Y".format(
        str(12 if d.hour % 12 == 0 else d.hour % 12),
        ("" if d.minute == 0 else ":%M"),
        (" sharp" if d.minute == 0 else ""),
        formatInteger(d.day)))

def formatTimedelta(d):
    s = d.total_seconds()
    days, s = divmod(s, 24 * 60 * 60)
    hours, s = divmod(s, 60 * 60)
    minutes, s = divmod(s, 60)
    return ", ".join(str(count) + " " + (name[:-1] if count == 1 else name) for count, name in zip(map(int, (days, hours, minutes, s)), ("days", "hours", "minutes", "seconds")) if count != 0)

class clock(daemon.daemon):
    REST_TIME = 5 # seconds of rest between checks
    DIR = os.path.expanduser("~/.clock/")
    if not os.path.exists(DIR):
        os.makedirs(DIR)
    NXT_ALARM_FILE = DIR + "next_alarm_cache.pkl"

    def run(self):
        while True:
            try:
                now = datetime.datetime.now()
                next_alarm = self.getNextAlarm()
                diff = now - next_alarm
                if diff >= datetime.timedelta(): # if the alarm is due
                    if diff.total_seconds() >= self.REST_TIME: # and we're late
                        say("I am the clock. Bloody hell. It looks like I am late by {}. I shall punish myself. Ouch. Ouch. Ouch. No, ’tis not so deep as a well nor so wide as a church-door, but ’tis enough, ’twill serve. Ask for me tomorrow, and you shall find me a grave clock.".format(formatTimedelta(diff)))
                    else: # otherwise
                        say("I am the clock. Beep beep. It is {}. It is time to wake up. It is time to accomplish your dreams.".format(formatDatetime(datetime.datetime.now())))
                    seconds_to_expiration = (next_alarm + datetime.timedelta(minutes=1) - datetime.datetime.now()).total_seconds()
                    time.sleep(max(self.REST_TIME, seconds_to_expiration + 0.1)) # sleep until alarm is expired
                else:
                    time.sleep(self.REST_TIME)
            except:
                say("ERROR!")
                traceback.print_exc()
                
    def getNextAlarm(self):
        now_dt = datetime.datetime.now()
        now = Time(day=now_dt.weekday(), hour=now_dt.hour, minute=now_dt.minute)
        nxt = min((alarm - now for alarm in alarms if alarm != now), default=None) # probably not worth binary search
        nxt_dt = (now_dt + datetime.timedelta(days=nxt.day(), hours=nxt.hour(), minutes=nxt.minute())).replace(second=0, microsecond=0)
        try:
            with open(self.NXT_ALARM_FILE, 'rb') as f:
                nxt_dt_cached = pickle.load(f)
        except FileNotFoundError:
            print("WARNING: cache file \"{}\" not found. Starting fresh.".format(self.NXT_ALARM_FILE))
            nxt_dt_cached = datetime.datetime.max
        with open(self.NXT_ALARM_FILE, 'wb') as f:
            pickle.dump(nxt_dt, f)
        return min(nxt_dt, nxt_dt_cached)
    
c = clock('/tmp/clock.pid')
getattr(c, sys.argv[1])()
