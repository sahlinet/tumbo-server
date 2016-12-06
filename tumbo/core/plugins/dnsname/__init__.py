import os
import logging
import requests
import inspect

from django.conf import settings

from core.plugins import Plugin
from core.plugins.registry import register_plugin

logger = logging.getLogger(__name__)


class DigitaloceanDns():

	def __init__(self, token, domain):
		self.URL = "https://api.digitalocean.com/v2/domains/%s/records" % domain
		self.headers = {'Authorization': "Bearer %s" % token}
		self.data = None

	def update(self, hostname, ip, type="A"):
		self.data = {
				'type': type,
				'name': hostname,
				'data': ip
		}
		self.r = requests.get(self.URL, data={'per_page': 200}, headers=self.headers)
		self.records = self.r.json()

		id = self._get_record(hostname, type)
		if id:
			r = requests.put(self.URL+"/%s" % id, self.data, headers=self.headers)
		else:
			r = requests.post(self.URL, self.data, headers=self.headers)
		logger.info((hostname, ip, r.status_code, r.text))
		return hostname, ip, r.status_code

	def delete(self, hostname, type="A"):
		id = self._get_record(hostname, type)
		r = requests.delete(self.URL+"/%s" % id,headers=self.headers)
		return r.status_code

	def _get_record(self, hostname, type):
		r = requests.get(self.URL, data={'per_page': 200}, headers=self.headers)
		records = r.json()

		for record in records['domain_records']:
				if record['name'] == hostname and record['type'] == type:
						logger.info("%s-Record for host %s found with id '%s'" % (type, hostname, record['id']))
						return record['id']
		logger.debug("%s-Record for host %s not found" % (type, hostname))
		return None


@register_plugin
class DNSNamePlugin(Plugin):

	@classmethod
	def init(cls):
		plugin_path = os.path.dirname(inspect.getfile(cls))
		template_path = os.path.join(plugin_path, "templates")
		settings.TEMPLATE_DIRS = settings.TEMPLATE_DIRS + (template_path,)

	def cockpit_context(self):
		plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.dnsname']
		token = plugin_settings['token']
		domain = plugin_settings['zone']
		return {'DIGITALOCEAN_ZONE': domain}

	def on_start_base(self, base, **kwargs):
		logger.info(str(self.__class__.name) + " " + inspect.stack()[0][3])

		plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.dnsname']
		token = plugin_settings['token']
		domain = plugin_settings['zone']
		dns = DigitaloceanDns(token, domain)

		for counter, executor in enumerate(base.executors):
			dns_name = self._make_dns_name(base, counter)
			logger.info("Add '%s' to DNS zone %s" % (dns_name, domain))
			dns.update(dns_name, executor['ip'])
			dns.update(dns_name+"-v4", executor['ip'])
			if executor['ip6']:
				dns.update(dns_name, executor['ip6'], type="AAAA")
				dns.update(dns_name+"-v6", executor['ip6'], type="AAAA")

	def on_destroy_base(self, base):
		logger.info(str(self.__class__.name) + " " + inspect.stack()[0][3])

		plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.dnsname']
		token = plugin_settings['token']
		domain = plugin_settings['zone']
		dns = DigitaloceanDns(token, domain)

		for counter, executor in enumerate(base.executors):
			logger.info(executor)
			dns_name = self._make_dns_name(base, counter)
			logger.info("Delete '%s' from DNS zone %s" % (dns_name, domain))
			dns.delete(dns_name)
			if executor['ip6']:
				dns.delete(dns_name, type="AAAA")

	def _executor_context(self, executor):
		context = {}
		#for counter, executor in enumerate(base.executors):
		#	k = "%s_executor_%s" % (base, counter)
		#	v =  self._make_dns_name(base, executor)
		#	context[k] = v

		#k = "%s_executor" % (executor.base)

		k = "SERVICE_DNS"
		v =  self._make_dns_name(executor.base, 0)
		plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.dnsname']
		domain = plugin_settings['zone']
		v = v + "." + domain
		context[k] = v

		k = "SERVICE_DNS_V4"
		v =  self._make_dns_name(executor.base, 0)+"-v4"
		plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.dnsname']
		domain = plugin_settings['zone']
		v = v + "." + domain
		context[k] = v

		k = "SERVICE_DNS_V6"
		v =  self._make_dns_name(executor.base, 0)+"-v6"
		plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.dnsname']
		domain = plugin_settings['zone']
		v = v + "." + domain
		context[k] = v

		return context

	def return_to_executor(self, executor):
		return self._executor_context(executor)

	def _make_dns_name(self, base, counter):
		dns_name = "%s-%s-%i" % (base.user.username, base.name, counter)
		return dns_name.replace("_", "-").lower()
