# MobiBook.py

import os
import urllib
import subprocess
import json as m_json
from shutil import rmtree
from mobi.mobi import Mobi

class MobiBook(object):
    def __init__(self, filename):
        self.bookLocation = filename

    # def __del__(self):
    #     if os.path.exists(self.tempDir):
    #         rmtree(self.tempDir, ignore_errors=True)

    @property
    def bookLocation(self):
        return self._bookLocation

    @bookLocation.setter
    def bookLocation(self, filename):
        if type(filename) == str:
            self._bookLocation = os.path.abspath(filename)
            self._bookName = os.path.splitext(os.path.basename(self.bookLocation))[0]
            self._xrayLocation = os.path.join(os.path.dirname(self.bookLocation), self.bookName + ".sdr")
            self._tempDir = os.path.join(os.getcwd(), "temp", self.bookName)
            self._bookConfig = self.GetBookConfig()
        else:
            raise TypeError("Expected string, got " + str(type(filename)))

    @property
    def bookName(self):
        return self._bookName

    @property
    def xrayLocation(self):
        return self._xrayLocation

    @property
    def tempDir(self):
        return self._tempDir

    @property
    def bookConfig(self):
        return self._bookConfig

    @property
    def htmlBook(self):
        return self._htmlBook

    @property
    def ASIN(self):
        return self._ASIN
    
    
    def GetBookConfig(self):
        book = Mobi(self.bookLocation)
        book.parse()
        return book.config

    def UnpackBook(self):
        if not os.path.exists(self.tempDir):
            os.makedirs(self.tempDir)
        subprocess.Popen(['python',
            os.path.join(os.path.dirname(__file__), 'KindleUnpack', 'kindleunpack.py'),
            self.bookLocation,
            self.tempDir,
            '-r'], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        #find HTML book
        for root, dirs, files in os.walk(self.tempDir):
            if 'book.html' in files:
                self._htmlBook = os.path.join(root, 'book.html')

    # Get ASIN from Amazon
    def getASIN(self):
        self._ASIN = -1
        query = urllib.urlencode ( { 'q' : "amazon kindle \"ebook\" " + self.bookName } )
        response = urllib.urlopen ( 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&' + query).read()
        json = m_json.loads ( response )
        results = json [ 'responseData' ] [ 'results' ]
        for result in results:
            title = result['title']
            url = result['url']
            if "amazon" in url:
                if "/dp/" in url:
                    index = url.find("/dp/")
                    ASIN = url[index + 4 : index + 14]
                    print "Found book on amazon..."
                    print "ASIN: " + ASIN
                    self._ASIN = ASIN
                    return
                else:
                    for i in range(10):
                        amazon_page = urllib.urlopen(url)
                        page_source = amazon_page.read()
                        index = page_source.find("ASIN.0")
                        if index > 0:
                            ASIN = page_source[index + 15 : index + 25]
                            print "Found book on amazon..."
                            print "ASIN: " + ASIN
                            self._ASIN = ASIN
                            return

    # Update ASIN in book using mobi2mobi
    def updateASIN(self):
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