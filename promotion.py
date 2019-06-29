# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import logging

from flexget import plugin
from flexget.event import event

import requests
# import brotli
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
			  promotion: free/twoupfree/halfdown/twouphalfdown/thirtypercent/none

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
	          },
	          }

	# Run later to avoid unnecessary lookups
	@plugin.priority(115)
	def on_task_filter(self, task, config):
		for entry in task.entries:
			link = entry.get('link')
			try:
				assert link
			except:
				log.critical('link not found, plz add "other_fields: [link]" to rss plugin config')

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
			response = r.text  # brotli.decompress(r.content).decode('utf-8')
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

		# detect promotion status
		if "hdchina.org" in link:
			promotion = self.analyze_hdc_promotion(response)
		else:
			promotion = self.analyze_nexusphp_promotion(response)

		# return accept or reject according to config['promotion']
		if promotion == config['promotion']:
			return True
		else:
			return False

	def analyze_hdc_promotion(self, response):
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
			return promotion
		else:
			log.verbose('torrent has no promotion')
			return 'none'

	def analyze_nexusphp_promotion(self, response):
		soup = BeautifulSoup(response, 'html.parser')
		topic_element = soup.find_all('h1', id="top")[0]
		promotion_element = topic_element.font
		if promotion_element:
			promotion = promotion_element['class'][0]
			log.verbose('torrent promotion status is {}'.format(promotion))
			return promotion
		else:
			log.verbose('torrent has no promotion')
			return 'none'


@event('plugin.register')
def register_plugin():
	plugin.register(Filter_Promotion, 'promotion', api_ver=2)
