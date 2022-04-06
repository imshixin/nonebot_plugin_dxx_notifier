"""
Author"imsixn
Date"2022-03-26 21:34:55
LastEditors"imsixn
LastEditTime"2022-04-06 13:41:20
Description"file content
"""
'''
Author: imsixn
Date: 2022-03-26 21:34:55
LastEditors: imsixn
LastEditTime: 2022-03-26 22:05:57
Description: 添加job
'''
import pytz
from calendar import month
from datetime import datetime, timedelta
from nonebot import Bot, get_driver,get_bot,logger
from nonebot.adapters.onebot.v11 import MessageSegment
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from . import tools,const

driver = get_driver()
tz = pytz.timezone('Asia/Shanghai')

async def add_cron_job(
    func, args: list, stamp: datetime, id: str = ''
):
    """
    创建并添加定时任务

    Params:
      func:要添加的函数
      str:任务id
      args:函数传入的参数
      stamp:要定义的时间
    """
    scheduler: AsyncIOScheduler = driver.scheduler
    now = datetime.now()
    specified_time = {
        'year': stamp['year'] if 'year' in stamp else str(now.year),
        'month': stamp['month'] if 'month' in stamp else str(now.month),
        'day': stamp['day'] if 'day' in stamp else str(now.day),
        'day_of_week': stamp['day_of_week']
        if 'day_of_week' in stamp
        else str(now.weekday),
        'hour': stamp['hour'] if 'hour' in stamp else str(now.hour),
        'minute': stamp['minute'] if 'minute' in stamp else str(now.minute),
        'second': stamp['second'] if 'second' in stamp else str(now.second),
    }
    scheduler.add_job(
        func, id=id if '' != id else func.__name__, args=args, trigger='cron', **stamp
    )


async def send_group_notice(notice_type, group, message):
    ret = await get_bot().call_api("send_group_msg", group_id=group, message=message)
    logger.opt(colors=True).success(f'<white>{notice_type}</white>:send message_id:{ret["message_id"]}')


async def send_private_notice(notice_type, group_id, user_id, message):
    ret = await get_bot().call_api('send_private_msg',user_id=user_id,group_id=group_id,message=message)
    logger.opt(colors=True).success(f'<white>{notice_type}</white>:send message_id:{ret["message_id"]}')


async def week0_12_sender(notice_type, group):
    global publish_state
    has_new = await tools.check_dxx_publish()
    if has_new:
        dxx = (await tools.get_dxx_list())[0]
        # MessageSegment.at('all')+
        message = '\n本周大学习已更新\n' + MessageSegment.image(dxx['imageUrl']) + f'\n标题：{dxx["title"][6:]}'
        await send_group_notice(notice_type, group, message)
        publish_state = True
    else:
        publish_state = False


async def week0_18_sender(notice_type, group):
    global publish_state
    if publish_state:
        return
    has_new = await tools.check_dxx_publish()
    if has_new:
        dxx = (await tools.get_dxx_list())[0]
        # MessageSegment.at('all')+
        message = '\n本周大学习已更新\n' + MessageSegment.image(dxx['imageUrl']) + f'\n标题：{dxx["title"][6:]}'
        await send_group_notice(notice_type, group, message)
    publish_state = False


async def add_week0_12_notice(scheduler:AsyncIOScheduler,group_id):
    """添加每周1, 12点的通知"""
    job = scheduler.add_job(
        week0_12_sender,
        args=['week0_12_notice', group_id],
        id=const.week0_12_notice,
        trigger="cron",
        day_of_week="1",
        hour="22",
        minute="*",
        second="*/10",
        timezone=tz,
        name='每周一12点群提醒',
        misfire_grace_time=5,
    )
    # logger.success('新的定时任务已添加: {},下一次运行时间: {}', job.id, job.next_run_time)


async def add_week0_18_notice(scheduler:AsyncIOScheduler,group_id:int):
    """添加每周1，12点的通知"""
    job = scheduler.add_job(
        week0_18_sender,
        args=['week0_12_notice', group_id],
        id=const.week0_12_notice,
        trigger="cron",
        day_of_week="1",
        hour="22",
        minute="*",
        second="*/10",
        timezone=tz,
        name='每周一18点群提醒', #超时不执行
        misfire_grace_time=0,
    )
    # logger.success('新的定时任务已添加: {},下一次运行时间: {}', job.id, job.next_run_time)


async def week3to4_12_sender():
    pass
    # studyed_List = await tools.get_dxx_studyed_member(plugin_config.dxx_username, plugin_config.dxx_password)


async def week3to4_12_notice(scheduler:AsyncIOScheduler):
    job = scheduler.add_job(
        week3to4_12_sender,
        id='week3to4_12_notice',
        name='每周3-4中午12点个人提醒',
        trigger='cron',
        day_of_week='2-3',
        hour='12',
        minute='0',
        misfire_grace_time=0, #超时不执行
    )
    logger.success('新的定时任务已添加: {},下一次运行时间: {}', job.id, job.next_run_time)


