
# -*- coding: utf-8 -*-
import json
import re
from urllib import parse
from urllib.parse import urlencode, urlparse
from lxml import etree
import scrapy, requests
import execjs

from IndComSpiders import rd_cli
from IndComSpiders.items import BaiduHonorItem
from IndComSpiders.tools.db_toos import read_redis, get_total_num
from IndComSpiders.tools.mylog import logger


class BaiduhonorSpider(scrapy.Spider):
	"""
	百度信用爬虫
	"""
	header = {
		"Host": "xin.baidu.com",
		"Referer": "https://xin.baidu.com/",
	}
	
	name = 'baidu_honor'
	allowed_domains = ['xin.baidu.com']
	start_urls = [("https://xin.baidu.com/", "baidu")]
	
	custom_settings = {
		"CONCURRENT_REQUESTS": 2
	}
	
	
	rules = {
		"list": {
			"link": "//div[contains(@class, 'zx-ent-info')]//a[@title]/@href"   # https://xin.baidu.com + xxx
		}
	}
	pp_url = re.compile(r"fromu=(.*)", re.S)

	def start_requests(self):
		for first_url, remark in self.start_urls:
			yield scrapy.Request(url=first_url, headers=self.header, callback=self.search)

	def search(self, response):
		"""
		搜索
		:param response:
		:return:
		"""
		base_link = "https://xin.baidu.com/s"
		pp = re.compile("（.*?）")
		total_num = get_total_num()
		while total_num:
			k = read_redis()
			_, cname = k.split("_")
			cname = cname.replace("’", "").replace("“", "").replace("※", "").replace("＊", "").replace("．", "").replace("：", "")
			for _ in re.findall(pp, cname):
				cname = cname.replace(_, "")
			if len(cname) < 5 or cname.isdigit() or "的" in cname or "业主" in cname:
				rd_cli.delete(k)
				continue
			full_url = (base_link + "?q={cname}".format(cname=cname)).replace(" ", "")
			# full_url = "https://xin.baidu.com/fs/check?type=0&fromu=http://xin.baidu.com/s?q=梁山运来汽车贸易有限公司"
			yield scrapy.Request(url=full_url, headers=self.header, callback=self.parse_list, priority=300, meta={"old_key": k})
			total_num -= 1
	
	def parse_list(self, response):
		"""
		解析列表页，获取内容页的链接
		:param response:
		:return:
		"""
		old_key = response.meta["old_key"]
		txt = "".join(response.xpath("//div[@class='info']//text()").extract()).replace("\n", "")
		if "抱歉" in txt:
			logger.info("返回异常,{}".format(txt))
			rd_cli.delete(old_key)
			return

		# 验证码
		if "fs/check" in response.url:
			url = re.search(self.pp_url, response.url).groups()[0] + "&t=0"
			meta = response.meta
			cnt = meta.get("cnt", 0)
			if cnt < 1:
				yield scrapy.Request(url, headers=self.header, callback=self.parse_list, dont_filter=True, meta={"cnt": 1, "old_key": old_key} , priority=320)
		else:
			href_li = self.handle_link(response.xpath("//div[@class='zx-list-item']//a[contains(@class, 'list-item-url')]/@href").extract())
			for href in  href_li:
				logger.info("href={}".format(href))
				self.header["Referer"] = response.url
				yield scrapy.Request(url=href, headers=self.header, callback=self.parse_detail, priority=350, meta={"old_key": old_key})

	def parse_detail(self, response):
		"""
		解析内容页，使用正则提取拼接tot参数
		:param response:
		:return: tot
		"""
		key_js = "".join(response.xpath("//script[contains(text(), 'mix')]/text()").extract())
		try:
			query_dict = {
				"tot": self.exe_js(response, key_js),
				"pid": self.get_query_pid(response.url)
			}
		except Exception as e:
			logger.error("[获取query_dict参数时出现异常]: {}".format(e))
			return
		base_url = "https://xin.baidu.com/detail/basicAjax"
		ajax_url = base_url + "?" + urlencode(query_dict)
		self.header["Referer"] = response.url
		old_key = response.meta["old_key"]
		yield scrapy.Request(ajax_url, callback=self.parse_ajax, headers=self.header, priority=400, meta={"old_key": old_key})
	
	def get_query_pid(self, link):
		"""
		获取查询字符串参数pid
		:return: pid
		"""
		query_dict = dict(parse.parse_qsl(urlparse(link).query))
		return query_dict["pid"]
	
	def parse_ajax(self, response):
		"""
		解析json数据
		:param response:
		:return: item
		"""
		if "fs/check" in response.url:
			url = re.search(self.pp_url, response.url).groups()[0]
			meta = response.meta
			cnt2 = meta.get("cnt2", 0)
			if cnt2 < 1:
				yield scrapy.Request(url, headers=self.header, callback=self.parse_ajax, dont_filter=True, meta={"cnt2": 1, "old_key": meta["old_key"]} , priority=420)

		json_data = json.loads(response.text)
		data = json_data["data"]
		if json_data["status"] != 0 or not data:
			logger.info("[ajax返回空数据]")
			return {}
		item = BaiduHonorItem()
		item["company_name"] = data["entName"]
		item["source_url"] = response.url
		item["credit_code"], item["legal_person"] = data.get("unifiedCode", data.get("regNo", "")), data["legalPerson"]
		item["register_status"], item["establish_date"] = data["openStatus"], data["startDate"]
		item["business_date"], item["register_capital"] = data["openTime"], self.handle_number(data["regCapital"])
		item["address"], item["register_office"] = data["regAddr"], data["authority"]
		item["company_type"], item["business_scope"] = data["entType"], data["scope"]
		item["business_license"] = data.get("licenseNumber", "")
		try:
			item["other"] = self.handle_other(data.get("shares", []), data.get("directors", []), data.get("licenseNumber", ""))
		except Exception as e:
			print("解析other出现异常:", str(e))
			item["other"] = ""
		item["site_name"] = "百度信用"
		item["old_key"] = response.meta["old_key"]
		yield item
	
	def exe_js(self, html, js_str):
		"""
		使用execjs执行js字符串
		:param js_str: 待执行的js
		:param html: 解析器, response对象
		:return: tk参数
		"""
		js = """function mix(tk, bid) {tk = tk.split('');var bdLen = bid.length;bid = bid.split('');var dk = parseInt(bid[3]);var one = tk[(parseInt(bid[bdLen - 1]) + dk) % 10];for (var i = bdLen - 1; i >= 0; i -= 1) {tk[(parseInt(bid[i]) + dk) % 10] = tk[(parseInt(bid[i - 1]) + dk) % 10];if ((i - 2) < 0) {tk[(parseInt(bid[i - 1]) + dk) % 10] = one;break;}}return tk.join('');}"""
		ctx = execjs.compile(js)
		
		pat = re.compile(r".*?getElementById\('(\w+)'\)\.getAttribute\('(\w+)'\)", re.DOTALL | re.UNICODE)
		_id, _attr_name = re.search(pat, js_str).groups()  # 大写字母
		
		# 参数tk的解析规则，需要转成小写字母
		tk_rule = "//*[@id='{}']/@{}".format(_id, _attr_name.lower())
		logger.info(tk_rule)
		tk = "".join(html.xpath(tk_rule).extract())
		logger.info("打印tk: {}".format(tk))
		baidu_code = html.xpath("//*[@id='baiducode']/text()").extract_first()
		tot = ctx.call("mix", tk, baidu_code)
		logger.info("tot参数值:{}".format(tot))
		return tot
	
	def handle_other(self, shares, directors, license):
		"""
		处理备用字段
		:param shares: 股东
		:param directors: 领导
		:param license: 执照编号
		:return: json
		"""
		info = dict({"license": license})
		tmp = []
		for _ in shares:
			if not _.get("name", ""):
				continue
			tmp.append({"name": _.get("name"), "share_type": _.get("type", ""), "amount": _.get("amount", "")})
		info["shares"] = tmp
		tmp = []
		for _ in directors:
			if not _.get("name", ""):
				continue
			tmp.append({"name": _.get("name"), "title": _.get("title", "")})
		info["directors"] = tmp
		return json.dumps(info, "utf8", ensure_ascii=False)  # 编码与ensure_ascii共同使用

	def handle_link(self, li):
		"""
		处理链接
		:param li: link列表
		:return: 列表
		"""
		href_li = ["https://xin.baidu.com" + _ for _ in li if not _.startswith("http")]
		return href_li
	
	def handle_number(self, s):
		s = s.split("万")[0]
		if not isinstance(s, (int, str, float)):
			s = 0.00
		return s
		