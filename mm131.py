import argparse
import asyncio
import itertools
import logging
import os
import re
import time

import aiohttp
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'


async def fetch_and_save(session, url, headers, path):
    logging.debug('Downloading {}...'.format(url))
    resp = await session.get(url, allow_redirects=False, headers=headers)
    content = await resp.content.read()
    with open(path, 'wb') as out:
        out.write(content)


async def crawler(session, category, index, save_dir):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    base_url = 'http://www.mm131.com/{}/{}.html'.format(category, index)
    success, fail = 0, 0
    resp = await session.get(base_url, allow_redirects=False)
    # ignore unexpected error
    if resp.status != 200:
        logging.warning('{} got status {}, ignore it.'.format(base_url, resp.status))
        return 0, 0

    html = await resp.content.read()
    text = BeautifulSoup(html, 'html.parser').select_one('.content-page > span').get_text()
    pages = int(re.findall(r'\d+', text)[0])

    tasks = []
    urls = []
    for i in range(1, pages + 1):
        path = os.path.join(save_dir, '{}.jpg'.format(i))
        pic_url = 'http://img1.mm131.me/pic/{}/{}.jpg'.format(index, i)
        headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': 'http://www.mm131.com/{}/{}{}.html'.format(category, index, "1" if i == 1 else "_{}".format(i))
        }

        urls.append(pic_url)
        tasks.append(fetch_and_save(session, pic_url, headers, path))

    rs = await asyncio.gather(*tasks, return_exceptions=True)

    for pic_url, result in zip(urls, rs):
        if isinstance(result, Exception):
            logging.error('{} got unexpected error {}'.format(pic_url, result))
            fail += 1
        else:
            success += 1

    return success, fail


async def download(category, start, end, save_dir):
    start_at = time.time()
    success, fail = 0, 0
    it = iter(range(start, end))
    async with aiohttp.ClientSession() as session:
        while 1:
            chunk = tuple(itertools.islice(it, 200))
            if not chunk:
                break

            contexts = []
            tasks = []
            for elem in chunk:
                folder = os.path.join(save_dir, str(elem))

                contexts.append(elem)
                tasks.append(crawler(session, category, elem, folder))

            rs = await asyncio.gather(*tasks, return_exceptions=True)
            for index, result in zip(contexts, rs):
                if isinstance(result, Exception):
                    logging.error('{}/{} got unexpected error {}'.format(category, index, result))
                else:
                    s, f = result
                    success += s
                    fail += f

    logging.info('-' * 20 + 'Statistics' + '-' * 20)
    logging.info('Success:{}\t\tFail:{}'.format(success, fail))
    logging.info('Cost time:{}'.format(time.time() - start_at))


def main():
    args = ARGS.parse_args()
    rr = list(map(int, args.r.split(',')))
    if len(rr) == 1:
        start = end = rr[0]
    else:
        start, end = rr

    logging.getLogger().setLevel(args.level)

    asyncio.run(download(args.c, start, end + 1, args.d))


ARGS = argparse.ArgumentParser(description='Picture downloader for mm131')
ARGS.add_argument('-c', metavar='CATEGORY',
                  choices=['xinggan', 'qingchun', 'xiaohua', 'chemo', 'qipao', 'mingxing'],
                  default='xinggan', help='Specify which category to download(default xinggan)')
ARGS.add_argument('-r', metavar='RANGE', help='Specify first index,format: start[,end]')
ARGS.add_argument('-d', metavar='DIRECTORY', help='Save directory(default /tmp)', default='/tmp')
ARGS.add_argument('--level', help='Logging level', default=logging.INFO, type=int)

if __name__ == '__main__':
    main()
