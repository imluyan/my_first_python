# -*- coding: utf-8 -*-
import urllib.request, urllib.error
from bs4 import BeautifulSoup
import ssl
import re
import sqlite3


conn = sqlite3.connect('models.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS Models')
cur.execute('CREATE TABLE Models (user_id TEXT PRIMARY KEY, name TEXT, '
            'info_card_url TEXT, album_list_url TEXT, the_album_url TEXT, the_pic_url TEXT)')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

page = 1
url = 'https://mm.taobao.com/json/request_top_list.htm?page=' + str(page)
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/57.0.2987.110 Safari/537.36'
header = {'User-Agent': user_agent}
try:
    request = urllib.request.Request(url=url, headers=header)
    response = urllib.request.urlopen(url=request, context=ctx)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup('a', 'lady-name')
    for tag in tags:
        info_http = tag.get('href', None)
        comp_info_http = 'https:' + info_http
        user_id = re.findall('[0-9]+', info_http)
        user_id = user_id[0]
        name = tag.contents[0]
        print(user_id, name)
        cur.execute('INSERT OR IGNORE INTO Models (user_id, name, info_card_url) VALUES (?, ?, ?)',
                    (user_id, name, comp_info_http))
except urllib.error as e:
    if hasattr(e, 'code'):
        print(e.code)
    if hasattr(e, 'reason'):
        print(e.reason)

conn.commit()
conn.close()