from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish, xmlstream
from twisted.internet import reactor
import time

name = 'cradle'
server='cradle.dyndns.org'
resource = 'AssaultVector'
password = 'ug0/*worz'
me = '%s@%s/%s' % (name, server, resource)

thexmlstream = None
tryandregister = 1

def initOnline(xmlstream):
     global factory
     print 'Initializing...'
     xmlstream.addObserver('/message', gotMessage)
     xmlstream.addObserver('/presence', gotPresence)
     xmlstream.addObserver('/iq', gotIq)
     xmlstream.addObserver('/*', gotSomething)

def authd(xmlstream):
     thexmlstream = xmlstream
     print "we've authd!"
     print repr(xmlstream)

     #need to send presence so clients know we're
     #actually online
     presence = domish.Element(('jabber:client', 'presence'))
     presence.addElement('status').addContent('Online')
     xmlstream.send(presence)

     initOnline(xmlstream)

def gotMessage(el):
     print 'Got message: %s' % str(el.attributes)

def gotSomething(el):
     print 'Got something: %s -> %s' % (el.name, str(el.attributes))

def gotIq(el):
     print 'Got IQ: %s' % str(el.attributes)

def gotPresence(el):
     print 'We got a presence message!'
     print repr(el.attributes)
     try:
         t = el.attributes['type']
         if t == 'subscribe':
             # Grant every subscription request
             xmlstream.send(domish.Element(('jabber:client', 'presence'), attribs={
                 'from': me,
                 'to':el.attributes['from'],
                 'type':'subscribed'
             }))
     except KeyError:
         # Big fat ignore
         pass

def invaliduserEvent(xmlstream):
     print 'Invalid user!'
     global tryandregister
     if tryandregister:
         tryandregister = 0
         print 'Attempting to register...'
         global factory
         factory.authenticator.registerAccount(name, password)
     else:
         global reactor
         reactor.stop()

def authfailedEvent(xmlstream):
     global reactor
     print 'Auth failed!'
     reactor.stop()

def registerfailedEvent(xmlstream):
     global reactor
     print 'Register failed!'
     reactor.stop()

myJid = jid.JID(me)
secret = password
factory = client.basicClientFactory(myJid,secret)

# Register authentication callbacks
factory.addBootstrap('//event/stream/authd', authd)
factory.addBootstrap('//event/client/basicauth/invaliduser', invaliduserEvent)
factory.addBootstrap('//event/client/basicauth/authfailed', authfailedEvent)
factory.addBootstrap('//event/client/basicauth/registerfailed', registerfailedEvent)

# Go!
reactor.connectTCP(server, 5222, factory)
reactor.startRunning()
while reactor.running:
    reactor.runUntilCurrent()
    reactor.doIteration(0)
    time.sleep(1)
