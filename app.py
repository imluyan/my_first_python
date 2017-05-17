# -*- coding: utf-8 -*-
import sqlite3
import ssl
import urllib.request, urllib.error
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import os
import time

conn = sqlite3.connect('models.sqlite')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Models')
cur.execute('CREATE TABLE Models (user_id TEXT PRIMARY KEY, name TEXT, '
            'info_card_url TEXT, albums_list_url TEXT, the_albums_url TEXT, the_pics_url TEXT)')

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
    html = response.read().decode('gbk', errors='replace')
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

cur.execute('SELECT info_card_url FROM Models WHERE albums_list_url is NULL')
info_card_url_lst = cur.fetchall()
for info_card_url in info_card_url_lst:
    go_info_card_url = info_card_url[0]
    try:
        request = urllib.request.Request(url=go_info_card_url, headers=header)
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
                    # print(comp_album_list_url)
                    cur.execute('UPDATE Models SET albums_list_url = ? WHERE info_card_url = ?',
                                (comp_album_list_url, go_info_card_url))
            except:
                pass
    except urllib.error as e:
        if hasattr(e, 'code'):
            print(e.code)
        if hasattr(e, 'reason'):
            print(e.reason)

conn.commit()

cur.execute('SELECT albums_list_url FROM Models WHERE the_albums_url is NULL')
albums_list_url_lst = cur.fetchall()

driver = webdriver.PhantomJS()

for albums_list_url in albums_list_url_lst:
    go_albums_list_url = albums_list_url[0]
    try:
        driver.get(go_albums_list_url)
        element_lst = driver.find_elements_by_class_name('mm-first')
        the_albums_url_lst = list()
        for element in element_lst:
            the_albums_url_lst.append(element.get_attribute('href'))
        # print(the_albums_url_lst)
        the_albums_url_lst_str = ','.join(the_albums_url_lst)
        cur.execute('UPDATE Models SET the_albums_url = ? WHERE albums_list_url = ?',
                    (the_albums_url_lst_str, go_albums_list_url))
    except:
        pass

conn.commit()

cur.execute('SELECT the_albums_url, name FROM Models WHERE the_pics_url is NULL')
the_albums_url_names_lst = cur.fetchall()

for the_albums_url in the_albums_url_names_lst:
    name = the_albums_url[1]
    path = 'Models' + '/' + name.strip()
    isThere = os.path.exists(path)
    if not isThere:
        os.makedirs(path)
    print(name)
    go_the_albums_url_str = the_albums_url[0]
    go_the_albums_url_lst = go_the_albums_url_str.split(',')
    the_pics_url_lst = list()
    for go_the_album_url in go_the_albums_url_lst:
        try:
            print(go_the_album_url)
            driver.implicitly_wait(5)
            driver.get(go_the_album_url)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            element_lst = list()
            comp_the_pic_url = None
            tags = soup.find_all('div', {'class': 'mm-photoimg-area'})
            for tag in tags:
                try:
                    the_pic_url = tag.contents[1]['href']
                    comp_the_pic_url = 'https:' + the_pic_url
                    element_lst.append(comp_the_pic_url)
                except:
                    pass
            for element in element_lst:
                try:
                    driver.implicitly_wait(0)
                    driver.get(element)
                    the_pic_class_lst = driver.find_elements_by_class_name('mm-p-img-panel')
                    for the_pic_class in the_pic_class_lst:
                        the_pic_tag = the_pic_class.find_element_by_tag_name('img')
                        the_pic = the_pic_tag.get_attribute('src')
                        the_pics_url_lst.append(the_pic)
                        request = urllib.request.Request(url=the_pic, headers=header)
                        response = urllib.request.urlopen(url=request, context=ctx)
                        data = response.read()
                        the_album_id = re.findall('album_id=([0-9]\S+?)&', go_the_album_url)
                        the_album_id = the_album_id[0]
                        print(the_album_id)
                        path = 'Models' + '/' + name.strip() + '/' + str(the_album_id).strip()
                        isThere = os.path.exists(path)
                        if not isThere:
                            os.makedirs(path)
                        file_name = re.findall('/([A-Z]\S+?.jpg)', the_pic)
                        file_name = file_name[0]
                        print(file_name)
                        f = open(path + '/' + file_name, 'wb')
                        f.write(data)
                        f.close()
                except:
                    pass
        except:
            pass
    the_pics_url_lst_str = ','.join(the_pics_url_lst)
    cur.execute('UPDATE Models SET the_pics_url = ? WHERE the_albums_url = ?',
                (the_pics_url_lst_str, go_the_albums_url_str))

driver.quit()

conn.commit()

conn.close()
