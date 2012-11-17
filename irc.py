#! /usr/bin/python

import time

# non stdlib internal
import permissions

# non stdlib external
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task, threads

import mobkills
import pastebins


class IRCBot(irc.IRCClient):
    
    def __init__(self, nickname):
        print "In ircbot"
        self.nickname = nickname
        self.realname = "MobBot 0.1"
        self.versionName = "MobBot - mob kill search bot by forty_two"
        self.versionNum = 0.1
        self.lineRate = 1
        self.checkLoop = task.LoopingCall(self.checkLogFile)
        print "Created checkloop"
        self.authChecker = permissions.AuthHandler("MobBot_permissions.json")
        self.commandPermissions = {'admin': ['*']}

    def checkLogFile(self):
        deferredCheck = threads.deferToThread(self.factory.fileWatcher.nextLines)
        deferredCheck.addCallbacks(self.checkLogFileCallback, self.errorCallback)

    def checkLogFileCallback(self, logLines):
        print "Log file checked at {}".format(time.ctime())
        for line in logLines:
            self.factory.mobKills.addNewKill(line)
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        

    def connectionLost(self, reason):
        self.checkLoop.stop()
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)
        print("Succesfully signed into IRC server")
        

    def joined(self, channel):
        print("Succesfully joined channel %s" % channel)
        self.checkLoop.start(120)

    def isAuthorised(self, command, username, hostmask):
        userPermissions = self.authChecker.get_user_permissions(username, hostmask)
        print username
        print hostmask
        print userPermissions
        if userPermissions:
            for group in userPermissions:
                if command in self.commandPermissions.get(group, []):
                    return True
                if "*" in self.commandPermissions.get(group, []):
                    return True
        return False

    def handleCommands(self, user, hostmask, command, options):
        mobHandlers =   {'findkills'      : self.factory.mobKills.findMatches,
                         'fk'             : self.factory.mobKills.findMatches,
                        }
        localHandlers = {'addhostmask'   : self.addUserHostmask,
                         'adduser'       : self.addUser,
                         'addusergroup'  : self.addUserGroup,
                         'mobhelp'      : self.helpMessage,
                         'permshelp'     : self.permsHelpMessage,
                         'removehostmask': self.removeUserHostmask,
                         'removegroup'   : self.removePermissionGroup,
                         'removeuser'    : self.removeUser,
                        }

        if self.isAuthorised(command, user, hostmask):
            if command in mobHandlers:
                mobRequest = threads.deferToThread(mobHandlers[command], *options)
                mobRequest.addCallbacks(self.commandsCallback, self.errorCallback)
            elif command in localHandlers:
                self.commandsCallback(localHandlers[command](*options))
            # activate following if desired, but will respond to anything that appears to be a command (e.g. other bots commands)
            # else:
            #     self.msg(self.factory.channel, "Command {} not known".format(command))

    def errorCallback(self, error):
        self.msg(self.factory.channel, "An error occurred whilst processing the request: {}".format(error.getErrorMessage()))
        error.printTraceback()

    def commandsCallback(self, response):
        if isinstance(response, list):
            if response:
                message = [self.factory.mobKills.prettyPrint(kill).encode('UTF-8', 'ignore') for kill in response]
                if len(message) > 5:
                    pastebinRequest = threads.deferToThread(self.makePastebinResponse, message)
                    pastebinRequest.addCallbacks(self.commandsCallback, self.errorCallback)
                else:
                    for line in message:
                        self.msg(self.factory.channel, line)
            else:
                self.msg(self.factory.channel, "No matching kills found")
        else:
            if response:
                response = response.encode('UTF-8', 'ignore')
                print('Command callback activated for response {}'.format(response))
                self.msg(self.factory.channel, response)

    def makePastebinResponse(self, linesList):
        message = '\n'.join(linesList)
        pastebinResponse = self.factory.pastebin.paste(message)
        if not 'exception' in pastebinResponse:
            return "Too many results to reasonably show in channel, go to http://paste.thezomg.com/{}/{}".format(pastebinResponse['result']['id'],
                pastebinResponse['result']['hash'])
        else:
            return "Too many results to reasonably show in channel, but putting them on a pastebin failed"

    def addUserHostmask(self, *args):
        if len(args) == 2:
            self.authChecker.add_user_hostmask(args[0], args[1])
            return "Added hostmask %s to user %s" % (args[1], args[0])
        else:
            return "Incorrect usage, use .addhostmask username hostmask"
        
    def addUser(self, *args):
        if len(args) == 3:
            self.authChecker.add_user(args[0], args[1], args[2])
            return "Created user %s" % (args[0])
        else:
            return "Incorrect usage, use .adduser username hostmask group"
            
    def addUserGroup(self, *args):
        if len(args) == 2:
            self.authChecker.add_user_group(args[0], args[1])
            return "Added user %s to group %s" % (args[0], args[1])
        else:
            return "Incorrect usage, use .addusergroup username group"

            
    def helpMessage(self, *args):
        return "Commands avaliable: .permshelp, .findkills [options] (example: \".findkills time=>2012,11,17 player=forty_two,Notch area=42,64,-42,50 mob=COW,SHEEP chunk=(42,-42)\")"
        
    def permsHelpMessage(self, *args):
        return "Commands availible: .adduser username hostname group, .addhostmask username hostmask, .removeuser username, .removehostmask username hostmask"
                             
        
    def removeUserHostmask(self, *args):
        if len(args) == 2:
            self.authChecker.remove_user_hostmask(args[0], args[1])
            return "Removed hostmask %s from user %s" % (args[1], args[0])
        else:
            return "Incorrect usage, use .removehostmask username hostmask"
            
    def removePermissionGroup(self, *args):
        if len(args) == 2:
            self.authChecker.remove_group(args[0], args[1])
            return "Removed permission group %s from user %s" % (args[1], args[0])
        else:
            return "Incorrect usage, use .removegroup username groupName"
    
    def removeUser(self, *args):
        if len(args) == 1:
            self.authChecker.remove_user(args[0])
            return "Removed user %s" % args[0]
        else:
            return "Incorrect usage, use .removeuser username"

    def privmsg(self, user, channel, msg):
        msg = msg.decode('UTF-8', 'ignore')
        userName = user.split('!', 1)[0]
        userHostmask = user.split('@', 1)[1]
        
        # Check to see if they're sending a private message
        if channel == self.nickname:
            msg = "Commands in the public channel only please"
            self.msg(userName, msg)
            return

        # Otherwise check to see if it is a command
        print msg
        if msg.startswith('.'):
            print "sending command"
            msg = msg.split(' ')
            command = msg[0].strip('.')
            if len(msg) > 1:
                options = msg[1:]
            else:
                options = []
            self.handleCommands(userName, userHostmask, command, options)

class MobBotFactory(protocol.ClientFactory):
    def __init__(self, nickname, channel, filename):
        print "in MobBot Factory"
        self.nickname = nickname
        self.channel = channel
        self.fileWatcher = mobkills.FileWatcher(filename)
        self.mobKills = mobkills.MobKills()
        self.pastebin = pastebins.StickyNotes()

        
    def buildProtocol(self, addr):
        p = IRCBot(self.nickname)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()    

