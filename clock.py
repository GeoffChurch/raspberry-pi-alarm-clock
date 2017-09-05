#! /usr/bin/env python3
from collections import namedtuple
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

alarms = [
    Time(day=day_stoi["Mo"], hour=9, minute=0),
    Time(day=day_stoi["Tu"], hour=9, minute=0),
    Time(day=day_stoi["We"], hour=9, minute=0),
    Time(day=day_stoi["Th"], hour=9, minute=0),
    Time(day=day_stoi["Fr"], hour=9, minute=0),
    Time(day=day_stoi["Mo"], hour=17, minute=33),
    Time(day=day_stoi["Mo"], hour=17, minute=34),
]

def say(utterance):
    print(utterance)
    subprocess.call(["espeak", utterance])

def alarm():
    say("beep beep!")

class clock(daemon.daemon):
    REST_TIME = 3.0
    DIR = os.path.expanduser("~/.clock/")
    if not os.path.exists(DIR):
        os.makedirs(DIR)
    NXT_ALARM_FILE = DIR + "next_alarm_cache.pkl"

    def run(self):
        say("Starting clock! Next alarm at {}.".format(self.getNextAlarm()))
        while True:
            try:
                now = datetime.datetime.now()
                next_alarm = self.getNextAlarm()
                diff = now - next_alarm
                if diff >= datetime.timedelta():
                    alarm()
                    if diff.seconds >= self.REST_TIME:
                        say("WARNING: alarm is late by {}!".format(diff)) # TODO read out loud
                    self.resetCache() # clear cache now that we've sounded the alarm
                    seconds_to_expiration = (next_alarm + datetime.timedelta(minutes=1) - datetime.datetime.now()).total_seconds()
                    time.sleep(max(self.REST_TIME, seconds_to_expiration + 0.1)) # sleep until alarm is expired
                else:
                    time.sleep(self.REST_TIME)
                1/""
            except:
                say("ERROR!")
                traceback.print_exc()
                
    def getNextAlarm(self):
        try:
            with open(self.NXT_ALARM_FILE, 'rb') as f:
                nxt_dt_cached = pickle.load(f)
        except FileNotFoundError:
            print("WARNING: cache file \"{}\" not found. Starting fresh.".format(self.NXT_ALARM_FILE))
            nxt_dt_cached = datetime.max

        now_dt = datetime.datetime.now()
        now = Time(day=now_dt.weekday(), hour=now_dt.hour, minute=now_dt.minute)
        nxt = min((alarm - now for alarm in alarms), default=None)
        nxt_dt = min(nxt_dt_cached, (now_dt + datetime.timedelta(days=nxt.day(), hours=nxt.hour(), minutes=nxt.minute())).replace(second=0, microsecond=0))
        with open(self.NXT_ALARM_FILE, 'wb') as f:
            pickle.dump(nxt_dt, f)
        return nxt_dt
    
    def resetCache(self):
         with open(self.NXT_ALARM_FILE, 'wb') as f:
            pickle.dump(datetime.datetime.max, f)

c = clock('/tmp/clock.pid')
getattr(c, sys.argv[1])()