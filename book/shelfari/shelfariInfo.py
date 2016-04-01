# shelfariInfo.py

from urllib import urlopen
from bs4 import BeautifulSoup

class ShelfariInfo(object):
    def __init__(self, url):
        self.url = url
        self.ImportData()

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url

    @property
    def spoilers(self):
        return self._spoilers
    
    @property
    def pageSource(self):
        return self._pageSource

    @property
    def characters(self):
        return self._characters

    @characters.setter
    def characters(self, value):
        self._characters = value

    @property
    def terms(self):
        return self._terms

    @terms.setter
    def terms(self, value):
        self._terms = value  

    @property
    def quotes(self):
        return self._quotes

    @quotes.setter
    def quotes(self, value):
        self._quotes = value  

    def ImportData(self):
        self.ReadPage()
        self.GetCharacters()
        self.GetTerms()
        self.GetQuotes()

    def ReadPage(self):
        response = urlopen(self.url).read()
        self._pageSource = BeautifulSoup(response, "html.parser")

    def GetCharacters(self):
        charModule = self.pageSource.find('div', {'id': 'WikiModule_Characters'})
        chars = charModule.find_all('li')
        self.characters = {char.find('span').getText(): char.getText() for char in chars}

    def GetTerms(self):
        settingsModule = self.pageSource.find('div', {'id': 'WikiModule_Settings'})
        terms = settingsModule.find_all('li')
        self.terms = {term.find('span').getText(): term.getText() for term in terms}

        glossaryModule = self.pageSource.find('div', {'id': 'WikiModule_Glossary'})
        terms = glossaryModule.find_all('li')
        self.terms.update({term.find('span').getText(): term.getText() for term in terms})

    def GetQuotes(self):
        quotesModule = self.pageSource.find('div', {'id': 'WikiModule_Quotations'})
        quotes = quotesModule.find_all('li')
        self.quotes = [quote.getText() for quote in quotes]