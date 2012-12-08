#!/usr/bin/env python

# Copyright (c) 2012, Kamal Bin Mustafa <kamal.mustafa@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted, provided 
# that the above copyright notice and this permission notice appear
# in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM 
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.

import os
import sys
import email
import sqlite3
import smtplib
import datetime
import logging
import ConfigParser

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import timedelta

HERE = os.path.abspath(os.path.dirname(__file__))

log_file = os.path.join(HERE, 'log.txt')
logging.basicConfig(filename=log_file, level=logging.DEBUG)
logging.info('Start')

config = ConfigParser.ConfigParser()
config.read(os.path.join(HERE, 'config.ini'))

conn = sqlite3.connect(os.path.join(HERE, 'data.db'))
conn.row_factory = sqlite3.Row

from_addr = config.get('general', 'from_address')
smtp_host = config.get('smtp', 'host') or 'localhost'
smtp_username = config.get('smtp', 'username') or None
smtp_password = config.get('smtp', 'password') or None
smtp_port = config.getint('smtp', 'port') or 25

RULES = {
    '1day': timedelta(days=1),
    '1week': timedelta(days=7),
    '1month': timedelta(days=30),
    '1hour': timedelta(minutes=60),
    '10minutes': timedelta(minutes=10),
    '5minutes': timedelta(minutes=5),
}

for i in xrange(1, 30):
    RULES['%dday' % i] = timedelta(days=i)

def add_reminder(message_id, subject, sender, remind_at, email=''):
    params = {
        'id': message_id,
        'subject': subject,
        'email': email,
        'sender': sender,
        'remind_at': remind_at,
        'sent': False,
    }
    conn.execute("INSERT INTO reminder (id, subject, email, sender, remind_at, sent) "
                 "VALUES (:id, :subject, :email, :sender, :remind_at, :sent)", params)
    conn.commit()

def delete_reminder(message_id):
    conn.execute("DELETE FROM reminder where id = ?", (message_id,))
    conn.commit()

def send_reminder():
    logging.info('Send start ...')
    time_end = datetime.datetime.now()
    time_start = time_end - timedelta(hours=1)
    params = {
        'time_start': time_start,
        'time_end': time_end,
    }
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminder WHERE sent = 0 AND remind_at "
                   "BETWEEN :time_start AND :time_end", params)

    s = smtplib.SMTP_SSL(smtp_host, smtp_port)
    s.set_debuglevel(True)
    s.login(smtp_username, smtp_password)
    for row in cursor.fetchall():
        logging.info('Sending to ' + row['sender'])
        msg = email.message_from_string('Follow up for ' + row['subject'])
        msg['From'] = from_addr
        msg['To'] = row['sender']
        msg['In-Reply-To'] = row['id']
        msg['References'] = row['id']
        msg['Subject'] = 'Re: ' + row['subject']
        to_addr = email.utils.parseaddr(row['sender'])[1]
        s.sendmail(from_addr, to_addr, msg.as_string())
        delete_reminder(row['id'])

    print time_start, time_end
    logging.info('Sending done')

def receive_email():
    logging.info('Received email')
    try:
        msg = email.message_from_string(sys.stdin.read())
        msg_id = msg.get('Message-ID')
        sender = msg.get('From')
        subject = msg.get('Subject')
        to = msg.get('To')
        body = msg.as_string()
        delta = to.split('@')[0]
        remind_at = datetime.datetime.now() + RULES[delta]
        add_reminder(msg_id, subject, sender, remind_at, body)
        logging.info('DONE')
    except Exception as e:
        logging.info(str(e))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        opt = sys.argv[1]
        if opt == 'send':
            send_reminder()
    else:
        receive_email()
