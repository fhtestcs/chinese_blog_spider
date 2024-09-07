#!/usr/bin/env python3
#-*- coding: utf-8 -*-


'''
1. 获取支持的tag，过滤自定义tag中不支持项目
2. 获取tag下博客总数
3. 获取博客订阅地址
4. 过滤
'''


### 过滤tag  

import time
from jinja2 import Template
import asyncio
import aiohttp

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


async def fetch(session, tag):
    category_blogs = []
    offset, total = 0, 10
    for offset in range(0, total, 10):
        async with session.get(f"https://{HOST}/api/blogs", params={'search':'', 'tags': tag, 'offset': offset, 'size': 10}) as response:
            data = await response.json()
            total, blogs = data["data"]["total"], data["data"]["blogs"]
            category_blogs.extend([(blog["name"], blog["url"], blog["feed"]) for blog in blogs if time.time() - blog["update_time"]<365*24*3600 and not set(blog["tags"]) & set(FILTER)])
    return category_blogs


async def main():
    feed = set()
    global EXPECT, FILTER
    blog_with_category = {}
    async with aiohttp.ClientSession() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0'})
        try:
            resp = await session.get(f"https://{HOST}/api/tags")
            data = await resp.json()
            tags = data['data']
            EXPECT = list(set(EXPECT) & set(tags))
            FILTER = list(set(FILTER) & set(FILTER))
        except:
            raise
        tasks = [fetch(session, tag) for tag in EXPECT]

        category_blogs = await asyncio.gather(*tasks)
        for tag, blogs in zip(EXPECT, category_blogs):
            blog_with_category[tag] = list(set(blogs) - feed)
            feed = feed | set(blogs)
    
    template = Template(FEED_TEMPLATE)
    rendered = template.render(data=blog_with_category)
    with open('feed.opml', 'w') as opml:
        opml.write(rendered)

if __name__ == '__main__':
    asyncio.run(main())

