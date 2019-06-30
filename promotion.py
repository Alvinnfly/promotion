# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import logging

from flexget import plugin
from flexget.event import event

import requests
from bs4 import BeautifulSoup

log = logging.getLogger('promotion')


class Filter_Promotion(object):
	"""
		Detect torrent's *current* promotion status.
		Only support sites based on NexusPHP
	Support sites (tested):
		HDChina TJUPT NYPT Ourbits BYRBT NPUBits MTeam...

		Example::
			promotion: 
			  action: accept
			  cookie: * your cookie here *
			  username: * your username here *
			  promotion: free/twoupfree/halfdown/twouphalfdown/thirtypercent/none
			  not_hr: yes [optional]

	"""

	schema = {'type': 'object',
	          'properties': {
		          'action': {
			          'type': 'string',
			          'enum': ['accept', 'reject'],
			          'default': 'accept',
		          },
		          'cookie': {
			          'type': 'string',
		          },
		          'username': {
			          'type': 'string',
		          },
		          'promotion': {
			          'type': 'string',
			          'enum': ['free', 'twoupfree', 'halfdown', 'twouphalfdown', 'thirtypercent', 'none'],
			          'default': 'free',
		          },
		          'not_hr': {
			          'type': 'boolean',
			          'enum': [True, False],
			          'default': False,
		          },
	          },
	          }

	# Run later to avoid unnecessary lookups
	@plugin.priority(115)
	def on_task_filter(self, task, config):
		# check some details first
		##check entry's link field
		if not task.entries[0].get('link'):
			log.critical('link not found, plz add "other_fields: [link]" to rss plugin config')
			return False
		##`not_hr` is only available for ourbits
		if config['not_hr'] and 'ourbits' not in task.entries[0].get('link'):
			log.critical('`not_hr` parameter is only available for ourbits')
			return False

		for entry in task.entries:
			link = entry.get('link')
			if config['action'] == 'accept':
				if self.detect_promotion_status(link, config):
					entry.accept('Entry `%s` is `%s`' % (entry['title'], config['promotion']), remember=True)
				else:
					entry.reject('Entry `%s` is not `%s`' % (entry['title'], config['promotion']), remember=True)

	def detect_promotion_status(self, link, config):
		log.verbose('start to detect %s promotion status' % link)

		cookie = config['cookie']
		username = config['username']

		# get detail page
		headers = {
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
			'accept-encoding': 'gzip, deflate',
			'cookie': cookie,
		}
		try:
			r = requests.get(link, headers=headers, timeout=30)
			r.raise_for_status()
			r.encoding = r.apparent_encoding
			response = r.text
			log.verbose('get page succeed')
		except:
			log.critical('get page failed, please check connection')
			try:
				log.info(response)
			except:
				log.info(r.status_code)
			finally:
				return False

		# assert login status
		try:
			assert username in response
			log.verbose('cookie is valid')
		except:
			log.critical('cookie is expired or username not right, response is logged')
			log.info(response)
			return False

		# assert torrent id
		try:
			assert '没有该ID的种子' not in response
		# log.verbose('torrent id is valid')
		except:
			log.critical('torrent id is not valid, torrent {} does not exist'.format(link))
			log.info(response)
			return False

		# get details_dict
		if "hdchina.org" in link:
			details_dict = self.analyze_hdc_detail(response)
		elif "tjupt.org" in link:
			details_dict = self.analyze_tju_detail(response)
		elif "ourbits.club" in link:
			details_dict = self.analyze_ob_detail(response)
		elif "npupt.com" in link:
			details_dict = self.analyze_npu_detail(response)
		elif "bt.byr.cn" in link:
			details_dict = self.analyze_byr_detail(response)
		else:
			details_dict = self.analyze_nexusphp_detail(response)

		# process ourbits's h&r
		if config['not_hr'] and details_dict['is_hr']:
			return False

		# return accept or reject according to config['promotion']
		if details_dict['promotion'] == config['promotion']:
			return True
		else:
			return False

	def analyze_hdc_detail(self, response):
		convert = {
			'Free': 'free',
			'2X Free': 'twoupfree',
			'50%': 'halfdown',
			'2X 50%': 'twouphalfdown',  # never seen, key maybe wrong
			'30%': 'thirtypercent',
		}
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('h2', id="top")[0]
		promotion_element = topic_element.img
		if promotion_element:
			promotion = convert[promotion_element['alt']]
			log.verbose('torrent promotion status is {}'.format(promotion))
			return {'promotion': promotion}
		else:
			log.verbose('torrent has no promotion')
			return {'promotion': 'none'}

	def analyze_nexusphp_detail(self, response):
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('h1', id="top")[0]
		promotion_element = topic_element.b
		if promotion_element:
			promotion = promotion_element.font['class'][0]
			log.verbose('torrent promotion status is {}'.format(promotion))
			return {'promotion': promotion}
		else:
			log.verbose('torrent has no promotion')
			return {'promotion': 'none'}

	def analyze_byr_detail(self, response):
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('h1', id="share")[0]
		promotion_element = topic_element.b
		if promotion_element:
			promotion = promotion_element.font['class'][0]
			log.verbose('torrent promotion status is {}'.format(promotion))
			return {'promotion': promotion}
		else:
			log.verbose('torrent has no promotion')
			return {'promotion': 'none'}

	def analyze_tju_detail(self, response):
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('h1', id="top")[0]
		promotion_element = topic_element.font
		if promotion_element:
			promotion = promotion_element['class'][0]
			log.verbose('torrent promotion status is {}'.format(promotion))
			return {'promotion': promotion}
		else:
			log.verbose('torrent has no promotion')
			return {'promotion': 'none'}

	def analyze_ob_detail(self, response):
		details_dict = {}
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('h1', id="top")[0]

		promotion_element = topic_element.b
		if promotion_element:
			promotion = promotion_element.font['class'][0]
			log.verbose('torrent promotion status is {}'.format(promotion))
			details_dict['promotion'] = promotion
		else:
			log.verbose('torrent has no promotion')
			details_dict['promotion'] = 'none'

		hr_element = topic_element.img
		if hr_element:
			log.verbose('torrent is h&r')
			details_dict['is_hr'] = True
		else:
			log.verbose('torrent is not h&r')
			details_dict['is_hr'] = False

		return details_dict

	def analyze_npu_detail(self, response):
		convert = {
			'Free': 'free',
			'2X Free': 'twoupfree',
			'50%': 'halfdown',
			'2X 50%': 'twouphalfdown',
			'30%': 'thirtypercent',
		}
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('div', class_="jtextfill")[0]
		promotion_element = topic_element.span.img
		if promotion_element:
			promotion = convert[promotion_element['alt']]
			log.verbose('torrent promotion status is {}'.format(promotion))
			return {'promotion': promotion}
		else:
			log.verbose('torrent has no promotion')
			return {'promotion': 'none'}


@event('plugin.register')
def register_plugin():
	plugin.register(Filter_Promotion, 'promotion', api_ver=2)
