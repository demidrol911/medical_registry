class Xml:
    
    def __init__(self, filename):
        self.file = open(filename, 'wb')
        self.whitespaces = 0
    
    def start(self, element):
        self.file.write('%s<%s>\n' % (' '*self.whitespaces, element))
        self.whitespaces += 2
    
    def end(self, element):
        self.whitespaces -= 2
        self.file.write('%s</%s>\n' % (' '*self.whitespaces, element))
        
    def put(self, element, value):
        self.file.write('%s<%s>%s</%s>\n' % (' '*self.whitespaces, element, value, element))
        
    def plain_put(self, value):
        self.file.write('%s\n' % value)
    
    def close(self):
        self.file.close()