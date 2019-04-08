# #!/usr/bin/env python
# # _*_ coding:utf-8 _*_

from scrapy.commands import ScrapyCommand

from IndComSpiders.tools.mylog import logger


class Command(ScrapyCommand):
	requires_project = True

	def syntax(self):
		return '[options]'

	def short_desc(self):
		"""
		自定义命令的描述，(命令就是该文件名)
		:return:
		"""
		return 'Runs all of the spiders'

	def run(self, args, opts):
		spider_list = self.crawler_process.spiders.list()
		logger.info("spider list：{}".format(spider_list))
		for name in spider_list:
			self.crawler_process.crawl(name, **opts.__dict__)
		self.crawler_process.start()
