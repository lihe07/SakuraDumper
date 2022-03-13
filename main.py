import time

import selenium.common.exceptions
from selenium import webdriver
import re
import requests
from bs4 import BeautifulSoup

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-u", "--url", dest="url", help="url to scrape", required=True)
args = parser.parse_args()

# driver = webdriver.PhantomJS("./phantomjs")
options = webdriver.FirefoxOptions()
options.add_argument('--headless')
driver = webdriver.Firefox(executable_path="./geckodriver", options=options)
driver.implicitly_wait(10)
driver.set_page_load_timeout(10)


def restart():
    global driver
    driver.quit()
    driver = webdriver.Firefox(executable_path="./geckodriver", options=options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(10)

def aria_down(url, filename):
    """
    调用Aria2c的jsonRPC下载链接
    :param url:
    :param filename:
    :return:
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "aria2.addUri",
        "params": [
            [url],
            {
                "out": filename
            }
        ],
        "id": "QXJpYU5nXzE2NDMyMDExMjJfMC43OTU3Mzk1OTU2OTAyNDkz"
    }
    requests.post("http://localhost:6800/jsonrpc", json=payload)


def fetch_multi_page(url):
    """
    处理多P的视频
    :param base_url:
    :return:
    """
    base_url = re.match("^((http://)|(https://))?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}(/)",
                        url).group()
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    play_urls = []
    for ele in soup.select("#playlist1 li > a"):
        # print(ele['href'])
        if len(re.findall("/play/.+.html", ele["href"])) > 0:
            if len(re.findall("https?://[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?",
                              ele["href"])) > 0:
                play_urls.append(ele["href"])
            else:
                play_urls.append(base_url + ele["href"].strip("/"))
    return play_urls


def fetch_single_page(base_url):
    while 1:
        try:
            driver.get(base_url)
            break
        except Exception as e:
            print(e)
            restart()
            time.sleep(1)

    frame_container = driver.find_element_by_id("playleft")

    frame = frame_container.find_element_by_tag_name("iframe")
    src = frame.get_attribute("src")

    name = driver.find_element_by_css_selector(".myui-player__data > h3:nth-child(1)").text

    if not src:
        print("src is empty", src)
        print(frame)
        raise Exception("Can't find src")

    driver.get(src)
    while 1:
        try:
            video = driver.execute_script("return lele.dp.video.src;")
            print(video)
            aria_down(video, name + ".mp4")
            break
        except selenium.common.exceptions.JavascriptException as e:
            print(e)
            time.sleep(0.3)


def main(url):
    if len(re.findall("/video/\d+.html", url)) > 0:
        # 处理多P的视频
        play_urls = fetch_multi_page(url)
        print(play_urls)
    else:
        play_urls = [url]
    for url in play_urls:
        fetch_single_page(url)


path = "lele.dp.video.src"

if __name__ == '__main__':
#     urls = [ 'http://www.857r.com/play/2333-1-7.html',
#             'http://www.857r.com/play/2333-1-8.html', 'http://www.857r.com/play/2333-1-9.html',
#             'http://www.857r.com/play/2333-1-10.html', 'http://www.857r.com/play/2333-1-11.html']
#     # main("http://www.857r.com/video/2333.html")
#     # fetch_single_page("http://www.857r.com/play/2333-1-1.html")
#     for url in urls:
#         fetch_single_page(url)
    main(args.url)
