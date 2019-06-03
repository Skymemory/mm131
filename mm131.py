import argparse
import asyncio
import logging
import os
import re
import time

import aiohttp
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36')


class DownloadError(Exception):
    pass


async def fetch_url(session, url, *, allow_redirects=False, headers=None, timeout=None):
    logging.debug(f'{url} starting....')
    async with session.get(url, allow_redirects=allow_redirects, headers=headers,
                           timeout=timeout) as resp:
        if resp.status != 200:
            raise DownloadError(f'fetch {url} got unexpected status code {resp.status}')
        return await resp.content.read()


async def get_pictures(sesssion, category, index, base_dir):
    url = f'https://www.mm131.net/{category}/{index}.html'
    html = await fetch_url(sesssion, url, timeout=3)
    text = BeautifulSoup(html, 'html.parser').select_one('.content-page > span').get_text()
    pages = int(re.findall(r'\d+', text)[0])

    headers = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Referer': url,
    }
    success, fail = 0, 0

    tid2cxt = dict()
    tasks = list()
    for i in range(1, pages + 1):
        picture_url = f'https://img1.mm131.me/pic/{index}/{i}.jpg'
        tobj = asyncio.create_task(fetch_url(sesssion, picture_url, headers=headers, ))
        tasks.append(tobj)
        tid2cxt[id(tobj)] = (picture_url, i)

    done, _ = await asyncio.wait(tasks)
    # ensure dir exist
    curr_dir = os.path.join(base_dir, f'{index}')
    if not os.path.exists(curr_dir):
        os.mkdir(curr_dir)

    for f in done:
        try:
            content = f.result()
            picture_url, pid = tid2cxt[id(f)]
            with open(os.path.join(curr_dir, f'{pid}.jpg'), 'wb') as out:
                out.write(content)
            logging.debug(f'{picture_url} download done')
            success += 1
        except Exception:
            picture_url = tid2cxt[id(f)][0]
            logging.exception(f'handle {picture_url} got unexpected error.')
            fail += 1

    return success, fail


async def download(category, start, end, path):
    success, fail = 0, 0
    tasks = list()
    tid2ctx = dict()
    async with aiohttp.ClientSession() as session:
        for i in range(start, end):
            tt = asyncio.create_task(get_pictures(session, category, i, path, ))
            tid2ctx[id(tt)] = i
            tasks.append(tt)

        start_at = time.monotonic()
        done, _ = await asyncio.wait(tasks)
        for f in done:
            try:
                ss, ff = f.result()
                success += ss
                fail += ff
            except Exception:
                index = tid2ctx[id(f)]
                logging.exception(f'{index} got some error')

    logging.info("**************statistics************")
    logging.info(f"success:{success}\tfail:{fail}")
    logging.info(f"cost time:{time.monotonic() - start_at}")


def main():
    args = argparse.ArgumentParser(description="A picture downloader from mm131.")
    args.add_argument('-c', '--category', choices=['xinggan', 'qingchun', 'xiaohua', 'chemo', 'qipao', 'mingxing'],
                      default='xinggan', help='specify category(default xinggan)', )
    args.add_argument('-v', '--verbose', action='store_true', help='show verbose information')
    args.add_argument('-d', '--directory', default='/tmp', help='download directory')
    args.add_argument('range', metavar='s[,e]', help='range')

    parsed = args.parse_args()

    category = parsed.category
    path = parsed.directory
    rr = parsed.range
    if ',' not in rr:
        left = right = int(parsed.range)
    else:
        left, right = tuple(map(int, rr.split(',')))

    if parsed.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    asyncio.run(download(category=category, start=left, end=right + 1, path=path))


if __name__ == '__main__':
    main()
