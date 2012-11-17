#! /usr/bin/python

import json
import sys

# non stdlib internals
import irc

from twisted.internet import reactor

def loadConfig():
    try:
        configFile = open('config.json')
        config = json.load(configFile)
        # data must not be unicode, twisted throws a fit if it is
        for key in config:
            config[key] = config[key].encode('ascii', 'ignore')
        return config
    except:
        return None
    
def writeDefaultConfig():
    defaultConfig = {'logFilename'  : 'server.log',
                     'IRC_server'   : 'irc.gamesurge.net',
                     'IRC_nickname' : 'MobBot',
                     'IRC_channel'  : 'MobBot_test_channel',
                     }
    configFile = open('config.json', 'w')
    configFile.write(json.dumps(defaultConfig, indent = 4, encoding = 'ASCII'))

def main():
    config = loadConfig()
    if not config:
        writeDefaultConfig()
        print("----------")
        print("Config file not found, default file generated")
        print("Program now exiting")
        print("----------")

        sys.exit()
     
    f = irc.MobBotFactory(config['IRC_nickname'], config['IRC_channel'], config['logFilename'])
    reactor.connectTCP(config['IRC_server'], 6667, f)
    reactor.run()

if __name__ == '__main__':
    main()
