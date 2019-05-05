
# coding=utf-8
import pymongo
import pymysql
import redis

__slot__ = ["mysql_cli", "mysql_cursor"]


mysql_info = {
	"remote": {
		"host": "47.105.57.179",
		"db": "spider_db",
		"user": "spider",
		"password": "Slf@0930",
		"charset": "utf8"
	},
	"win":{
		"host": "192.168.2.103",
		"db": "mytmp",
		"user": "python",
		"password": "123456",
	}

}

MONGO_INFO = {
	"win":{
		"host": "192.168.2.103",
	}
}


REDIS_INFO = {
	"win": {
		"host": "192.168.2.103",
		"db": 0,    # 集合名tmp_com_set
		"port": 6379
	}
}

mysql_conn = pymysql.connect(**mysql_info["win"], cursorclass=pymysql.cursors.DictCursor)
mysql_cursor = mysql_conn.cursor()
rd_cli = redis.Redis(**REDIS_INFO["win"])
new_rd_cli = redis.Redis(host="192.168.2.103", db=4)


mogo_db = pymongo.MongoClient(**MONGO_INFO["win"]).Ind_Com


if __name__ == "__main__":
	pass