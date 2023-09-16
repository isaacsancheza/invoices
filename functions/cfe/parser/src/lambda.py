from os import getenv
from typing import TypedDict

from cfdi import CFDI
from boto3 import resource
from requests import get
from lxml.html import fromstring


class Event(TypedDict):
    data: str
    provider: str
    object_key: str
    bucket_name: str


s3 = resource('s3')
bucket_name = getenv('BUCKET_NAME')


def handler(event: Event, _):
    assert event['provider'] == 'cfe'

    html = fromstring(event['data'])
    td = html.xpath('//td[contains(text(), "Número de Servicio")]')[0]
    table = td.xpath('./parent::tr/parent::tbody/parent::table')[0]
    service_id, pdf, xml = table.xpath('./tbody/tr[2]/td')

    service_id = int(service_id.text.strip())
    pdf = pdf.xpath('./a')[0].attrib.get('href')
    xml = xml.xpath('./a')[0].attrib.get('href')

    xml_response = get(xml)
    if not xml_response.ok:
        xml_response.raise_for_status()

    pdf_response = get(pdf)
    if not pdf_response.ok:
        pdf_response.raise_for_status()

    pdf = pdf_response.content
    xml = xml_response.content
    
    cfdi = CFDI(xml.decode('utf-8')) 
    prefix = f'invoices/cfe/{service_id}/{cfdi.fecha.year}/{02:cfdi.fecha.month}{cfdi.fecha.year}'
    bucket = s3.Bucket(bucket_name)
    
    bucket.put_object(Key=prefix + '.pdf', Body=pdf)
    bucket.put_object(Key=prefix + '.xml', Body=xml)
