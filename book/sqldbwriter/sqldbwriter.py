# sqldbwriter.py

from sqlite3 import *

class SQLDBWriter(object):
    def __init__(self, dbFilename):
        self.connection = connect(dbFilename)

    def __del__(self):
        connection.close()

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value
        self._cursor = self.connection.cursor()

    @property
    def cursor(self):
        return self._cursor

    def importBaseDB(self, filename):
        with open(filename) as f:
            script = f.read()
            self.cursor.executescript(script)

    def createTable(self, tableName, colNames, colTypes):
        #check length of lists to make sure they match
        if len(colNames) != len(colTypes):
            raise ListLengthMismatch("colNames and colTypes are not the same length.")

        cmd = 'CREATE TABLE %s (' % str(tableName)
        for colName, colType in zip(colNames, colTypes):
            cmd += '%s %s, ' % (str(colName), str(colType))
        cmd = cmd[:-2] + ')'
        self.cursor.execute(cmd)
        self.connection.commit()

    def insert(self, tableName, *values):
        cmd = 'INSERT INTO %s VALUES (' % str(tableName)
        if type(values[0]) is list:
            values = values[0]
        if type(values[0]) is tuple:
            values = list(values)
        else:
            values = [values]
        for i in xrange(len(values[0])):
            cmd += '?,'
        cmd = cmd[:-1] + ')'
        self.cursor.executemany(cmd, values)
        self.connection.commit()

class ListLengthMismatch(Exception):
    pass