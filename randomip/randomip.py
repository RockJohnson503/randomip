# encoding: utf-8

"""
File: randomip.py
Author: Rock Johnson
"""
import requests, random
from treq import request, content
from scrapy.selector import Selector
from twisted.internet import reactor, defer, task


class BaseIp:
    def __init__(self, spider=None, delay=0, page_size=None, concurrent=16, headers=None):
        """
        :param spider: 在scrapy中使用时为必填项
        :param delay: 下载延迟,同scrapy的DOWNLOAD_DELAY作用一样
        :param page_size: 抓取多少个页面,一般5个左右就够用了
        :param concurrent: 并发量,同scrapy的CONCURRENT_REQUESTS作用一样
        :param headers: 请求的参数
        """
        self.ips = []
        self.spider = spider
        self.delay = delay
        self.page_size = page_size
        self.concurrent = concurrent
        self.headers = headers
        self._get_url()
        defer.DeferredList([self._crawl_ip()])
        if not spider:
            reactor.run()

    def _get_url(self):
        pass

    @defer.inlineCallbacks
    def _crawl_ip(self):
       pass

    @defer.inlineCallbacks
    def _treq_crawl_ip(self, url):
        yield task.deferLater(reactor, self.delay, lambda: None)
        re = request('GET', self._url + str(url), headers=self.headers)
        re.addCallback(self._treq_download_page)
        yield re

    @defer.inlineCallbacks
    def _treq_download_page(self, response):
        if response.code >= 200 and response.code < 300:
            con = content(response)
            con.addCallback(self._treq_get_content)
            yield con

    def _treq_get_content(self, content):
        pass

    def _get_type_ip(self, type):
        self._new_ips = []
        for ip in self.ips:
            if type.lower() == ip[:ip.index('://')].lower():
                self._new_ips.append(ip)
        if self._new_ips == [] and self.ips != []:
            raise ValueError('没有您需要的%s的代理,您可以换个代理模块或通过 page_size 属性增加获取的ip数量.' % type)

    def get_random_ip(self, type):
        """
        :param type: 协议的类型,根据自己抓取的网站来输入对应的类型.
        """
        if type.lower() != 'http' and type.lower() != 'https':
            raise KeyError('请输入正确的协议类型.(http, https不分大小写)')
        self._get_type_ip(type)
        if self.ips != []:
            return random.choice(self._new_ips)

    def judge_ip(self):
        http_url = 'https://www.baidu.com'
        errcount = 0

        for ip in self.ips:
            try:
                proxy_dict = {
                    ip[:ip.index('://')]: ip
                }
                res = requests.get(http_url, proxies=proxy_dict, timeout=2)
            except:
                self.delete_ip(ip)
                errcount += 1
            else:
                code = res.status_code
                if code >= 200 and code < 300:
                    continue
                else:
                    self.delete_ip(ip)
                    errcount += 1
        return errcount

    def delete_ip(self, ip):
        # 删除错误的ip
        self.ips.remove(ip)


class XiciIp(BaseIp):
    # 获取西刺代理的ip池

    def __init__(self, spider=None, delay=0, page_size=None, concurrent=16, headers=None):
        BaseIp.__init__(self, spider=spider, delay=delay, page_size=page_size, concurrent=concurrent, headers=headers)

    def _get_url(self):
        self._url = 'https://www.xicidaili.com/nn/'

    @defer.inlineCallbacks
    def _crawl_ip(self):
        page_size = self.page_size
        if not page_size:
            html = requests.get("https://www.xicidaili.com/nn", headers=self.headers)
            page_size = int(Selector(text=html.text).css(".pagination a:nth-child(13)::text").get(""))
        works = (self._treq_crawl_ip(url) for url in range(1, page_size + 1))
        coop = task.Cooperator()
        join = defer.DeferredList([coop.coiterate(works) for i in range(self.concurrent)])
        if self.spider:
            join.addCallback(lambda _: None)
        else:
            join.addCallback(lambda _: reactor.stop())
        yield None

    def _treq_get_content(self, content):
        select = Selector(text=content.decode())
        all_trs = select.css("#ip_list tr")

        for tr in all_trs[1:]:
            all_texts = tr.css("td")
            ip = all_texts[1].css('::text').get().strip()
            port = all_texts[2].css('::text').get().strip()
            proxy_type = all_texts[5].css('::text').get().strip()
            time = all_texts[6].css('.bar::attr(title)').get()
            time = float(time.replace('秒', ''))

            ip = '%s://%s:%s' % (proxy_type.lower(), ip, port)
            if time < 1 and ip not in self.ips:
                self.ips.append(ip)


class KuaiIp(BaseIp):
    # 获取快代理的ip池

    def __init__(self, spider=None, delay=0, page_size=None, concurrent=16, headers=None):
        BaseIp.__init__(self, spider=spider, delay=delay, page_size=page_size, concurrent=concurrent, headers=headers)

    def _get_url(self):
        self._url = 'https://www.kuaidaili.com/free/inha/'

    @defer.inlineCallbacks
    def _crawl_ip(self):
        # 爬取西刺的ip代理
        page_size = self.page_size
        if not page_size:
            html = requests.get("https://www.kuaidaili.com/free/inha/1/", headers=self.headers)
            page_size = int(Selector(text=html.text).css("#listnav li:nth-child(9) a::text").get(""))
        works = (self._treq_crawl_ip(url) for url in range(1, page_size + 1))
        coop = task.Cooperator()
        join = defer.DeferredList([coop.coiterate(works) for i in range(self.concurrent)])
        if self.spider:
            join.addCallback(lambda _: None)
        else:
            join.addCallback(lambda _: reactor.stop())
        yield None

    def _treq_get_content(self, content):
        select = Selector(text=content.decode())
        all_trs = select.css("#list tbody tr")

        for tr in all_trs:
            all_texts = tr.css("td")
            ip = all_texts[0].css('::text').get().strip()
            port = all_texts[1].css('::text').get().strip()
            proxy_type = all_texts[3].css('::text').get().strip()

            ip = '%s://%s:%s' % (proxy_type.lower(), ip, port)
            if ip not in self.ips:
                self.ips.append(ip)