"""
Author: imsixn
Date: 2022-03-25 09:57:20
LastEditors"imsixn
LastEditTime"2022-04-05 22:06:12
Description: file content
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter


# Custom your logger
#
# from nonebot.log import logger, default_format
# logger.add("error.log",
#            rotation="00:00",
#            diagnose=False,
#            level="ERROR",
#            format=default_format)

# You can pass some keyword args config to init function
nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()

config = driver.config


driver.register_adapter(ONEBOT_V11Adapter)
nonebot.load_builtin_plugins("echo")
nonebot.load_from_toml("pyproject.toml")

@driver.on_shutdown
def on_shutdown():
    nonebot.require('redis_db').redis.close()
    nonebot.require("scheduler").scheduler.shutdown()
    nonebot.logger.opt(colors=True).info("<y>Scheduler</y>:shutdown")
    nonebot.logger.opt(colors=True).info("<y>Redis</y>: connection close")


if __name__ == "__main__":
    nonebot.logger.warning(
        "Always use `nb run` to start the bot instead of manually running!"
    )
    nonebot.run(app="__mp_main__:app")

