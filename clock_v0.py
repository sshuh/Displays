# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 23:30:13 2019

@author: sshuh
"""
from multiprocessing import Process, Queue
import datetime
import time
import tkinter as tk


def f(q):
    
    while 1:
        t = datetime.datetime.now()
        str_date = t.strftime('%Y %m %d %a')
        str_time = t.strftime('%H:%M:%S')

        q.put([str_date, str_time])
        time.sleep(0.25)


def tk_clock():

    root = tk.Tk()
    
    #root.attributes("-fullscreen", True) 
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
    p = Process(target=f, args=(q,))
    p.start()
    
    tk_clock()
    
#    for i in range(100):
#        time.sleep(0.25)
#        try:
#            print(q.get(False))    # prints "[42, None, 'hello']"
#        except:
#            pass
        
    p.join()
    
    