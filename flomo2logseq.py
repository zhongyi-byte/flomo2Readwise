from github import Github
from datetime import datetime
import os
import pytz

import EnvVariable
import timeparse
from flomoDatabase import FlomoDatabase
from logger import loguru_logger

OBSIDIAN_SYNC_GITHUB_TOKEN = os.getenv("OBSIDIAN_SYNC_GITHUB_TOKEN")

# GitHub 认证
g = Github(OBSIDIAN_SYNC_GITHUB_TOKEN)
repo = g.get_repo("zhongyi-byte/obsidian-sync")

logger = loguru_logger('flomo2logseq')

# Logseq 日志目录
logseq_directory = "journals"

# 获取上海时区
shanghai_timezone = pytz.timezone('Asia/Shanghai')

# 获取上海时间的当天日期
current_time = datetime.now(shanghai_timezone)
today = current_time.strftime("%Y_%m_%d")


# 获取 flomo_memos 的内容，假设你已经从 Notion 拉取了 flomo_memos
# flomo_memos = flomo_database.fetch_flomo_memos(last_sync_time=start_of_day)

def group_memos_by_date(flomo_memos):
    """
    将 flomo_memos 按照 'created_time' 分组，确保每个日期的笔记被放到对应的文件中
    """
    grouped_memos = {}

    for memo in flomo_memos:
        created_time = memo['created_time']
        # 提取日期，格式化为 YYYY_MM_DD
        memo_date = created_time.strftime("%Y_%m_%d")

        if memo_date not in grouped_memos:
            grouped_memos[memo_date] = []

        grouped_memos[memo_date].append(memo)

    return grouped_memos

def convert_to_logseq_content(grouped_memos):
    """
    将按日期分组的笔记转换为 Logseq 格式
    """
    all_content = {}

    for date, memos in grouped_memos.items():
        content = ""
        for memo in memos:
            text = memo['text']
            # 构建 Logseq 内容格式
            logseq_entry = "- ---\n"
            logseq_entry += f"- {text}\n"  # 添加笔记内容

            content += logseq_entry

        # 保存按日期生成的内容
        all_content[date] = content

    return all_content


def push_to_github(content):
    """
    将 Logseq 格式的笔记推送到 GitHub，采用追加而不是覆盖的方式
    """
    for date, date_content in content.items():
        file_name = f"{date}.md"
        file_path = f"{logseq_directory}/{file_name}"

        try:
            # 如果文件不存在，创建文件并推送
            repo.create_file(file_path, f"Add {file_name}", date_content, branch="main")
            logger.log(f"Successfully added {file_name} to GitHub.")
        except Exception as e:
            # 如果文件已存在，追加新内容
            try:
                existing_file = repo.get_contents(file_path, ref="main")
                # 尝试多种编码方式
                try:
                    # 首先尝试 UTF-8
                    existing_content = existing_file.decoded_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        # 如果 UTF-8 失败，尝试 GB18030（支持所有中文字符）
                        existing_content = existing_file.decoded_content.decode('gb18030')
                    except UnicodeDecodeError:
                        # 最后尝试 GBK
                        existing_content = existing_file.decoded_content.decode('gbk')
                
                # 将新内容追加到现有内容后面
                updated_content = existing_content + "\n" + date_content
                
                repo.update_file(
                    existing_file.path, 
                    f"Update {file_name}", 
                    updated_content, 
                    existing_file.sha, 
                    branch="main"
                )
                logger.log(f"Successfully appended content to {file_name} on GitHub.")
            except Exception as e:
                logger.error(f"Error while updating {file_name}: {str(e)}")


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
        # 按日期分组笔记
        grouped_memos = group_memos_by_date(flomo_memos)
        # 转换为 Logseq 格式的内容
        content = convert_to_logseq_content(grouped_memos)
        # 推送到 GitHub
        push_to_github(content)
        logger.log('Finished syncing flomo memos to Github')
    else:
        logger.log('No flomo memos to sync')

    # Update last sync time
    update_time = timeparse.update_last_sync_time()
    logger.log('Update last sync time:', update_time)
    logger.log('Finished')
    logger.log('')
