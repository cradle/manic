from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish, xmlstream
from twisted.internet import reactor
import time

class NetCode:
        def __init__(self, name, server, resource, password):
                self.reactor = reactor
                self.thexmlstream = None
                self.tryandregister = 1
                self.messageNum = 0
                self.el = None

                me = u'%s@%s/%s-%i' % (name, server, resource, time.time())
                self.myJID = jid.JID(me)
                self.factory = client.basicClientFactory(self.myJID, password)

                # Register authentication callbacks
                self.factory.addBootstrap('//event/stream/authd', self.authd)
                self.factory.addBootstrap('//event/client/basicauth/invaliduser', self.invaliduserEvent)
                self.factory.addBootstrap('//event/client/basicauth/authfailed', self.authfailedEvent)
                self.factory.addBootstrap('//event/client/basicauth/registerfailed', self.registerfailedEvent)

                # Go!
                self.reactor.connectTCP(server, 5222, self.factory)
                self.reactor.startRunning()

        def gotMessage(self, el):
                self.el = el
                message = ''.join([''.join(x.children) for x in el.elements() if x.name == 'body'])
                if len(message) != 0:
                        self.statusListener(str(jid.JID(el.attributes['from']).userhost()), str(message))

        def sendMessage(self, text):
                split = text.split(":",1)
                to = None
                if len(split) == 2:
                        try:
                                to = jid.JID(text.split(":")[0])
                                text = split[1]
                        except jid.InvalidFormat:
                                pass

                if to and to.user and to.host:
                        to = to.full()
                else:
                        to = 'cradle@gmail.com'

                if len(text) == 0:
                        return
                
                message = domish.Element((None, 'message'))
                message['to'] = to
                message['id'] = "%i" % self.messageNum
                message['type'] = 'chat'
                self.messageNum += 1
                message.addElement('body', content=str(text))
                event = domish.Element(('jabber:x:event', 'x'))
                event.addElement("offline")
                event.addElement("delivered")
                event.addElement("composing")
                message.addChild(event)
                if(self.thexmlstream):
                    self.thexmlstream.send(message)
                    return True
                else:
                    return False
                 
        def update(self):
                self.reactor.runUntilCurrent()
                self.reactor.doIteration(0)

        def authd(self, xmlstream):
                self.thexmlstream = xmlstream
                self.statusListener("System", "Logged in")

                #need to send presence so clients know we're
                #actually online
                presence = domish.Element(('jabber:client', 'presence'))
                presence.addElement('status').addContent('Online')
                xmlstream.send(presence)

                xmlstream.addObserver('/message', self.gotMessage)
                xmlstream.addObserver('/presence', self.gotPresence)
                xmlstream.addObserver('/iq', self.gotIq)

        def gotIq(self, el):
                pass
                #self.statusListener("System", 'Got IQ')

        def gotPresence(self, el):
                status = ''
                
                if el.hasAttribute('type'):
                        status = el.attributes['type']
                else:
                        status = 'online'

                if jid.JID(el.attributes['from']).userhost == self.myJID.userhost:
                        return
                
                self.statusListener(str(jid.JID(el.attributes['from']).userhost()), 'is %s' % status)
                        
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

        def invaliduserEvent(self, xmlstream):
                self.statusListener("System", 'Invalid user')
                if self.tryandregister:
                        self.tryandregister = 0
                        self.statusListener("System", 'Attempting to register new account')
                        self.factory.authenticator.registerAccount(name, password)
                else:
                        self.statusListener("System", 'Registration failed')
                        self.reactor.stop()

        def authfailedEvent(self, xmlstream):
                self.statusListener("System", 'Authentication failed')
                self.reactor.stop()

        def registerfailedEvent(self, xmlstream):
                self.statusListener("System", 'Registration failed')
                self.reactor.stop()

        def statusListener(self, name, message):
                #print "%s: %s" % (name, message)
                self.remoteStatusListener(name, message)

        def registerMessageListener(self, method):
                self.remoteStatusListener = method

def aMethod(a,b):
        print a,b

if __name__ == "__main__":
        n = NetCode("cradle", "cradle.dyndns.org", "test", "enter")
        n.registerMessageListener(aMethod)

        #while 1:
        #        time.sleep(0.1)
        #        n.update()
        #        #n.sendMessage("test")

n = NetCode("cradle", "cradle.dyndns.org", "test", "enter")
n.registerMessageListener(aMethod)
