#! -*- coding: utf-8 -*-

from lxml import etree
from os import path


def print_xml(output_file, xml_obj, tab=0):
    for node in xml_obj.getchildren():
        output_file.write(' '*tab)
        output_file.write('<%s>' % node.tag)
        if node.getchildren():
            output_file.write('\n')
            print_xml(output_file, node, tab+1)
            output_file.write(' '*tab)
        else:
            output_file.write((node.text or '').encode('utf-8'))

        output_file.write('</%s>\n' % node.tag)


def main():
    xml_file_name = 'HM280007S28004_160514.xml'
    output_dir = ur'C:\work\dir'
    target_dir = ur'c:\work\xml_struct'

    file_xml = file(path.join(output_dir, xml_file_name))
    xml_str = ""
    for line in file_xml:
        xml_str += line
    xml_obj = etree.fromstring(xml_str)

    new_xml_name = xml_file_name.split('.')[0]+'_st.xml'
    output_file = file(path.join(target_dir, new_xml_name), 'w')
    print_xml(output_file, xml_obj)
    output_file.close()

main()