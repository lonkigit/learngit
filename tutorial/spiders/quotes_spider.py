import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes"

    # def start_requests(self):
    #     urls = [
    #         'http://quotes.toscrape.com/page/1/',
    #         'http://quotes.toscrape.com/page/2/',
    #     ]
    #
    #     for url in urls:
    #         yield scrapy.Request(url=url,callback=self.parse)

    start_urls = [
        'http://quotes.toscrape.com/page/3/',
        'http://quotes.toscrape.com/page/4/',
    ]

    def parse(self, response):
        page = response.url.split('/')[-2]
        filename = 'quotes-%s.html' % page
        with open(filename,'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' %filename)


class DoubanSpider(scrapy.Spider):
    name = "douban"

    def start_requests(self):
        yield scrapy.Request(url="https://doc.scrapy.org/en/master/intro/tutorial.html",callback=self.parse)

    def parse(self, response):
        pageNo = response.url.split('/')[-2]
        filename = 'douban-%s.html' % pageNo
        with open(filename,'wb') as f:
            f.write(response.body)
        self.log('Save file %s' %filename)


