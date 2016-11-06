# -*- encoding: utf-8 -*-
import sqlite3
import logging
from os.path import join, abspath, split
from os import getcwd
from models import User

PROJECT_PATH = join(*split(getcwd())[:-1])

# logging
db_logger = logging.getLogger()
db_logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('{levelname:8}: {asctime} {name:10} {message}')
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
fh = logging.FileHandler(join(PROJECT_PATH, 'log', 'db.log'))
fh.setLevel(logging.WARNING)
fh.setFormatter(formatter)
db_logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
db_logger.addHandler(ch)


class DataManager:
    def __init__(self, db_path=join(PROJECT_PATH, 'bot_data.db')):
        self.db_path = db_path

    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            # create USERS table

            conn.execute('''CREATE TABLE USERS
                   (id INT PRIMARY KEY     NOT NULL,
                   first_name     TEXT,
                   last_name      TEXT,
                   username       TEXT);''')
            db_logger.warning('Table USERS created succesfully')

            # create CHANNELS table
            conn.execute('''CREATE TABLE CHANNELS
                           (id INT PRIMARY KEY      NOT NULL,
                           display_name     TEXT    NOT NULL,
                           name             TEXT    NOT NULL,
                           status           BOOLEAN NOT NULL );''')
            db_logger.warning('Table CHANNELS created succesfully')

            # create SUBSCRIPTIONS table
            conn.execute('''CREATE TABLE SUBSCRIPTIONS
                           (id INT PRIMARY KEY     NOT NULL,
                           user_id         TEXT,
                           channel_id      TEXT);''')
            db_logger.warning('Table SUBSCRIPTIONS created succesfully')





if __name__ == '__main__':
    # user = User(id=54329385, username='Frozenberg', first_name='Dmitry', last_name='Rodionov')
    man = DataManager()
    man.create_tables()
    # man.add_user(user=user)
    # user = man.get_user(54329385)
    # print(user.first_name)