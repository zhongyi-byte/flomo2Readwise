import os

import EnvVariable
import timeparse
from flomoDatabase import FlomoDatabase
from readwise import Readwise
from logger import loguru_logger


last_sync_time_file = 'last_sync_time.txt'
logger = loguru_logger('flomo2readwise')


def sync_flomo_to_readwise():
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
        # Sync flomo memos to Readwise
        readwise = Readwise(EnvVariable.READWISE_ACCESS_TOKEN, logger)
        readwise.create_highlights_from_memos(flomo_memos)
        logger.log('Finished syncing flomo memos to Readwise')
    else:
        logger.log('No flomo memos to sync')

    # Update last sync time
    update_time = timeparse.update_last_sync_time()
    logger.log('Update last sync time:', update_time)
    logger.log('Finished')
    logger.log('')


if __name__ == '__main__':
    sync_flomo_to_readwise()
