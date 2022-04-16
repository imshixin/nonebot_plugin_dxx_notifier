"""
Author"imsixn
Date"2022-03-29 22:11:49
LastEditors"imsixn
LastEditTime"2022-04-16 14:11:11
Description"file content
"""
from pydantic import BaseModel, validator

class Config(BaseModel):
  dxx_notifier_group_id:str #需要通知的群号
  dxx_username:str #后台登录名
  dxx_password:str #后台登录密码
  dxx_member_file:str #人员名单文件名
  dxx_superuser:int #默认通知qq
  dxx_page_size:int #获取学习人数每页大小

  @validator('dxx_member_file')
  def path_not_start_with(cls,v):
    """ 禁止路径开头包含/或\ """
    if v.startswith('/') or v.startswith('\\'):
      raise ValueError("dxx_member_file:验证失败，禁止路径开头包含/或\ ")
    return v

