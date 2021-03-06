# XRayCreator.py

import os
import sys
import argparse
import re
import httplib
from kindle.books import Books
from kindle.customexceptions import *
from time import sleep
from glob import glob
from shutil import move, rmtree
from pywinauto import *

#--------------------------------------------------------------------------------------------------------------------------END OF IMPORTS--------------------------------------------------------------------------------------------------------------------------#
MAX_LINE_LENGTH = 60

def UpdateAll():
    for book in kindleBooks:
        MarkForUpdate(book)

def Update():
    kindleBooks.PrintListOfBooks()
    books = raw_input('Please enter book number(s) of the book(s) you\'d like to update in a comma separated list: ')
    books = books.replace(' ', '')
    books = books.split(',')
    pattern = re.compile('([0-9]+[-][0-9]+)')
    for bookID in books:
        if bookID.isdigit():
            if  int(bookID) <= len(kindleBooks):
                book = kindleBooks.books[int(bookID) - 1]
                MarkForUpdate(book)
        elif pattern.match(bookID):
            bookRange = bookID.split('-')
            rangeA = int(bookRange[0])
            rangeB = int(bookRange[1])
            if rangeA > rangeB:
                print 'Numbers are reversed. Will start with %s and end with %s' % (rangeB, rangeA)
                temp = rangeA
                rangeA = rangeB
                rangeB = temp
            if rangeA < 1:
                print '%i is less than 1. Will start with 1.' % rangeA
                rangeA = 1
            if rangeA > len(kindleBooks):
                print '%i is more than %s. Will start with %s.' % (rangeA, len(kindleBooks), len(kindleBooks))
                rangeA = len(kindleBooks)
            if rangeB > len(kindleBooks):
                print '%i is more than %s. Will end with %s.' % (rangeB, len(kindleBooks), len(kindleBooks))
                rangeB = len(kindleBooks)
            if rangeB < 1:
                print '%i is less than 1. Will end with 1.' % rangeB
                rangeB = 1
            for bookNum in xrange(rangeA, rangeB+1):
                book = kindleBooks.books[int(bookNum) - 1]
                MarkForUpdate(book)
        else:
            print 'Skipping book number %s as it is not in the list.' % bookID

def New():
    for book in kindleBooks:
         if not book.xrayExists:
            MarkForUpdate(book)

def MarkForUpdate(book, checkForXRay=False):    
    book.update = True
    if checkForXRay:
        RemoveXRay(book)

def UnmarkforUpdate(book):
    book.update = False

def RemoveXRay(book):
    if book.xrayExists:
        for file in glob(os.path.join(book.xrayLocation, '*')):
            os.remove(file)

def SetupXRayBuilder():
    # create global variables
    global app, mainWindow, aliasesWindow, chaptersWindow, settingsWindow
    global xrayButton, sheflariURLButton, shelfariButton, aliasesNoButton, chaptersNoButton
    global bookTextBox, shelfariURLTextBox, outputTextBox, outputDir

    # open X-Ray Builder GUI
    app = Application().start(os.path.join('X-Ray Builder GUI','X-Ray Builder GUI.exe'))
    mainWindow = app['X-Ray Builder GUI']
    aliasesWindow = app['Aliases']
    chaptersWindow = app['Chapters']
    settingsWindow = app['Settings']

    # get buttons
    buttons = [button for button in mainWindow._ctrl_identifiers() if type(button) is controls.win32_controls.ButtonWrapper]
    buttons.sort(key=lambda x:x.Rectangle().left)
    xrayButton = buttons[6]
    sheflariURLButton = buttons[2]
    settingsButton = buttons[10]
    settingsSaveButton = settingsWindow['SaveButton']
    shelfariButton = mainWindow['ShelfariButton']
    aliasesNoButton = aliasesWindow['No']
    chaptersNoButton = chaptersWindow['No']

    # get text boxes
    textBoxes = [box for box in mainWindow._ctrl_identifiers() if type(box) is controls.win32_controls.EditWrapper]
    textBoxes.sort(key=lambda x:x.Rectangle().top)
    bookTextBox = textBoxes[0]
    shelfariURLTextBox = textBoxes[1]
    outputTextBox = textBoxes[2]

    # minimize window
    # mainWindow.Minimize()

    # Get output directory
    ClickButton(settingsButton)
    settingsWindow.Wait('exists', timeout=60)
    outputDir = settingsWindow['Output Directory:Edit'].Texts()[0]
    ClickButton(settingsSaveButton)
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    
    # make sure Source is Shelfari
    ClickButton(shelfariButton)

    # make sure output directory is empty
    if os.path.exists(outputDir): rmtree(outputDir)
    os.mkdir(outputDir)

def ClickButton(button):
    while not button.IsEnabled():
        sleep(1)
    button.Click()

def EditTextBox(textBox, text):
    while not textBox.IsEnabled():
        sleep(1)
    numOfTries = 10
    textBox.SetEditText(text)
    while textBox.Texts()[0] != text and numOfTries > 0:
        textBox.SetEditText(text)
        numOfTries -= 1

    if textBox.Texts()[0] == text:
        return
    raise CouldNotEditTextBox('could not edit text box to %s' % text)

def ProgressBar(percentage, processingText='Processing'):
    progressBar = '#' * (percentage / 5)
    perc = str(percentage) + '%'

    # check if line is too long and shorten accordingly
    if len(processingText) + 28 > MAX_LINE_LENGTH: processingText = processingText[:MAX_LINE_LENGTH-31] + '...'

    sys.stdout.write('\r%s\r' % ('\0'*MAX_LINE_LENGTH)) # clear line
    sys.stdout.write('%-4s |%-20s| %s' % (perc, progressBar, processingText))
    sys.stdout.flush()

def UpdateASINAndUrl(books):
    aConn = httplib.HTTPConnection('www.amazon.com')
    sConn = httplib.HTTPConnection('www.shelfari.com')

    # get and update shelfari url
    print 'Updating ASINs and getting shelfari URLs'
    for progress, book in enumerate(books):
        ProgressBar(progress*100/len(books), processingText = book.bookNameAndAuthor)
        try:
            aConn, sConn = book.GetShelfariURL(aConnection=aConn, sConnection=sConn)
        except Exception as e:
            booksSkipped.append((book, e))
            if type(e) is CouldNotFindASIN:
                UnmarkforUpdate(book)
    ProgressBar(100, processingText='Done.\n\n')

def CreateXRayFile(book):
    ClickButton(xrayButton) # click create xray button

    # wait for aliases window and respond
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    aliasesWindow.Wait('exists', timeout=30)
    ClickButton(aliasesNoButton)

    # wait for chapters window and respond
    app.WaitCPUUsageLower(threshold=.5, timeout=300)
    chaptersWindow.Wait('exists', timeout=5)
    ClickButton(chaptersNoButton)

    # wait for xray creation to be done
    app.WaitCPUUsageLower(threshold=.5, timeout=300)

def MoveXRayFiles(booksUpdate):
    # move x-ray files to their respective locations
    xrayFiles = []
    for dirName, subDirList, fileList in os.walk(outputDir):
        for file in glob(os.path.join(dirName,'*.asc')):
            xrayFiles.append(file)

    if len(xrayFiles)> 0:
        print 'Moving X-Ray Files to their directories'

    for xrayFile in xrayFiles:
        book = kindleBooks.GetBookByASIN(os.path.basename(xrayFile).split('.')[2])
        xrayLoc = book.xrayLocation
        RemoveXRay(book)
        if xrayLoc and os.path.exists(xrayLoc):
            move(xrayFile, xrayLoc)

def CleanUp():
    # delete dmp, ext, log,  out
    print "Cleaning up..."
    if os.path.exists(outputDir): rmtree(outputDir)
    if os.path.exists('dmp'): rmtree('dmp')
    if os.path.exists('ext'): rmtree('ext')
    if os.path.exists('log'): rmtree('log')
    if os.path.exists(os.path.join('X-Ray Builder GUI', 'dmp')): rmtree(os.path.join('X-Ray Builder GUI', 'dmp'))
    if os.path.exists(os.path.join('X-Ray Builder GUI', 'log')): rmtree(os.path.join('X-Ray Builder GUI', 'log'))
    if os.path.exists(os.path.join('X-Ray Builder GUI', 'out')): rmtree(os.path.join('X-Ray Builder GUI', 'out'))

#--------------------------------------------------------------------------------------------------------------------------END OF FUNCTIONS--------------------------------------------------------------------------------------------------------------------------#

# main
parser = argparse.ArgumentParser(description='Create and update kindle X-Ray files')
parser.add_argument('-u', '--update', action='store_true', help='Will give you a list of all books on kindle and asks you to return a comma separated list of book numbers for the books you want to update; Note: You can use a range in the list')
parser.add_argument('-ua', '--updateall', action='store_true',  help='Deletes all X-Ray files and recreates them. Will also create X-Ray files for books that don\'t already have one')
parser.add_argument('-n', '--new', action='store_true', help='Creates X-Ray files for books that don\'t already have one')
args = parser.parse_args()

# check to make sure only one argument is chosen
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
    global booksUpdated, booksSkipped
    booksUpdated = []
    booksSkipped = []
    # update books' ASIN and get shelfari urls, run setup
    UpdateASINAndUrl(booksToUpdate)
    SetupXRayBuilder()
    print 'Creating X-Ray Files'
    for book in booksToUpdate:
        try:
            # insert book location
            print '\t%s' % book.bookNameAndAuthor
            EditTextBox(bookTextBox, book.bookLocation)

            if book.shelfariURL:
                EditTextBox(shelfariURLTextBox, book.shelfariURL)

                # create xray file and add to updated list
                CreateXRayFile(book)
                booksUpdated.append(book)
            else:
                # clear shelfari url, click shelfari button and wait for it to finish
                EditTextBox(bookTextBox, '')
                ClickButton(sheflariURLButton)
                app.WaitCPUUsageLower(threshold=.5, timeout=300)
                if shelfariURLTextBox.Texts()[0]:
                    CreateXRayFile(book)
                    booksUpdated.append(book)
                else:
                    booksSkipped.append((book, 'could not find shelfari url.'))
        except Exception, e:
            booksSkipped.append((book, e))
    print

    # close X-Ray Builder GUI
    killed = False
    numOfTries = 10
    while not killed and numOfTries > 0:
        try:
            killed = app.kill_()
        except:
            numOfTries -= 1
    if not killed:
        print "Could not close X-Ray Builder GUI."

    MoveXRayFiles(booksUpdated)

    # print updated books
    print
    if len(booksUpdated) > 0:
        print 'Books Updated: '
    for book in booksUpdated:
        print '\t%s' % book.bookNameAndAuthor

    # print skipped books
    print
    if len(booksSkipped) > 0:
        print 'Books Skipped: '
    for book in booksSkipped:
        if book[1] is '':
            print '%s skipped because %s' % (book[0].bookNameAndAuthor, repr(book[1]))
        else:
            print '%s skipped because %s' % (book[0].bookNameAndAuthor, book[1])

    CleanUp()
else:
    print 'No books to update.'

print 'Done!'