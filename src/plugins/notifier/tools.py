"""
Author"imsixn
Date"2022-03-29 21:47:23
LastEditors"imsixn
LastEditTime"2022-04-16 14:21:02
Description"file content
"""
import json
from pathlib import Path
from typing import List
from httpx import AsyncClient
from httpx import Timeout
from bs4 import BeautifulSoup
from nonebot import Bot, get_bot, get_driver, require
from nonebot.log import logger
from datetime import datetime, timedelta
import re, asyncio

from .config import Config
from . import const
from redis import Redis

dxx_publish_url = 'http://news.cyol.com/gb/channels/vrGlAKDl/index.html'
dxx_backend_url = 'http://dxx.scyol.com/dxxBackend/#/index'
dxx_login_url = 'http://dxx.scyol.com/backend/adminUser/login'
dxx_study_list_url = 'http://dxx.scyol.com/backend/study/student/list'
dxx_stage_list_url = 'http://dxx.scyol.com/backend/stages/list'
dxx_detail_url = 'http://dxx.scyol.com/backend/study/organize/detail'

info = {'token': ''}  # 全局info，存储token，orgId，member，防止频繁发送登录请求
member_list = {'filterd': [], 'other': []}
driver = get_driver()
db: Redis = require('env').redis
plugin_config = Config.parse_obj(driver.config)
path = Path('.') / plugin_config.dxx_member_file


async def check_dxx_publish():
    """检查是否有新的大学习视频发布"""
    async with AsyncClient() as client:
        raw = (await client.get(dxx_publish_url)).content.decode('utf-8')
        lis = BeautifulSoup(raw, 'lxml').select('ul.movie-list li')
        _pub_times = map(lambda li: re.search('</span>(.+?)</div>', str(li))[1], lis)
        return any(map(lambda t: (datetime.now() - datetime.fromisoformat(t)).days < 7, _pub_times))


async def get_dxx_list() -> List[dict]:
    """返回大学习数据
    Return：
      [
        {
          'title':str,
          'imageUrl':str,
          'pub_time':str,
        },
        ...
      ]

    """
    async with AsyncClient() as client:
        raw = (await client.get(dxx_publish_url)).content.decode('utf-8')
        # 获取大学习列表node
        lis = BeautifulSoup(raw, 'lxml').select('ul.movie-list li')
        # _pub_times = map(lambda li:re.search('</span>(.+?)</div>',str(li))[1], lis)
        dxx_list = []
        for li in lis:
            dxx_list.append(
                {
                    'title': li.select_one('h3 a').text,  # 大学习标题
                    'imageUrl': li.select_one('a img').attrs['data-src'],  # 封面url
                    'pub_time': re.search('</span>(.+?)</div>', str(li))[1],  # 发布时间
                }
            )
        return dxx_list


async def _get_info(username, password, retry=1):
    global info
    db_info: bytes = db.get(const.dxx_info)
    if db_info:
        info = json.loads(db_info)
        logger.info("get redis info:  " + db_info.decode('utf-8'))
    # 验证token可用性，否则获取新token
    while retry > 0:
        try:
            if not info:
                raise KeyError("Need info init")
            await get_dxx_stages(info['token'])
            logger.success("use exists token to return !")
            return info
        except (ValueError, KeyError) as e:
            retry -= 1
            logger.info("get new token to return ")
            info = await login_dxx_backend(username, password)
            db.set(const.dxx_info, json.dumps(info, ensure_ascii=False))
    return info


async def _get_dxx_studyed_member(stages_id, org_id, token=''):
    """返回已学人员信息

    [{
        'name':'', #姓名
        'startTime':'' #学习时间戳
        'stage_snum':'' #学的哪一期
    },
    ...
    ]"""
    async with AsyncClient(headers={'token': token}, timeout=Timeout(20.0, connect=10.0)) as client:
        logger.opt(colors=True).info(f'<b>获取到INFO</b>  {stages_id}, {org_id}, {token}')
        page_no = 1
        merge = []
        while True:  # 多次查询获取完整列表
            data = {
                "orgId": org_id,
                "stagesId": stages_id,
                "name": "",
                "tel": "",
                "pageNo": page_no,
                "pageSize": plugin_config.dxx_page_size,
            }
            json_data = (await client.post(dxx_study_list_url, json=data)).json()
            if str(json_data['code']) != '200':
                raise ValueError("获取已学习成员列表失败：" + json_data['msg'] + "\ndata::" + json.dumps(data, ensure_ascii=False))
            merge += json_data['data']
            if json_data['paginator']['pages'] == page_no:
                break
            page_no += 1

        result = [{'name': _['name'], 'start_time': _['startTime'], 'stage_snum': _['stageSnum']} for _ in merge]
        return result


async def get_dxx_stages(token) -> List:
    async with AsyncClient(headers={'token': token}) as client:
        json_data = (await client.post(dxx_stage_list_url, json={"pageNo": 1, "pageSize": 500})).json()
        if str(json_data['code']) != '200':
            raise ValueError("获取大学习各期信息失败：" + json_data['msg'])
        result = [
            {'created': _['created'], 'id': _['id'], 'name': _['name'], 'snum': _['snum'], 'status': _['status']} for _ in json_data['data']
        ]
        return result


async def login_dxx_backend(username: str = plugin_config.dxx_username, password: str = plugin_config.dxx_password) -> dict:
    """返回登录信息，包括
    {
        "orgId":'',  组织id
        "token":'',  登录token
        "member":int 成员人数
    }
    """
    data = {
        'username': username,
        'password': password,
    }
    async with AsyncClient() as client:
        result = await client.post(dxx_login_url, json=data)
        json_data = result.json()
        if str(json_data['code']) != '200':
            raise ValueError("大学习后台登录失败，请检查账号密码\n 请求返回值为" + json.dumps(json_data, ensure_ascii=False))

        data2 = {"orgId": json_data['data']['orgId'], "stagesId": ''}
        # 获取member
        result2 = (await client.post(dxx_detail_url, json=data2, headers={'token': json_data['data']['token']})).json()
        if str(result2['code']) != '200':
            raise ValueError(
                "大学习组织信息获取失败，\n 请求返回值为" + json.dumps(result2, ensure_ascii=False) + "上一个请求返回值为" + json.dumps(json_data, ensure_ascii=False)
            )
        return {'orgId': json_data['data']['orgId'], 'token': json_data['data']['token'], 'member': result2['data']['member']}


async def get_dxx_studyed_member(username: str = plugin_config.dxx_username, password: str = plugin_config.dxx_password):
    """返回已学人员信息

    会将信息存入Redis，过期时间为10分钟，下次获取不在需要请求网络数据

    [{
        'name':'', #姓名
        'start_time':'' #学习时间戳
        'stage_snum':'' #学的哪一期
    },
    ...
    ]"""
    if db.exists(const.dxx_studyed_list):
        member = json.loads(db.get(const.dxx_studyed_list))
        return member
    _info = await _get_info(username, password)
    _stages = await get_dxx_stages(_info['token'])
    filter_stages = list(filter(lambda _: _['status'] == 1, _stages))
    if len(filter_stages) == 0:  # 没有当周的大学习视频
        raise IndexError('没有正在开启的大学习视频：' + json.dumps(_stages))
    member = await _get_dxx_studyed_member(filter_stages[0]['id'], _info['orgId'], _info['token'])
    db.set(const.dxx_studyed_list, json.dumps(member, ensure_ascii=False), ex=3 * 60 * 60)
    return member


async def write_members_info(group_id: int, bot: Bot, path: str = path):
    """
    将指定群的成员信息写入到指定文件中
    """
    result = await bot.call_api('get_group_member_list', group_id=group_id)
    member_list = list(map(lambda _: {'name': '', 'card_name': _['card'], 'nickname': _['nickname'], 'user_id': _['user_id']}, result))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(
            member_list,
            f,
            ensure_ascii=False,
            indent=4,
        )
        logger.opt(colors=True).info("<y>Tools</y>: write members info")


async def read_members_info(path: str = path) -> dict:
    """
    将指定文件的成员信息读入Redis
    返回dict
    dict['filterd']:所有匹配的人员信息
    dict['other']:所有未匹配的人员信息
    """
    global redis
    with open(path, encoding='utf-8') as f:
        members = json.load(f)
        # if _filter:
        filterd = list(filter(lambda member: member['name'] != '', members))
        members = {'filterd': filterd, 'other': list(filter(lambda x: x not in filterd, members))}
        db.set(
            const.member_list_filterd,
            json.dumps(members['filterd'], ensure_ascii=False),
        )
        db.set(const.member_list_other, json.dumps(members['other'], ensure_ascii=False))
        logger.opt(colors=True).info("<y>Redis</y>:store member_list")


async def get_member_list(update=False):
    """
    将指定文件的成员信息返回
    返回dict
    dict['filterd']:所有匹配的人员信息
    dict['other']:所有未匹配的人员信息
    """
    global member_list
    if (len(member_list['filterd']) > 0 or len(member_list['other']) > 0) and not update:
        return member_list
    if not db.exists(const.member_list_filterd, const.member_list_other):
        await read_members_info()
    member_list['filterd'] = json.loads(db.get(const.member_list_filterd))
    member_list['other'] = json.loads(db.get(const.member_list_other))
    return member_list


async def get_notice_member_list():
    """获取待通知人员列表"""
    studyed_list = await get_dxx_studyed_member()
    logger.debug(const.dxx_studyed_list)
    logger.debug(studyed_list)
    if not db.exists(const.member_list_filterd):
        raise ValueError("找不到member_list_filterd的值")
    member_list = json.loads(db.get(const.member_list_filterd))
    name_list = [m['name'] for m in studyed_list]
    notice_list = list(filter(lambda m: m['name'] not in name_list, member_list))
    logger.debug("notice_list")
    logger.debug(notice_list)
    return notice_list
