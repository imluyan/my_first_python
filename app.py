# -*- coding: utf-8 -*-
import sqlite3
import ssl
import urllib.request, urllib.error
from bs4 import BeautifulSoup
import re

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

cur.execute('SELECT info_card_url FROM Models WHERE album_list_url is NULL')
info_url_lst = cur.fetchall()
for info_url in info_url_lst:
    go_info_url = info_url[0]
    try:
        request = urllib.request.Request(url=go_info_url, headers=header)
        response = urllib.request.urlopen(url=request, context=ctx)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup('a')
        for tag in tags:
            try:
                content = tag.contents[0]
                if content == '相册':
                    album_list_url = tag.get('href', None)
                    comp_album_list_url = 'https:' + album_list_url
                    print(comp_album_list_url)
                    cur.execute('UPDATE Models SET album_list_url = ? WHERE info_card_url = ?',
                                (comp_album_list_url, go_info_url))
            except:
                pass
    except urllib.error as e:
        if hasattr(e, 'code'):
            print(e.code)
        if hasattr(e, 'reason'):
            print(e.reason)

conn.commit()

cur.execute('SELECT album_list_url FROM Models WHERE the_album_url is NULL')
the_album_url = cur.fetchall()
for album_url in the_album_url:
    go_album_url = album_url[0]
    try:
        request = urllib.request.Request(url=go_album_url, headers=header)
        response = urllib.request.urlopen(url=request, context=ctx)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        print(soup.prettify())
    except urllib.error as e:
        if hasattr(e, 'code'):
            print(e.code)
        if hasattr(e, 'reason'):
            print(e.reason)

conn.close()
