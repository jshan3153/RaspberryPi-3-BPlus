'''
GPS Interfacing with Raspberry Pi using Pyhton
http://www.electronicwings.com
'''
import serial               #import serial pacakge
from time import sleep
import webbrowser           #import package for opening link in browser
import sys                  #import system package
import RPi.GPIO as GPIO
import threading
import http.client

gpgga_info = "$GPGGA,"

GPGGA_buffer = 0
NMEA_buff = 0
lat_in_degrees = 0
long_in_degrees = 0
error = 0
led = 0
txtime = 0
txlat = 0
txlon = 0
txready = 0

def GPS_Info():
    global NMEA_buff
    global lat_in_degrees
    global long_in_degrees
    global txready
    global txtime, txlat, txlon
    nmea_time = [] #list
    nmea_latitude = []
    nmea_longitude = []
    try:
        nmea_time = NMEA_buff[0]                    #extract time from GPGGA string
        nmea_latitude = NMEA_buff[1]                #extract latitude from GPGGA string
        nmea_longitude = NMEA_buff[3]               #extract longitude from GPGGA string
        satelite = NMEA_buff[6]                     #extract gps satelite from GPGGA string
    except:
        print(NMEA_buff)
        return
    
    #print("NMEA Time: ", nmea_time,'\n')
    #print ("NMEA Latitude:", nmea_latitude,"NMEA Longitude:", nmea_longitude,'\n')
    #print("Satelite : ", satelite, '\n')
    
    lat = float(nmea_latitude)                  #convert string into float for calculation
    longi = float(nmea_longitude)               #convertr string into float for calculation
    
    lat_in_degrees = convert_to_degrees(lat)    #get latitude in degree decimal format
    long_in_degrees = convert_to_degrees(longi) #get longitude in degree decimal format
    
    print(nmea_time, "LAT:", lat_in_degrees, " LON:", long_in_degrees, "[", satelite, "]", '\n')
    
    txtime = nmea_time.replace('.','')
    txtime = txtime.ljust(10,'0')
    #print(nmea_time, txtime)
    
    txlat = nmea_latitude.replace('.','')
    #print(nmea_latitude, txlat)

    txlon = nmea_longitude.replace('.','')
    #print(nmea_longitude, txlon)
    #payload = "8931440400065254618626990010010002000005000120000#"+txtime+txlat+txlon+"20#"
    txready = 1
    #print(payload)

#convert raw NMEA string into degree decimal format   
def convert_to_degrees(raw_value):
    decimal_value = raw_value/100.00
    degrees = int(decimal_value)
    mm_mmmm = (decimal_value - int(decimal_value))/0.6
    position = degrees + mm_mmmm
    position = "%.4f" %(position)
    return position

def send_to_server(reportType):
    print('send2server')
    global txready
    global txtime
    global txlat
    global txlon
    usim = "89314404000652546186" #"89314404000476684577"
    
    timer=threading.Timer(60, send_to_server, args=['1'])
    timer.start()

    conn = http.client.HTTPSConnection("protocol.cleancitynetworks.com")

    headers = {
      'Content-Type': 'text/plain'
    }
    
    if txready == 1:
        payload = usim + "26990010010304"+reportType+"00000800251000#"+txtime+'+'+txlat+'+'+txlon+"20#"
        #print(payload)
        txready = 0
    else:
        payload = usim + "26990010010304"+reportType+"00000800251000##"    
        print('tx not ready')

    conn.request("POST", "/ttk", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    return
    
def main():
    global ser
    global lat_in_degrees
    global long_in_degrees
    global NMEA_buff
    led = 0
    error = 0
    
    ser = serial.Serial(
        port='/dev/ttyS0',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
        )
        
    # GPIO setup
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(36, GPIO.OUT)
    GPIO.setup(37, GPIO.OUT)
    GPIO.setup(38, GPIO.OUT)
    GPIO.setup(40, GPIO.OUT)

    GPIO.output(37, GPIO.HIGH)

    GPIO.output(36, GPIO.LOW)
    GPIO.output(38, GPIO.LOW)
    GPIO.output(40, GPIO.LOW)

    #set timer
    send_to_server('0')
    
    try:
        while True:
            received_data = (str)(ser.readline())                   #read NMEA string received
            #print(received_data)
            #received_data = 0
        
            GPGGA_data_available = received_data.find(gpgga_info)   #check for NMEA GPGGA string                 
        
            if (GPGGA_data_available>0):
                comma_count = received_data.count(',')
                
                if(comma_count<13):
                    error += 1
                    print('error %d' % error)
                else:
                    GPGGA_buffer = received_data.split("$GPGGA,",1)[1]  #store data coming after "$GPGGA," string
                    NMEA_buff = (GPGGA_buffer.split(','))               #store comma separated data in buffer
                    #check null buffer
                    if not NMEA_buff[5]:
                        print('no fix flag\n')
                        error += 1
                    elif NMEA_buff[5] != '0':
                        GPS_Info()                                          #get time, latitude, longitude
                        #print("lat in degrees:", lat_in_degrees," long in degree: ", long_in_degrees, '\n')
                        #map_link = 'http://maps.google.com/?q=' + lat_in_degrees + ',' + long_in_degrees    #create link to plot location on Google map
                        #print("<<<<<<<<press ctrl+c to plot location on google maps>>>>>>\n")               #press ctrl+c to plot on map and exit 
                        #print("------------------------------------------------------------\n")
                        GPIO.output(38, GPIO.LOW)
                        
                        if led == 0:
                            GPIO.output(40, GPIO.HIGH)
                            led = 1
                        else:
                            GPIO.output(40, GPIO.LOW)
                            led = 0

                    else:
                        print('not fixed :', NMEA_buff)
                        GPIO.output(38, GPIO.HIGH)
                        if led:
                            GPIO.output(40, GPIO.LOW)
                            
                GPGGA_data_available = 0
           
            received_data = 0

    except KeyboardInterrupt:
        #webbrowser.open(map_link)        #open current position information in google map
        GPIO.cleanup()
        sys.exit(0)
        
if __name__ == '__main__':
    main()
