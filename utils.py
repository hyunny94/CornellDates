from datetime import date
import boto3
from boto3.dynamodb.conditions import Key
import time

SSML_START = "<speak>"
SSML_EMPHASIS_STRONG_START = '<emphasis level="strong">'
SSML_EMPHASIS_STRONG_END = '</emphasis>'
SSML_EMPHASIS_MODERATE_START = '<emphasis level="moderate">'
SSML_EMPHASIS_MODERATE_END = '</emphasis>'
SSML_END = "</speak>"

def get_default_academic_year():
    today = date.today()
    # mm/dd/yy
    d = today.strftime("%m/%d/%y")
    year = int(d.split('/')[2])
    return str(year) + "-" + str(year+1)

def pick_closest_event_for_grade(events, grade):
    for e in events:
        for g in e['grade']['L']:
            if g['S'] == 'all' or g['S'] == grade:
                return e
    raise Exception("event for " + grade + " not found.")

def get_event_abb_name(slots, possible_slot_types):
    for slot_type in possible_slot_types:
        if slots[slot_type].resolutions:
            if slots[slot_type].resolutions.resolutions_per_authority[0].values:
                event_abb_name = slots[slot_type].resolutions.resolutions_per_authority[0].values[0].value.name
                return event_abb_name
            else:
                raise Exception("sorry we have the event on record but can you try rephrasing your question?")
    raise Exception("sorry we cannot answer the question at this time.")
    
def query_ddb(ddb_table_name, grade, event_abb_name):
    client = boto3.client('dynamodb')
    response = client.query(
        ExpressionAttributeValues={
            ':v1': {
                'S': event_abb_name,
            },
        },
        KeyConditionExpression="event_abb_name = :v1",
        TableName=ddb_table_name,
    )
    event = pick_closest_event_for_grade(response['Items'], grade)
    return event

def get_default_apologetic_response(handler_input):
    speak_output = "We are sorry. We cannot answer your question right now. We will look to fix the issue as soon as possible."
    return (
        handler_input.response_builder
        .speak(speak_output)
        .ask(speak_output)
        .response
    )

def get_speak_output(event):
    speak_output = SSML_START
    speak_output += event['event_abb_name']['S']
    date_granularity = event['date_granularity']['S']
    internal_category = event['internal_category']['S']
    start = int(event['start']['N'])

    # 1 this event's ['date_granularity'] => one of ["date", "hour"]
    if internal_category == 'period':
        end = int(event['end']['N'])
        if date_granularity == "date":
            start = time.strftime('%Y-%m-%d', time.localtime(start))
            end = time.strftime('%Y-%m-%d', time.localtime(end))
        elif date_granularity == "hour": 
            start = time.strftime('%Y-%m-%d %H:%M', time.localtime(start))
            end = time.strftime('%Y-%m-%d %H:%M', time.localtime(end))
    elif internal_category == 'release':
        if date_granularity == "date":
            start = time.strftime('%Y-%m-%d', time.localtime(start))
        elif date_granularity == "hour": 
            start = time.strftime('%Y-%m-%d %H:%M', time.localtime(start))
    elif internal_category == 'deadline':  
        if date_granularity == "date":
            start = time.strftime('%Y-%m-%d', time.localtime(start))
        elif date_granularity == "hour": 
            start = time.strftime('%Y-%m-%d %H:%M', time.localtime(start))
    else:
        raise Exception("wrong internal category " + internal_category + " for the intent")
    
    # 2 this event's ['internal_category'] => "period" means the event has "start" and "end"
    if internal_category == 'period':
        speak_output += " is from " +\
                SSML_EMPHASIS_MODERATE_START + start + SSML_EMPHASIS_MODERATE_END +\
                    " until " +\
                        SSML_EMPHASIS_MODERATE_START + end + SSML_EMPHASIS_MODERATE_END
    elif internal_category == 'release':
        speak_output += " is on " +\
            SSML_EMPHASIS_MODERATE_START + start + SSML_EMPHASIS_MODERATE_END
    elif internal_category == 'deadline':
        speak_output += " is on " +\
            SSML_EMPHASIS_MODERATE_START + start + SSML_EMPHASIS_MODERATE_END
    else:
        raise Exception("wrong internal category " + internal_category + " for the intent")

    speak_output += SSML_END
    
    return speak_output


# def format_output(event_abb_name, start, end, date_granularity, )