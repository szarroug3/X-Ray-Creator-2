# MobiBook.py

import os
import sys
from glob import glob
from urllib import urlencode
from urllib2 import urlopen
import subprocess
import json
import httplib
import re
from time import sleep
from bs4 import BeautifulSoup
from mobi.mobi import Mobi
from customexceptions import *

class MobiBook(object):
    amazonURLPat = re.compile(r'www\.amazon\.com\/.+\/dp\/([a-zA-Z0-9]+)')
    shelfariURLPat = re.compile(r'href="(.+/books/.+?)"')
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "User-Agent": "Mozilla/5.0"}

    def __init__(self, filename):
        self.bookLocation = filename
        self.update = False
        self._ASIN = None
        self._shelfariURL = None

    def __str__(self):
        string = self.bookNameAndAuthor
        if self.update:
            string += '\n\tMarked for update'
        string +='\n\t%s' % self.bookLocation
        if not self.xrayExists: string += str('\n\tNo')
        else: string += '\n\t'
        string += ' X-Ray found at %s' % self.xrayLocation
        if self.ASIN:
            string += '\n\tASIN: ' % self.ASIN
        if self.shelfariURL:
            string += '\n\tShelfari URL: %s' % self.shelfariURL
        return string

    @property
    def bookLocation(self):
        return self._bookLocation

    @bookLocation.setter
    def bookLocation(self, filename):
        if type(filename) == str:
            if filename[:-1] == '\n': filename = filename[:-1]
            if os.path.exists(filename):
                self._bookLocation = os.path.abspath(filename)
                self._bookFileName = os.path.splitext(os.path.basename(self.bookLocation))[0]
                self._xrayLocation = os.path.join(os.path.dirname(self.bookLocation), self.bookFileName + '.sdr')
                self._xrayExists = glob(os.path.join(self.xrayLocation, '*.asc'))
            else:
                raise FileNotFound('File %s not found' % filename)
        else:
            raise TypeError('Expected string, got ' + str(type(filename)))

    @property
    def update(self):
        return self._update

    @update.setter
    def update(self, value):
        self._update = value
    
    @property
    def xrayLocation(self):
        return self._xrayLocation

    @property
    def bookFileName(self):
        return self._bookFileName

    @property
    def xrayExists(self):
        return self._xrayExists

    @property
    def bookConfig(self):
        return self._bookConfig

    @property
    def author(self):
        return self._author
    
    @property
    def bookName(self):
        return self._bookName

    @property
    def bookNameAndAuthor(self):
        return self._bookNameAndAuthor
    
    @property
    def ASIN(self):
        return self._ASIN

    @property
    def shelfariURL(self):
        return self._shelfariURL

    def GetBookConfig(self):
        book = Mobi(self.bookLocation)
        book.parse()
        self._bookConfig = book.config
        self._author = self.bookConfig['exth']['records'][100]
        self._bookName = self.bookConfig['mobi']['Full Name']
        if self._author and self.bookName:
            if self.author[:-1] == '\n': self._author = self.author[:-1]
            if self.bookName[:-1] == '\n': self._bookName = self.bookName[:-1]
            self._bookNameAndAuthor = '%s - %s' % (self.author, self.bookName)
        else:
            self._bookNameAndAuthor = self.bookFileName

    def GetASIN(self, connection=None):
        self._ASIN = None
        if not connection:
            connection = httplib.HTTPConnection('www.amazon.com')
        query = urlencode ({'field-keywords': self.bookNameAndAuthor})
        connection.request('GET', '/s/ref=nb_sb_noss_2?url=node%3D154606011&' + query, None, self.headers)
        try:
            response = connection.getresponse().read()
        except httplib.BadStatusLine:
            connection.close()
            connection = httplib.HTTPConnection('www.amazon.com')
            connection.request('GET', '/s/ref=nb_sb_noss_2?url=node%3D154606011&' + query, None, self.headers)
            response = connection.getresponse().read()
        # check to make sure there are results
        if 'did not match any products' in response and not 'Did you mean:' in response:
            raise CouldNotFindASIN('Could not find ASIN for %s' % self.bookNameAndAuthor)
        urlsearch = self.amazonURLPat.search(response)
        if not urlsearch:
            raise CouldNotFindASIN('Could not find ASIN for %s' % self.bookNameAndAuthor)
        self._ASIN = urlsearch.group(1)
        return connection

    # Update ASIN in book using mobi2mobi
    def UpdateASIN(self):
        # remove extra file if it exists
        if os.path.exists(self.bookLocation + '_NEW'):
            os.remove(self.bookLocation + '_NEW')

        # create new file with updated ASIN
        with open(os.devnull, 'w') as fNull:
            mobi2mobi_path = os.path.join(os.path.dirname(__file__), 'MobiPerl', 'mobi2mobi.exe')
            subprocess.Popen([mobi2mobi_path,
                self.bookLocation,
                '--outfile', self.bookLocation + '_NEW',
                '--exthtype', 'asin',
                '--exthdata', self.ASIN],
                stdout=fNull, stderr=fNull).communicate()

        # wait to make sure OS knows file is created
        sleep(1)
        # remove old file, rename new file to old filename
        os.remove(self.bookLocation)
        os.rename(self.bookLocation + '_NEW', self.bookLocation)

    # Searches for shelfari url for book
    def GetShelfariURL(self, updateASIN=True, aConnection=None, sConnection=None,):
        if updateASIN:
            self.GetASIN(connection=aConnection)
            aConnection = self.UpdateASIN()
        if not sConnection:
            sConnection = httplib.HTTPConnection('www.shelfari.com')

        if self.ASIN:
            query = urlencode ({'Keywords': self.ASIN})
            sConnection.request('GET', '/search/books?' + query)
            try:
                response = sConnection.getresponse().read()
            except httplib.BadStatusLine:
                sConnection.close()
                sConnection = httplib.HTTPConnection('www.shelfari.com')
                sConnection.request('GET', '/search/books?' + query)
                response = sConnection.getresponse().read()
            
            # check to make sure there are results
            if 'did not return any results' in response:
                self._shelfariURL = None
                return [aConnection, sConnection]
            urlsearch = self.shelfariURLPat.search(response)
            if not urlsearch:
                self._shelfariURL = None
                return [aConnection, sConnection]
            self._shelfariURL = urlsearch.group(1)
            return [aConnection, sConnection]
        raise CouldNotFindASIN('ASIN not set for %s' % self.bookNameAndAuthor)