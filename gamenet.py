from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish, xmlstream
from twisted.names.srvconnect import SRVConnector
from twisted.internet import reactor
import time

### (used for gmail accounts)
##class XMPPClientConnector(SRVConnector):
##    def __init__(self, reactor, domain, factory):        
##	SRVConnector.__init__(self, reactor, 'xmpp-client', domain, factory)
##
##    def pickServer(self):
##        host, port = SRVConnector.pickServer(self)
##        if not self.servers and not self.orderedServers:
##		# no SRV record, fall back..             
##		port = 5222
##        return host, port

class NetCode:
        def __init__(self, name, server, resource, password, chatroom, updateInterval = 0.1):
                self.reactor = reactor
                self.thexmlstream = None
                self.server = server
                self.tryandregister = 1
                self.messageNum = 0
                self.updateInterval = updateInterval
                self.nextUpdateTime = time.time() + self.updateInterval

                me = u'%s@%s/%s-%i' % (name, server, resource, time.time())
                self.myJID = jid.JID(me)
                self.factory = client.XMPPClientFactory(self.myJID, password)

                # Register authentication callbacks
                self.factory.addBootstrap('//event/stream/authd', self.authd)
                self.factory.addBootstrap('//event/client/basicauth/invaliduser', self.invaliduserEvent)
                self.factory.addBootstrap('//event/client/basicauth/authfailed', self.authfailedEvent)
                self.factory.addBootstrap('//event/client/basicauth/registerfailed', self.registerfailedEvent)
        	#self.factory.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connectedEvent)
        	self.factory.addBootstrap('//event/stream/connected', self.connectedEvent)
		self.factory.addBootstrap(xmlstream.STREAM_END_EVENT, self.disconnectedEvent)             

                # Must be lower case
		self.globalChat = "av-" + chatroom + "-all"
		self.teamChat = "av-" + chatroom + "-team"
		self.chatRoomServer = "conference.cradle.dyndns.org"
		self.nickName = None

                # Don't start until we get a nickname

        def gotMessage(self, el):
                error = ''.join([''.join(x.attributes['code']) for x in el.elements() if x.name == 'error'])
                message = ''.join([''.join(x.children) for x in el.elements() if x.name == 'body'])
                
                if len(error) != 0:
                        self.statusListener("System", "Error, %s" % error)      
                elif len(message) != 0:
			sender = jid.JID(el.attributes['from'])
			if el.attributes['type'] == 'groupchat':
                            if str(sender.user) == self.teamChat:
                                    self.statusListener(str(sender.resource), "(team) " + str(message))
                            else:
                                    self.statusListener(str(sender.resource), str(message))
			else:
				self.statusListener(str(sender.userhost()), str(message))
				
        def sendTeamMessage(self, message):
            self.sendGroupMessage(message, self.teamChat)

        def sendAllMessage(self, message):
            self.sendGroupMessage(message, self.globalChat)

	def sendGroupMessage(self, message, room):
		self.sendMessage(room + "@" + self.chatRoomServer + ":" + message, type="groupchat")

        def sendMessage(self, text, type='groupchat'):
                split = text.split(":",1)
                to = None
                if len(split) == 2 and split[0].lower() == "team":
                        self.sendTeamMessage(split[1].strip())
                        return
                
                if len(split) == 2 and len(split[0]) != 0:
                        try:
                                to = jid.JID(split[0])
                                theBody = split[1].strip()
                        except jid.InvalidFormat:
                                pass
                
                if to and to.user and to.host:
                        to = to.full()
                else:
                        to = self.globalChat + "@" + self.chatRoomServer
                        type = "groupchat"
                        theBody = text.strip()

                if len(text) == 0:
                        return
                
                message = domish.Element((None, 'message'))
                message['to'] = to
                message['id'] = "%i" % self.messageNum
                message['type'] = type
                self.messageNum += 1
                message.addElement('body', content=str(theBody))
                event = domish.Element(('jabber:x:event', 'x'))
                event.addElement("offline")
                event.addElement("delivered")
                event.addElement("composing")
                message.addChild(event)
		#if message['type'] == 'groupchat'
		#	nick = domish.Element(('http://jabber.org/protocol/nick',"nick"))
		#	nick.addChild("test")
	        #	message.addChild(nick)

                if(self.thexmlstream):
                    self.thexmlstream.send(message)
                else:
                    self.statusListener("System", "Not online")
                 
        def update(self):
                if time.time() > self.nextUpdateTime:
                        self.reactor.runUntilCurrent()
                        self.reactor.doIteration(0)
                        self.nextUpdateTime = time.time() + self.updateInterval

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
                xmlstream.addObserver('/*', self.debug)

		self.joinChatroom(self.teamChat)
		self.joinChatroom(self.globalChat)
		

	def joinChatroom(self, roomName):
		xmlstream = self.thexmlstream
		message = domish.Element((None, 'presence'))
		message['to'] = roomName + "@conference.cradle.dyndns.org/" + self.nickName
		message.addElement("priority",content="5")
		c = domish.Element(("http://jabber.org/protocol/caps","c"))
		c['ext'] = 'cs ep-notify'
		x = domish.Element(("http://jabber.org/protocol/muc#user","x"))
		message.addChild(c)
		message.addChild(x)

                if(self.thexmlstream):
                    self.thexmlstream.send(message)
                else:
                    self.statusListener("System", "Not online")

	def debug(self, eq):
		pass
		#print eq.toXml()

        def gotIq(self, el):
		#TODO: Process and respond to IQ's (eg version number)
		#print eq.toXml()
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
                
                #self.statusListener(str(jid.JID(el.attributes['from']).userhost()), str('is %s' % status))
                        
                try:
                        t = el.attributes['type']
                        if t == 'subscribe':
                                # Grant every subscription request
                                self.thexmlstream.send(domish.Element(('jabber:client', 'presence'), attribs={
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
		print xmlstream.toXml()
                self.reactor.stop()

        def connectedEvent(self, xmlstream):
                self.statusListener("System", 'Connected')

        def disconnectedEvent(self, xmlstream):
                self.statusListener("System", 'Disconnected')

        def registerfailedEvent(self, xmlstream):
                self.statusListener("System", 'Registration failed')
                self.reactor.stop()

        def statusListener(self, name, message):
                #print "%s: %s" % (name, message)
                self.remoteStatusListener(str(name), str(message))

        def registerMessageListener(self, method):
                self.remoteStatusListener = method

	def stop(self):
		self.reactor.stop()
                self.statusListener("System", 'Shutting down')

        def setNickName(self, nick):
                self.nickName = nick
                self.reactor.connectTCP(self.server, 5222, self.factory)
                self.reactor.startRunning()

def aMethod(a,b):
        print a,"=>",b

if __name__ == "__main__":
	user = raw_input("Login (user@host.com):")
	u = jid.JID(user + "/AssaultVector")
	password = raw_input("Password:")
        n = NetCode(u.user, u.host, u.resource, password, 'av-cradle.dyndns.org-10001')
	n.setNickName(u.user)
        n.registerMessageListener(aMethod)
	i = ""
	while i != "exit":
		n.update()
		time.sleep(0.1)
		i = raw_input(":")
		cmd = i.split(" ",1)
		if len(cmd) > 0:
			if cmd[0] == "send" and len(cmd) > 1:
				n.sendMessage(cmd[1])
			if cmd[0] == "run":
				n.reactor.run()

	print "Shutting Down"			
	n.stop()
	print "Cleaning Up"
	del n.reactor
	print "More Cleaning Up"
	del n
	print "Cleaned Up"
	import os
	os._exit(1)
