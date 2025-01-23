import os

import pytz
from datetime import datetime

# Only sync new memos by managing a last sync time
# Both Github Actions and Notion API are in UTC time zone
last_sync_time_file = 'last_sync_time.txt'


def parse_created_time(created_time_str):
    # 解析 UTC 时间字符串
    utc_time = datetime.strptime(created_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')

    # 设置 UTC 时区
    utc_timezone = pytz.utc
    utc_time = utc_timezone.localize(utc_time)

    # 转换为上海时区
    shanghai_timezone = pytz.timezone('Asia/Shanghai')
    shanghai_time = utc_time.astimezone(shanghai_timezone)

    return shanghai_time


def get_last_sync_time():
    if not os.path.exists(last_sync_time_file):
        return None

    with open(last_sync_time_file, 'r') as f:
        time_str = f.read().strip()
        # 解析时间字符串并转换为datetime对象，指定时区
        try:
            # 假设时间字符串格式是 "YYYY-MM-DD HH:MM:SS+08:00"
            time = datetime.fromisoformat(time_str)
        except ValueError:
            print("时间格式错误")
            return None

        return time


def update_last_sync_time():
    # 获取当前时间（UTC时间）
    update_time = datetime.now(pytz.utc)  # 获取 UTC 时间

    # 转换为上海时间
    shanghai_timezone = pytz.timezone('Asia/Shanghai')
    update_time_shanghai = update_time.astimezone(shanghai_timezone)

    # 保存上海时间
    with open(last_sync_time_file, 'w') as f:
        f.write(update_time_shanghai.strftime("%Y-%m-%d %H:%M:%S") + '+08:00')

    # 返回上海时间字符串
    return update_time_shanghai.strftime("%Y-%m-%d %H:%M:%S") + '+08:00'