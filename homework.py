import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TOKEN_TELEGRAM')
CHAT_ID = os.getenv('MY_CHAT_ID')

handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO, handlers=[handler])

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}

REQUEST_OK = f'Запрос к {ENDPOINT} прошёл успешно.'
STATUS_CHANGE = 'Изменился статус проверки работы "{name}". {value}'
MESSAGE_OK = 'Бот отправил сообщение: "{mes}"'
MESSAGE_ERROR = 'Сбой при отправке сообщения: "{mes}". Текст ошибки: "{err}".'
START_ERROR = ('Отсутствует обязательная переменная окружения "{param}".'
               + ' Программа принудительно остановлена.')
PROGRAM_ERROR = 'Сбой в работе программы:'
API_ERROR = (f'{PROGRAM_ERROR} Эндпоинт {ENDPOINT} недоступен. Код ответа API:'
             + ' {err}.')
KEY_ERROR = f'{PROGRAM_ERROR} Ответ API не содержит ключ ' + '"{err}".'
STATUS_ERROR = (f'{PROGRAM_ERROR} В ответе API обнаружен недокументированный'
                + ' статус домашней работы "{err}".')
UNKNOWN_ERROR = f'{PROGRAM_ERROR} ' + '{err}.'


class ServerError(Exception):
    """Исключение на случай, если API недоступен."""

    pass


class KeysAnswerError(Exception):
    """Исключение на случай, если ответ API некорректен."""

    pass


class StatusHomeworkError(Exception):
    """Исключение на случай, если у задачи неизвестный статус."""

    pass


def send_message(bot, message):
    """Отправляет в Telegram сообщение 'message'."""
    try:
        bot.send_message(CHAT_ID, message)
        logging.info(MESSAGE_OK.format(mes=message))
    except telegram.error.TelegramError as er:
        logging.error(MESSAGE_ERROR.format(mes=message, err=er))


def get_api_answer(url, current_timestamp):
    """Отправляет запрос к API и возвращает ответ."""
    if current_timestamp is None:
        current_timestamp = int(time.time())
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(url, headers=HEADERS, params=payload)
        logging.info(REQUEST_OK)
    except Exception as er:
        raise ServerError(er)
    if response.status_code != HTTPStatus.OK:
        raise ServerError(response.status_code)
    return response.json()


def parse_status(homework):
    """Анализирует статус задачи."""
    status = homework.get('status', None)
    homework_name = homework.get('homework_name', None)
    if status is None:
        raise KeysAnswerError('status')
    if homework_name is None:
        raise KeysAnswerError('homework_name')
    verdict = HOMEWORK_VERDICTS.get(status, None)
    if verdict is None:
        raise StatusHomeworkError(status)
    return STATUS_CHANGE.format(name=homework_name, value=verdict)


def check_response(response):
    """Проверяет ответ API на корректность.
    При изменении статуса вызывает функцию анализа статуса.
    """
    homeworks = response.get('homeworks', None)
    current_date = response.get('current_date', None)
    if homeworks is None:
        raise KeysAnswerError('homeworks')
    if current_date is None:
        raise KeysAnswerError('current_date')
    messages = []
    for homework in homeworks:
        messages.append(parse_status(homework))
    return messages, current_date


def _handler_exceptions(bot, message, last_message):
    """Логирует исключения.
    При необходимости вызывает функцию отправки сообщения в Telegram.
    """
    logging.error(message)
    if message != last_message:
        send_message(bot, message)
    return message, int(time.time())


def main():
    """Основная функция. Активирует и управляет ботом."""
    params = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'CHAT_ID': CHAT_ID}
    for par in params:
        if params[par] is None:
            logging.critical(START_ERROR.format(param=par))
            sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_message = ''
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            messages, current_timestamp = check_response(response)
            for message in messages:
                send_message(bot, message)
        except ServerError as er:
            message = API_ERROR.format(err=er)
            last_message, current_timestamp = _handler_exceptions(bot, message,
                                                                  last_message)
        except KeysAnswerError as er:
            message = KEY_ERROR.format(err=er)
            last_message, current_timestamp = _handler_exceptions(bot, message,
                                                                  last_message)
        except StatusHomeworkError as er:
            message = STATUS_ERROR.format(err=er)
            last_message, current_timestamp = _handler_exceptions(bot, message,
                                                                  last_message)
        except Exception as er:
            message = UNKNOWN_ERROR.format(err=er)
            last_message, current_timestamp = _handler_exceptions(bot, message,
                                                                  last_message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
