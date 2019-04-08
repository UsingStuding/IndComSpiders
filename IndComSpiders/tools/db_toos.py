# # coding=utf-8
#
# from IndComSpiders import mysql_cursor, rd_cli
# from IndComSpiders.tools.mylog import logger
#
# """
# 	将全部公司写入redis，从redis读取公司信息，并更新次数，防止重复更新
# """
# end_id = 282580  # 用于断点续查
#
# def read_mysql(table="company", start=0, end=100):
# 	"""
# 	从mysql中读取公司表
# 	:param count: 每次读取的数量
# 	:return: [{}, {}]
# 	"""
# 	query_sql = "select id sid, company_name cname from company order by id asc limit {}, {}".format(start, end)
# 	affect_rows = mysql_cursor.execute(query_sql)
# 	result = mysql_cursor.fetchall()
# 	logger.info("本地共查询{}".format(affect_rows))
# 	return result
#
# def record_finger(all_coms):
# 	"""
# 	redis记录指纹(将全部公司)
# 	:param all_coms: 数据库中所有的公司记录行
# 	:return:
# 	"""
# 	global end_id
# 	key = "{cnt}_{cname}"
# 	v = 1
# 	for com_li in  all_coms:
# 		k = key.format(cnt=1, cname=com_li["cname"])
# 		v = com_li["sid"]
# 		rd_cli.set(k, v)
# 	end_id = v or end_id
#
from IndComSpiders import rd_cli, new_rd_cli
from IndComSpiders.tools.mylog import logger


def read_redis():
	"""
	从redis中读取公司
	:return:
	"""
	com_name = rd_cli.randomkey()
	return com_name.decode()

def get_total_num():
	return rd_cli.dbsize()

def modify_redis(com_name, state):
	
	finger = "1_{}".format(com_name)
	v = str(rd_cli.get(finger))
	if not state:
		new_name = "3_{}".format(com_name)
		rd_cli.rename(finger, new_name)
	else:
		new_finger = "2_{}".format(com_name)
		new_rd_cli.set(new_finger, v)
		rd_cli.delete(finger)
		logger.info("finger={} 删除成功".format(finger))


# read_redis()
print(get_total_num())
#
#
#
# if __name__ == "__main__":
#
# 	while 1:
# 		try:
# 			result = read_mysql(start=end_id, end=end_id+300)
# 			record_finger(result)
# 		except:
# 			with open("query_last_id", "w", encoding="utf-8") as fp:
# 				fp.write(str(end_id))
# 	pass

