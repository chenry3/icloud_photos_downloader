"""
Connector class to faciliate sqlite interactions
"""
import sqlite3


class SqliteConnector:
    """
    connector to sqlite
    """

    def __init__(self, db_file, schema):
        self.db_file = db_file
        self.schema = schema

        # establish sqlite connection
        self.connection = self.connect()

        # initialize sqlite schema
        # apache touches the db on startup so we cannot be sure if our schema
        # exists or not.  calls a create if not exists
        self.initialize()

    def initialize(self):
        """
        initialize new sqlite file by applying schema
        """
        self.trans_query(self.schema)

    def connect(self):
        """
        connect to sqlite
        """
        try:
            connection = sqlite3.connect(self.db_file)
            return connection
        except Exception as err:
            raise

    def query(self, query, params=()):
        """
        query sqlite (no transaction)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
        except Exception as err:
            raise
        return rows

    def trans_query(self, query, params=()):
        """
        transactional sqlite query
        """
        try:
            # create cursor
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            # commit query
            self.connection.commit()
            rows = cursor.fetchall()
            cursor.close()
        except Exception as err:
            # drop connection (abandon commits)
            self.connection.close()
            self.connection = self.connect()
            raise
        return rows
