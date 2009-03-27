import sys
import time

def func (a,b):
    c = int(sys.argv[1])
    d = int(sys.argv[2])
    time.sleep(5)
    print 'a = '+str(a)+' b = '+str(b)+' c = '+str(c)+' d = '+str(d)

func(1,2)