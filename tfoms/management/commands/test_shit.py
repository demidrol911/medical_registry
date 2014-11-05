# -*- coding: utf-8 -*-

from lxml import etree


class Node(dict):
    def __init__(self, element):
        self.element = element
        dict.__init__(self)

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            value = None

        if not value and isinstance(value, dict):
            value = value.element.text

        return value


class XmlLikeFileReader(object):

    def __init__(self, file_name):
        self.file_name = file_name

    def find(self, tags):

        file_stream = open(self.file_name, 'rb')

        item = Node(None)

        parents = []
        node_weight = 0

        for event, element in etree.iterparse(
                file_stream, events=("start", "end"),
                encoding='utf-8'):

            if event == 'start':

                if element.tag in tags:
                    node_weight += 1

                if node_weight > 0:
                    parents.append(item)
                    item = Node(element)

            else:

                if node_weight <= 0:
                    continue

                if element.tag in tags:
                    node_weight -= 1
                    element.clear()
                    yield item

                parent = parents.pop()

                if node_weight > 0:

                    if element.tag in parent:

                        items = parent.get(element.tag)

                        if type(items) != list:
                            items = [items]

                        parent[element.tag] = items
                        items.append(item)

                    else:

                        parent[element.tag] = item

                item = parent

        file_stream.close()

sum = 0
xml = XmlLikeFileReader(file_name='D:/work/medical_service_register/HS28002T28_14081.XML')
for i, rec in enumerate(xml.find(tags=('USL'))):
    sum += float(rec['SUMV_USL'] or 0)
    #print i, rec['SUMV_USL'], rec['IDSERV']

print sum