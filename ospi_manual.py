#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os
from quick2wire.gpio import pins, Out
#import RPi.GPIO as GPIO
import atexit


# GPIO PIN DEFINES

# pin_sr_clk =  4
# pin_sr_noe = 17
# pin_sr_dat = 21 # NOTE: if you have a RPi rev.2, need to change this to 27
# pin_sr_lat = 22

# pin_sr_clk = pins.pin(4, Out) 7
# pin_sr_noe = pins.pin(17, Out) 0
# pin_sr_dat = pins.pin(21, Out) 2 # Note: if you have a RPi rev.2, need to change this to 27
# pin_sr_lat = pins.pin(22, Out) 3

# NUMBER OF STATIONS
num_stations = 16

# STATION BITS 
values = [0]*num_stations

pin_sr_clk = pins.pin(7, Out)
pin_sr_noe = pins.pin(0, Out)
pin_sr_dat = pins.pin(2, Out) # Note: if you have a RPi rev.2, need to change this to 27
pin_sr_lat = pins.pin(3, Out)

pin_sr_clk.open()
pin_sr_lat.open()
pin_sr_noe.open()
pin_sr_dat.open()






def enableShiftRegisterOutput():
    pin_sr_noe.value = 0

def disableShiftRegisterOutput():
    pin_sr_noe.value = 1

def setShiftRegister(values):
    print ("In set")
    print (values)
    
    pin_sr_clk.value = False
    pin_sr_lat.value = False
    for s in range(num_stations):
        pin_sr_clk.value = False
        pin_sr_dat.value = values[num_stations-1-s]
        pin_sr_clk.value = True
    pin_sr_lat.value = True

#Create custom HTTPRequestHandler class
class KodeFunHTTPRequestHandler(BaseHTTPRequestHandler):

    # def __init__(self):
    #     self.Comm = StationComm()
    
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
                self.send_header('Content-type','text/html')
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
                v  = int(parsed['v'][0])                        
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
                self.send_header('Content-type','text/html')
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
    #GPIO.cleanup()
    # setup GPIO pins to interface with shift register
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(pin_sr_clk, GPIO.OUT)
    # GPIO.setup(pin_sr_noe, GPIO.OUT)
    # disableShiftRegisterOutput()
    # GPIO.setup(pin_sr_dat, GPIO.OUT)
    # GPIO.setup(pin_sr_lat, GPIO.OUT)

    disableShiftRegisterOutput()
    setShiftRegister(values)
    enableShiftRegisterOutput()


    # setShiftRegister(values)
    # enableShiftRegisterOutput()

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
