#!/usr/bin/env python3
#-*- coding: utf-8 -*-


'''
1. 获取支持的tag，过滤自定义tag中不支持项目
2. 获取tag下博客总数
3. 获取博客订阅地址
4. 过滤
'''


### 过滤tag  

import requests
import time
from jinja2 import Template

HOST = "zhblogs.ohyee.cc"

EXPECT = [
    "运维", "Docker", "Linux", "DevOps", "容器",
    "软件工具", "软件", "教程", "资源",
    '''C/C++''', "Go", "Rust", "Python",
]

FILTER = [
    "长期不更", "文章较少", "非原创", "无内容", "敏感内容"
]

FEED_TEMPLATE='''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
    <body>
        <!-- category -->
        {% for category, items in data.items() %}
        <outline text="{{ category }}">
            {%for blog in items %}<outline text="{{blog[0]}}" type="rss" htmlUrl="{{blog[1]}}" xmlUrl="{{blog[2]}}"/>{% endfor %}
        </outline>
        {% endfor %}
    </body>
</opml>
'''

feed = set()
blog_with_category = {}

with requests.Session() as session:
    session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0'})
    resp = session.get(f"https://{HOST}/api/tags")
    try:
        tags = resp.json()['data']
        EXPECT = list(set(EXPECT) & set(tags))
        FILTER = list(set(FILTER) & set(FILTER))
    except:
        raise

    offset, size, total = 0, 10, 10
    category_blogs = []

    for tag in EXPECT:
        for offset in range(0, total, 10):
            try:
                resp = session.get(f"https://{HOST}/api/blogs",
                               params={'search':None, 'tags': tag, 'offset': offset, 'size': 10})
                data = resp.json()["data"]
                total, blogs = data["total"], data["blogs"]
                category_blogs.extend([(blog["name"], blog["url"], blog["feed"]) for blog in blogs if time.time() - blog["update_time"]<365*24*3600])
            except:
                raise

        blog_with_category[tag] = set(category_blogs) - feed
        feed = set(category_blogs) | feed

template = Template(FEED_TEMPLATE)
rendered = template.render(data=blog_with_category)

with open('feed.opml', 'w') as opml:
    opml.write(rendered)

