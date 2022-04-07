"""
Author: imsixn
Date: 2022-03-26 14:15:14
LastEditors"imsixn
LastEditTime"2022-04-07 15:35:03
Description: file content
"""
from functools import reduce
import json, pytz
from typing import List
from . import const, tools,schedule
from datetime import timedelta, datetime
from lib2to3.pgen2 import driver
from nonebot import Bot, get_bot, get_driver, require, on_command, logger
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .tools import member_list
from .config import Config
from pathlib import Path

driver = get_driver()
scheduler: AsyncIOScheduler = require("scheduler").scheduler

publish_state = False
plugin_config = Config.parse_obj(driver.config)

dxx_init = on_command('init_member', permission=SUPERUSER, aliases={'初始化'})
dxx_check = on_command('check', permission=SUPERUSER, aliases={'检查'})
dxx_priv_notify = on_command('pnotice',aliases={'通知',},permission=SUPERUSER)
dxx_on_task = on_command('open',aliases={'开启任务'},permission=SUPERUSER)
dxx_studyed = on_command('studyed',aliases={'已学'},permission=SUPERUSER)
dxx_group_notify =on_command('gnotice',aliases={'群通知',},permission=SUPERUSER)

@dxx_init.handle()
async def init_member(bot: Bot):
    logger.info("收到消息，准备初始化")
    path = Path('.') / plugin_config.dxx_member_file
    if not path.exists():
        await tools.write_members_info(plugin_config.dxx_notifier_group_id,bot)
        await dxx_init.send(
            r'''初始化，请补充目录下的member_list.json中QQ号对应的人员姓名并填在‘name’,然后再发送一次 /初始化
                 例如
                {
                    "name": "张三",
                    "card_name": "群名片",
                    "nickname": "qq昵称",
                    "user_id": 123456789
                }'''
        )
        return
    global member_list
    await tools.read_members_info()
    member_list = await tools.get_member_list()
    message1 = '\n'.join([f"{x['name']} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in member_list['filterd']])
    message2 = '\n'.join([f"{x['name']} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in member_list['other']])
    await dxx_init.send(f"-----初始化完成,当前读取的人员有({len(member_list['filterd'])}人)：\n\n姓名 | 网名 | QQ号\n" + message1+f"\n-----忽略的QQ有({len(member_list['other'])}人)\n\n"+message2)

    # jobs = [job.id for job in scheduler.get_jobs()]
    # if const.week3to4_12_notice not in jobs:
    #     await schedule.add_week3to4_12_notice(scheduler)




@dxx_priv_notify.handle()
async def check_study_state(bot:Bot):
    """ 主动给没做的发通知 """
    global member_list
    if len(member_list['filterd']) ==0:
        await dxx_check.send("暂未初始化，请发送/初始化")
        return
    notice_list = await tools.get_notice_member_list()
    for m in notice_list:#逐个通知
        await schedule.send_private_notice('personal check',plugin_config.dxx_notifier_group_id,m['user_id'],const.private_notice_message)
    message = '\n'.join([f"{x['name']} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in notice_list])
    await dxx_priv_notify.send("通知发送成功，以下人员已发送通知：\n\n姓名 | 网名 | QQ号\n"+message)


@dxx_group_notify.handle()
async def send_group_notify():
    await schedule.week0_12_sender('week0_12_sender',plugin_config.dxx_notifier_group_id,force=True)
    await dxx_group_notify.send("发送通知成功")

@dxx_check.handle()
async def view_study_state(bot:Bot):
    """ 查看有哪些人没做 """
    global member_list
    if len(member_list['filterd']) ==0:
        await dxx_check.send("暂未初始化，请发送/初始化")
        return
    notice_list = await tools.get_notice_member_list()
    message = '\n'.join([f"{x['name']} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in notice_list])
    await dxx_check.send("以下人员未做：\n\n姓名 | 网名 | QQ号\n"+message+'\n\n发送通知请回复 /通知')

@dxx_studyed.handle()
async def view_studyed_list(bot:Bot):
    """ 看看那些人做了 """
    mem_list = await tools.get_dxx_studyed_member()
    message = '\n'.join([f"{x['name']} | {x['startTime']} | {x['s']}" for x in mem_list])
    await dxx_studyed.send(f"以下人员已做（{len(mem_list)}/18）：\n\n姓名 | 网名 | QQ号\n"+message+'\n\n发送通知请回复 /通知')







# 检查发布默认任务
@driver.on_bot_connect
async def check_default_jobs(bot: Bot):


    scheduler.remove_all_jobs()
    jobs = scheduler.get_jobs()
    logger.info("current jobs:")
    scheduler.print_jobs()
    global member_list
    member_list = await tools.get_member_list()
    # if "week0_12_notice" not in map(lambda j: j.id, jobs):
    #     await week0_12_notice(bot)
    # else:
    #     logger.info("week0_12_notice job is existed")
