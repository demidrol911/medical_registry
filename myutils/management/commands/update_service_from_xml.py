from main.models import ProvidedService
from medical_service_register.path import IMPORT_ARCHIVE_DIR
import shutil, os
from registry_import.xml_parser import XmlLikeFileReader
from django.core.management.base import BaseCommand
from main.funcs import safe_int

"""
files_name = [
    'DOM280065S28002_14114.xml',
'DPM280065S28002_14114.xml',
'HM280065S28002_14114.xml',
'DPM280037S28002_14114.xml',
'HM280037S28002_14114.xml',
'HM280070S28002_14116.xml',
'HM280023S28002_14115.xml',
'HM280091S28002_141112.xml',
'HM280010S28002_14112.xml',
'DFM280041S28002_141123.xml',
'DOM280041S28002_141123.xml',
'DPM280041S28002_141123.xml',
'HM280041S28002_141123.xml'

    ]

input_dir = IMPORT_ARCHIVE_DIR
output_dir = ur'c:\work\dir'

for name in files_name:
    if os.path.exists(os.path.join(input_dir, name)):
        shutil.copy(os.path.join(input_dir, name), os.path.join(output_dir, name))
    else:
        print name


"""
output_dir = ur'c:\work\dir'


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = '2014'
        period = '11'
        file_not_found = file('not_found.csv', 'w')
        ignore = ['HM280083S28002_14114.xml'
        ]
        #os.listdir(output_dir)
        for n, file_name in enumerate(ignore):
            """
            if file_name in ignore:
                continue
            """
            print file_name, n
            service_file = XmlLikeFileReader(os.path.join(output_dir, file_name))
            file_not_found.write(' '+file_name+'\n')
            for item in service_file.find(tags='ZAP'):
                #service['EXTR']
                events = [item['SLUCH']] if type(item['SLUCH']) != list else \
                    item['SLUCH']
                for event in events:
                    #print '****', event['IDCASE']
                    #print (item['N_ZAP'], event['IDCASE'], event['LPU'], event['LPU_1'], event['USL'], file_name)
                    services = [event['USL']] if type(
                                event['USL']) != list else event['USL']
                    for service in services:
                        comment = service['COMENTU']
                        if event['USL_OK'] == '1':
                            print event['USL_OK'],
                            if service['CODE_USL'].startswith('A'):
                                print service['CODE_USL']
                            else:
                                print 'no'
                        """if comment:
                            #print comment
                            db_service = ProvidedService.objects.filter(
                                event__id=event['IDCASE'],
                                organization__code=event['LPU'],
                                department__old_code=event['LPU_1'],
                                event__record__register__filename=file_name,
                                event__record__id=item['N_ZAP'],
                                event__record__register__is_active=True,
                                event__record__register__year=year,
                                id=service['IDSERV'],
                                event__record__register__period=period)

                            if db_service.count() == 1:

                                #print (item['N_ZAP'], event['IDCASE'],  service['IDSERV'], event['LPU'], event['LPU_1'], file_name)
                                 #= db_event[0]
                                ProvidedService.objects.filter(id_pk=db_service[0].pk).update(comment=comment)
                                #event_obj.hospitalization__id_pk = hosp
                                #print event_obj.hospitalization__id_pk
                                #event_obj.
                            elif db_service.count() > 1:
                                pass

                                print ''(item['N_ZAP'], event['IDCASE'],  service['IDSERV'], event['LPU'], event['LPU_1'], file_name)
                            else:
                                #print (item['N_ZAP'], event['IDCASE'], event['LPU'], event['LPU_1'], file_name)
                                file_not_found.write(str((item['N_ZAP'], event['IDCASE'],  service['IDSERV'], event['LPU'], event['LPU_1'], file_name))+'\n')
                            """
        file_not_found.close()



