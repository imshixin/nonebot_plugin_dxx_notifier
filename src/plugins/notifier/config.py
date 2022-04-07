"""
Author"imsixn
Date"2022-03-29 22:11:49
LastEditors"imsixn
LastEditTime"2022-04-07 14:36:41
Description"file content
"""
from pydantic import BaseModel

class Config(BaseModel):
  dxx_notifier_group_id:str #需要通知的群号
  dxx_username:str #后台登录名
  dxx_password:str #后台登录密码
  dxx_member_file:str #人员名单文件名
  dxx_superuser:int #默认通知qq
  dxx_page_size:int #获取学习人数每页大小

