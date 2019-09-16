# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 23:30:13 2019

@author: sshuh
"""
from multiprocessing import Process, Queue
import datetime
import time
import tkinter as tk

import serial
import struct

import numpy as np

import os


def f(q):
    
    while 1:
        t = datetime.datetime.now()
        str_date = t.strftime('%Y %m %d %a')
        str_time = t.strftime('%H:%M:%S')

        q.put([str_date, str_time])
        time.sleep(0.25)


def getChecksum( _checksum, _header, _payload ):
    
    ck_a = 0
    ck_b = 0
    for i in range(4):
        ck_a = ck_a + _header[i]
        ck_b = ck_b + ck_a
        
    for i in range(len(_payload)):
        ck_a = ck_a + _payload[i]
        ck_b = ck_b + ck_a
        
    ck_a = np.mod(ck_a, 256)
    ck_b = np.mod(ck_b, 256)
    
    if not _checksum[0] == int(ck_a):
        print('ck_a ', _checksum[0], ck_a )
        return False
        
    if not _checksum[1] == int(ck_b):   
        print('ck_b ', _checksum[1], ck_b )        
        return False
    
    return True
    

def runGPS(q):

    str_port = '/dev/ttyUSB0'

    str_cmd = 'sudo chmod +x ' + str_port

    ret_os = os.system(str_cmd)

    if not ret_os == 0:
        print('failed ', str_cmd)
        return

    ser = serial.Serial(port=str_port, baudrate=38400, parity=serial.PARITY_NONE,\
                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,\
                            timeout=0)
    
    ser.flush()
    
    try:
        
        while True:
            
            w = ser.inWaiting()
            if w < 6:
                time.sleep(0.02)
                continue
                    
            sync_ch0 = int.from_bytes(ser.read(1), byteorder='little')
            if sync_ch0 == 0xB5:
                sync_ch1 = int.from_bytes(ser.read(1), byteorder='little')
                if sync_ch1 != 0x62:
                    continue
            else:
                continue
                        
            header4 = ser.read(4)
            header_class = struct.unpack('B', header4[0:1])[0]
            header_id = struct.unpack('B', header4[1:2])[0]
            payload_length = struct.unpack('H', header4[2:4])[0]
            
            while True:
                w = ser.inWaiting()
                if w < payload_length+2:
                    time.sleep(0.02)
                else:
                    break
                            
            payload = ser.read(payload_length)
            
            checksum = ser.read(2)
            ret_ck = getChecksum( checksum, header4, payload )
          
            # UBX-NAV-SOL (0x01 0x06) : Navigation Solution Information
            if header_class == 0x01 and header_id == 0x06:
                iTOW = struct.unpack('I', payload[0:4])[0]
                fTOW = struct.unpack('i', payload[4:8])[0]
                week = struct.unpack('h', payload[8:10])[0]
                gpsFix = struct.unpack('B', payload[10:11])[0]
                flags = struct.unpack('B', payload[11:12])[0]
                ecefX = struct.unpack('i', payload[12:16])[0]
                ecefY = struct.unpack('i', payload[16:20])[0]
                ecefZ = struct.unpack('i', payload[20:24])[0]
                pAcc = struct.unpack('I', payload[24:28])[0]
                ecefVX = struct.unpack('i', payload[28:32])[0]
                ecefVY = struct.unpack('i', payload[32:36])[0]
                ecefVZ = struct.unpack('i', payload[36:40])[0]
                sAcc = struct.unpack('I', payload[40:44])[0]
                pDOP = struct.unpack('H', payload[44:46])[0]
                numSV = struct.unpack('B', payload[47:48])[0]
                        
                GPStime = float(iTOW)*1E-3 + float(fTOW)*1E-9
                
                # 18 sec : UTC - GPS difference
                d_time = datetime.timedelta(seconds=GPStime + week*86400*7 + 3600*9 -18)
                ref_time = datetime.datetime(1980,1,6,0,0,0)
                dst_time = ref_time + d_time
                str_dst_time = dst_time.strftime('%Y%m%d_%H%M%S') + '.' + str(dst_time.microsecond)[0:3]
                print('KST', str_dst_time)
                
                str_date = dst_time.strftime('%Y %m %d %a')
                str_time = dst_time.strftime('%H:%M:%S')
        
                q.put([str_date, str_time])                
                
                if GPStime > 200000.0:
                    print( GPStime, iTOW, fTOW )
                    break
        
            if ret_ck == False:
                break
            
            time.sleep(0.02)
            
    finally:
        ser.close()
        
    return        


def tk_clock():

    root = tk.Tk()
    
    root.attributes("-fullscreen", True) 
    root.configure(background='black')
    
    label_date = tk.Label(root, font=('arial', 75, 'bold'), fg='yellow',bg='black')
    label_date.pack()
    
    label_time = tk.Label(root, font=('arial', 180, 'bold'), fg='yellow',bg='black')
    label_time.pack()
    
    def run_clock():
        
#        t = datetime.datetime.now()
#        str_date = t.strftime('%Y %m %d %a')
#        str_time = t.strftime('%H:%M:%S')
        
        l = q.get(True)
        str_date = l[0]
        str_time = l[1]
        
        label_date.config(text=str_date)
        label_time.config(text=str_time)
        
        label_time.after(100, run_clock)      
    
    
    run_clock()
    
    root.mainloop()
    
#%%

if __name__ == '__main__':
    
    q = Queue()
    p = Process(target=runGPS, args=(q,))
    p.start()
    
    tk_clock()
    
#    for i in range(100):
#        time.sleep(0.25)
#        try:
#            print(q.get(False))
#        except:
#            pass
        
    p.join()
    
    