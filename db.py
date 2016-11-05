# -*- encoding: utf-8 -*-

import sqlite3
import logging
from os.path import join, abspath

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('{levelname:8}: {asctime} {name:10} {message}')
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
fh = logging.FileHandler(join(abspath('log'), 'db.log'))
fh.setLevel(logging.WARNING)
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)

class DataManager:
    def __init__(self, db_path='bot_data.db'):
        self.db_path = db_path

    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            # create USERS table

            conn.execute('''CREATE TABLE USERS
                   (ID INT PRIMARY KEY     NOT NULL,
                   FIRST_NAME     TEXT,
                   LAST_NAME      TEXT,
                   USERNAME       TEXT);''')
            logger.warning('Table USERS created succesfully')

            # create CHANNELS table
            self.conn.execute('''CREATE TABLE CHANNELS
                           (ID INT PRIMARY KEY      NOT NULL,
                           DISPLAY_NAME     TEXT    NOT NULL,
                           NAME             TEXT    NOT NULL,
                           STATUS           BOOLEAN NOT NULL );''')
            logger.warning('Table CHANNELS created succesfully')

            # create SUBSCRIPTIONS table
            self.conn.execute('''CREATE TABLE SUBSCRIPTIONS
                           (ID INT PRIMARY KEY     NOT NULL,
                           FIRST_NAME     TEXT,
                           LAST_NAME      TEXT,
                           USERNAME       TEXT);''')
            logger.warning('Table USERS created succesfully')

if __name__ == '__main__':
    man = DataManager()
    man.create_tables()