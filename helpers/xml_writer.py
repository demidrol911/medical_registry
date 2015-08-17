class Xml:

    started_tags = 0
    ended_tags = 0

    tags = 0

    def __init__(self, filename):
        self.file = open(filename, 'wb')
        self.whitespaces = 0
    
    def start(self, element):
        self.tags += 2
        self.file.write('%s<%s>\n' % (' '*self.whitespaces, element.upper()))
        self.whitespaces += 2

        self.started_tags += 1

    def end(self, element):
        #if self.ended_tags >= self.started_tags -1 and element != 'EXP_CASES':
        #    return False

        #if self.tags == 0:
        #    return False

        self.tags -= 1
        self.whitespaces -= 2
        self.file.write('%s</%s>\n' % (' '*self.whitespaces, element.upper()))

        self.ended_tags += 1
        
    def put(self, element, value):
        self.file.write('%s<%s>%s</%s>\n' % (' '*self.whitespaces,
                                             element.upper(),
                                             value,
                                             element.upper()))
        
    def plain_put(self, value):
        self.file.write('%s\n' % value)
    
    def close(self):
        self.file.close()