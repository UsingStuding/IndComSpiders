#! /home/python/.virtualenvs/py3_spider/bin/python
# coding=utf-8

import logging.handlers

from IndComSpiders.settings import LOG_FILE

__slot__ = "logger"


class MyLog(object):
	fmt = "%(levelname)s %(asctime)s %(filename)s[line:%(lineno)d] %(funcName)s: %(message)s\n"
	logging.basicConfig(level=logging.INFO, format=fmt,  datefmt='%d %b %Y %H:%M:%S', filename=LOG_FILE, filemode='a+')
	
	# 控制台打印
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
	formatter = logging.Formatter(fmt)
	console.setFormatter(formatter)

	logger = logging.getLogger()
	logger.addHandler(console)


logger = MyLog.logger
