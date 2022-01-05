
import os
import sys, getopt
import random
from random import randint
import select
from bluetooth import BluetoothSocket, RFCOMM, discover_devices
import bluetooth
import datetime
import time
import socket
from colour import Color
from PIL import Image, ImageDraw, ImageFont
from itertools import product

from playsound import playsound
from requests import get

import json
import bs4
from bs4 import BeautifulSoup



target_name = "My Phone"
target_address = "11:75:58:1B:52:85"


nearby_devices = bluetooth.discover_devices()

for bdaddr in nearby_devices:
    if target_name == bluetooth.lookup_name( bdaddr ):
        target_address = bdaddr
        break

if target_address is not None:
    print ( "Appareil trouvé", target_address )
else:
    print ( "Appareil non trouvé" )


port=4

s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
s.connect((target_address,port))

print("connecté !")

VIEWTYPES = {
    "clock": 0x00,
    "temp": 0x01,
    "off": 0x02,
    "anim": 0x03,
    "graph": 0x04,
    "image": 0x05,
    "stopwatch": 0x06,
    "scoreboard": 0x07
}
def mask(bytes):
    _bytes = []
    for b in bytes:
        if (b == 0x01):
            _bytes = _bytes + [0x03, 0x04]
        elif (b == 0x02):
            _bytes = _bytes + [0x03, 0x05]
        elif (b == 0x03):
            _bytes = _bytes + [0x03, 0x06]
        else:
            _bytes += [b]

    return _bytes



def checksum(s):
    ck1 = s & 0x00ff
    ck2 = s >> 8

    return ck1, ck2

def set_time_color(r, g, b, x=0x00, h24=True):
    head = [0x09, 0x00, 0x45, 0x00, 0x01 if h24 else 0x00]
    s = sum(head) + sum([r, g, b, x])
    ck1, ck2 = checksum(s)

    # create message mask 0x01,0x02,0x03
    msg = [0x01] + mask(head) + mask([r, g, b, x]) + mask([ck1, ck2]) + [0x02]

    return msg

# Images
def conv_image(data):
    # should be 11x11 px => 
    head = [0xbd, 0x00, 0x44, 0x00, 0x0a, 0x0a, 0x04]
    data = data
    ck1, ck2 = checksum(sum(head) + sum(data))

    msg = [0x01] + head + mask(data) + mask([ck1, ck2]) + [0x02]
    return msg

def process_image(imagedata, sz=11, scale=None):
    img = [0]
    bc = 0
    first = True

    if (scale):
        src = imagedata.resize((sz, sz), scale)
    else:
        src = imagedata.resize((sz, sz))

    for c in product(range(sz), range(sz)):
        y, x = c
        r, g, b, a = src.getpixel((x, y))

        if (first):
            img[-1] = ((r & 0xf0) >> 4) + (g & 0xf0) if a > 32 else 0
            img.append((b & 0xf0) >> 4) if a > 32 else img.append(0)
            first = False
        else:
            img[-1] += (r & 0xf0) if a > 32 else 0
            img.append(((g & 0xf0) >> 4) + (b & 0xf0)) if a > 32 else img.append(0)
            img.append(0)
            first = True
        bc += 1
    return img


def load_image(file, sz=11, scale=None):
    with Image.open(file).convert("RGBA") as imagedata:
        return process_image(imagedata, sz)

def load_gif_frames(file, sz=11, scale=None):
    with Image.open(file) as imagedata:
        for f in getFrames(imagedata):
            yield process_image(f, sz, scale)

file = "count.png"

url = "https://www.instagram.com/mat.sansen/"



# gif:

def getFrames(im):
    '''
    Iterate the GIF, extracting each frame.
    '''
    mode = analyseImage(im)['mode']

    p = im.getpalette()
    last_frame = im.convert('RGBA')

    try:
        while True:
            '''
            If the GIF uses local colour tables, each frame will have its own palette.
            If not, we need to apply the global palette to the new frame.
            '''
            if not im.getpalette():
                im.putpalette(p)

            new_frame = Image.new('RGBA', im.size)

            '''
            Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
            If so, we need to construct the new frame by pasting it on top of the preceding frames.
            '''
            if mode == 'partial':
                new_frame.paste(last_frame)

            new_frame.paste(im, (0, 0), im.convert('RGBA'))
            yield new_frame

            last_frame = new_frame
            im.seek(im.tell() + 1)
    except EOFError:
        pass



while (1):
    text = input()
    if ( text == "quit" ):
        break
    #s.send(bytes(text, 'UTF-8'))
    if ( text == "test" ):

        s.send(bytes(set_time_color(0, 120, 255)))

    if ( text == "disco" ):
        while (1):
            rR = (random.randint(0, 255))
            gR = (random.randint(0, 255))
            bR = (random.randint(0, 255))
            s.send(bytes(set_time_color(rR, gR, bR)))
            time.sleep(.1)
    
    if ( text == "count" ):
        s.send(bytes(conv_image(load_image(file))))

    if ( text == "sound" ):
        playsound('son1.wav')

    if ( text == "insta"):
        while (1):
            response = get(url)

            html_soup = BeautifulSoup(response.text, 'html.parser')
            type(html_soup)



            img = Image.new('RGB', (11, 11), color = (0, 0, 0))
            fnt = ImageFont.truetype('font2.ttf', 8)
            d = ImageDraw.Draw(img)
            
            first=input("1:")
            sec=input("2:")
            third=input("3:")
            d.text((0,0), first, font=fnt, fill=(255, 0, 0))
            d.text((4,3), sec, font=fnt, fill=(0, 255, 0))
            d.text((7,0), third, font=fnt, fill=(0, 0, 255))

            img.save("count.png")
            time.sleep(.1)
            s.send(bytes(conv_image(load_image(file))))

            time.sleep(2)
    
    if ( text == "anim"):
        print("animation")



s.close()

#s.send(bytes([0x01] + mask([0x04, 0x00, 0x05, 0x01, 0x0a, 0x00]) + [0x02]))

