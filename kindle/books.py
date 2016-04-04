# books.py

import ctypes
import os
from mobibook import MobiBook
from customexceptions import *

# Drive types
DRIVE_UNKNOWN     = 0  # The drive type cannot be determined.
DRIVE_NO_ROOT_DIR = 1  # The root path is invalbookID; for example, there is no volume mounted at the specified path.
DRIVE_REMOVABLE   = 2  # The drive has removable media; for example, a floppy drive, thumb drive, or flash card reader.
DRIVE_FIXED       = 3  # The drive has fixed media; for example, a hard disk drive or flash drive.
DRIVE_REMOTE      = 4  # The drive is a remote (network) drive.
DRIVE_CDROM       = 5  # The drive is a CD-ROM drive.
DRIVE_RAMDISK     = 6  # The drive is a RAM disk.
books_updated = []
books_skipped = []

class Books(object):
    def __init__(self):
        self.FindKindle()
        self.GetBooks()

    def __iter__(self):
        for book in self.books:
            yield book

    def __str__(self):
        string = ''
        for book in self.books:
            string += str(book) + '\n'
        return string[:-1]

    def __len__(self):
        return len(self.books)

    @property
    def kindleDrive(self):
        return self._kindleDrive

    @kindleDrive.setter
    def kindleDrive(self, value):
        self._kindleDrive = value

    @property
    def books(self):
        return self._books
    
    @books.setter
    def books(self, value):
        self._books = value
    
    # Return drive letter of kindle if found or None if not found
    def FindKindle(self):
        print "Checking for kindle..."
        drive_info = self.GetDriveInfo()
        removable_drives = [drive_letter for drive_letter, drive_type in drive_info if drive_type == DRIVE_REMOVABLE]
        for drive in removable_drives:
            for dirName, subDirList, fileList in os.walk(drive):
                if dirName == drive + "system\.mrch":
                    for fName in fileList:
                        if "amzn1_account" in fName:
                            print "Kindle found!"
                            self.kindleDrive = drive
                            return
        raise KindleNotFound("Please make sure kindle is plugged in.")

    # Return list of tuples mapping drive letters to drive types
    def GetDriveInfo(self):
        result = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            bit = 2 ** i
            if bit & bitmask:
                drive_letter = '%s:' % chr(65 + i)
                drive_type = ctypes.windll.kernel32.GetDriveTypeA('%s\\' % drive_letter)
                result.append((drive_letter, drive_type))
        return result

    # Get list of books
    def GetBooks(self):
        books_directory = os.path.join(self.kindleDrive, 'documents')
        self.books = []
        index = 0
        print "Searching for books..."
        for dirName, subDirList, fileList in os.walk(books_directory):
            for fName in fileList:
                if ".mobi" in fName:
                    index += 1
                    self.books.append(MobiBook(os.path.join(dirName,fName)))
        print '%i books found.' % index


        print 'Get metadata for books...'
        for book in self.books:
            book.GetBookConfig()
        self.books.sort(key=lambda x:x.bookNameAndAuthor)
        print "Done getting metadata"
        print

    def PrintListOfBooks(self):
        for bookNum, book in enumerate(self.books, 1):
            print '%i. %s' % (bookNum, book.bookNameAndAuthor)
        print

    def RemoveBooksWithXray(self):
        for book in self.books:
            if book.xrayExists:
                self.books.remove(book)

    def GetBooksToUpdate(self):
        booksToUpdate = []
        for book in self.books:
            if book.update:
                booksToUpdate.append(book)
        return booksToUpdate

    def GetBookByASIN(self, ASIN, onlyCheckUpdated=True):
        for book in self.books:
            if (onlyCheckUpdated and book.update) or not onlyCheckUpdated:
                if book.ASIN == ASIN:
                    return book