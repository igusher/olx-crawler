#!/usr/bin/python
import sys
import os
from logging.handlers import TimedRotatingFileHandler
import urllib
import time
import string
import mymails
import json
import codecs
import requests
from HTMLParser import HTMLParser
import re
import sqlalchemy
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime 
import logging

format_str = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
formatter = logging.Formatter(format_str)
logging.basicConfig(level=logging.INFO, format=format_str)
handler = TimedRotatingFileHandler("olx.log", when="H", interval=1, backupCount=5)
handler.setFormatter(formatter)
logger = logging.getLogger("OLXMonitor")
logger.addHandler(handler)

Base = declarative_base()
# create a subclass and override the handler methods
def send_email_notifications(offers):
    offers_str = map(lambda x: x['ad_price'] + ' ' + x['currency'] + '\n' + x['title'] + '\n' + x['time'] + '\nBomber:\n' + string.join(map(lambda b: str(b), x['bombers']),'\n').decode('utf-8') + '\n' + x['url'], offers)
    msg = string.join(offers_str, "\n\n")
    mymails.send("Hi,\n\n" + msg)

host = os.environ.get("PG_HOST", 'localhost')
logger.info("Host = " + host)
url = sqlalchemy.engine.url.URL('postgresql+psycopg2', 'postgres', None, host, None, 'postgres')
engine = create_engine(url, echo=False)
connection = engine.connect()
Session = sessionmaker(bind=engine)

class Offer(Base):
    __tablename__ = 'offers'
    olxid = Column(String, primary_key=True)
    title = Column(String)
    url = Column(String)
    time = Column(String)
    phone = Column(String)
    query_date = Column(DateTime)
    details = Column(String)
    ad_price = Column(String)
    currency = Column(String)
    bomber = Column(String)

    def __repr__(self):
      return   'Offer: (' + str({'olxid': self.olxid})


Base.metadata.create_all(engine)


#o = Offer(olxid='abs', url='url1', time = 't', phone='ph')

session = Session()
#session.add(o)
#session.commit()

q = session.query(Offer).filter(Offer.olxid == 'abs')
#print session.query(q.exists()).scalar()

def store_offer(offer):
 #   session = Session()
    session.add(offer)
    session.commit()

def already_seen(olxid):
  #  session = Session()

    q = session.query(Offer).filter(Offer.olxid == olxid)
    return session.query(q.exists()).scalar()
    

#sys.exit(1)



class MyHTMLParser(HTMLParser):

    def init(self):
        self.count = 0
        self.offers = []
        self.counters = []
        self.cur = 0
        self.start_handlers = [self.search_offers_table, self.search_offer, self.search_details_url, self.search_title, self.null]
        self.data_handlers = [self.null]
 #       self.end_handlers = [self.null, self.found_offers_table, self.found_offer, self.found_details_url]

    def search_offers_table(self, tag, attrs):
        if tag == 'table':
            if 'offers' in dict(attrs)['class'] and 'offers--top' not in dict(attrs)['class'] :
                return True
        return False

    def search_offer(self, tag, attrs):
        if tag == 'table':
            if 'data-id' in dict(attrs):
                self.offers.append({})
                classes = dict(attrs)['class'].split(' ')
                classes = filter(lambda x: x.startswith('ad_id'), classes)
                if len(classes) > 0:
                    self.offers[-1]['id'] = classes[0][5:]
                return True
        return False

    def search_details_url(self, tag, attrs):
        if tag == 'a':
            if 'detailsLink' in dict(attrs)['class']:
                self.offers[-1]['url'] = dict(attrs)['href']
                return True
        return False
    
    def search_title(self, tag, attrs):
        if tag == 'strong':
            self.data_handlers.append(self.handle_title)
            return True
        return False

    def end_offer(self, tag):
        pass
    

    def handle_starttag(self, tag, attrs):
        if self.start_handlers[self.cur](tag, attrs):
            self.counters.append(self.count)
            self.cur = self.cur + 1;
            self.count = 0
        else:
            self.count  = self.count + 1

    def null(self, *kwargs):
        return False

    def handle_endtag(self, tag):
        if self.count == 0 and self.cur > 0:
            self.cur = self.cur - 1
            self.count = self.counters.pop()
        else:
            self.count = self.count - 1
    
    def handle_title(self, data):
        self.offers[-1]['title'] = data
        self.data_handlers.pop()


    def handle_data(self, data):
        self.data_handlers[-1](data)

def get_phone(olxid, phone_token, headers, referer):
    reqH = string.join((map(lambda kv: (kv[0].strip() + "="+  kv[1].strip()) ,filter(lambda x: len(x) == 2 and x[0].strip() not in ['path', 'expires','Max-Age', 'domain'] ,map(lambda x : x.split("="), re.split(";|,",headers['set-cookie']))))),"; ")
    referer = referer[:referer.find("html")+4]
    reqHeaders = {'Cookie': reqH, 'Referer': referer}
    phone_url = "https://www.olx.ua/ajax/misc/contact/phone/{}/?pt={}".format(olxid, phone_token)
    logger.info(phone_url)
    response = requests.get(phone_url, headers=reqHeaders)
    if response.status_code == 200:
        js = response.json()
        if 'value' in js:
            val = js['value'].decode('utf-8')
            if 'span' in val:
                p = re.compile('(<span class="block">)([^<]*)(</span>)')
                matches = p.findall(val)
                phones = map(lambda x: x[1], matches)
                return phones
            else:
                return [val]
    return []
 

def get_time(url):
    data = str(response.content)
    return get_time_page(get_page(url))

def get_time_page(page):
    p = re.compile(" \d\d:\d\d, \d\d? \W* \d\d\d\d, ")
    m = p.search(page)
    return m.group() if m is not None else "-"
    

def get_details(url):
    data = str(response.content)
    return get_details_page(get_page(url))

def get_details_page(page):
    p = re.compile("(GPT.targeting = )(.*)")
    m = p.search(page)
    return m.group(2)[:-1] if m is not None else None

def get_page(url):
    response = requests.get(url)
    return (response.text, response.headers) if response.status_code == 200 else "Failed to load: " + str(url)



def query():
    params = {
        'search[city_id]': '62',
        'search[region_id]': '9',
        'search[dist]': '0',
        'search[district_id]': '0',
        'search[category_id]': '13',
        'search[private_business]': 'private'
    }

    response = requests.post("https://www.olx.ua/ajax/search/list/", data=params) 
    html = str(response.content).replace("&quot", "\"").replace("&amp","&")
    return html, response.headers

class Bomber(object):
    def __init__(self, phone, state, ad_count, url):
        self.phone = phone.encode('utf-8')
        self.state = state.strip().encode('utf-8')
        self.ad_count = str(ad_count).encode('utf-8')
        self.url = url

    def to_json(self):
        return json.dumps({
                'phone': self.phone,
                'state': self.state,
                'ad_count': self.ad_count,
                'url': self.url
            })

    def __repr__(self):
        return "{}: {}. Total {} ad. Check: {}".format(self.phone, self.state, self.ad_count, self.url)
    
    def __str__(self):
        return "{}: {}. Total {} ad. Check: {}".format(self.phone, self.state, self.ad_count, self.url)
    

def get_bomber_status(phone):
    url = "https://ua.m2bomber.com/phone/{}".format(phone)
    r = requests.get(url)
    page = r.text if r.status_code == 200 else ""
    bomber_state = "UNKNOWN"
    ad_count = 0
    if 'phone-type' in page:
        p = re.compile('(<h2 class="phone-type">\s*)([^<]*)(\s*</h2>)')
        bomber_state = p.search(page).group(2)
        ad_count = page.count("row object-list")
    
    return Bomber(phone, bomber_state, ad_count, r.url)

def get_phone_token(page):
    p = re.compile("var phoneToken = '([a-z0-9]*)'")
    m = p.search(page)
    return m.group(1) if m is not None else "-"
    


while(True):
	try:    
	    parser = MyHTMLParser()
	    parser.init()
	    html, headers = query()
	    parser.feed(html)
	    parser.offers = filter(lambda x: 'id' in x and 'title' in x and not already_seen(x['id']), parser.offers )
	    for o in parser.offers:
	        page, headers = get_page(o['url'])
                phone_token = get_phone_token(page)
	        o['phone'] = get_phone(o['id'], phone_token, headers, o['url'])
	        o['time'] = get_time_page(page)
	        o['details'] = get_details_page(page)
	        details = json.loads(o['details'])
	        o['ad_price'] = details['ad_price'] if 'ad_price' in details else '-'#.encode('utf-8')
	        try:
	            o['title'] = details['ad_title'].replace("&quot", "\"").replace("&amp","&")
	        except:
	            o['title'] = '-'

	        o['currency'] = details['currency'] if 'currency' in details else "-"

	        logger.info(o['id'])
	        logger.info(o['title'])
	        logger.info(o['time'])
	        logger.info(o['ad_price'])
	        logger.info(o['phone'])
	        logger.info(o['currency'])
                
                o['bombers'] = map(lambda p: get_bomber_status(p), o['phone'])
                bomber_str = json.dumps(map(lambda b: b.__dict__, o['bombers']))
	        logger.info(len(o['bombers']))
                logger.info(bomber_str)
	        logger.info(string.join(map(lambda x: str(x), o['bombers']), '\n'))

	        offer = Offer(olxid=o['id'], 
	                    title=o['title'], 
	                    url=o['url'], 
	                    time=o['time'], 
	                    phone=string.join(o['phone'], ","), 
	                    query_date=datetime.now(), 
	                    details=o['details'], 
	                    ad_price=o['ad_price'], 
	                    currency=o['currency'],
                            bomber=bomber_str)
	        store_offer(offer)
	        
	    
	        
	    if(len(parser.offers) > 0):
	        logger.info("Send {} offers".format(len(parser.offers)))
	        send_email_notifications(parser.offers)
	    time.sleep(60)
	except Exception as e:
	    logger.exception(e)
	    time.sleep(60)
    
