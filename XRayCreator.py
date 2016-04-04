# XRayCreator.py

import os
import sys
import argparse
from kindle.books import Books
from time import sleep
from glob import glob
from shutil import move, rmtree
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
    for bookID in books:
        if  int(bookID) <= len(kindleBooks):
            book = kindleBooks.books[int(bookID) - 1]
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


#main
parser = argparse.ArgumentParser(description='Create and update kindle X-Ray files')
parser.add_argument('-u', '--update', action='store_true', help='Will give you a list of all books on kindle and asks you to return a list of book numbers for the books you want to update')
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
    CleanUp()
    booksSkipped = []

    #try to connect to X-Ray Builder; if it's not open, open it
    app = Application()
    try:
        app = app['X-Ray Builder GUI']
    except Exception, e:
        app = Application().start(os.path.join('X-Ray Builder GUI','X-Ray Builder GUI.exe'))
    mainWindow = app['X-Ray Builder GUI']
    aliasesWindow = app['Aliases']
    chaptersWindow = app['Chapters']
    settingsWindow = app['Settings']

    #minimize window
    #mainWindow.Minimize()

    #Get output directory
    mainWindow['Button3'].Click()
    settingsWindow.Wait('exists', timeout=60)
    outputDir = settingsWindow['Edit4'].Texts()[0]
    if os.path.exists(outputDir): rmtree(outputDir)
    settingsWindow['Button23'].Click()

    #update books
    for book in booksToUpdate:
        try:
            print book.bookName
            print '\tUpdating ASIN and getting shelfari URL'
            book.GetShelfariURL()
        except Exception as e:
            booksToUpdate.remove(book)
            booksSkipped.append((book, e))

        print '\tCreating X-Ray file'
        mainWindow['Edit1'].SetEditText(book.bookLocation)
        mainWindow['Edit2'].SetEditText(book.shelfariURL)
        mainWindow['Button6'].Click()   #make sure Source is Shelfari
        mainWindow['Button11'].Click()  #click create xray button

        #wait for aliases window
        aliasesWindow.Wait('exists', timeout=60)
        aliasesWindow['No'].Click()

        #wait for chapters window
        chaptersWindow.Wait('exists', timeout=60)
        chaptersWindow['No'].Click()

        #wait for xray creation to be done
        app.WaitCPUUsageLower(timeout=60)

    #close X-Ray Builder GUI
    app.kill_()

    #move x-ray files to their respective locations
    print 'Moving X-Ray Files to their directories'
    xrayFiles = []
    for dirName, subDirList, fileList in os.walk(outputDir):
        for file in glob(os.path.join(dirName,'*.asc')):
            print file
            xrayFiles.append(file)
    
    for xrayFile in xrayFiles:
        xrayLoc = kindleBooks.GetBookByASIN(os.path.basename(xrayFile).split('.')[2]).xrayLocation
        if xrayLoc and os.path.exists(xrayLoc):
            move(xrayFile, xrayLoc)

    for book in booksSkipped:
        print '%s skipped because %s' % (book[0].bookName, book[1])
else:
    print "No books to update."

#clean up
#delete dmp, ext, log,  out
print "Cleaning up..."
if os.path.exists(outputDir): rmtree(outputDir)
if os.path.exists('dmp'): rmtree('dmp')
if os.path.exists('ext'): rmtree('ext')
if os.path.exists('log'): rmtree('log')

print "Done!"