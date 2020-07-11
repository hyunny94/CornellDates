import csv
import boto3
from utils import get_default_academic_year
import datetime

def read_csv_into_dictlst():
    with open('CornellDates - Events.csv') as f:
        a = [{k: v for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
        return a

def import_to_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

    table = dynamodb.Table('CornellDates' + get_default_academic_year())

    dict_lst = read_csv_into_dictlst()

    with table.batch_writer() as batch:
        for item in dict_lst:
    
            # Add non-nullable fields
            dict = {
                'event_org_name': item['event_org_name'],
                'category': item['category'],
                'semester': item['semester'],
                'academic_year': item['academic_year'],
                'event_abb_name': item['event_abb_name'],
                'internal_category': item['internal_category'],
                'grade': item['grade'].split(','),
                'date_granularity': item['date_granularity']
            } 

            # Handle nullable fields
            start = item['start']
            end = item['end']
            event_verb = item['event_verb']
            # start is sort-key thus required.
            if start != '':
                dict['start'] = convert_to_epoch_time(start)
                if end != '':
                    dict['end'] = convert_to_epoch_time(end)
            else:
                dict['start'] = convert_to_epoch_time(end)
            
            if event_verb != '':
                dict['event_verb'] = event_verb
                
            batch.put_item(
                Item = dict
            )

'''
time is a string in the following format
"2020,8,10,23,59" 
returns 1597118340
'''
def convert_to_epoch_time(time):
    times = time.split(',')
    year = int(times[0])
    month = int(times[1])
    date = int(times[2])
    hour = int(times[3])
    minute = int(times[4])
    epoch_time = int(datetime.datetime(year, month, date, hour, minute).timestamp())
    return epoch_time

def update_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('CornellDates' + get_default_academic_year())
    dict_lst = read_csv_into_dictlst()

    with table.batch_writer() as batch:
        for item in dict_lst:
            event_abb_name = item['event_abb_name']
            start = item['start'] if item['start'] != '' else item['end']
            start = convert_to_epoch_time(start)
            
            batch.update_item(
                Key = {
                    'event_abb_name': event_abb_name,
                    'start': start
                },
                UpdateExpression='SET end = :val1',
                ExpressionAttributeValues={
                    ':val1': "CHANGE ME~~~~"
                })

if __name__ == "__main__":
    import_to_dynamodb()