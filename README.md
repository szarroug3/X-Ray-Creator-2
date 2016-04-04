# X-Ray-Creator-2

Requirements:
	* Python packages: Google, Pywinauto
	* You must open X-Ray Builder GUI at least once to close out the one time
		dialog box that pops up; You should also go and set the settings

usage: XRayCreator.py [-h] [-u] [-ua] [-n]

Create and update kindle X-Ray files

optional arguments:
  -h, --help        show this help message and exit
  -u, --update      Will give you a list of all books on kindle and asks you
                    to return a list of book numbers for the books you want to
                    update
  -ua, --updateall  Deletes all X-Ray files and recreates them. Will also
                    create X-Ray files for books that don't already have one
  -n, --new         Creates X-Ray files for books that don't already have one