# MobiBook.py

import os
from glob import glob
from urllib import urlopen, urlencode
import subprocess
from google import search
from bs4 import BeautifulSoup
from mobi.mobi import Mobi

class MobiBook(object):
    def __init__(self, filename, bookID):
        self.bookLocation = filename
        self.bookID = bookID
        self.update = False
        self._ASIN = None
        self._shelfariURL = None

    def __str__(self):
        string = '%i. ' % self.bookID
        if self.author: string += '%s - %s' % (self.author, self.bookName)
        else: string = '%s' % self.bookFileName
        if self.update:
            string += "\n\tMarked for update"
        string +='\n\t%s' % self.bookLocation
        if not self.xrayExists: string += '\n\tNo',
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
            if os.path.exists(filename):
                self._bookLocation = os.path.abspath(filename)
                self._bookFileName = os.path.splitext(os.path.basename(self.bookLocation))[0]
                self._xrayLocation = os.path.join(os.path.dirname(self.bookLocation), self.bookFileName + ".sdr")
                self._xrayExists = glob(os.path.join(self.xrayLocation, '*.asc'))
            else:
                raise FileNotFoundError('File %s not found' % filename)
        else:
            raise TypeError('Expected string, got ' + str(type(filename)))

    @property
    def update(self):
        return self._update

    @update.setter
    def update(self, value):
        self._update = value
        
    @property
    def bookID(self):
        return self._bookID

    @bookID.setter
    def bookID(self, value):
        self._bookID = value
    
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
        if self._author:
            self._bookName = self.bookConfig['mobi']['Full Name']
        else:
            self._bookName = self.bookFileName
 
    # Get ASIN from Amazon
    def GetASIN(self):
        self._ASIN = -1
        query = 'amazon kindle \"ebook\" %s' % self.bookName
        if self.author: query += ' %s' % self.author
        for url in search(query, stop=5):
            if "amazon" in url:
                if "/dp/" in url:
                    index = url.find("/dp/")
                    ASIN = url[index + 4 : index + 14]
                    self._ASIN = ASIN
                    return
        raise CouldNotFindASIN('Could not find ASIN for %s' % self.bookFileName)

    # Update ASIN in book using mobi2mobi
    def UpdateASIN(self):
        #remove extra file if it exists
        if os.path.exists(self.bookLocation + '_NEW'):
            os.remove(self.bookLocation + '_NEW')

        #create new file with updated ASIN
        mobi2mobi_path = os.path.join(os.path.dirname(__file__), 'MobiPerl', 'mobi2mobi.exe')
        subprocess.Popen([mobi2mobi_path,
            self.bookLocation,
            '--outfile', self.bookLocation + '_NEW',
            '--exthtype', 'asin',
            '--exthdata', self.ASIN],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

        #remove old file, rename new file to old filename
        os.remove(self.bookLocation)
        os.rename(self.bookLocation + "_NEW", self.bookLocation)

    # Searches for shelfari url for book
    def GetShelfariURL(self, updateASIN=True):
        if updateASIN:
            self.GetASIN()
            self.UpdateASIN()
        response = urlopen ( 'http://www.shelfari.com/search/books?Keywords=' + self.ASIN ).read()
        page_source = BeautifulSoup(response, "html.parser")
        for link in page_source.find_all("a"):
            url = link.get('href')
            if "http://www.shelfari.com/books/" in url and url.count('/') == 5:
                shelfari_bookID = url[30:url[30:].find('/') + 30]
                if shelfari_bookID.isdigit():
                    self._shelfariURL = url
                    return
        raise CouldNotFindShelfariURL('Could not find Shelfari URL for %s.' % self.bookFileName)

class CouldNotFindASIN(Exception):
    pass
class CouldNotFindShelfariURL(Exception):
    pass