"""
Author"imsixn
Date"2022-04-16 14:06:14
LastEditors"imsixn
LastEditTime"2022-04-16 14:14:40
Description"file content
"""
from nonebot import get_driver, logger, export
import redis
from redis import Redis
from apscheduler.events import EVENT_JOB_ADDED, JobEvent
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import get_driver, export

driver = get_driver()
exp = export()
"""初始化redis数据库"""
db = Redis(host=driver.config.redis_host, port=driver.config.redis_port, db=0)
logger.opt(colors=True).info(f'<r>Redis</r>:redis db connect state: {db.ping()}')

jobstore = RedisJobStore(
    db=0,
    jobs_key="apscheduler.notifier.jobs",
    run_times_key="apscheduler.notifier.run_times",
    host=driver.config.redis_host,
    port=driver.config.redis_port,
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

def task_add(e: JobEvent):
    logger.opt(colors=True).info(f"<y>Scheduler</y>:新任务已添加:id={e.job_id}")
scheduler.add_listener(task_add, mask=EVENT_JOB_ADDED)

#导出
exp.redis = db
exp.scheduler = scheduler

@driver.on_startup
async def init_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.opt(colors=True).success("<y>Scheduler</y> start success")

@driver.on_shutdown
def on_shutdown():
    db.close()
    scheduler.shutdown()
    logger.opt(colors=True).info("<y>Scheduler</y>:shutdown")
    logger.opt(colors=True).info("<y>Redis</y>: connection close")


