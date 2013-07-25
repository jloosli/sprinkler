#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os
from quick2wire.gpio import pins, Out
import atexit
import time, datetime
import threading
from uuid import uuid1
from pymongo import MongoClient

# GPIO PIN DEFINES (using quick2wire GPIO numbers)

# NUMBER OF STATIONS
num_stations = 16

# STATION BITS
values = [0]*num_stations

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
    print("Turning on zone %d" % zone)
    values = [0]*num_stations
    values[zone] = 1
    setShiftRegister(values)


def zonesOff():
    print("Turning off all zones")
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

    def addSet(self, start, zones):
        '''
        Add watering set
        start datetime
        zones = [(zone, duration), (zone, duration)]
        '''
        if start > datetime.datetime.now():
            delta = start - datetime.datetime.now()
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
        idx, waterSet = self.getSet(setId)
        print (waterSet)
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
        for idx, waterset in enumerate(self.pool):
            if waterset['setId'] == setId:
                return (idx, waterset)
        return False

    def removeSet(self, id):
        idx, waterset = self.getSet(id)
        waterset['thread'].cancel()
        if waterset['status'] != 'queued':
            zonesOff()
        del self.pool[idx]

    def removeAll(self):
        for idx in range(len(self.pool)):
            self.removeSet(idx)

    def status(self):
        thePool = []
        for event in self.pool:
            if event['status'] == 'queued':
                event['timeUntilStart'] = event['start'] - datetime.datetime.now()
            elif event['status'] == 'started':
                event['timeLeft'] = event['finish'] - datetime.datetime.now()
            thePool.append(event)
        return thePool


#Create custom HTTPRequestHandler class
class KodeFunHTTPRequestHandler(BaseHTTPRequestHandler):

    # handle GET command
    def do_GET(self):
        global values
        rootdir = '.'  # file location
        try:
            if self.path.endswith('.js') or self.path.endswith('.html'):
                with open(rootdir + self.path) as f:  # open requested file

                    #send code 200 response
                    self.send_response(200)

                    #send header first
                    contentType = 'javascript' if self.path.endswith('js') else 'html'
                    self.send_header('Content-type', 'text/' + contentType)
                    self.end_headers()

                    #send file content to client
                    self.wfile.write(bytes(f.read(), "utf-8"))
                return
            elif '/api/' in self.path:
                '''
                pattern: /api/{command}/{id:optional}
                rest options:
                get: get all programs
                save: save new program
                query: get specific program
                remove: remove specific program
                delete: delete all programs
                '''

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                sn = int(parsed['sid'][0])
                v = int(parsed['v'][0])
                if sn < 0 or sn > (num_stations-1) or v < 0 or v > 1:
                    self.wfile.write(bytes('<script>alert(\"Wrong value!\");</script>', 'utf-8'))
                else:
                    if v == 0:
                        values[sn] = 0
                    else:
                        values[sn] = 1
                    setShiftRegister(values)

                self.wfile.write(bytes('<script>window.location=\".\";</script>', 'utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes("<script>\nvar nstations=", "utf-8"))
                self.wfile.write(bytes(str(num_stations), "utf-8"))
                self.wfile.write(bytes(', values=[', "utf-8"))
                for s in range(0, num_stations):
                    self.wfile.write(bytes(str(values[s]), "utf-8"))
                    self.wfile.write(bytes(',', "utf-8"))
                self.wfile.write(bytes('0];\n</script>\n', "utf-8"))
                self.wfile.write(bytes('<script src=\'manual.js\'></script>', 'utf-8'))

        except IOError:
            self.send_error(404, 'file not found')

    def do_POST(self):
        pass


def run():
    disableShiftRegisterOutput()
    setShiftRegister(values)
    enableShiftRegisterOutput()

    # Setup Mongo
    db = MongoClient()['sprinkler']
    settings = db.settings
    programs = db.programs
    sprinklerLog = db.log

    print([x for x in db.settings.find()])
    print([x for x in db.programs.find()])

    s = Scheduler()
    # s.addSet(nextStart, [(0, 5), (1, 10), (2, 10), (3, 5)])
    for p in db.programs.find():
        print(p)
        startTime = datetime.time(*minToHM(p['start']))
        print("Start is at %s" % startTime)
        s.addSet(startTime, p['zones'])



    #start at 7 am
    # startTime = datetime.time(7)
    # nextStart = datetime.datetime.now() + datetime.timedelta(seconds=5)
    # if nextStart < datetime.datetime.now():
    #     nextStart = nextStart + datetime.timedelta(days=1)

    # print ("Next start is %s" % nextStart)


    #ip and port of servr
    #by default http server port is 8080
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, KodeFunHTTPRequestHandler)
    print('OpenSprinkler Pi is running...')
    while True:
        httpd.handle_request()


def progexit():
    global values
    values = [0]*num_stations
    setShiftRegister(values)
    pin_sr_clk.close()
    pin_sr_lat.close()
    pin_sr_noe.close()
    pin_sr_dat.close()


if __name__ == '__main__':
    atexit.register(progexit)
    run()

    # Setup Mongo
    db = MongoClient()['sprinkler']
    settings = db.settings
    programs = db.programs
    sprinklerLog = db.log

    print([x for x in db.settings.find()])
    print([x for x in db.programs.find()])

