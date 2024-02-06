import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN = './config/token.json'
SERVICE_CRED = './config/korsakov134.json'


def get_creds():
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


def get_upcoming_event(creds):
  """
  Get the nearest event
  """
  try:
    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=1,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")

  
def create_event(creds, summary, start_event_dt, start_event_tm, end_event_dt, end_event_tm, description=None):
  """
  Adding an event to the calendar
  """
  service = build("calendar", "v3", credentials=creds)
  start_event = start_event_dt + 'T' + start_event_tm + ':00'
  end_event = end_event_dt + 'T' + end_event_tm + ':00'

  event = {
    'summary': f'{summary}',
    'location': '',
    'description': f'{description}',
    'start': {
      'dateTime': f'{start_event}',
      'timeZone': 'Europe/Moscow',
    },
    'end': {
      'dateTime': f'{end_event}',
      'timeZone': 'Europe/Moscow',
    },
    'recurrence': [],
    'attendees': [],
    'reminders': {
      'useDefault': False,
      'overrides': [
        {'method': 'popup', 'minutes': 10},
      ],
    },
  }

  event = service.events().insert(calendarId='eps150189@gmail.com', body=event).execute()
  print('Event created: %s' % (event.get('htmlLink')))



if __name__ == "__main__":
  get_upcoming_event(get_creds())
  create_event(get_creds(), 'TEST EVENT', '2024-02-07', '09:00', '2024-02-07', '17:00', 'TEST DESCRIPTION')
