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
from time import sleep
from pywinauto import *

def UpdateAll():
    for book in kindleBooks:
        MarkForUpdate(book)
        if book.xrayExists:
            for xrayFile in glob(os.path.join(book.xrayLocation, '*.asc')):
                os.remove(xrayFile)

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
                if book.xrayExists:
                    for xrayFile in glob(os.path.join(book.xrayLocation, '*.asc')):
                        os.remove(xrayFile)
        elif pattern.match(bookID):
            bookRange = bookID.split('-')
            for bookNum in xrange(int(bookRange[0]), int(bookRange[1])+1):
                book = kindleBooks.books[int(bookNum) - 1]
                MarkForUpdate(book)
                if book.xrayExists:
                    for xrayFile in glob(os.path.join(book.xrayLocation, '*.asc')):
                        os.remove(xrayFile)
        else:
            print "Skipping book number %s as it is not in the list." % bookID

def New():
    for book in kindleBooks:
         if not book.xrayExists:
            MarkForUpdate(book)

def MarkForUpdate(book):    
    book.update = True

def CreateXRayFile(book):
    print '\tCreating X-Ray file'
    xrayButton.Click()  #click create xray button

    #wait for aliases window
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    aliasesWindow.Wait('exists', timeout=30)
    aliasesNoButton.Click()

    #wait for chapters window
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    chaptersWindow.Wait('exists', timeout=5)
    chaptersNoButton.Click()

    #wait for xray creation to be done
    app.WaitCPUUsageLower(threshold=.5, timeout=300)

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
    booksUpdated = []
    booksSkipped = []

    #open X-Ray Builder GUI
    app = Application().start(os.path.join('X-Ray Builder GUI','X-Ray Builder GUI.exe'))
    mainWindow = app['X-Ray Builder GUI']
    aliasesWindow = app['Aliases']
    chaptersWindow = app['Chapters']
    settingsWindow = app['Settings']

    #get buttons
    buttons = [button for button in mainWindow._ctrl_identifiers() if type(button) is controls.win32_controls.ButtonWrapper]
    buttons.sort(key=lambda x:x.Rectangle().left)
    xrayButton = buttons[6]
    sheflariURLButton = buttons[2]
    settingsButton = buttons[10]
    settingsSaveButton = settingsWindow['SaveButton']
    shelfariButton = mainWindow['ShelfariButton']
    aliasesNoButton = aliasesWindow['No']
    chaptersNoButton = chaptersWindow['No']

    #get text boxes
    textBoxes = [box for box in mainWindow._ctrl_identifiers() if type(box) is controls.win32_controls.EditWrapper]
    textBoxes.sort(key=lambda x:x.Rectangle().top)
    bookTextBox = textBoxes[0]
    shelfariURLTextBox = textBoxes[1]
    outputTextBox = textBoxes[2]

    #minimize window
    #mainWindow.Minimize()

    #Get output directory
    settingsButton.Click()
    settingsWindow.Wait('exists', timeout=60)
    outputDir = settingsWindow['Output Directory:Edit'].Texts()[0]
    settingsSaveButton.Click()
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    shelfariButton.Click()   #make sure Source is Shelfari
    if os.path.exists(outputDir): rmtree(outputDir)
    os.mkdir(outputDir)

    #update books
    for book in booksToUpdate:
        try:
            print book.bookNameAndAuthor
            while not bookTextBox.IsEnabled():
                sleep(1)
            bookTextBox.SetEditText(book.bookLocation)
            print '\tUpdating ASIN and getting shelfari URL'
            book.GetShelfariURL()
            shelfariURLTextBox.SetEditText(book.shelfariURL)
            CreateXRayFile(book)
            booksUpdated.append(book)
        except CouldNotFindShelfariURL:
            try:
                print '\tMaking X-Ray Builder GUI get shelfari URL'
                sheflariURLButton.Click()
                #wait for it to finish getting url
                app.WaitCPUUsageLower(threshold=.5, timeout=300)
                CreateXRayFile(book)
                booksUpdated.append(book)
            except Exception, e:
                print '\t1 - %s' % repr(e)
                booksSkipped.append((book, e))
        except Exception, e:
            print '\t2 - %s' % repr(e)
            booksSkipped.append((book, e))

    #close X-Ray Builder GUI
    app.kill_()

    #move x-ray files to their respective locations
    xrayFiles = []
    for dirName, subDirList, fileList in os.walk(outputDir):
        for file in glob(os.path.join(dirName,'*.asc')):
            print file
            xrayFiles.append(file)
    if len(xrayFiles)> 0:
        print 'Moving X-Ray Files to their directories'
    for xrayFile in xrayFiles:
        xrayLoc = kindleBooks.GetBookByASIN(os.path.basename(xrayFile).split('.')[2]).xrayLocation
        if xrayLoc and os.path.exists(xrayLoc):
            move(xrayFile, xrayLoc)

    if len(booksUpdated) > 0:
        print 'Books Updated: '
    for book in booksUpdated:
        print '\t%s' % book.bookNameAndAuthor
    print
    if len(booksSkipped) > 0:
        print 'Books Skipped: '
    for book in booksSkipped:
        print '%s skipped because %s' % (book[0].bookNameAndAuthor, book[1])

    #clean up
    #delete dmp, ext, log,  out
    print "Cleaning up..."
    if os.path.exists(outputDir): rmtree(outputDir)
    if os.path.exists('dmp'): rmtree('dmp')
    if os.path.exists('ext'): rmtree('ext')
    if os.path.exists('log'): rmtree('log')
    if os.path.exists('.google-cookie'): os.remove('.google-cookie')
    if os.path.exists(os.path.join('X-Ray Builder GUI', 'log')): rmtree(os.path.join('X-Ray Builder GUI', 'log'))
    if os.path.exists(os.path.join('X-Ray Builder GUI', 'out')): rmtree(os.path.join('X-Ray Builder GUI', 'out'))
else:
    print "No books to update."


print "Done!"