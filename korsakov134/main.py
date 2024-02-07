from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from telegram.ext import CallbackContext

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import io
import re
import json
import os.path
from datetime import datetime, timedelta


# Auth Google
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN = './config/token.json'
SERVICE_CRED = './config/korsakov134.json'

# Auth Telegram
path_telegram = './config/token_tg.json'
with io.open(path_telegram, "r", encoding="utf-8") as json_file:
  data = json.load(json_file)

TOKEN_TG = data['token']
CHAT_TG = data['chat_id']

# День недели
def next_date_of_weekday(weekday_name):
    weekdays = {'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3, 'пятница': 4, 'суббота': 5, 'воскресенье': 6,
                'пн': 0, 'вт': 1, 'ср': 2, 'чт': 3, 'пт': 4, 'сб': 5, 'вс': 6,
                'сегодня': 0, 'завтра': 1, 'послезавтра': 2}
    today = datetime.now()
    current_weekday = today.weekday()
    target_weekday = weekdays[weekday_name.lower()]
    
    days_until_target = (target_weekday - current_weekday) % 7
    if days_until_target == 0:
        days_until_target = 7
    
    next_date = today + timedelta(days=days_until_target)
    return next_date.strftime('%Y-%m-%d')


def get_creds(scopes, token, service_cred):
  """
  Getting credentials for authorization
  """

  creds = None
  if os.path.exists(TOKEN):
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(SERVICE_CRED, SCOPES)
      creds = flow.run_local_server(port=0)

    with open(TOKEN, "w") as token:
      token.write(creds.to_json())
  
  return creds


# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот, который отслеживает сообщения в этом чате.")


# Обработчик новых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    if update.message:
        message_text = update.message.text
        print("Received message:", message_text)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Сообщение принято")
        
        match = re.match(r"^(.*), (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) (\d{1})$", message_text)
        if match:
           event_start_dt = match.group(2) # start date event

        else:
            match = re.match(r"^(.*), (.*), (\d{2}:\d{2}) (\d{1})$", message_text)
            event_start_dt = next_date_of_weekday(match.group(2))

        event_summary = match.group(1)  # name event
        event_start_tm = match.group(3) # start time event
        event_duration = int(match.group(4)) # duration event in hours
        
        start_event = datetime.strptime(event_start_dt + ' ' + event_start_tm + ':00', '%Y-%m-%d %H:%M:%S')
        end_event = start_event + timedelta(hours=event_duration)
        
        # Создаем объект события для Google Calendar
        event = {
            'summary': event_summary,
            'start': {
                'dateTime': f'{str(start_event.date())}T{str(start_event.time())}',
                'timeZone': 'Europe/Moscow',
            },
            'end': {
                'dateTime': f'{str(end_event.date())}T{str(end_event.time())}',
                'timeZone': 'Europe/Moscow',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10}
                ],
            },
        }

        service = build("calendar", "v3", credentials=get_creds(SCOPES, TOKEN, SERVICE_CRED))
        event = service.events().insert(calendarId='eps150189@gmail.com', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))

        context.bot.send_message(chat_id=update.effective_chat.id, text="Событие успешно добавлено в ваш календарь!")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Неверный формат сообщения. Пример: Сделать зарядку, 2024-02-10, 10:00, 2")


def main():
    # Создаем объект Updater и передаем ему токен вашего бота
    updater = Updater(TOKEN_TG, use_context=True)

    # Получаем диспетчер для зарегистрированных обработчиков
    dp = updater.dispatcher

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))

    # Регистрируем обработчик сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Начинаем поиск обновлений
    updater.start_polling()

    # Запускаем бота и обновление, пока Ctrl + C не будет нажато для остановки
    updater.idle()

if __name__ == '__main__':
    main()
