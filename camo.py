import codecs
import hashlib
import hmac
import re
from memoize import mproperty
from lxml import html


class CamoClient(object):
    def __init__(self, server, key):
        self.server = re.sub('/+$', '', server)
        self.key = key

    def image_url(self, url):
        return self.server + Image(url, self.key).path

    def _rewrite_url(self, url):
        if url.startswith(self.server):
            return url
        elif not any(map(url.startswith, ["http://", "https://"])):
            return url
        else:
            return self.image_url(url)

    def _rewrite_image_urls(self, node):
        for img in node.xpath('.//img'):
            if img.get('src'):
                img.set('src', self._rewrite_url(img.get('src')))
        return node

    def _rewrite_style_urls(self, node):
        for link in node.xpath('.//link[@rel="stylesheet"]'):
            if link.get('href'):
                link.set('href', self._rewrite_url(link.get('href')))
        return node

    def parse_html(self, string):
        doc = html.fromstring(string.join(['<div>', '</div>']))
        doc = self._rewrite_image_urls(doc)
        doc = self._rewrite_style_urls(doc)
        # iterating over a node returns all the tags within that node
        # ..if there are none, return the original string
        return ''.join(html.tostring(node, encoding='unicode') for node in doc) or string


class Image(object):
    def __init__(self, url, key):
        self.url = url.encode('utf-8')
        self.key = key

    @mproperty
    def path(self):
        return "/%s/%s" % (self.digest, self.encoded_url)

    @mproperty
    def digest(self):
        return hmac.new(self.key, self.url, hashlib.sha1).hexdigest()

    @mproperty
    def encoded_url(self):
        return codecs.encode(self.url, "hex").decode('utf-8')
