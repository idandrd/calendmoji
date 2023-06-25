import json
import os
from datetime import datetime

import emoji
import openai
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
openai.api_key = os.getenv("OPENAI_API_KEY")


def contains_emojis(s):
    return len([c for c in s if emoji.is_emoji(c)]) > 0


def is_item_relevant(item):
    is_by_self = item.get('organizer', {}).get('self', False)
    no_attendees = item.get('attendees') is None
    is_no_emojis = len([c for c in item.get(
        'summary', '') if emoji.is_emoji(c)]) == 0
    return (
        is_by_self
        # and no_attendees
        and is_no_emojis
    )


def filter_relevant_events(events):
    items = events.get('items', [])
    return [x for x in items if is_item_relevant(x)]


def get_events(token):
    current_time = f"{datetime.now().isoformat().split('.')[0]}Z"
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={current_time}"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_event_emoji(event):
    role_description = "You are a personal assistant, and your job is to add the right emoji to calendar events. Your answer should include only the emoji with no additional text."
    prompt_request = f"What would be the appropriate emoji for the following event title: {event.get('summary')}"
    messages = [
        {"role": "system", "content": role_description},
        {"role": "user", "content": prompt_request}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=.5,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    response_text = response["choices"][0]["message"]['content'].strip()
    for c in response_text:
        if emoji.is_emoji(c):
            return c
    return ''


def update_event_name(token, event, new_name):
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event['id']}"
    payload = json.dumps({**event, 'summary': new_name})
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.put(url, headers=headers, data=payload)
    return response


def add_emojis_to_events(token):
    events = get_events(token)
    relevant_events = filter_relevant_events(events)
    for event in relevant_events:
        event_emoji = get_event_emoji(event)
        new_name = f'{event_emoji} {event["summary"]}'
#         res = update_event_name(token, event, new_name)
        print(new_name)


add_emojis_to_events(os.getenv("OPENAI_API_KEY"))
