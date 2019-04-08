# -*- coding: utf-8 -*-

import scrapy


class BaiduHonorItem(scrapy.Item):
    # 百度信用:
    company_name = scrapy.Field()
    # 营业执照或者注册号
    business_license = scrapy.Field()
    # 统一社会信用代码
    credit_code = scrapy.Field()  # unifiedCode
    # 法人
    legal_person = scrapy.Field()  # legalPerson
    # 经营状态
    register_status = scrapy.Field()  # openStatus
    # 成立日期
    establish_date = scrapy.Field()  # startDate
    # 营业期限
    business_date = scrapy.Field()  # openTime
    # 注册资本
    register_capital = scrapy.Field()  # regCapital
    # 位置
    address = scrapy.Field()  # regAddr
    # 登记机关
    register_office = scrapy.Field()   # authority
    # 企业类型
    company_type = scrapy.Field()   # entType
    # 经营范围
    business_scope = scrapy.Field()  # scope
    # 网站url
    source_url = scrapy.Field()
    # 备用字段，存放股东shares、公司领导directors、licenseNumber
    other  = scrapy.Field()
    
    # 网站来源
    site_name = scrapy.Field()
