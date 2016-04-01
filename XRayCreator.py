# XRayCreator.py

from time import sleep
from pywinauto import *
from book.mobibook import MobiBook

book = MobiBook("test\TFE.mobi")
book.GetASIN()
book.UpdateASIN()
book.GetShelfariInfo()
app = Application.start("C:\Users\szarroug3\Documents\X-Ray Builder GUI\X-Ray Builder GUI.exe")

mainWindow = app['X-Ray Builder GUI']
aliasesWindow = app['Aliases']
chaptersWindow = app['Chapters']

mainWindow['Edit1'].TypeKeys(book.bookLocation)
mainWindow['Edit2'].TypeKeys(book.shelfariURL)
mainWindow['Button6'].Click()	#make sure Source is Shelfari
mainWindow['Button11'].Click()	#create xray button

#wait for aliases window
while not aliasesWindow.Exists():
	sleep(.5)
aliasesWindow['No'].Click()
#wait for chapters window
while not chaptersWindow.Exists():
	sleep(.5)
chaptersWindow['No'].Click()
app.WaitCPUUsageLower(timeout=30)
app.kill_()