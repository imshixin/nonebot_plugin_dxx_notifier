"""
Author"imsixn
Date"2022-03-26 21:34:55
LastEditors"imsixn
LastEditTime"2022-04-25 22:33:47
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
from nonebot import Bot, get_driver, get_bot, logger, require
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.exception import ActionFailed
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis import Redis
from . import tools, const
from .config import Config

driver = get_driver()
tz = pytz.timezone('Asia/Shanghai')
plugin_config = Config.parse_obj(driver.config)
db: Redis = require('env').redis
publish_state = False


async def send_group_notice(notice_type, group, message):
    ret = await get_bot().call_api("send_group_msg", group_id=group, message=message)
    logger.opt(colors=True).success(f'<white>{notice_type}</white>:send message_id:{ret["message_id"]}')


async def send_private_notice(notice_type, group_id, user_id, message):
    ret = await get_bot().call_api('send_private_msg', user_id=user_id, group_id=group_id, message=message)
    logger.opt(colors=True).success(f'<white>{notice_type}</white>:send message_id:{ret["message_id"]}')


async def week0_12_sender(notice_type, group, force=False):
    global publish_state
    has_new = await tools.check_dxx_publish()
    if force or has_new:
        dxx = (await tools.get_dxx_list())[0]
        # MessageSegment.at('all')+
        message = '本周大学习已更新\n' + MessageSegment.image(dxx['imageUrl']) + f'\n标题：{dxx["title"][6:]}'
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
        message = '本周大学习已更新\n' + MessageSegment.image(dxx['imageUrl']) + f'\n标题：{dxx["title"][6:]}'
        await send_group_notice(notice_type, group, message)
    publish_state = False


async def week3to4_12_sender(notice_type, group_id: int):
    if publish_state == False:
        await get_bot().call_api('send_msg', user_id=plugin_config.dxx_superuser, message="无更新，不通知")
    notice_list = await tools.get_notice_member_list()
    errs = []
    for m in notice_list:  # 逐个通知
        try:
            await send_private_notice('personal check', plugin_config.dxx_notifier_group_id, m['user_id'], const.private_notice_message)
        except ActionFailed as e:
            errs.append(m)
    message = '\n'.join([f"{x['name']} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in notice_list])
    message_err = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in errs])
    await get_bot().call_api(
        'send_msg',
        user_id=plugin_config.dxx_superuser,
        message="通知发送成功，以下人员已发送通知：\n\n姓名 | 网名 | QQ号\n" + message + f'\n\n 以下发送失败({len(errs)}):\n' + message_err,
    )


async def add_week0_12_notice(scheduler: AsyncIOScheduler, group_id):
    """添加每周1, 12点的通知"""
    scheduler.add_job(
        week0_12_sender,
        args=['week0_12_notice', group_id],
        id=const.week0_12_notice,
        name='每周一12点群提醒',
        trigger="cron",
        day_of_week="0",
        hour="12",
        minute="0",
        second="0",
        timezone=tz,
        misfire_grace_time=1,
    )


async def add_week0_18_notice(scheduler: AsyncIOScheduler, group_id: int):
    """添加每周1，18点的通知"""
    scheduler.add_job(
        week0_18_sender,
        id=const.week0_18_notice,
        name='每周一18点群提醒',
        args=[const.week0_18_notice, group_id],
        trigger="cron",
        day_of_week="0",
        hour="18",
        minute="0",
        second="0",
        timezone=tz,
        misfire_grace_time=1,  # 超时不执行
    )


async def add_week3to4_12_notice(scheduler: AsyncIOScheduler, group_id: int):
    scheduler.add_job(
        week3to4_12_sender,
        id=const.week3to4_12_notice,
        name='每周3-4中午12点个人提醒',
        args=[const.week3to4_12_notice, group_id],
        trigger='cron',
        day_of_week='2-3',
        hour='12',
        minute='0',
        second='0',
        misfire_grace_time=1,  # 超时不执行
    )
