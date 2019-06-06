# encoding: utf-8

"""
File: randomip.py
Author: Rock Johnson
"""
import requests, random, json
from txrequests.sessions import Session
from scrapy.selector import Selector
from twisted.internet import reactor, defer, task


class BaseIp:
    def __init__(self, scrapy=False, delay=0, page_size=None, concurrent=16, headers=None):
        """
        :param scrapy: 在scrapy中使用时为必填项
        :param delay: 下载延迟,同scrapy的DOWNLOAD_DELAY作用一样
        :param page_size: 抓取多少个页面,一般5个左右就够用了
        :param concurrent: 并发量,同scrapy的CONCURRENT_REQUESTS作用一样
        :param headers: 请求的参数
        """
        self.ips = []
        self.scrapy = scrapy
        self.delay = delay
        self.page_size = page_size
        self.concurrent = concurrent
        self.headers = headers
        self._over = False
        self._errcount = None
        self._get_url()
        defer.DeferredList([self._crawl_ip()])
        if not scrapy:
            reactor.run()

    def __len__(self):
        return len(self.ips)

    def _get_url(self):
        pass

    def _crawl_over(self, res):
        self._over = True

    @defer.inlineCallbacks
    def _crawl_ip(self):
       pass

    @defer.inlineCallbacks
    def _download_page(self, url):
        yield task.deferLater(reactor, self.delay, lambda: None)
        with Session() as session:
            def bg_cb(session, response):
                return response

            re = session.get(self._url + str(url), headers=self.headers, background_callback=bg_cb, timeout=5)
            content = yield re
        self._treq_download_page(content)

    @defer.inlineCallbacks
    def _treq_download_page(self, response, protocol=None):
        if response.status_code >= 200 and response.status_code < 300:
            args = (response.text, protocol) if protocol else (response.text,)
            self._treq_get_content(*args)
        yield None

    def _treq_get_content(self, content):
        pass

    def _get_type_ip(self, type):
        self._new_ips = []
        for ip in self.ips:
            if type.lower() == ip[:ip.index('://')].lower():
                self._new_ips.append(ip)
        if self._over and self._new_ips == [] and self.ips != []:
            raise ValueError('没有您需要的%s的代理,您可以换个代理模块或通过 page_size 属性增加获取的ip数量.' % type)

    def get_random_ip(self, type):
        """
        :param type: 协议的类型,根据自己抓取的网站来输入对应的类型.
        """
        if type.lower() != 'http' and type.lower() != 'https':
            raise KeyError('请输入正确的协议类型.(http, https不分大小写)')
        self._get_type_ip(type)
        if self.ips != []:
            while self._new_ips:
                res_ip = random.choice(self._new_ips)
                self.judge_ip(res_ip)
                if self._errcount != None and self._errcount == 0:
                    return res_ip

    def judge_ip(self, ip=None):
        http_url = '%s://httpbin.org/get'
        ips = [ip] if ip else self.ips
        has_new = True if ip else False

        defer.DeferredList([self._judge_ip(http_url % ip[:ip.index('://')], {ip[:ip.index('://')]: ip}, has_new) for ip in ips])

    @defer.inlineCallbacks
    def _judge_ip(self, url, proxies, has_new):
        ip = [ip for ip in proxies.values()][0]
        self._errcount = 0

        try:
            with Session() as session:
                def bg_cb(session, response):
                    return response

                re = session.get(self._url + str(url), headers=self.headers, background_callback=bg_cb, timeout=5)
                res = yield re
        except:
            self.delete_ip(ip, has_new)
            self._errcount += 1
        else:
            code = res.status_code
            if code >= 200 and code < 300:
                origin = json.loads(res.text)['origin'].split(', ')
                if origin[0] not in ip or origin[1] not in ip:
                    self.delete_ip(ip, has_new)
                    self._errcount += 1
            else:
                self.delete_ip(ip, has_new)
                self._errcount += 1

    def delete_ip(self, ip, has_new=False):
        # 删除错误的ip
        self.ips.remove(ip)
        if has_new:
            self._new_ips.remove(ip)
        if len(self) < 300:
            defer.DeferredList([self._crawl_ip()])


class XiciIp(BaseIp):
    # 获取西刺代理的ip池

    def __init__(self, scrapy=False, delay=0, page_size=None, concurrent=16, headers=None):
        BaseIp.__init__(self, scrapy=scrapy, delay=delay, page_size=page_size, concurrent=concurrent, headers=headers)

    def _get_url(self):
        self._url = 'https://www.xicidaili.com/nn/'

    @defer.inlineCallbacks
    def _crawl_ip(self):
        page_size = self.page_size
        if not page_size:
            html = requests.get(self._url, headers=self.headers)
            page_size = int(Selector(text=html.text).css(".pagination a:nth-child(13)::text").get(""))
        works = (self._download_page(url) for url in range(1, page_size + 1))
        coop = task.Cooperator()
        join = defer.DeferredList([coop.coiterate(works) for i in range(self.concurrent)])
        if self.scrapy:
            join.addCallback(self._crawl_over)
        else:
            join.addCallback(lambda _: reactor.stop())
        yield None

    def _treq_get_content(self, content):
        select = Selector(text=content)
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

    def __init__(self, scrapy=False, delay=0, page_size=None, concurrent=16, headers=None):
        BaseIp.__init__(self, scrapy=scrapy, delay=delay, page_size=page_size, concurrent=concurrent, headers=headers)

    def _get_url(self):
        self._url = 'https://www.kuaidaili.com/free/inha/'

    @defer.inlineCallbacks
    def _crawl_ip(self):
        page_size = self.page_size
        if not page_size:
            html = requests.get(self._url + '1', headers=self.headers)
            page_size = int(Selector(text=html.text).css("#listnav li:nth-child(9) a::text").get(""))
        works = (self._download_page(url) for url in range(1, page_size + 1))
        coop = task.Cooperator()
        join = defer.DeferredList([coop.coiterate(works) for i in range(self.concurrent)])
        if self.scrapy:
            join.addCallback(self._crawl_over)
        else:
            join.addCallback(lambda _: reactor.stop())
        yield None

    def _treq_get_content(self, content):
        select = Selector(text=content)
        all_trs = select.css("#list tbody tr")

        for tr in all_trs:
            all_texts = tr.css("td")
            ip = all_texts[0].css('::text').get().strip()
            port = all_texts[1].css('::text').get().strip()
            proxy_type = all_texts[3].css('::text').get().strip()

            ip = '%s://%s:%s' % (proxy_type.lower(), ip, port)
            if ip not in self.ips:
                self.ips.append(ip)


class DaxiangIp(BaseIp):
    # 获取大象代理ip池

    def __init__(self, data, scrapy=False, delay=0, headers=None):
        data['num'] = data['num'] if data.get('num') else 100
        data['format'] = 'json' if not data.get('format') else data.get('format')
        self._protocols = None

        if not isinstance(data, dict):
            raise TypeError('data类型为字典!')
        if not data.get('tid'):
            raise KeyError('tid为必须传入!')
        if data.get('protocol') and (data.get('protocol').lower() != 'http' and data.get('protocol').lower() != 'https'):
            raise KeyError('protocol必须为(http,https)或者不填该字段!')
        elif not data.get('protocol'):
            data['num'] = data['num'] / 2
            self._protocols = ['http', 'https']
        self._data = data
        BaseIp.__init__(self, scrapy=scrapy, delay=delay, page_size=1, headers=headers)

    def _get_url(self):
        self._url = 'http://tpv.daxiangdaili.com/ip/'

    @defer.inlineCallbacks
    def _crawl_ip(self):
        works = (self._download_page(url) for url in range(2 if self._protocols else 1))
        coop = task.Cooperator()
        join = defer.DeferredList([coop.coiterate(works) for i in range(self.concurrent)])
        if self.scrapy:
            join.addCallback(self._crawl_over)
        else:
            join.addCallback(lambda _: reactor.stop())
        yield None

    @defer.inlineCallbacks
    def _download_page(self, url):
        protocol = self._protocols[url] if self._protocols else self._data['protocol']
        yield task.deferLater(reactor, self.delay, lambda: None)
        with Session() as session:
            def bg_cb(sess, response):
                return response

            if self._protocols:
                self._data['protocol'] = protocol
            re = session.get(self._url, data=self._data, headers=self.headers, background_callback=bg_cb, timeout=5)
            content = yield re
        self._treq_download_page(content, protocol)

    def _treq_get_content(self, content, protocol):
        contents = json.loads(content)
        for ip in contents:
            new_ip = '%s://%s:%s' % (protocol, ip['host'], ip['port'])
            if new_ip not in self.ips:
                self.ips.append(new_ip)