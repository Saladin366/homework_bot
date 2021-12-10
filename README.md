# Учебный проект "Telegram-бот"

## Telegram-бот для обращения к API сервиса "Практикум.Домашка" и получения статуса домашней работы студента.

Бот раз в 10 минут опрашивает API сервиса "Практикум.Домашка" и проверяет статус отправленной на ревью домашней работы,
при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram,
логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

Проект реализован на python3, для работы с Bot API использована библиотека python-telegram-bot.

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Saladin366/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/Scripts/activate
```

или

```
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Запустить проект:

```
python3 homework.py
```
