# XRayCreator.py

import os
import sys
import argparse
import re
from kindle.books import Books
from kindle.customexceptions import *
from time import sleep
from glob import glob
from shutil import move, rmtree
from pywinauto import *

#--------------------------------------------------------------------------------------------------------------------------END OF IMPORTS--------------------------------------------------------------------------------------------------------------------------#

def UpdateAll():
    for book in kindleBooks:
        MarkForUpdate(book)

def Update():
    kindleBooks.PrintListOfBooks()
    books = raw_input("Please enter book number(s) of the book(s) you'd like to update in a comma separated list: ")
    books = books.replace(" ", "")
    books = books.split(',')
    pattern = re.compile("([0-9]+[-][0-9]+)")
    for bookID in books:
        if bookID.isdigit():
            if  int(bookID) <= len(kindleBooks):
                book = kindleBooks.books[int(bookID) - 1]
                MarkForUpdate(book)
        elif pattern.match(bookID):
            bookRange = bookID.split('-')
            for bookNum in xrange(int(bookRange[0]), int(bookRange[1])+1):
                book = kindleBooks.books[int(bookNum) - 1]
                MarkForUpdate(book)
        else:
            print "Skipping book number %s as it is not in the list." % bookID

def New():
    for book in kindleBooks:
         if not book.xrayExists:
            MarkForUpdate(book, checkForXRay=False)

def MarkForUpdate(book, checkForXRay=True):    
    book.update = True
    if checkForXRay and book.xrayExists:
        for xrayFile in glob(os.path.join(book.xrayLocation, '*.asc')):
            os.remove(xrayFile)

def SetupXRayBuilder():
	booksUpdated = []
    global booksSkipped = []

    #open X-Ray Builder GUI
    global app = Application().start(os.path.join('X-Ray Builder GUI','X-Ray Builder GUI.exe'))
    global mainWindow = app['X-Ray Builder GUI']
    global aliasesWindow = app['Aliases']
    global chaptersWindow = app['Chapters']
    global settingsWindow = app['Settings']

    #get buttons
    buttons = [button for button in mainWindow._ctrl_identifiers() if type(button) is controls.win32_controls.ButtonWrapper]
    buttons.sort(key=lambda x:x.Rectangle().left)
    global xrayButton = buttons[6]
    global sheflariURLButton = buttons[2]
    settingsButton = buttons[10]
    settingsSaveButton = settingsWindow['SaveButton']
    global shelfariButton = mainWindow['ShelfariButton']
    global aliasesNoButton = aliasesWindow['No']
    global chaptersNoButton = chaptersWindow['No']

    #get text boxes
    textBoxes = [box for box in mainWindow._ctrl_identifiers() if type(box) is controls.win32_controls.EditWrapper]
    textBoxes.sort(key=lambda x:x.Rectangle().top)
    global bookTextBox = textBoxes[0]
    global shelfariURLTextBox = textBoxes[1]
    global outputTextBox = textBoxes[2]

    #minimize window
    #mainWindow.Minimize()

    #Get output directory
    ClickButton(settinsButton)
    settingsWindow.Wait('exists', timeout=60)
    global outputDir = settingsWindow['Output Directory:Edit'].Texts()[0]
    ClickButton(settingsSaveButton)
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
	
	#make sure Source is Shelfari
    ClickButton(shelfariButton)

    #make sure output directory is empty
    if os.path.exists(outputDir): rmtree(outputDir)
    os.mkdir(outputDir)

def ClickButton(button):
	while not button.IsEnabled():
        sleep(1)
    button.Click()

def EditTextBox(textBox, text):
	while not textBox.IsEnabled():
        sleep(1)
    textBox.SetEditText(text)

def CreateXRayFile(book):
    print '\tCreating X-Ray file'
    ClickButton(xrayButton) #click create xray button

    #wait for aliases window and respond
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    aliasesWindow.Wait('exists', timeout=30)
	ClickButton(aliasesNoButton)

    #wait for chapters window and respond
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    chaptersWindow.Wait('exists', timeout=5)
    ClickButton(chaptersNoButton)

    #wait for xray creation to be done
    app.WaitCPUUsageLower(threshold=.5, timeout=300)

def MoveXRayFiles(booksUpdate)
	#move x-ray files to their respective locations
    xrayFiles = []
    for dirName, subDirList, fileList in os.walk(outputDir):
        for file in glob(os.path.join(dirName,'*.asc')):
            xrayFiles.append(file)

    if len(xrayFiles)> 0:
        print 'Moving X-Ray Files to their directories'

    for xrayFile in xrayFiles:
        xrayLoc = kindleBooks.GetBookByASIN(os.path.basename(xrayFile).split('.')[2]).xrayLocation
        if xrayLoc and os.path.exists(xrayLoc):
            move(xrayFile, xrayLoc)


#--------------------------------------------------------------------------------------------------------------------------END OF FUNCTIONS--------------------------------------------------------------------------------------------------------------------------#

#main
parser = argparse.ArgumentParser(description='Create and update kindle X-Ray files')
parser.add_argument('-u', '--update', action='store_true', help='Will give you a list of all books on kindle and asks you to return a comma separated list of book numbers for the books you want to update; Note: You can use a range in the list')
parser.add_argument('-ua', '--updateall', action='store_true',  help='Deletes all X-Ray files and recreates them. Will also create X-Ray files for books that don\'t already have one')
parser.add_argument('-n', '--new', action='store_true', help='Creates X-Ray files for books that don\'t already have one')
args = parser.parse_args()

#check to make sure only one argument is chosen
numOfArgs = 0
if args.updateall: numOfArgs += 1
if args.update: numOfArgs += 1
if args.new: numOfArgs += 1
if numOfArgs > 1:
    raise Exception('Please choose only one argument.')
if numOfArgs < 1:
    parser.print_help()
    sys.exit()

kindleBooks = Books()
if args.updateall:
    UpdateAll()
elif args.update:
    Update()
elif args.new:
    New()

booksToUpdate = kindleBooks.GetBooksToUpdate()
if len(booksToUpdate) > 0:
	#update books
    for book in booksToUpdate:
        try:
            #insert book location
            print book.bookNameAndAuthor
            EditTextBox(bookTextBox, book.bookLocation)

            #get and update shelfari url
            print '\tUpdating ASIN and getting shelfari URL'
            book.GetShelfariURL()
            EditTextBox(shelfariURLTextBox, book.shelfariURL)

        	#create xray file and add to updated list
            CreateXRayFile(book)
            print '\tCreated X-Ray File'
            booksUpdated.append(book)
        except CouldNotFindShelfariURL:
            try:
                print '\tMaking X-Ray Builder GUI get shelfari URL'
                #clear shelfari url, click shelfari button and wait for it to finish
            	EditTextBox(bookTextBox, '')
                ClickButton(sheflariURLButton)
                app.WaitCPUUsageLower(threshold=.5, timeout=300)

                #check if shelfari url is updated
                if shelfariURLTextBox.Texts()[0]:
                    CreateXRayFile(book)
                    print '\tCreated X-Ray File'
                    booksUpdated.append(book)
                else:
                	print '\tSkipping book because could not find shelfari url'
                    booksSkipped.append((book, 'could not find shelfari url.'))
            except Exception, e:
                print '\tSkipping book because %s' % e
                booksSkipped.append((book, e))
        except Exception, e:
            print '\tSkipping book because %s' % e
            booksSkipped.append((book, e))

    #close X-Ray Builder GUI
    app.kill_()

    MoveXRayFiles(booksUpdated)

    #print updated books
 	print
    if len(booksUpdated) > 0:
        print 'Books Updated: '
    for book in booksUpdated:
        print '\t%s' % book.bookNameAndAuthor

    #print skipped books
    print
    if len(booksSkipped) > 0:
        print 'Books Skipped: '
    for book in booksSkipped:
        if book[1]:
            print '%s skipped because %s' % (book[0].bookNameAndAuthor, book[1])
        else:
            print '%s skipped because %s' % (book[0].bookNameAndAuthor, repr(book[1]))
else:
    print "No books to update."

print "Done!"