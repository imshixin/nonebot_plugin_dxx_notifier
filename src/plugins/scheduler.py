"""
Author: imsixn
Date: 2022-03-26 21:27:07
LastEditors"imsixn
LastEditTime"2022-04-05 22:23:36
Description: file content
"""


import asyncio
from nonebot.log import logger
from lib2to3.pgen2 import driver
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import get_driver, export

# plugin_name='scheduler'
jobstore = RedisJobStore(
    db=1,
    jobs_key="apscheduler.notifier.jobs",
    run_times_key="apscheduler.notifier.run_times",
    host="localhost",
    port=6379,
    password="",
)
executor = AsyncIOExecutor()

init_scheduler_options = {
    "jobstores": {"default": jobstore},
    "executors": {"default": executor},
    "job_defaults": {
        "coalesce": False,  # 取消合并执行
        "max_instances": 10,  # 最大实例
        "misfire_grace_time": 10,
    },
}
scheduler = AsyncIOScheduler(**init_scheduler_options)
export().scheduler = scheduler


async def init_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.opt(colors=True).success("<y>Scheduler</y> start success")


get_driver().on_startup(init_scheduler)
