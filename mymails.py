#!/usr/bin/python

import smtplib
import os
import configparser
from email.mime.text import MIMEText

config = configparser.ConfigParser()
config.read('config')

me = os.environ.get('me', config['DEFAULT']['me'])
you = os.environ.get('you', config['DEFAULT']['you'])
cc = os.environ.get('cc', config['DEFAULT']['cc'])
login = os.environ.get('login', config['DEFAULT']['login'])
pwd = os.environ.get('pwd', config['DEFAULT']['pwd'])
smtp = str(os.environ.get('smtp', config['DEFAULT']['smtp']))
port = int(os.environ.get('port', config['DEFAULT']['port']))

recepients = [you]
if cc is not None and cc != '':
    recepients.append(cc)

def send(msgtext):

    smtpObj = smtplib.SMTP_SSL(smtp, port)
    smtpObj.login(login, pwd)


    msg = MIMEText(msgtext.encode('utf-8'))
    #.encode('utf-8'))
    msg['Subject'] = 'OLX Notifications'
    msg['From'] = me
    msg['To'] = you


    smtpObj.sendmail(me, recepients, msg.as_string())

    
