<!--
 * @Author: imsixn
 * @Date: 2022-03-25 09:57:20
 * @LastEditors: imsixn
 * @LastEditTime: 2022-04-16 14:50:09
 * @Description: file content
-->


<div align="center">

# NoneBot Plugin dxx_notifier

_✨ NoneBot 大学习提醒插件 ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/imshixin/nonebot_plugin_dxx_notifier/main/LICENSE">
    <img src="https://img.shields.io/github/license/imshixin/nonebot_plugin_dxx_notifier" alt="license">
  </a>
  <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="python">
</p>

> 仅供学习用途，禁止商业化

## 注意

仅支持如下后台的通知

![use_scope.png](./use_scope.png)


## 使用方式

下载所有代码
在代码目录下创建文件 `.env`和`.env.prod`

`.env` :
```env
ENVIRONMENT=prod
```
`.env.prod` :
```env
HOST=0.0.0.0
PORT=8788
superusers=["123456789"]
command_start=["/","!"]
command_sep=[".","/"]

dxx_notifier_group_id=12345678
dxx_username=xxx
dxx_password=xxxxxx
dxx_member_file=info/member_list.json
dxx_superuser=123456789
dxx_page_size=25

redis_host=redis
redis_port=6379
```


### 插件配置
- superusers=["123456789"]

  机器人超级用户or管理员

- redis_host=redis
  redis地址，如果使用仓库内的docker-compose启动机器人，建议写成`redis`
- redis_port=6379
  redis端口，不建议改动
- dxx_username=大学习后台登录用户名

- dxx_password=大学习后台登录密码

- dxx_member_file=用户信息存放路径与文件名

  推荐为 `info/member_list.json`， 注意不要在路径前写`/`或`\`，会报错

  程序会将群用户信息写入到这里

- dxx_superuser=123456789
  大学习通知的超级用户

  注意，这是这个插件的超级用户，在定时任务执行后会向这个QQ用户发送反馈，建议与机器人超级用户相同

- dxx_page_size=20

  后台查询每页人数：查询已学人员时用到，**请根据自己团员人数来写**，建议20左右

### 命令汇总：

大学习通知插件的命令菜单：

-     /初始化 ：初始化机器人，分两种情况
  - 1.第一次初始化，机器人会将通知群所有QQ信息写入到一个文件中（这个文件在配置中指定）

  - 2.第二次初始化，机器人会读取文件中QQ信息载入到内存
-     /检查：查询哪些人还没做
-     /已学：看看那些人做了
-     /通知：给没学的人发送群私聊通知
-     /群通知：发送群通知告知新一期大学习
-     /任务：查看当前开启的定时任务
-     /开启：开启机器人默认的定时任务