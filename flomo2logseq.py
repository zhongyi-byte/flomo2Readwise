from github import Github
from datetime import datetime
import os
import pytz

import EnvVariable
import timeparse
from flomoDatabase import FlomoDatabase
from logger import loguru_logger
from readwise import Readwise

OBSIDIAN_SYNC_GITHUB_TOKEN = os.getenv("OBSIDIAN_SYNC_GITHUB_TOKEN")

# GitHub 认证
g = Github(OBSIDIAN_SYNC_GITHUB_TOKEN)
repo = g.get_repo("zhongyi-byte/obsidian-sync")

logger = loguru_logger('flomo2logseq')

# Logseq 日志目录
logseq_directory = "journals"

# 获取当天的日期
# 获取上海时区
shanghai_timezone = pytz.timezone('Asia/Shanghai')

# 获取上海时间的当天日期
current_time = datetime.now(shanghai_timezone)
today = current_time.strftime("%Y_%m_%d")


# 获取 flomo_memos 的内容，假设你已经从 Notion 拉取了 flomo_memos
# flomo_memos = flomo_database.fetch_flomo_memos(last_sync_time=start_of_day)


def convert_to_logseq_content(flomo_memos):
    content = ""
    for memo in flomo_memos:
        text = memo['text']

        # 构建 Logseq 内容格式
        logseq_entry = "- ---\n"
        logseq_entry += f"- {text}\n"  # 添加笔记内容

        content += logseq_entry

    return content


def push_to_github(content):
    # 文件路径：确保它指向 `journals` 文件夹，并且使用当前日期作为文件名
    file_name = f"{today}.md"
    file_path = f"{logseq_directory}/{file_name}"

    try:
        # 如果文件不存在，创建文件并推送
        repo.create_file(file_path, f"Add {file_name}", content, branch="main")
        print(f"Successfully added {file_name} to GitHub.")
    except Exception as e:
        # 如果文件已存在，更新文件内容
        existing_file = repo.get_contents(file_path, ref="main")
        repo.update_file(existing_file.path, f"Update {file_name}", content, existing_file.sha, branch="main")
        print(f"Successfully updated {file_name} on GitHub.")


def sync_flomo_to_github():
    # Get last sync time
    last_sync_time = timeparse.get_last_sync_time()
    if last_sync_time:
        logger.log('Last sync time:', last_sync_time)
    else:
        logger.log('First sync')

    # Fetch flomo memos
    flomo_database = FlomoDatabase(EnvVariable.NOTION_INTEGRATION_TOKEN, EnvVariable.NOTION_DATABASE_ID, logger)
    flomo_memos = flomo_database.fetch_flomo_memos(last_sync_time=last_sync_time)
    logger.log('Number of flomo memos to sync:', len(flomo_memos))

    if len(flomo_memos) > 0:
        # Sync flomo memos to Github logseq
        content = convert_to_logseq_content(flomo_memos)
        push_to_github(content)
        logger.log('Finished syncing flomo memos to Github')
    else:
        logger.log('No flomo memos to sync')

    # Update last sync time
    update_time = timeparse.update_last_sync_time()
    logger.log('Update last sync time:', update_time)
    logger.log('Finished')
    logger.log('')
