# -*- encoding: utf-8 -*-
import sqlite3
import logging
from os.path import join, abspath, split
from os import getcwd


PROJECT_PATH = join(*split(getcwd())[:-1])
DB_PATH = join(PROJECT_PATH, 'bot_data.db')


class User:
    def __init__(self, id, first_name=None, last_name=None, username=None, locale='en'):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.locale = locale

    def save(self):
        """
        dump data to db if no exists update if exists
        :return:
        """
        attrs = ('id', 'first_name', 'last_name', 'username')
        values = tuple(getattr(self, i) for i in attrs)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO USERS (ID,FIRST_NAME,LAST_NAME,USERNAME) \
                                  VALUES(?,?,?,?)", values);

    def notify(self):
        """
        notify user
        may be different notifiers for stream announce etc
        :return:
        """

    @staticmethod
    def from_db(uid):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT * FROM USERS WHERE id={}".format(uid));
            user = cursor.fetchone()
            return User(id=user[0], first_name=user[1], last_name=user[2])
