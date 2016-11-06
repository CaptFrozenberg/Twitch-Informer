# !usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import requests
from os import getcwd, remove
from os.path import abspath, join
from urllib.request import urlretrieve
from time import sleep
from re import sub

import telebot
from telebot import types
from twitch import exceptions
from twitch.api import v3 as twitch

import config
from time_zone_offset import get_duration

bot = telebot.TeleBot(config.TOKEN)

CONNECTION_RETRY_TIME = 120

COMMANDS = [
    '/start',
    '/help',
    '/info_channel',
    '/info_stream',
    '/info_user',
    '/top'
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

# logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('{levelname:8}: {asctime} {name:10} {message}')
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
fh = logging.FileHandler(join(abspath('log'), 'events.log'))
fh.setLevel(logging.WARNING)
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)

LOGGING_MSG_TEMPLATE = 'Chat id: {0:10} Sender: {1:7} Message: {2}'
LOGGING_BOT_RESPONSE_TEMPLATE = 'Chat id: {0:10} Sender: {1:48} Message: {2}'
LOGGING_USER_INFO_TEMPLATE = '{0!s:12s}{1!s:12s}{2!s:12s}{3!s:12s}'

NOT_FOUND_MESSAGE_TEMPLATE = '''
Sorry, but a can't give you information about all {item}s!
Write me a {item} you need.
Use syntax: {usage}
'''


def file_by_url(url, extension='.jpg'):
    resp = requests.get(url)
    # return resp.content # WTF????
    with open('tmp.jpg', 'wb') as f:
        f.write(resp.content)
    data = open('tmp.jpg', 'rb') # ????
    remove('tmp.jpg')
    return data


def date_from_raw(raw):
    raw_date = raw.split('T')
    date = raw_date[0]
    time = raw_date[1][:-1]
    return date, time


def send_stream_channel_info(chat_id, channel_name, channel_info=False):
    """
        дописать чтобы был статус если он лайн предлагать смотреть стрим инфо
        добавить информаци ю о пользователе партнер ли когда зарегался и тд
        :param channel_name:
        :param chat_id:
        :param channel_info: if True send channel info too
        :return:
    """
    try:
        stream_by_channel = twitch.streams.by_channel(channel_name)
    except exceptions.ResourceUnavailableException:
        stream_by_channel = None

    if stream_by_channel is None:
        text = "Unknown channel"
        bot.send_message(chat_id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))
    else:
        stream = stream_by_channel.get('stream')
        if stream is None:
            text = "{0}'s stream is currently offline.".format(channel_name)
            bot.send_message(chat_id, text)
            logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))
        else:
            message_template = \
                '''
                <b>Channel: </b>{channel}
                <b>Title: </b>{title}
                <b>The stream started {duration} ago.</b>
                <b>Viewers: </b>{viewers}
                '''
            kwargs = {
                'channel': stream['channel']['name'],
                'title': stream['channel']['status'],
                'duration': get_duration(stream['created_at']),
                'viewers': stream['viewers'],
            }
            text = message_template.format(**kwargs).replace('    ', '')
            log_msg = sub(r'<.*?>', '', text).replace(':', ':\n').replace(' ', '').replace('\n', ' ')

            bot.send_message(chat_id, text, disable_web_page_preview=True, parse_mode='HTML')
            logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', log_msg))
            url = stream['preview']['medium']
            photo = file_by_url(url, '.jpeg')
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text='Watch now!', url=stream['channel']['url'])
            keyboard.add(url_button)
            bot.send_photo(chat_id, photo, reply_markup=keyboard)
            logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', 'photo'))

        if channel_info:
            send_channel_info(chat_id, stream['channel'])


def send_channel_info(chat_id, channel_name=None, channel=None):
    """
    функция отправляющая информацию о канале
    возможна добыча информации как из словаря {channel}
    так и через запрос к api
    такая вариативность имеет смысл так как запрос на получение информации о стриме так же содержит канал
    чтобы не делать лишний запрос к api воспользоваться уже готовым материалом

    :param chat_id:
    :param channel_name:
    :param channel:
    :return: 0 если успешно 1 если ошибка
    """

    if channel_name is None and channel is None:
        return 1

    keyboard = types.InlineKeyboardMarkup()

    if channel is None:
        # если вызов был из stream info то информация о стриме не нужна и кнопка с командой отображена не будет
        # иначе кнопка будет добавлена к клавиатуре в последнем сообщении
        try:
            channel = twitch.channels.by_name(channel_name)
            # from pprint import pprint; pprint(channel)
        except exceptions.ResourceUnavailableException:
            text = "Unknown channel"
            bot.send_message(chat_id, text)
        else:
            callback_button = types.InlineKeyboardButton(text='Get stream info!',
                                                         callback_data='info_stream {0}'.format(channel_name))
            keyboard.add(callback_button)

    message_template = \
        '''
        <b>Display name: </b>{display_name}
        <b>Game: </b>{game}
        <b>Created at: </b>{created_at}
        <b>Broadcaster language: </b> {broadcaster_language}
        <b>Followers: </b>{followers}
        <b>Views: </b>{views}
        <b>Partner: </b>{partner}
        '''
    kwargs = {
        'display_name': channel['display_name'],
        'game': channel['game'],
        'created_at': '{0} {1}'.format(*date_from_raw(channel['created_at'])),
        'broadcaster_language': channel['broadcaster_language'],
        'followers': channel['followers'],
        'views': channel['views'],
        'partner': channel['partner'],
    }
    text = message_template.format(**kwargs).replace('    ','')
    log_msg = sub(r'<.*?>', '', text).replace(':', ':\n').replace(' ', '').replace('\n', ' ')

    url_button = types.InlineKeyboardButton(text='Open channel!', url=channel['url'])
    keyboard.add(url_button)
    bot.send_message(chat_id, text, disable_web_page_preview=True, reply_markup=keyboard, parse_mode='HTML')
    logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', log_msg))

    return 0


def send_user_info(chat_id, user_name):
    try:
        user = twitch.users.by_name(user_name)
    except exceptions.ResourceUnavailableException:
        text = "Unknown user"
        bot.send_message(chat_id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))
    else:
        text = 'Logo:'
        bot.send_message(chat_id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))

        photo = file_by_url(user['logo'])
        bot.send_photo(chat_id, photo)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', 'photo'))

        text = 'Display name: {0}'.format(user['display_name'])
        bot.send_message(chat_id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))

        text = 'Created at: {0} {1}'.format(*date_from_raw(user['created_at']))
        bot.send_message(chat_id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))

        text = 'Last action: {0} {1}'.format(*date_from_raw(user['updated_at']))
        bot.send_message(chat_id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(chat_id, 'bot', text))


@bot.message_handler(commands=['start', 'help'])
def start_help_reply(message):
    user = message.from_user
    user_info = LOGGING_USER_INFO_TEMPLATE.format(user.id, user.username, user.first_name, user.last_name)
    logger.warning(LOGGING_MSG_TEMPLATE.format(message.chat.id, user_info, message.text))

    text = "Hi! It'll be a cool bot. Please wait till we finish it!"
    bot.send_message(message.chat.id, text)
    logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', text))

    text = 'Now, a few commands are available'
    bot.send_message(message.chat.id, text)
    logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', text))
    bot.send_message(message.chat.id, HELP)
    logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', 'help'))


@bot.message_handler(commands=['info_channel'])
def info_channel(message):
    user = message.from_user
    user_info = LOGGING_USER_INFO_TEMPLATE.format(user.id, user.username, user.first_name, user.last_name)
    logger.warning(LOGGING_MSG_TEMPLATE.format(message.chat.id, user_info, message.text))
    if '/info_channel' in message.text and (len(message.text.split()) < 2):
        text = NOT_FOUND_MESSAGE_TEMPLATE.format(item='channel', usage='/info_channel <channel_name>')
        bot.send_message(message.chat.id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', text.replace('\n', ' ')))
    else:
        channel_name = message.text.split()[1]
        send_channel_info(message.chat.id, channel_name=channel_name)


@bot.message_handler(commands=['info_user'])
def info_user(message):
    user = message.from_user
    user_info = LOGGING_USER_INFO_TEMPLATE.format(user.id, user.username, user.first_name, user.last_name)
    logger.warning(LOGGING_MSG_TEMPLATE.format(message.chat.id, user_info, message.text))
    if '/info_user' in message.text and (len(message.text.split()) < 2):
        text = NOT_FOUND_MESSAGE_TEMPLATE.format(item='user', usage='/info_user <user_name>')
        bot.send_message(message.chat.id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', text.replace('\n', ' ')))
    else:
        username = message.text.split()[1]
        send_user_info(message.chat.id, username)


@bot.message_handler(commands=['info_stream'])
def info_stream(message):
    user = message.from_user
    user_info = LOGGING_USER_INFO_TEMPLATE.format(user.id, user.username, user.first_name, user.last_name)
    logger.warning(LOGGING_MSG_TEMPLATE.format(message.chat.id, user_info, message.text))

    if '/info_stream' in message.text and (len(message.text.split()) < 2):
        text = NOT_FOUND_MESSAGE_TEMPLATE.format(item='stream', usage='/info_stream <channel_name>')
        bot.send_message(message.chat.id, text)
        logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', text.replace('\n', ' ')))
    else:
        channel_name = message.text.split()[1]
        send_stream_channel_info(message.chat.id, channel_name=channel_name)


@bot.message_handler(commands=['top'])
def top(message):
    user = message.from_user
    user_info = LOGGING_USER_INFO_TEMPLATE.format(user.id, user.username, user.first_name, user.last_name)
    logger.warning(LOGGING_MSG_TEMPLATE.format(message.chat.id, user_info, message.text))
    try:
        count = int(message.text.split()[1])
    except IndexError:
        count = 3
    result = twitch.streams.all(limit=count)
    keyboard = types.InlineKeyboardMarkup()
    for stream in result['streams']:
        name = stream['channel']['name']
        callback_button = types.InlineKeyboardButton(text=name, callback_data='info_stream {0}'.format(name))
        keyboard.add(callback_button)
    text = 'Top {0} channels by viewers.'.format(str(count))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)
    logger.warning(LOGGING_BOT_RESPONSE_TEMPLATE.format(message.chat.id, 'bot', text))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user = call.from_user
    user_info = LOGGING_USER_INFO_TEMPLATE.format(user.id, user.username, user.first_name, user.last_name)
    logger.warning('Chat id: {0!s:10s} Sender: {1!s} Message: {2}'.format(call.message.chat.id, user_info, call.data))
    if call.message:
        data = call.data.split()
        if data[0] == 'info_stream':
            channel_name = data[1]
            send_stream_channel_info(call.message.chat.id, channel_name=channel_name)


@bot.message_handler(content_types=['text'])
def not_implemented(message):
    if not (message.chat.id < 0):
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
            except Exception as e:		
                start = False
                logger.error(e)
                logger.error('Connection lost')
                sleep(CONNECTION_RETRY_TIME)


if __name__ == '__main__':
    main()
