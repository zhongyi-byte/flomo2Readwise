from notion_client import Client
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt
import pytz

class FlomoDatabase:
	def __init__(self, api_key, database_id, logger, update_tags=True, skip_tags=['', 'welcome']):
		self.notion = Client(auth=api_key)
		self.database_id = database_id
		self.logger = logger
		self.update_tags = update_tags
		self.skip_tags = skip_tags

	@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
	def fetch_flomo_memos(self, last_sync_time=None):
		all_memos = []
		## get 100 pages at a time
		result_list = self.notion.databases.query(self.database_id)
		while result_list:
			# Save content of each page
			for page in result_list['results']:
				flomo_memo = self.fetch_flomo_memo(page, last_sync_time=last_sync_time)
				if flomo_memo:
					all_memos.append(flomo_memo)

			# Check the last page's last_edited_time
			if last_sync_time:
				last_page_created_time = self.parse_created_time(result_list['results'][-1]['created_time'])
				if last_page_created_time < last_sync_time:
					break

			# Get next 100 pages, until no more pages
			if "next_cursor" in result_list and result_list["next_cursor"]:
				result_list = self.notion.databases.query(self.database_id, start_cursor=result_list["next_cursor"])
			else:
				break
		return all_memos
	
	@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
	def fetch_flomo_memo(self, page, last_sync_time=None):
		# Skip pages edited before last_sync_time
		created_time = self.parse_created_time(page['created_time'])
		last_edit_time = self.parse_created_time(page['last_edited_time'])
		if last_sync_time and created_time < last_sync_time:
			return None

		# Get tags, which are separated by slash in flomo
		tags = self.fetch_and_seperate_tags(page)
		for skip_tag in self.skip_tags:
			if skip_tag=='' and len(tags)==0:
				return None
			if skip_tag in tags:
				return None

		# Store seperated tags as a new Multi-select property in Notion
		if self.update_tags:
			self.update_seperated_tags(page, tags)
		
		# Get content text, flomo memo has only one block
		page_blocks = self.notion.blocks.children.list(page['id'])
		text_content = page_blocks['results'][0]['paragraph']['rich_text'][0]['plain_text']
		
		flomo_memo = {
			'tags':			tags,
			'flomo_url':	page['properties']['Link']['url'],
			'created_time': created_time,
			'edit_time':	last_edit_time,
			'text':			text_content
		}

		if flomo_memo['text'] == '':
			return None

		return flomo_memo
	
	""" Tools """
	
	def test_connection(self):
		## Need 'Read user information' permission in Notion Integration
		list_users_response = self.notion.users.list()
		self.logger.log(list_users_response)

	def fetch_and_seperate_tags(self, page):
		# Get tags, which are separated by slash in flomo
		tags_property = page['properties']['Tags']['multi_select']
		if len(tags_property) == 0:
			return []
		tags_slashs = [tag['name'] for tag in tags_property]
		tags = []
		for tags_slash in tags_slashs:
			tags += tags_slash.split('/')
		return tags

	def update_seperated_tags(self, page, tags):
		# add new property to the database if not exist
		if 'Seperated Tags' not in page['properties']:
			self.add_multi_select_property('Seperated Tags')
		# update property if not match
		st = page['properties']['Seperated Tags']['multi_select']
		if len(st) != len(tags) or not all([st[i]['name'] == tags[i] for i in range(len(tags))]):
			self.notion.pages.update(page['id'], properties={
				'Seperated Tags': {
					'multi_select': [{'name': tag} for tag in tags]
				}
			})

	def add_multi_select_property(self, property_name, options=[]):
		# Get the database schema
		database = self.notion.databases.retrieve(self.database_id)
		properties = database['properties']
		# Check if the property already exists
		if property_name in properties:
			return
		# Add the property
		properties[property_name] = {
			'type': 'multi_select',
			'multi_select': {
				'options': options
			}
		}
		# Update the database schema
		self.notion.databases.update(self.database_id, properties=properties)

	def parse_created_time(self, created_time_str):
		# 解析 UTC 时间字符串
		utc_time = datetime.strptime(created_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')

		# 设置 UTC 时区
		utc_timezone = pytz.utc
		utc_time = utc_timezone.localize(utc_time)

		# 转换为上海时区
		shanghai_timezone = pytz.timezone('Asia/Shanghai')
		shanghai_time = utc_time.astimezone(shanghai_timezone)

		return shanghai_time
