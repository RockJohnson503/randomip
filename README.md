# Randomip

randomip是一个随机ip代理池,可以很好的在scrapy中使用,其中有西刺代理(XiciIp)以及快代理(KuaiIp)模块.

个人推荐使用西刺代理,因为西刺代理里的ip速度普遍比快代理的速度快.

快速使用
-------

1. 安装randomip.

    ```
    cd randomip

    python setup.py sdist

    pip install dist/randomip-(版本号).tar.gz(.zip)
    ```

2. 使用randomip.

    ```
    >>> from randomip.randomip import XiciIp

    >>> ip = XiciIp(page_size=2)

    >>> ip.get_random_ip('https')
    'https://112.85.128.209:9999'
    ```

3. 在scrapy中使用randomip.

    ```
    from randomip import randomip


    class SpiderMiddleware:
        def __init__(self, crawler):
            cs = crawler.signals
            cs.connect(self.spider_opened, signal=signals.spider_opened)

        @classmethod
        def from_crawler(cls, crawler):
            return cls(crawler)

        def spider_opened(self, spider):
            self.ips = randomip.KuaiIp(spider=spider, delay=self.delay, page_size=self.page_size, concurrent=self.concurrent, headers=self.headers)

        def process_request(self, request, spider):
            request.meta['proxy'] = self.ips.get_random_ip('http')
    ```

在scrapy中实例化时,spider为必填属性,后面的属性可以根据自己的需求来填.