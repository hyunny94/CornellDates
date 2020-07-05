import csv
import boto3

def read_csv_into_dictlst():
    with open('CornellDatesTest - Events.csv') as f:
        a = [{k: v for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
        print(a)
        return a

def import_to_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

    table = dynamodb.Table('CornellDates')

    dict_lst = read_csv_into_dictlst()

    with table.batch_writer() as batch:
        for item in dict_lst:
            batch.put_item(
                Item={
                    'category': item['category'],
                    'subcategory': item['subcategory'],
                    'event': item['event'],
                    'event_abb_name': item['event_abb_name'],
                    'event_verb': item['event_verb'],
                    'semester': item['semester'],
                    'academic_year': item['academic_year'],
                    'grade': item['grade'].split(','),
                    'location': item['location'].split(','),
                    'start': int(item['start']),
                    'end': int(item['end']),
                    'date_granularity': item['date_granularity']
                }
            )

if __name__ == "__main__":
    import_to_dynamodb()