# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 00:00:06 2019

@author: sshuh
"""

import time
import serial
import struct

import numpy as np

import datetime


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
    


def runGPS():

    ser = serial.Serial(port='COM3', baudrate=38400, parity=serial.PARITY_NONE,\
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
            
                    
        #    print( hex(header0), hex(header1), hex(header_class), hex(header_id), hex(header_length) )
        
            while True:
                w = ser.inWaiting()
                if w < payload_length+2:
                    time.sleep(0.02)
                else:
                    break
                    
        
            payload = ser.read(payload_length)
            
            checksum = ser.read(2)
            ret_ck = getChecksum( checksum, header4, payload )
          
            
        #    print( len(payload), len(checksum) )
        
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
                
                print( str_date, str_time )
                
                if GPStime > 200000.0:
                    print( GPStime, iTOW, fTOW )
                    break
        
            # UBX-NAV-POSLLH (0x01 0x02) : Geodetic Position Solution
            if header_class == 0x01 and header_id == 0x02:
                iTOW = struct.unpack('I', payload[0:4])[0]
                lon = struct.unpack('i', payload[4:8])[0]
                lat = struct.unpack('i', payload[8:12])[0]
                height = struct.unpack('i', payload[12:16])[0]
                hMSL = struct.unpack('i', payload[16:20])[0]
                hAcc = struct.unpack('I', payload[20:24])[0]
                vAcc = struct.unpack('I', payload[24:28])[0]
        
        #        break
                
                
            if ret_ck == False:
                break
            
            time.sleep(0.02)
    
        
    finally:
        ser.close()
        
    return

#%%
    
runGPS()


#%%

import numpy as np

from datetime import datetime
from datetime import timedelta

def convertTime_J2KsecToDate( _J2Ksec ):
    #jd_day = np.floor(_J2Ksec/86400)
    #jd_sec = np.mod(_J2Ksec, 86400)
    #d_time = timedelta(int(jd_day), jd_sec)
    d_time = timedelta(seconds=_J2Ksec)
    ref_time = datetime(2000,1,1,12,0,0)
    dst_time = ref_time + d_time
    str_dst_time = dst_time.strftime('%Y%m%d_%H%M%S')
    #str_dst_time = '{0.year:04}{0.month:02}{0.day:02}_{0.hour:02}{0.minute:02}{0.second:02}'.format(dst_time)
    return str_dst_time


def convertTime_DateToJ2Ksec( _str_date ):
    src_time = datetime.strptime(_str_date, '%Y%m%d_%H%M%S')
    ref_time = datetime(2000,1,1,12,0,0)
    d_time = src_time - ref_time
    J2Ksec = d_time.total_seconds()
    return J2Ksec


import numpy as np
import matplotlib.pyplot as plt
import struct

size_datapath = struct.unpack('I', file_in.read(4))
num_datapath = int(size_datapath[0] / 4)

for i in range(num_datapath):
    tmp = struct.unpack('B', file_in.read(1))
    data_path.append(tmp[0])
    tmp = struct.unpack('B', file_in.read(1))
    beginning_row.append(tmp[0])
    tmp = struct.unpack('H', file_in.read(2))
    num_row_dnlk.append(tmp[0])