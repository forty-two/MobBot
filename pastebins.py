#! /usr/bin/python

import xmlrpclib
import urllib
import json

class LodgeIt():
    def __init__(self, API_ADDRESS = 'http://paste.pocoo.org/xmlrpc/'):
        self.server = xmlrpclib.ServerProxy(API_ADDRESS)

    def getDiff(self, old_id, new_id):
        try:
            return self.server.pastes.getDiff(old_id, new_id)
        except Exception as e:
            return {'exception': e}

    def getLanguages(self):
        try:
            return self.server.pastes.getLanguages()
        except Exception as e:
            return {'exception': e}
    def getLast(self):
        try:
            return self.server.pastes.getLast()
        except Exception as e:
           return {'exception': e}


    def getPaste(self, paste_id):
        try:
            return self.server.pastes.getPaste(paste_id)
        except Exception as e:
            return {'exception': e}

    def getRecent(self, amount = 5):
        try:
            return self.server.pastes.getRecent(amount)
        except Exception as e:
            return {'exception': e}

    def newPaste(self, text, language = 'text', parent_id = '', filename = '', mimetype = '', private = True):
        try:
            return self.server.pastes.newPaste(language, text, parent_id, filename, mimetype, private)
        except Exception as e:
            return {'exception': e}

    def styles(self):
        try:
            return self.server.styles.getStyles()
        except Exception as e:
            return {'exception': e}

    def getStyleSheet(self, style_name):
        try:
            return self.server.styles.getStyleSheet(style_name)
        except Exception as e:
            return {'exception': e}


class StickyNotes():
    def __init__(self, API_URL = "http://paste.thezomg.com", username = "MobLog bot"):
        self.API_URL = API_URL
        self.username = username

    def paste(self, data):
        try:
            request = urllib.urlencode({"paste_user"   : self.username,
                                        "paste_data"   : data,
                                        "paste_lang"   : "text",
                                        "api_submit"   : "true",
                                        "mode"         : "json",
                                        "paste_private": "true"
                                        })
            response = urllib.urlopen(self.API_URL, request)
            return json.load(response)
        except Exception as e:
            return {'exception': e}