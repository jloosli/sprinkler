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


# GPIO PIN DEFINES (using quick2wire GPIO numbers)

# NUMBER OF STATIONS
num_stations = 16

# STATION BITS
values = [0]*num_stations

pin_sr_clk = pins.pin(7, Out) # Pin 7 (GPIO 4)
pin_sr_noe = pins.pin(0, Out) # Pin 11 (GPIO 17)
pin_sr_dat = pins.pin(2, Out) # Pin 13 (GPIO 21) # May need to be changed with rev.2 board
pin_sr_lat = pins.pin(3, Out) # Pin 15 (GPIO 22)

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


class Scheduler:

    def __init__(self):
        # self.s = sched.scheduler(time.time, time.sleep)
        self.pool = []

    def add(self, zone, start, duration):
        #id: uuid, zone, start, duration, startThread, endThread, status : queue|started|completed
        if start > datetime.datetime.now():
            delta = start - datetime.datetime.now()
            event = {
                "id": uuid1(),
                "zone": zone,
                "start": start,
                "finish": start + duration,
                "status": 'queued',
                "startThread": threading.Timer(delta.total_seconds(), zoneOn, args=[zone]),
                "endThread": threading.Timer((delta + duration).total_seconds(), zonesOff)
            }
            # duration = datetime.timedelta(duration)
            print ("Turning on zone %d in %s" % (zone, str(delta)))
            event['startThread'].name = "Zone_%d_start" % zone
            event['endThread'].name = "Zone_%d_end" % zone
            event['startThread'].start()
            event['endThread'].start()
            self.pool.append(event)

    def drop(self, id):
        pass

    def status(self):
        thePool = []
        for event in self.pool:
            if event['status'] == 'queue':
                event['timeUntilStart'] = event['start'] - datetime.datetime.now()
            elif event['status'] == 'started':
                event['timeLeft'] = event['finish'] - datetime.datetime.now()
            thePool.append(event)
        return thePool

    def run(self):
        # print ["\n".split(x) for x in self.s.queue]
        # self.s.run()
        pass




#Create custom HTTPRequestHandler class
class KodeFunHTTPRequestHandler(BaseHTTPRequestHandler):

    #handle GET command
    def do_GET(self):
        global values
        rootdir = '.' #file location
        try:
            if self.path.endswith('.js'):
                f = open(rootdir + self.path) #open requested file

                #send code 200 response
                self.send_response(200)

                #send header first
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                #send file content to client
                self.wfile.write(bytes(f.read(), "utf-8"))
                f.close()
                return
            elif '/cv?' in self.path:
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                parsed=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                sn = int(parsed['sid'][0])
                v = int(parsed['v'][0])                        
                if sn<0 or sn>(num_stations-1) or v<0 or v>1:
                    self.wfile.write(bytes('<script>alert(\"Wrong value!\");</script>', 'utf-8'))
                else:
                    if v==0:
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
                for s in range(0,num_stations):
                    self.wfile.write(bytes(str(values[s]), "utf-8"))
                    self.wfile.write(bytes(',', "utf-8"))
                self.wfile.write(bytes('0];\n</script>\n', "utf-8"))
                self.wfile.write(bytes('<script src=\'manual.js\'></script>', 'utf-8'))

        except IOError:
            self.send_error(404, 'file not found')
   
def run():
    disableShiftRegisterOutput()
    setShiftRegister(values)
    enableShiftRegisterOutput()

    #start at 7 am
    startTime = datetime.time(7)
    nextStart = datetime.datetime.now() + datetime.timedelta(seconds=5)
    #nextStart = datetime.datetime.combine(datetime.date.today(),startTime)
    if nextStart < datetime.datetime.now():
        nextStart = nextStart + datetime.timedelta(days=1)

    print ("Next start is %s" % nextStart)

    gap = datetime.timedelta(minutes=5)
    pause = datetime.timedelta(seconds=10)
    s = Scheduler()
    s.add(2, nextStart * 2, gap)
    s.add(1, nextStart+gap+pause, gap)
    s.add(0, nextStart+gap*2 + pause, gap)
    s.add(3, nextStart+gap*3 + pause, gap/5*2)
    # s.run()
    while threading.active_count() > 1:
        print ("Current threading:")
        print(s.status())
        # for thread in threading.enumerate():
        #     print (thread)
        time.sleep(10)



    #ip and port of servr
    #by default http server port is 8080
    # server_address = ('', 8080)
    # httpd = HTTPServer(server_address, KodeFunHTTPRequestHandler)
    # print('OpenSprinkler Pi is running...')
    # while True:
    #     httpd.handle_request()

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
