'''Creates .random_bytes folder and populates with 1kb random byte files.'''

import os
import decimal
import multiprocessing
import sys
import time

def function(joint_queue):
    while True:
        t1 = decimal.Decimal('%.6f'%(time.time()))
        t2 = decimal.Decimal('%.6f'%(time.time())) +\
             decimal.Decimal(str('.1'))
        loopcount = 0
        while decimal.Decimal(str(time.time())) < t2:
            loopcount += 1
        joint_queue.put(loopcount % 2)

def queue_process(joint_queue, output_size):
    while True:
        if joint_queue.qsize() > output_size*8:
            bit_list = []
            # Queue to list
            for x in range(0, output_size*8):
                bit = joint_queue.get()
                bit_list.append(bit)
            byte_list = []
            # Create byte from bits
            while len(bit_list) > 0:
                current_byte = []
                while len(current_byte) < 8:
                    current_byte.append(str(bit_list.pop()))
                byte_text_rep = ''.join(current_byte)
                byte_int = int(byte_text_rep, 2)
                byte_list.append(byte_int)
                #0b111 is format
            write_array = bytearray(byte_list)    
            timestamp = '%.6f'%(time.time())
            with open('NUK_' + str(timestamp) + '.bin', 'w+b') as f:
                f.write(write_array)
            print('Wrote ' + 'NUK_' + str(timestamp) + '.bin')
        time.sleep(1)
######

HOMEDIR = os.path.expanduser("~")
DATADIR = os.path.join(HOMEDIR, '.random_bytes')

try:
    os.nice(20)
except Exception:
    pass

if not os.path.exists(DATADIR):
    print('Creating .random_bytes folder.')
    os.mkdir(DATADIR)
    
os.chdir(DATADIR)

joint_q = multiprocessing.Queue()

print('Starting random byte generation.')

for x in range(0, 4):
    t = multiprocessing.Process(target=function, args=(joint_q,))
    t.start()

for x in range(0,1):
    t = multiprocessing.Process(target=queue_process, args=(joint_q, 1024))
    time.sleep(1)
    t.start()
    
    
   
