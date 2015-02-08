from main.models import ProvidedEvent
from medical_service_register.path import IMPORT_ARCHIVE_DIR
import shutil, os
from registry_import.xml_parser import XmlLikeFileReader
from django.core.management.base import BaseCommand
from main.funcs import safe_int

"""
files_name = [
'DPM280009S28002_141214.xml',
'HM280009S28002_141214.xml',
'DPM280040S28002_141214.xml',
'HM280040S28002_141214.xml',
'HM280023S28002_14126.xml',
'DPM280037S28002_14128.xml',
'HM280037S28002_14128.xml',
'HM280061S28002_14127.xml',
'HM280093S28002_14123.xml',
'DFM280078S28002_14126.xml',
'DPM280078S28002_14126.xml',
'DRM280078S28002_14126.xml',
'DVM280078S28002_14126.xml',
'HM280078S28002_14126.xml',
'HM280013S28002_14123.xml',
'DFM280084S28002_14129.xml',
'DOM280084S28002_14129.xml',
'DPM280084S28002_14129.xml',
'DRM280084S28002_14129.xml',
'DVM280084S28002_14129.xml',
'HM280084S28002_14129.xml',
'DPM280074S28002_14123.xml',
'HM280074S28002_14123.xml',
'DFM280024S28002_141215.xml',
'DOM280024S28002_141215.xml',
'DPM280024S28002_141215.xml',
'DRM280024S28002_141215.xml',
'DSM280024S28002_141215.xml',
'HM280024S28002_141215.xml',
'HM280096S28002_14126.xml',
'DDM280007S28002_14127.xml',
'DFM280007S28002_14127.xml',
'DOM280007S28002_14127.xml',
'DPM280007S28002_14127.xml',
'DRM280007S28002_14127.xml',
'DUM280007S28002_14127.xml',
'DVM280007S28002_14127.xml',
'HM280007S28002_14127.xml',
'DFM280071S28002_141216.xml',
'DOM280071S28002_141216.xml',
'DPM280071S28002_141216.xml',
'DVM280071S28002_141216.xml',
'HM280071S28002_141216.xml',
'DFM280019S28002_14125.xml',
'DOM280019S28002_14125.xml',
'DPM280019S28002_14125.xml',
'DRM280019S28002_14125.xml',
'HM280019S28002_14125.xml',
'HM280088S28002_141215.xml',
'DOM280069S28002_14125.xml',
'DPM280069S28002_14125.xml',
'DVM280069S28002_14125.xml',
'HM280069S28002_14125.xml',
'HM280005S28002_14125.xml',
'DDM280067S28002_14124.xml',
'DFM280067S28002_14124.xml',
'HM280067S28002_14124.xml',
'HM280043S28002_14121.xml',
'TM280043S28002_14121.xml',
'DFM280029S28002_14128.xml',
'DOM280029S28002_14128.xml',
'DPM280029S28002_14128.xml',
'DRM280029S28002_14128.xml',
'DUM280029S28002_14128.xml',
'HM280029S28002_14128.xml',
'HM280004S28002_14121.xml',
'DFM280001S28002_141211.xml',
'DOM280001S28002_141211.xml',
'DPM280001S28002_141211.xml',
'DRM280001S28002_141211.xml',
'DSM280001S28002_141211.xml',
'DUM280001S28002_141211.xml',
'DVM280001S28002_141211.xml',
'HM280001S28002_141211.xml',
'DFM280020S28002_14126.xml',
'DOM280020S28002_14126.xml',
'DPM280020S28002_14126.xml',
'DUM280020S28002_14126.xml',
'HM280020S28002_14126.xml',
'HM280070S28002_14126.xml',
'DDM280059S28002_14124.xml',
'DFM280059S28002_14124.xml',
'DOM280059S28002_14124.xml',
'DPM280059S28002_14124.xml',
'DRM280059S28002_14124.xml',
'DSM280059S28002_14124.xml',
'HM280059S28002_14124.xml',
'DDM280012S28002_141212.xml',
'DFM280012S28002_141212.xml',
'DOM280012S28002_141212.xml',
'DPM280012S28002_141212.xml',
'DRM280012S28002_141212.xml',
'DSM280012S28002_141212.xml',
'DVM280012S28002_141212.xml',
'HM280012S28002_141212.xml',
'DFM280076S28002_14126.xml',
'DOM280076S28002_14126.xml',
'HM280076S28002_14126.xml',
'HM280018S28002_14128.xml',
'DFM280002S28002_14129.xml',
'DOM280002S28002_14129.xml',
'DSM280002S28002_14129.xml',
'DUM280002S28002_14129.xml',
'DVM280002S28002_14129.xml',
'HM280002S28002_14129.xml',
'DFM280025S28002_141211.xml',
'DOM280025S28002_141211.xml',
'DPM280025S28002_141211.xml',
'HM280025S28002_141211.xml',
'DOM280022S28002_14126.xml',
'DPM280022S28002_14126.xml',
'HM280022S28002_14126.xml',
'DDM280080S28002_14127.xml',
'DFM280080S28002_14127.xml',
'DOM280080S28002_14127.xml',
'DPM280080S28002_14127.xml',
'DRM280080S28002_14127.xml',
'DUM280080S28002_14127.xml',
'DVM280080S28002_14127.xml',
'HM280080S28002_14127.xml',
'DOM280083S28002_14124.xml',
'DPM280083S28002_14124.xml',
'DVM280083S28002_14124.xml',
'HM280083S28002_14124.xml',
'DFM280039S28002_14127.xml',
'DOM280039S28002_14127.xml',
'DPM280039S28002_14127.xml',
'HM280039S28002_14127.xml',
'DFM280017S28002_141210.xml',
'DOM280017S28002_141210.xml',
'DPM280017S28002_141210.xml',
'DRM280017S28002_141210.xml',
'DUM280017S28002_141210.xml',
'DVM280017S28002_141210.xml',
'HM280017S28002_141210.xml',
'DVM280066S28002_141212.xml',
'HM280066S28002_141212.xml',
'DDM280064S28002_141215.xml',
'DFM280064S28002_141215.xml',
'DRM280064S28002_141215.xml',
'DSM280064S28002_141215.xml',
'DUM280064S28002_141215.xml',
'HM280064S28002_141215.xml',
'DDM280053S28002_14128.xml',
'DFM280053S28002_14128.xml',
'DOM280053S28002_14128.xml',
'DPM280053S28002_14128.xml',
'DRM280053S28002_14128.xml',
'DVM280053S28002_14128.xml',
'HM280053S28002_14128.xml',
'DDM280068S28002_14128.xml',
'DFM280068S28002_14128.xml',
'DOM280068S28002_14128.xml',
'DPM280068S28002_14128.xml',
'HM280068S28002_14128.xml',
'DDM280041S28002_141216.xml',
'DPM280041S28002_141216.xml',
'HM280041S28002_141216.xml',
'HM280026S28002_141212.xml',
'HM280082S28002_14121.xml',
'HM280086S28002_14121.xml',
'DDM280027S28002_14127.xml',
'DFM280027S28002_14127.xml',
'DOM280027S28002_14127.xml',
'DPM280027S28002_14127.xml',
'DRM280027S28002_14127.xml',
'DUM280027S28002_14127.xml',
'DVM280027S28002_14127.xml',
'HM280027S28002_14127.xml',
'DFM280003S28002_14123.xml',
'DOM280003S28002_14123.xml',
'DPM280003S28002_14123.xml',
'DVM280003S28002_14123.xml',
'HM280003S28002_14123.xml',
'TM280003S28002_14123.xml',
'DDM280075S28002_14129.xml',
'DFM280075S28002_14129.xml',
'DOM280075S28002_14129.xml',
'DPM280075S28002_14129.xml',
'DVM280075S28002_14129.xml',
'HM280075S28002_14129.xml',
'DOM280015S28002_14127.xml',
'DPM280015S28002_14127.xml',
'HM280015S28002_14127.xml',
'DOM280036S28002_14121.xml',
'DPM280036S28002_14121.xml',
'DVM280036S28002_14121.xml',
'HM280036S28002_14121.xml',
'HM280010S28002_14126.xml',
'HM280054S28002_14121.xml',
'DVM280085S28002_14121.xml',
'HM280085S28002_14121.xml',
'DOM280038S28002_14121.xml',
'DPM280038S28002_14121.xml',
'DVM280038S28002_14121.xml',
'HM280038S28002_14121.xml',
'DOM280065S28002_14127.xml',
'DPM280065S28002_14127.xml',
'HM280065S28002_14127.xml',
'DOM280052S28002_14127.xml',
'DPM280052S28002_14127.xml',
'DVM280052S28002_14127.xml',
'HM280052S28002_14127.xml',
'HM280091S28002_141211.xml',
'DOM280028S28002_14123.xml',
'DPM280028S28002_14123.xml',
'HM280028S28002_14123.xml']

input_dir = ur"C:\work\register_import_archive"
output_dir = ur'c:\work\dir'

for name in files_name:
    print os.path.join(input_dir, name)
    if os.path.exists(os.path.join(input_dir, name)):
        shutil.copy(os.path.join(input_dir, name), os.path.join(output_dir, name))
    else:
        print name
"""


output_dir = ur'c:\work\dir'


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = '2014'
        period = '12'
        file_not_found = file('not_found.csv', 'w')
        ignore = [
            'HM280001S28002_141013.xml',
            'HM280002S28002_141010.xml',
            'HM280003S28002_14104.xml',
            'HM280004S28002_14101.xml',
            'HM280007S28002_141010.xml',
            'HM280009S28002_14101.xml',
            'HM280010S28002_14104.xml',
            'HM280012S28002_141015.xml',
            'HM280013S28002_141010.xml',
            'HM280015S28002_14107.xml',
            'HM280017S28002_141020.xml'
        ]
        #os.listdir(output_dir)
        for n, file_name in enumerate(os.listdir(output_dir)):

            print file_name, n
            service_file = XmlLikeFileReader(os.path.join(output_dir, file_name))
            file_not_found.write(' '+file_name+'\n')
            for item in service_file.find(tags='ZAP'):
                #service['EXTR']
                events = [item['SLUCH']] if type(item['SLUCH']) != list else \
                    item['SLUCH']
                for event in events:
                    #print (item['N_ZAP'], event['IDCASE'], event['LPU'], event['LPU_1'], file_name)
                    db_event = ProvidedEvent.objects.filter(id=event['IDCASE'],
                                                            organization__code=event['LPU'],
                                                            department__old_code=event['LPU_1'],
                                                            record__register__filename=file_name,
                                                            record__id=item['N_ZAP'],
                                                            record__register__is_active=True,
                                                            record__register__year=year,
                                                            record__register__period=period)
                    if db_event.count() == 1:
                        hosp = event['COMENTSL']
                         #= db_event[0]
                        if hosp:
                            #print hosp
                            ProvidedEvent.objects.filter(id_pk=db_event[0].pk).update(comment=hosp)
                        #event_obj.hospitalization__id_pk = hosp
                        #print event_obj.hospitalization__id_pk
                        #event_obj.
                    elif db_event.count() > 1:
                        print (item['N_ZAP'], event['IDCASE'], event['LPU'], event['LPU_1'], file_name)
                    else:
                        #print (item['N_ZAP'], event['IDCASE'], event['LPU'], event['LPU_1'], file_name)
                        file_not_found.write(str((item['N_ZAP'], event['IDCASE'], event['LPU'], event['LPU_1'], file_name))+'\n')
        file_not_found.close()

