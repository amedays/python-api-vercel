from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from xml.dom import minidom as DOM
import requests
from urllib import parse
import logging
# import urllib


class handler(BaseHTTPRequestHandler):
    '''合并rss'''
    # TODO: 添加更多的筛选功能

    def do_GET(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - "%(pathname)s", line %(lineno)d, - %(levelname)s: %(message)s')
        logger = logging.getLogger(__name__)
        try:
            class Item():
                '''能够根据指定属性判断item重复'''

                def __init__(self, node, diff="guid"):
                    self._node = node
                    self.diff = diff

                def __eq__(self, other):
                    return self._node.getAttribute(self.diff) == other._node.getAttribute(self.diff)

            def get_rss_xml(url: str):
                ''':param url: rss url\n
                :return: xml string'''
                res = requests.get(url)
                return res.text

            def get_dom(xml: str):
                tree = DOM.parseString(xml)
                return tree

            def get_items_from_xml(tree):
                ''':param xml: xml string\n
                :return: items list'''
                root = tree.documentElement
                channel = root.getElementsByTagName("channel")
                if channel:
                    channel = channel[0]
                    items = channel.getElementsByTagName("item")
                return items if items else None

            path = self.path
            query = parse.parse_qs(parse.urlsplit(path).query)
            items = []
            first = None
            # 获取模板rss与items
            if "rss" in query:
                urls = query["rss"]
                first = get_dom(get_rss_xml(urls[0]))
                items = [item for item in get_items_from_xml(first)]
                items_first = items.copy()
                items = [Item(item) for item in items]
                for url in urls[1:]:
                    xml = get_rss_xml(url)
                    tree = get_dom(xml)
                    tree_item = get_items_from_xml(tree)
                    for item in tree_item:
                        item = Item(item)
                        if item not in items:
                            items.append(item)
            if items:
                items = [item._node for item in items]
                root = first.documentElement
                channel = root.getElementsByTagName("channel")
                if channel:
                    channel = channel[0]
                    for item in items_first:
                        channel.removeChild(item)
                    for item in items:
                        channel.appendChild(item)
            res = first.toprettyxml(encoding="utf-8") if first else None
        except Exception as e:
            raise e
        self.send_response(200)
        self.send_header('Content-type', 'application/xml')
        self.end_headers()

        if not res:
            res = "无返回错误"
        if isinstance(res, str):
            logger.debug(res)
            res = res.encode()
        elif isinstance(res, bytes):
            logger.debug(res.decode())
        self.wfile.write(res)
        return


if __name__ == "__main__":
    def start_server(port):
        http_server = HTTPServer(('', int(port)), handler)
        http_server.serve_forever()
    start_server(8000)
