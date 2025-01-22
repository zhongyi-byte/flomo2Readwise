import os
from datetime import datetime, timedelta
from flomoDatabase import FlomoDatabase
from readwise import Readwise
from logger import loguru_logger
from dotenv import load_dotenv

load_dotenv()

NOTION_INTEGRATION_TOKEN = os.getenv('NOTION_INTEGRATION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
READWISE_ACCESS_TOKEN = os.getenv('READWISE_ACCESS_TOKEN')

# Only sync new memos by managing a last sync time
# Both Github Actions and Notion API are in UTC time zone
last_sync_time_file = 'last_sync_time.txt'
# Save all logs to a same file
logger = loguru_logger('flomo2readwise')


def get_last_sync_time():
    if not os.path.exists(last_sync_time_file):
        return None
    with open(last_sync_time_file, 'r') as f:
        time = f.read().strip()
        return datetime.fromisoformat(time)


def update_last_sync_time():
    update_time = datetime.now()  # UTC time on Github Actions
    with open(last_sync_time_file, 'w') as f:
        f.write(str(update_time))
    return update_time


def sync_flomo_to_readwise():
    # Get last sync time
    last_sync_time = get_last_sync_time()
    if last_sync_time:
        logger.log('Last sync time:', last_sync_time)
    else:
        logger.log('First sync')

    # Fetch flomo memos
    flomo_database = FlomoDatabase(NOTION_INTEGRATION_TOKEN, NOTION_DATABASE_ID, logger)
    flomo_memos = flomo_database.fetch_flomo_memos(last_sync_time=last_sync_time)
    logger.log('Number of flomo memos to sync:', len(flomo_memos))

    if len(flomo_memos) > 0:
        # Sync flomo memos to Readwise
        readwise = Readwise(READWISE_ACCESS_TOKEN, logger)
        readwise.create_highlights_from_memos(flomo_memos)
        logger.log('Finished syncing flomo memos to Readwise')
    else:
        logger.log('No flomo memos to sync')

    # Update last sync time
    update_time = update_last_sync_time()
    logger.log('Update last sync time:', update_time)
    logger.log('Finished')
    logger.log('')


if __name__ == '__main__':
    sync_flomo_to_readwise()
