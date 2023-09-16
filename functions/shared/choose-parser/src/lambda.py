from email import message_from_bytes
from email.message import EmailMessage

from boto3 import resource
from aws_lambda_powertools.utilities.data_classes import event_source, S3Event


class NotCFE(Exception):
    pass


def is_cfe(message: EmailMessage, bucket_name: str, object_key: str) -> dict[str, str]:
    for part in message.walk():
        if part.get_content_type == 'text/html':
            html = part.get_payload(decode=True).decode('utf-8')
            if 'CFEMail' in html:
                return {
                    'data': html,
                    'provider': 'cfe',
                    'object_key': object_key,
                    'bucket_name': bucket_name,
                }
    raise NotCFE()


s3 = resource('s3')
parsers = (
    (is_cfe, NotCFE,),
)


@event_source(data_class=S3Event)
def handler(event: S3Event, _):
    pairs = []
    bucket_name = event.bucket_name
    
    for record in event.records:
        object_key = record.s3.get_object.key
        
        object = s3.Object(bucket_name, object_key)
        message = message_from_bytes(object.get().body())
        
        for parser, exception in parsers:
            try:
                pairs.append(parser(message, bucket_name, object_key))
                break
            except exception():
                pass
    
    return pairs
