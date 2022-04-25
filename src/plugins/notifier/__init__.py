"""
Author: imsixn
Date: 2022-03-26 14:15:14
LastEditors"imsixn
LastEditTime"2022-04-25 23:08:30
Description: file content
"""
from datetime import datetime
from functools import reduce
import os

# import json, pytz
# from datetime import timedelta, datetime
from httpx import ReadTimeout
from typing import List
from . import const, tools, schedule
from lib2to3.pgen2 import driver
from nonebot import Bot, get_bot, get_driver, require, on_command, logger
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job
from .tools import member_list
from .config import Config
from pathlib import Path

driver = get_driver()
scheduler: AsyncIOScheduler = require("env").scheduler

publish_state = False
plugin_config = Config.parse_obj(driver.config)

dxx_init = on_command('init_member', permission=SUPERUSER, aliases={'初始化'})
dxx_check = on_command('check', permission=SUPERUSER, aliases={'检查'})
dxx_priv_notify = on_command(
    'pnotice',
    aliases={
        '通知',
    },
    permission=SUPERUSER,
)
dxx_studyed = on_command('studyed', aliases={'已学'}, permission=SUPERUSER)
dxx_group_notify = on_command(
    'gnotice',
    aliases={
        '群通知',
    },
    permission=SUPERUSER,
)

dxx_on_task = on_command('open', aliases={'开启任务', '开启'}, permission=SUPERUSER)
dxx_task_check = on_command('task', aliases={'任务'}, permission=SUPERUSER)

dxx_help = on_command("dxxhelp", aliases={"大学习帮助", '帮助'}, permission=SUPERUSER)


@dxx_help.handle()
async def dxx_help_command():
    message = """ 大学习通知插件的命令菜单：
    /初始化 ：初始化机器人，分两种情况
        1.第一次初始化，机器人会将通知群所有QQ信息写入到一个文件中（这个文件在配置中指定）
        2.第二次初始化，机器人会读取文件中QQ信息载入到内存
    /检查：查询哪些人还没做
    /已学：看看那些人做了
    /通知：给没学的人发送群私聊通知
    /群通知：发送群通知告知新一期大学习
    /任务：查看当前开启的定时任务
    /开启：开启机器人默认的定时任务 """
    await dxx_help.send(message)


@dxx_init.handle()
async def init_member(bot: Bot):
    logger.info("收到消息，准备初始化")
    path = Path('.') / plugin_config.dxx_member_file

    if not path.exists():
        logger.info(path.absolute())
        if not path.parent.exists():
            os.makedirs(path.parent,exist_ok=True)
        await tools.write_members_info(plugin_config.dxx_notifier_group_id, bot)
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
    member_list = await tools.get_member_list(True)
    message1 = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in member_list['filterd']])
    message2 = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in member_list['other']])
    await dxx_init.send(
        f"-----初始化完成,当前读取的人员有({len(member_list['filterd'])}人)：\n\n姓名 | 网名 | QQ号\n"
        + message1
        + f"\n-----忽略的QQ有({len(member_list['other'])}人)\n\n"
        + message2
    )


@dxx_priv_notify.handle()
async def send_study_priv(bot: Bot):
    """主动给没做的发通知"""
    global member_list
    if len(member_list['filterd']) == 0:
        await dxx_check.send("暂未初始化，请发送/初始化")
        return
    try:
        notice_list = await tools.get_notice_member_list()
    except (ConnectionError, ReadTimeout) as e:
        await dxx_priv_notify.send("获取通知名单超时")
        return
    errs=[]
    for m in notice_list:  # 逐个通知
        try:
            await schedule.send_private_notice(
                'personal check', plugin_config.dxx_notifier_group_id, m['user_id'], const.private_notice_message
            )
        except ActionFailed as e:
            errs.append(m)
    message = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in notice_list])
    message_err = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in errs])
    await dxx_priv_notify.send("通知发送成功，以下人员已发送通知：\n\n姓名 | 网名 | QQ号\n" + message+f'\n\n 以下发送失败({len(errs)}):\n'+message_err)


@dxx_group_notify.handle()
async def send_group_notify():
    await schedule.week0_12_sender('week0_12_sender', plugin_config.dxx_notifier_group_id, force=True)
    await dxx_group_notify.send("发送通知成功")


@dxx_check.handle()
async def view_study_state(bot: Bot):
    """查看有哪些人没做"""
    global member_list
    if len(member_list['filterd']) == 0:
        await dxx_check.send("暂未初始化，请发送/初始化")
        return
    await dxx_check.send("查询中")
    notice_list = await tools.get_notice_member_list()
    message = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {x['card_name'] or x['nickname']} | {x['user_id']}" for x in notice_list])
    await dxx_check.send(f"以下人员未做({len(notice_list)})：\n\n姓名 | 网名 | QQ号\n" + message + '\n\n发送通知请回复 /通知')


@dxx_studyed.handle()
async def view_studyed_list(bot: Bot):
    """看看那些人做了"""
    global member_list
    mem_list = await tools.get_dxx_studyed_member()
    message = '\n'.join([f"{x['name'].rjust(5,chr(12288))} | {datetime.fromtimestamp(x['start_time']).strftime('%m-%d 周%w %H:%M')}" for x in mem_list])
    await dxx_studyed.send(
        f"以下人员已做（{len(mem_list)}/{len(member_list['filterd'])}）：\n\n姓名 | 时间 \n" + message + '\n\n发送通知请回复 /通知'
    )


@dxx_task_check.handle()
async def check_tasks():
    jobs: List[Job] = scheduler.get_jobs()
    message_head = '任务ID | 任务描述 | 下次执行时间\n'
    message = '\n'.join([f'{job.id} | {job.name} | {job.next_run_time}' for job in jobs])
    await dxx_task_check.send(message_head + message)


@dxx_on_task.handle()
async def set_tasks():
    jobs: List[Job] = scheduler.get_jobs()
    job_names: List[str] = [job.id for job in jobs]
    if const.week0_12_notice not in job_names:
        await schedule.add_week0_12_notice(scheduler, plugin_config.dxx_notifier_group_id)
    if const.week0_18_notice not in job_names:
        await schedule.add_week0_18_notice(scheduler, plugin_config.dxx_notifier_group_id)
    if const.week3to4_12_notice not in job_names:
        await schedule.add_week3to4_12_notice(scheduler, plugin_config.dxx_notifier_group_id)
    await dxx_on_task.send("任务添加完成，发送 /任务 查看所有任务")


# 检查发布默认任务
@driver.on_bot_connect
async def check_default_jobs(bot: Bot):

    logger.info("current jobs:")
    scheduler.print_jobs()
    global member_list
    member_list = await tools.get_member_list()
