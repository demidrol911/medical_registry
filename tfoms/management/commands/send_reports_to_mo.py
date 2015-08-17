# -*- coding: utf-8 -*-

import os
import re
import shutil

#OUTBOX_DIR = u'd:/work/outbox/'
OUTBOX_DIR = u'//s01-2800-fs01/vipnet/medical_registry/outbox/'
ACTS_DIR = u'x:/reestr/g2015/period06/'

AGMA_DIR = u'x:/reestr/g2015/period06/'
custom_file = ''#u'X:/REESTR/G2014/Period10/Больницам октябрь.jpg'

act_name_pattern = re.compile(r'_+\d*$')


def get_outbox_dict(dir):
    dirs = os.listdir(dir)
    outbox_dict = {}

    for d in dirs:
        t = d#.encode('cp1251')
        code, name = t[:6], t[7:]

        outbox_dict[name] = t

    return outbox_dict

outbox_dict = get_outbox_dict(OUTBOX_DIR)

acts = os.listdir(ACTS_DIR)

for act in acts:
    if act.startswith('~'):
        continue

    encoded_act = act#.decode('cp1251')
    name, ext = os.path.splitext(encoded_act)
    parsed_name = act_name_pattern.sub('', name)
    copy_to_dir = outbox_dict.get(parsed_name, None)

    if encoded_act.startswith('~') or encoded_act == u'АГМА' or not copy_to_dir:
        print encoded_act, u'странный акт'
        continue

    #print repr(ACTS_DIR), repr(encoded_act)#.decode('cp1251'))
    src_path = os.path.join(ACTS_DIR, encoded_act)
    #print repr(src_path)

    outbox_dir = outbox_dict.get(parsed_name, None)
    if outbox_dir:
        dst_path = os.path.join(OUTBOX_DIR, copy_to_dir)
        #print dst_path
    else:
        print parsed_name, u'Не нашёл'
        continue

    try:
        shutil.copy2(src_path, dst_path)
        #shutil.copy2(custom_file, dst_path)
    except:
        print u'не смог', dst_path

"""
acts = os.listdir(AGMA_DIR)

for act in acts:
    encoded_act = act
    name, ext = os.path.splitext(encoded_act)
    parsed_name = act_name_pattern.sub('', name)

    copy_to_dir = u'280069 ГБОУ ВПО Амурская государственная медицинская академия Министерства здравоохранения и социального развития Российской Федерации'

    if encoded_act.startswith('~') or not copy_to_dir:
        print 'не смог', encoded_act
        continue

    src_path = os.path.join(AGMA_DIR, encoded_act)
    dst_path = os.path.join(OUTBOX_DIR, copy_to_dir)

    try:
        shutil.copy2(src_path, dst_path)
        #shutil.copy2(custom_file, dst_path)
    except:
        print u'не смог', dst_path
"""