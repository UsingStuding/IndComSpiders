# -*- coding: utf-8 -*-
import pymysql

from IndComSpiders import mysql_cursor, mysql_conn, mogo_db
from IndComSpiders.tools.db_toos import modify_redis
from IndComSpiders.tools.mylog import logger


class IndComPipeline(object):
	
	def value_fmt(self, item):
		"""
		item的value进行简单处理，如去空格，金额单位等等
		:param item:
		:return:
		"""
		for k, v in item.items():
			if k == "register_capital":
				v = v.replace(",", "").split("万")[0]
			else:
				v = str(v).replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
			item[k] = v
	
	def process_item(self, item, spider):
		old_key = item.pop("old_key")
		self.value_fmt(item)
		state = self.write_mysql(item)
		if state:
			
			logger.info("write tname={} successful!".format("company"))
		else:
			logger.info("write tname={}, company_name={} fail!".format("company", item["company_name"]))
		
		modify_redis(item["company_name"], state, old_key)
		return item
	
	def write_mysql(self, data):
		insert_sql = self.gen_sql(tname="company", optype="I", **{"insert_info": data})
		try:
			mysql_cursor.execute(insert_sql)
			mysql_conn.commit()
		except:
			try:
				mogo_db["err"].insert_one({"data": data})
			except Exception as e:
				if "duplicate" in str(e):
					logger.info("mongo的公司={}已经存在".format(data["company_name"]))
			mysql_conn.rollback()
			return 0
			
		else:
			return 1
			
		

	def gen_sql(self, tname, optype="S", **kwargs):
		where_info = kwargs.get("where_info", {})
		select_info = kwargs.get("select_info", {})
		insert_info = kwargs.get("insert_info", {})
		update_info = kwargs.get("update_info", {})
		_w = []
		for k1, v1 in where_info.items():
			if v1:
				_w.append("{}='{}'".format(k1, v1))
		where_str = " and ".join(_w)
		if where_str:
			where_str = " where " + where_str
	
		_s = []
		for k2, v2 in select_info.items():
			if v2:
				_s.append("{} {}".format(k2, v2))
			else:
				_s.append("{}".format(k2))
		select_str = ", ".join(_s)
	
		cols, vals = [], []
		for k3, v3 in insert_info.items():
			if ("time" in k3 or "date" in k3) and not v3:
				v3 = "0000-00-00 00:00:00"
			elif "html_txt" in k3 or "html_str" in k3:
				v3 = pymysql.escape_string(v3)
			elif not v3 and v3 != 0 or v3 == "-":
				v3 = "0.00"
			cols.append(k3)
			vals.append("'{}'".format(v3))
	
		_u = []
		for k4, v4 in update_info.items():
			_u.append("{}='{}'".format(k4, v4))
		update_part = ", ".join(_u)
	
		if optype in "I":
			assert all(vals) and all(cols), "insert操作但列名或值不对应"
			insert_sql = "insert into {} ({}) value({})".format(tname, ", ".join(cols), ", ".join(vals))
			sql = insert_sql
		elif optype in "U":
			assert len(where_str) > 0, "【gen_sql错误警告】：update操作没有where条件或where条件有None值"
			flag = 0
			assert flag, "update操作的where条件不具有唯一性(不支持多条更新)"
			update_sql = "update {} set {} {}".format(tname, update_part, where_str)
			sql = update_sql
		else:
			assert select_str, "select操作但查询字段不存在"
			select_sql = "select {} from {} {}".format(select_str, tname, where_str)
			sql = select_sql
		return sql

	# 暂时未用
	def query_insert(self, tname, flag=0, **info):
		"""
		查询表id，不存在则insert并返回id
		:param tname: 表名
		:param flag: flag=1，表示如果query结果不存在，执行insert后在返回id;
					flag=0, 若不存在，不执行insert，直接返回;
					flag=2, 直接执行insert并返回
		:param info: 字典的字典，select_info、insert_info、update_info、where_info
		:return: 字典
		"""
		assert flag in {0, 1, 2}, "[query_insert]: flag值有误"
		if flag == 2:
			assert "insert_info" in info, "insert操作缺少insert_info字段"
			insert_sql = self.gen_sql(tname=tname, optype="I", **{"insert_info": info.get("insert_info")})
			print("直接写入: insert_sql={}".format(insert_sql))
			result = self.exe_sql(insert_sql)
			result["rid"] = self.get_last_id(tname)
			return result
	
		select_info, where_info = info.get("select_info"), info.get("where_info")
		query_sql = self.gen_sql(tname=tname, optype="S",
								 **{"select_info": select_info, "where_info": where_info})  # 取select_info, where_info
		print("query_sql: {}".format(query_sql))
		result = self.exe_sql(query_sql)
		if result["affect_num"]:
		
			return result
		else:
			assert "insert_info" in info, "insert操作缺少insert_info字段"
			insert_sql = self.gen_sql(tname=tname, optype="I", **{"insert_info": info.get("insert_info")})
			result = self.exe_sql(insert_sql)
			result["rid"] = self.get_last_id(tname)
			return result


if __name__ == "__main__":
	data = {'address': '昆山市玉山镇震川西路111号1114、1115室',
			 'business_date': '2017-11-09至无固定期限',
			 'business_scope': '服务：企业信用信息的采集、整理、保存、加工并向信息使用者提供，企业信用评估评级，企业信用咨询调查，数据信息处理和存储，市场调查，企业管理咨询限制经营、禁止经营的除外）（依法须经批准的项目，经相关部门批准后方可开展经营活动）',
			 'company_name': '杭州数立方征信有限公司苏州分公司',
			 'company_type': '有限责任公司分公司',
			 'credit_code': '91320583MA1T937Y5Y',
			 'establish_date': '2017-11-09',
			 'legal_person': '沈淑英',
			 'other': "{'shares':[],'directors':[{'name':'沈淑英','title':'-'}],'license':'320583001250244'}",
			 'register_capital': '-',
			 'register_office': '昆山市市场监督管理局',
			 'register_status': '开业',
			 'site_name': '百度信用',
			 'source_url': 'https://xin.baidu.com/detail/basicAjax?pid=xlTM-TogKuTwbADC6eRQpawkYcW1Hdiw1Amd&tot=ugoT-lKxTMTwmPX%2AGu5xMz5MxCOpWSVWsQmd'}
	IndComPipeline().write_mysql(data)