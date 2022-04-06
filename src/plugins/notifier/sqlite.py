"""
Author"imsixn
Date"2022-04-03 22:10:35
LastEditors"imsixn
LastEditTime"2022-04-03 22:10:36
Description"file content
"""
from pathlib import Path
import sqlite3

conn = sqlite3.connect(Path('.')/'db.sqlite3',)
