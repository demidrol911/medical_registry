# -*- coding: utf-8 -*-

import os
import re
import shutil

#OUTBOX_DIR = 'd:/work/test/outbox/'
OUTBOX_DIR = u'//alpha/vipnet/medical_registry/outbox/'
ACTS_DIR = 'x:/reestr/g2014/period09/'

AGMA_DIR = u'x:/reestr/g2014/period09/АГМА'
custom_file = u'X:/REESTR/G2014/Period09/Больницам акты МЭК.jpg'

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
    encoded_act = act.decode('cp1251')
    name, ext = os.path.splitext(encoded_act)
    parsed_name = act_name_pattern.sub('', name)

    copy_to_dir = outbox_dict.get(parsed_name, None)

    if encoded_act.startswith('~') or encoded_act == u'АГМА' or not copy_to_dir:
        continue

    src_path = os.path.join(ACTS_DIR, encoded_act)
    dst_path = os.path.join(OUTBOX_DIR, outbox_dict[parsed_name])

    try:
        shutil.copy2(src_path, dst_path)
        shutil.copy2(custom_file, dst_path)
    except:
        print u'не смог', dst_path

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
        shutil.copy2(custom_file, dst_path)
    except:
        print u'не смог', dst_path