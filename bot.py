# !usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from os import getcwd
from urllib.request import urlretrieve

import telebot
from telebot import types
from twitch import exceptions
from twitch.api import v3 as twitch

import config
from time_zone_offset import get_duration

bot = telebot.TeleBot(config.TOKEN)

COMMANDS = [
    '/start',
    '/help',
    '/info_channel',
    '/info_stream',
    '/info_user'
]

HELP = '''
        List of available commands:
        /start
        /help
        /info_channel <channel_name>
        /info_stream <channel_name>
        /info_user <user_name>
        /top <count>
        '''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#formatter = logging.Formatter('{levelname:8}: {asctime} {name:10} {message}')
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
fh = logging.FileHandler('log.txt')
fh.setLevel(logging.WARNING)
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)

def file_by_url(url, extension='.jpeg'):
    fname = url.split('/')[2] + extension
    path = getcwd() + '\\images\\' + fname  # abspath подставляет букву диска с файлом но не весь путь
    urlretrieve(url, path)
    file = open(path, 'rb')
    return file


def date_from_raw(raw):
    raw_date = raw.split('T')
    date = raw_date[0]
    time = raw_date[1][:-1]
    return date, time


def send_stream_channel_info(chat_id, channel_name, channel_info=False):
    '''
        дописать чтобы был статус если он лайн предлагать смотреть стрим инфо
        добавить информаци ю о пользователе партнер ли когда зарегался и тд
        :param channel_name:
        :param chat_id:
        :return:
    '''
    try:
        stream_by_channel = twitch.streams.by_channel(channel_name)
    except exceptions.ResourceUnavailableException:
        stream_by_channel = None

    if stream_by_channel == None:
        text = "Unknown channel"
        bot.send_message(chat_id, text)
    else:
        stream = stream_by_channel.get('stream')
        if stream == None:
            text = "{0}'s stream is currently offline.".format(channel_name)
            bot.send_message(chat_id, text)
        else:
            bot.send_message(chat_id, 'Channel: {0}'.format(stream['channel']['name']), \
                             disable_web_page_preview=True)
            bot.send_message(chat_id, 'Title: {0}'.format(stream['channel']['status']), \
                             disable_web_page_preview=True)
            # bot.send_message(message.chat.id, stream['game'])
            url = stream['preview']['medium']
            photo = file_by_url(url, '.jpeg')
            bot.send_photo(chat_id, photo)
            # bot.send_message(message.chat.id, 'Followers: {0}'.format(stream['channel']['followers']))
            duration = get_duration(stream['created_at'])
            bot.send_message(chat_id, 'The stream started {0} ago.'.format(duration))
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text='Watch now!', url=stream['channel']['url'])
            keyboard.add(url_button)
            bot.send_message(chat_id, 'Viewers: {0}'.format(stream['viewers']), reply_markup=keyboard)
        if channel_info:
            send_channel_info(chat_id, stream['channel'])


def send_channel_info(chat_id, channel_name=None, channel=None):
    '''
    функция отправляющая информацию о канале
    возможна добыча информации как из словаря {channel}
    так и через запрос к api
    такая вариативность имеет смысл так как запрос на получение информации о стриме так же содержит канал
    чтобы не делать лишний запрос к api воспользоваться уже готовым материалом

    :param chat_id:
    :param channel_name:
    :param channel:
    :return: 0 если успешно 1 если ошибка

    '''
    if channel_name is None and channel is None:
        return 1

    keyboard = types.InlineKeyboardMarkup()

    if channel == None:
        # если вызов был из stream info то информация о стриме не нужна и кнопка с командой отображена не будет
        # иначе кнопка будет добавлена к клавиатуре в последнем сообщении
        try:
            channel = twitch.channels.by_name(channel_name)
        except exceptions.ResourceUnavailableException:
            text = "Unknown channel"
            bot.send_message(chat_id, text)
        else:
            callback_button = types.InlineKeyboardButton(text='Get stream info!',
                                                         callback_data='info_stream {0}'.format(channel_name))
            keyboard.add(callback_button)

    bot.send_message(chat_id, 'Display name: {0}'.format(channel['display_name']), \
                     disable_web_page_preview=True)
    bot.send_message(chat_id, 'Game: {0}'.format(channel['game']), \
                     disable_web_page_preview=True)
    date, time = date_from_raw(channel['created_at'])
    bot.send_message(chat_id, 'Created at: {0} {1}'.format(date, time), \
                     disable_web_page_preview=True)
    bot.send_message(chat_id, 'Broadcaster language: {0}'.format(channel['broadcaster_language']), \
                     disable_web_page_preview=True)
    bot.send_message(chat_id, 'Followers: {0}'.format(channel['followers']), \
                     disable_web_page_preview=True)
    bot.send_message(chat_id, 'Views: {0}'.format(channel['views']), \
                     disable_web_page_preview=True)
    url_button = types.InlineKeyboardButton(text='Open channel!', url=channel['url'])
    keyboard.add(url_button)
    bot.send_message(chat_id, 'Partner: {0}'.format(channel['partner']), \
                     disable_web_page_preview=True, reply_markup=keyboard)
    return 0


def send_user_info(chat_id, user_name):
    try:
        user = twitch.users.by_name(user_name)
    except exceptions.ResourceUnavailableException:
        text = "Unknown user"
        bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, 'Logo:')
        photo = file_by_url(user['logo'])
        bot.send_photo(chat_id, photo)
        bot.send_message(chat_id, 'Display name: {0}'.format(user['display_name']))
        date, time = date_from_raw(user['created_at'])
        bot.send_message(chat_id, 'Created at: {0} {1}'.format(date, time))
        date, time = date_from_raw(user['updated_at'])
        bot.send_message(chat_id, 'Last action: {0} {1}'.format(date, time))


@bot.message_handler(commands=['start', 'help'])
def start_help_reply(message):
    text = "Hi! It'll be a cool bot. Please wait till we finish it!"
    bot.send_message(message.chat.id, text)
    text = 'Now, few commands are available'
    bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, HELP)


@bot.message_handler(commands=['info_channel'])
def info_channel(message):
    if message.text == '/info_channel':
        text = "Sorry, but a can't give you information about all channels!"
        bot.send_message(message.chat.id, text)
        text = "Write me a channel you need."
        bot.send_message(message.chat.id, text)
        text = "Use syntax: /info_channel <channel name>"
        bot.send_message(message.chat.id, text)
    else:
        channel_name = message.text.split()[1]
        send_channel_info(message.chat.id, channel_name=channel_name)


@bot.message_handler(commands=['info_user'])
def info_user(message):
    if message.text == '/info_user':
        text = "Sorry, but a can't give you information about all users!"
        bot.send_message(message.chat.id, text)
        text = "Write me a user you need."
        bot.send_message(message.chat.id, text)
        text = "Use syntax: /info_user <username>"
        bot.send_message(message.chat.id, text)
    else:
        username = message.text.split()[1]
        send_user_info(message.chat.id, username)


@bot.message_handler(commands=['info_stream'])
def info_stream(message):
    if message.text == '/info_stream':
        text = "Sorry, but a can't give you information about all streams!"
        bot.send_message(message.chat.id, text)
        text = "Write me a stream you need."
        bot.send_message(message.chat.id, text)
        text = "Use syntax: /info_stream <channel name>"
        bot.send_message(message.chat.id, text)
    else:
        channel_name = message.text.split()[1]
        send_stream_channel_info(message.chat.id, channel_name=channel_name)


@bot.message_handler(commands=['top'])
def top(message):
    if message.text == '/top':
        count = 3
    else:
        count = int(message.text.split()[1])
    result = twitch.streams.all(limit=count)
    keyboard = types.InlineKeyboardMarkup()
    for stream in result['streams']:
        name = stream['channel']['name']
        callback_button = types.InlineKeyboardButton(text=name, callback_data='info_stream {0}'.format(name))
        keyboard.add(callback_button)
    bot.send_message(message.chat.id, 'Top {0} channels by viewers.'.format(str(count)), reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        data = call.data.split()
        if data[0] == 'info_stream':
            channel_name = data[1]
            send_stream_channel_info(call.message.chat.id, channel_name=channel_name)


@bot.message_handler(content_types=['text'])
def not_implemented(message):
    if message.text.split()[0] not in COMMANDS:
        text = 'Unknown command :('
        bot.send_message(message.chat.id, text)
        bot.send_message(message.chat.id, HELP)







def main():
    start = False
    while True:
        while not start:
            try:
                start = True
                logger.warning('Bot trying to start!')
                bot.polling(none_stop=True, timeout=120)
            except:
                start = False
                logger.warning('Connection lost')








if __name__ == '__main__':
   main()
