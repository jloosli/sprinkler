#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os
from quick2wire.gpio import pins, Out
#import RPi.GPIO as GPIO
import atexit

# GPIO PIN DEFINES

pin_sr_clk =  4
pin_sr_noe = 17
pin_sr_dat = 21 # NOTE: if you have a RPi rev.2, need to change this to 27
pin_sr_lat = 22

# pin_sr_clk = pins.pin(7, Out)
# pin_sr_noe = pins.pin(11, Out)
# pin_sr_dat = pins.pin(13, Out) # Note: if you have a RPi rev.2, need to change this to 27
# pin_sr_lat = pins.pin(15, Out)
pin_sr_clk = pins.pin(4, Out)
pin_sr_noe = pins.pin(17, Out)
pin_sr_dat = pins.pin(21, Out) # Note: if you have a RPi rev.2, need to change this to 27
pin_sr_lat = pins.pin(22, Out)

# NUMBER OF STATIONS
num_stations = 16

# STATION BITS 
values = [0]*num_stations

def enableShiftRegisterOutput():
    with pin_sr_noe:
        pin_sr_noe.value = False

def disableShiftRegisterOutput():
    with pin_sr_noe:
        pin_sr_noe.value = True

def setShiftRegister(values):
    with pin_sr_clk, pin_sr_lat, pin_sr_clk, pin_sr_dat:
        pin_sr_clk.value = False
        pin_sr_lat.value = False
        for s in range(num_stations):
            pin_sr_clk.value = False
            pin_sr_dat.value = values[num_stations-1-s]
            pin_sr_clk.value = True
        pin_sr_lat.value = True

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
                self.send_header('Content-type','text/html')
                self.end_headers()

                #send file content to client
                self.wfile.write(f.read())
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
                    self.wfile.write('<script>alert(\"Wrong value!\");</script>');
                else:
                    if v==0:
                        values[sn] = 0
                    else:
                        values[sn] = 1
                    setShiftRegister(values)

                self.wfile.write('<script>window.location=\".\";</script>')
            else:
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<script>\nvar nstations=')
                self.wfile.write(num_stations)
                self.wfile.write(', values=[')
                for s in range(0,num_stations):
                    self.wfile.write(values[s])
                    self.wfile.write(',')
                self.wfile.write('0];\n</script>\n')
                self.wfile.write('<script src=\'manual.js\'></script>')

        except IOError:
            self.send_error(404, 'file not found')
    
def run():
    #GPIO.cleanup()
    # setup GPIO pins to interface with shift register
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(pin_sr_clk, GPIO.OUT)
    # GPIO.setup(pin_sr_noe, GPIO.OUT)
    disableShiftRegisterOutput()
    # GPIO.setup(pin_sr_dat, GPIO.OUT)
    # GPIO.setup(pin_sr_lat, GPIO.OUT)

    setShiftRegister(values)
    enableShiftRegisterOutput()

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
    #GPIO.cleanup()

if __name__ == '__main__':
    atexit.register(progexit)
    run()
