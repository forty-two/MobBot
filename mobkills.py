#! /usr/bin/python

import datetime
import re

# Assuming correct input

class MobKills():

    def __init__(self):
        self.kills = []

    def addNewKill(self, logLine):
        self.kills.append(self.createKillRecord(logLine))

    def createKillRecord(self, loggedKill):
        splitInput = loggedKill.split(' ')
        killData = splitInput[5].split('|')

        newKill = {'player' : killData[0].lower(),
                   'mobType': killData[1].lower(),
                   'coords' : {'x': int(killData[3].split('.')[0]),
                               'y': int(killData[4].split('.')[0]),
                               'z': int(killData[5].split('.')[0]),
                               },
                   'time'   : datetime.datetime.strptime(' '.join((splitInput[0], splitInput[1])), '%Y-%m-%d %H:%M:%S'),
                   'world'  : killData[2],
                   'chunk'  : tuple([int(num) for num in splitInput[6].strip('C[]').split(',')])
                   }

        return newKill

    def findMatches(self, *searchOptions):
        print searchOptions

        searchFunctions = {'time'  : self.timeSearch,
                           'player': self.playerSearch,
                           'mob'   : self.mobSearch,
                           'area'  : self.areaSearch,
                           'chunks': self.chunkSearch,
                           }
        searchTokens = [token.split('=') for token in searchOptions]

        matches = []

        for token in searchTokens:
            if token[0] in searchFunctions:
                matches.append(searchFunctions[token[0]](token[1]))

        if matches:
            completeMatches = matches[0]

            for matchList in matches:
                completeMatches = [kill for kill in matchList if kill in matchList]

            return completeMatches

        else:
            return []

    # Search functions

    def areaSearch(self, searchString):
        # example x-z coord input: '120,-50,15'
        # example x-y-z coord input: '120,64,-50,15'
        searchInput = [int(value) for value in searchString.split(',')]
        searchRadius = int(searchInput[-1])
        matchingKills = []

        if len(searchInput[:-1]) == 3:
            coords = {'x' : searchInput[0],
                      'y' : searchInput[1],
                      'z' : searchInput[2],
                      }
        elif len(searchInput[:-1]) == 2:
            coords = {'x' : searchInput[0],
                      'z' : searchInput[1],
                      }

        for kill in self.kills:
            match = True
            for direction in coords:
                if abs(coords[direction] - kill['coords'][direction]) > searchRadius:
                    match = False

            if match:
                matchingKills.append(kill)

        return matchingKills

    def chunkSearch(self, searchString):
        # example input: "(70,74),(50,30)"
        chunkList = re.findall(r'\((\d+|-\d+)\,(\d+|\-\d+)\)', searchString)
        chunkList = [(int(x), int(y)) for x,y in chunkList]
        matchingKills = [kill for kill in self.kills if kill['chunk'] in chunkList]
        return matchingKills

    def mobSearch(self, searchString):
        # example input: 'cow'
        # example multiple input: 'cow,sheep,pig'
        mobsRequested = [mob.lower() for mob in searchString.split(',')]
        return [kill for kill in self.kills if kill['mobType'] in mobsRequested]

    def playerSearch(self, searchString):
        # example input: 'Notch'
        # example multiple input: 'Notch,Dinnerbone'
        playerNames = [name.lower() for name in searchString.split(',')]
        matchingKills = [kill for kill in self.kills if kill['player'] in playerNames]
        return matchingKills

    def timeSearch(self, searchString):
        # example input: '<2012,11,10,8,45,11'
        timeArguments = [int(x) for x in searchString[1:].split(',')]
        timeRequested = datetime.datetime(*timeArguments)
        if searchString[0] == "<":
            return [kill for kill in self.kills if kill['time'] < timeRequested]
        elif searchString[0] == ">":
            return [kill for kill in self.kills if kill['time'] > timeRequested]

    def prettyPrint(self, kill):
        outputString = "{} - Player {} killed a {} at location {} in chunk {} of world {}"
        timeString = datetime.datetime.strftime(kill['time'], '%Y-%m-%d %H:%M:%S')
        locationString = ', '.join([str(kill['coords']['x']), str(kill['coords']['y']), str(kill['coords']['z'])])
        return outputString.format(timeString, kill['player'], kill['mobType'], locationString, kill['chunk'], kill['world'])

class FileWatcher():
    def __init__(self, filename):
        self.file = open(filename)
        self.killRegex = re.compile(r"\d+\-\d+\-\d+ \d+\:\d+\:\d+ \[INFO\] \[KitchenSink\] \[MobKill\] [A-Za-z0-9_]+\|\w+\|\w+\|((\d+|\-\d+)\.\d+\|){3} C\[(\-\d+|\d+)\,(\-\d+|\d+)\]")
        
    def nextLines(self):
        line = self.file.readline().strip()
        while line:
            if self.killRegex.match(line):
                yield line
            line = self.file.readline().strip()


