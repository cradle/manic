from twisted.spread import jelly
from twisted.spread import banana
from zlib import compress, decompress
import random
import time
import cerealizer as cerealizer

class timer:
    def __init__(self):
        self.s = 0
        self.t = 0

    def start(self):
        self.s = time.clock()

    def stop(self):
        self.t = time.clock() - self.s

    def time(self):
        return self.t

def a(var):
    t = timer()


    
    t.start(); data = banana.encode(var); t.stop()
    print "Enc B       :", t.time(), len(data)
    t.start(); banana.decode(data); t.stop()
    print "Dec B       :", t.time()
    t.start(); data = compress(banana.encode(var),9); t.stop()
    print "Enc B (zip9):", t.time(), len(data)
    t.start(); banana.decode(decompress(data)); t.stop()
    print "Dec B (zip9):", t.time()
    t.start(); data = compress(banana.encode(var),4); t.stop()
    print "Enc B (zip4):", t.time(), len(data)
    t.start(); banana.decode(decompress(data)); t.stop()
    print "Dec B (zip4):", t.time()
    t.start(); data = compress(banana.encode(var),1); t.stop()
    print "Enc B (zip1):", t.time(), len(data)
    t.start(); banana.decode(decompress(data)); t.stop()
    print "Dec B (zip1):", t.time()


    
    t.start(); data = cerealizer.dumps(var); t.stop()
    print "Enc C       :", t.time(), len(data)
    t.start(); cerealizer.loads(data); t.stop()
    print "Dec C       :", t.time()
    t.start(); data = compress(cerealizer.dumps(var),9); t.stop()
    print "Enc C (zip9):", t.time(), len(data)
    t.start(); cerealizer.loads(decompress(data)); t.stop()
    print "Dec C (zip9):", t.time()
    t.start(); data = compress(cerealizer.dumps(var),4); t.stop()
    print "Enc C (zip4):", t.time(), len(data)
    t.start(); cerealizer.loads(decompress(data)); t.stop()
    print "Dec C (zip4):", t.time()
    t.start(); data = compress(cerealizer.dumps(var),1); t.stop()
    print "Enc C (zip1):", t.time(), len(data)
    t.start(); cerealizer.loads(decompress(data)); t.stop()
    print "Dec C (zip1):", t.time()


    
    t.start(); data = banana.encode(jelly.jelly(var)); t.stop()
    print "Enc BJ      :", t.time(), len(data)
    t.start(); jelly.unjelly(banana.decode(data)); t.stop()
    print "Dec BJ      :", t.time()
    t.start(); data = compress(banana.encode(jelly.jelly(var)),9); t.stop()
    print "Enc BJ(zip9):", t.time(), len(data)
    t.start(); jelly.unjelly(banana.decode(decompress(data))); t.stop()
    print "Dec BJ(zip9):", t.time()
    t.start(); data = compress(banana.encode(jelly.jelly(var)),4); t.stop()
    print "Enc BJ(zip4):", t.time(), len(data)
    t.start(); jelly.unjelly(banana.decode(decompress(data))); t.stop()
    print "Dec BJ(zip4):", t.time()
    t.start(); data = compress(banana.encode(jelly.jelly(var)),1); t.stop()
    print "Enc BJ(zip1):", t.time(), len(data)
    t.start(); jelly.unjelly(banana.decode(decompress(data))); t.stop()
    print "Dec BJ(zip1):", t.time()

def generateData(num):
    return [[name,\
             [[random.random(),random.random()],\
              [random.random(),random.random()],\
              random.random(),\
              random.random(),\
              random.random(),\
              random.randint(0,100),\
              random.randint(0,30)], \
             True, \
             "BulletObject",\
             ["shoot"]] for name in [("b%i" % i) for i in range(num)]]
    
