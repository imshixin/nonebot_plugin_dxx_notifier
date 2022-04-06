"""
Author"imsixn
Date"2022-03-25 23:18:31
LastEditors"imsixn
LastEditTime"2022-04-05 23:07:19
Description"file content
"""

from nonebot import get_driver, logger, export
import redis
from redis import Redis

driver = get_driver()
exp = export()
"""初始化redis数据库"""
db = Redis(host=driver.config.redis_host, port=driver.config.redis_port, db=0)
logger.opt(colors=True).info(f'<r>Redis</r>:redis db connect {db.ping()}')
#导出Redis
exp.redis = db
