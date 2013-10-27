#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from quick2wire.gpio import pins, Out
import atexit
import time, datetime
import threading
import logging
from uuid import uuid1
from subprocess import call
from pymongo import MongoClient
log = logging.getLogger()
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - Line: %(lineno)d\n%(message)s')
thisPath = os.path.abspath(os.path.dirname(__file__))
fh = logging.FileHandler(os.path.join(thisPath, 'sprinkler.log'))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)



# GPIO PIN DEFINES (using quick2wire GPIO numbers)

# NUMBER OF STATIONS
num_stations = 16

# STATION BITS
values = [0]*num_stations

# In case things don't close correctly, we'll just clear the pins and be ok if the command yields errors
pinsToClear = [4, 17, 21, 22]
for p in pinsToClear:
    call(['gpio-admin', 'unexport', str(p)])

pin_sr_clk = pins.pin(7, Out)  # Pin 7 (GPIO 4)
pin_sr_noe = pins.pin(0, Out)  # Pin 11 (GPIO 17)
pin_sr_dat = pins.pin(2, Out)  # Pin 13 (GPIO 21) # May need to be changed with rev.2 board
pin_sr_lat = pins.pin(3, Out)  # Pin 15 (GPIO 22)

pin_sr_clk.open()
pin_sr_lat.open()
pin_sr_noe.open()
pin_sr_dat.open()


def enableShiftRegisterOutput():
    pin_sr_noe.value = 0


def disableShiftRegisterOutput():
    pin_sr_noe.value = 1


def setShiftRegister(values):
    pin_sr_clk.value = False
    pin_sr_lat.value = False
    for s in range(num_stations):
        pin_sr_clk.value = False
        pin_sr_dat.value = values[num_stations-1-s]
        pin_sr_clk.value = True
    pin_sr_lat.value = True


def zoneOn(zone):
    log.info("Turning on zone %d" % zone)
    values = [0]*num_stations
    values[int(zone)] = 1
    setShiftRegister(values)


def zonesOff():
    log.info("Turning off all zones")
    values = [0]*num_stations
    setShiftRegister(values)


def minToHM(minutes):
    minutes = int(minutes)
    hrs = int(minutes / 3600)
    mins = int(minutes - hrs * 3600)
    return (hrs, mins)


def HMToMin(hm):
    return hm[0] * 3600 + hm[1]


class Scheduler:

    def __init__(self):
        # self.s = sched.scheduler(time.time, time.sleep)
        self.pool = []

        log.info("Application Started")
        disableShiftRegisterOutput()
        setShiftRegister(values)
        enableShiftRegisterOutput()

        # Setup Mongo
        self.db = MongoClient()['sprinkler']
        settings = self.db.settings
        self.programs = self.db.programs
        sprinklerLog = self.db.log

        log.debug([x for x in self.db.settings.find()])
        log.debug([x for x in self.db.programs.find()])


    def addSet(self, start, zones):
        '''
        Add watering set
        start datetime
        zones = [(zone, duration), (zone, duration)]
        '''
        if start > datetime.datetime.now():
            delta = start - datetime.datetime.now()
            log.info("Adding set that starts in {0}: {1}".format(delta.total_seconds(), 
                ",".join(["({0},{1})".format(x[0],x[1]) for x in zones])
            ))
            waterset = {
                "setId": uuid1(),  # Unique ID
                "start": start,  # Start time
                "status": 'queued',  # Current Status
                "zones": zones,  # Zones to run
                "zonePos": 0  # Current position in zones to run
            }
            waterset["thread"] = threading.Timer(delta.total_seconds(), self.runSet, args=[waterset['setId']])
            waterset['thread'].start()
            self.pool.append(waterset)

    def runSet(self, setId):
        ''' Run a program set (called one after the other) '''
        idx, waterSet = self.getSet(setId)
        log.info(waterSet)
        # If zonePos > zones, wrap everything up
        if (len(waterSet['zones'])) <= waterSet['zonePos']:
            self.pool[idx]['status'] = 'completed'
            zonesOff()
            return

        if waterSet['status'] == 'queued':
            self.pool[idx]['status'] = 'started'
        zoneOn(waterSet['zones'][waterSet['zonePos']][0])
        self.pool[idx]['thread'] = threading.Timer(datetime.timedelta(
            minutes=waterSet['zones'][waterSet['zonePos']][1]).total_seconds(),
            self.runSet, args=[waterSet['setId']])
        self.pool[idx]['thread'].start()
        self.pool[idx]['zonePos'] += 1

    def getSet(self, setId):
        ''' Return given set '''
        for idx, waterset in enumerate(self.pool):
            if waterset['setId'] == setId:
                return (idx, waterset)
        return False

    def removeSet(self, id):
        ''' Remove set '''
        idx, waterset = self.getSet(id)
        waterset['thread'].cancel()
        if waterset['status'] != 'queued':
            zonesOff()
        del self.pool[idx]

    def removeAll(self):
        ''' Remove All Sets '''
        for idx in range(len(self.pool)):
            self.removeSet(idx)

    def status(self):
        ''' Return the current status of running events '''
        thePool = []
        for event in self.pool:
            if event['status'] == 'queued':
                event['timeUntilStart'] = event['start'] - datetime.datetime.now()
            elif event['status'] == 'started':
                event['timeLeft'] = event['finish'] - datetime.datetime.now()
            thePool.append(event)
        return thePool

    def getPrograms(self):
        ''' Return the current programs '''
        return self.programs.find()



    def run(self):

        nextStart = datetime.datetime.now() + datetime.timedelta(seconds=5)
        self.addSet(nextStart, [(2, 1), (0, 1), (1, 1), (3, 1), (4, 1)])
        for p in self.db.programs.find():
            log.debug(p)
            #  @todo: Allow relative start times, e.g. sunrise, sunset, now 
            #         in addition to things like sunrise + (1,21) = an hour and 21 minutes past sunrise
            #         Also needs to handle things like every other day, every 3 days, Mon, tues, fri, etc.
            p['start'] = [int(x) for x in p['start']]
            startTime = datetime.datetime.combine(datetime.date.today(), datetime.time(*p['start']))
            log.debug("Start for program %s is at %s" % (p['_id'], startTime))
            self.addSet(startTime, p['zones'])
        timeToNextMidnight = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1), datetime.time(0)) - datetime.datetime.now()
        log.debug("Will check again in %s" % timeToNextMidnight)
        nextRun = threading.Timer(timeToNextMidnight.total_seconds(), self.run)
        nextRun.start()
        log.debug(nextRun)


def progexit():
    values = [0]*num_stations
    setShiftRegister(values)
    pin_sr_clk.close()
    pin_sr_lat.close()
    pin_sr_noe.close()
    pin_sr_dat.close()
    log.debug("Shutting Down")



if __name__ == '__main__':
    atexit.register(progexit)
    s = Scheduler()
    s.run()


