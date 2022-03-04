# door v1.0
#
#
from mfrc522 import MFRC522
from machine import Pin,SPI
from machine import SoftI2C
from LCD1602 import LCD1602
from i2c_lcd import I2cLcd

import os
import network
import utime 
import ufirebase as firebase
import json

wifi = False

sta_if = network.WLAN(network.STA_IF); sta_if.active(True)


DEFAULT_I2C_ADDR = 0x27
role = Pin(32,Pin.OUT)

i2c = SoftI2C(scl=Pin(22, Pin.OUT, Pin.PULL_UP),
              sda=Pin(21, Pin.OUT, Pin.PULL_UP),
              freq=400000)

print(hex(i2c.scan()[0]))

lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 2, 16)

lcd.clear()
lcd.putstr("Starting....")

spi = SPI(2, baudrate=2500000, polarity=0, phase=0)
spi.init()

firebase.setURL("your firebase url")

door = False
rdr = MFRC522(spi=spi, gpioRst=4, gpioCs=5)

wifiDict={'wi-fi ssid1':'wi-fi password1','wi-fi ssid2':'wi-fi password2'}

def Check_Wifi():
    if wifi:
      return
    
    try:
        print("checking")
        nets = sta_if.scan()
        for i in range(0,len(nets)):
            for a in wifiDict:                
                if nets[i][0] == b'{}'.format(a):
                    print("wifi founded: "+a)
                    while not sta_if.isconnected():
                        sta_if.connect(a,wifiDict[a])
                    break 
        return sta_if.isconnected()
    except:
        print("error1")
        NoWifiJob()
        return False

def GetUsers():
    try:
        firebase.get("users","users")
        print("Users alınıyor")
        while 1:
            utime.sleep(0.01)
            try:
                firebase.users
                break
            except:
                pass
    except:
        print("error2")

def GetDoor():
    firebase.get("door","door")
    return firebase.door

def OpenDoor(username):
    global door
    door = True
    role.value(1)
    print("Door opened")
    lcd.clear()
    lcd.putstr("    Welcome")
    lcd.move_to(0,1)
    lcd.putstr(username)
    utime.sleep(2)

def CloseDoor(username):
    global door
    door = False
    role.value(0)
    print("Door Closed")
    lcd.clear()
    lcd.putstr("     Goodbye")
    lcd.move_to(0,1)
    lcd.putstr(username)
    utime.sleep(2)

def NoWifiJob():
    print("NoWifiJob")
    try:
        (stat, tag_type) = rdr.request(rdr.REQIDL)
        if stat == rdr.OK:
            (stat, raw_uid) = rdr.anticoll()
            if stat == rdr.OK:
                card_id = "0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                print(card_id)
                lcd.clear()
                lcd.putstr("  Card Readed")
                lcd.move_to(0,1)
                lcd.putstr("  Checking Perm ")
                CheckFromFile(card_id)
                #door = GetDoor()
        print("Place card")
        lcd.clear()
        lcd.putstr("------IEEE------")
        lcd.move_to(0,1)
        lcd.putstr("   Place Card")
        print("Card Checked")
    except:
        print("error3")
    
def WithWifiJob():
    print("with wifi job")
    UpdateFile()
    NoWifiJob()

def UpdateFile():
    GetUsers()
    userFile = open("userdata.txt","w+")
    userDict = firebase.users
    text = str(firebase.users)
    userFile.write(str(firebase.users).replace("'",'"').replace("True",'"True"').replace("False",'"False"'))
    userFile.close()
    
def CheckFromFile(cardUID):
    userFile = open("userdata.txt","r")
    userText = userFile.read()
    userJson = json.loads(userText)
    userFile.close()
    try:
        if userJson[cardUID]["doorPerm"] == "True":
            if door:
                CloseDoor(userJson[cardUID]["name"])
            else:
                OpenDoor(userJson[cardUID]["name"])
        else:
            print("No perm")
            lcd.clear()
            lcd.putstr("  Card Readed ")
            lcd.move_to(0,1)
            lcd.putstr("    No Perm")
    except KeyError:
        print("no user")
        SendUnknownCard(cardUID)
    utime.sleep(2)

def SendUnknownCard(cardUID):
    global wifi
    try:
        if wifi:
            lcd.clear()
            lcd.putstr("  Unknown Card  ")
            lcd.move_to(0,1)
            lcd.putstr("  Data Sending")
            firebase.put("unknownCards/"+cardUID+"/lastDate","00.00.1000")
        else:
            print("No Wifi Connection. Unknown Card can not sended")
            lcd.clear()
            lcd.putstr("  Unknown Card  ")
            lcd.move_to(0,1)
            lcd.putstr(" No Connection")
    except:
        print("error sendunknowncard")
    
while True:
    if not sta_if.isconnected():
        if Check_Wifi():
            print("wifi: ",sta_if.isconnected())
        else:
            NoWifiJob()
        wifi = False
    else:
        WithWifiJob()
        wifi = True

