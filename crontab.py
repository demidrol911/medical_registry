#! -*- coding: utf-8 -*-

import subprocess
import time
import logging
import os
from main.logger import LOGGING_DIR

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler(os.path.join(LOGGING_DIR, 'crontab.log'))
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console_handler)


class Job:
    COMPLETED_RECENTLY = 0
    COMPLETED_LONG_TIME = 1
    PERFORMED = 2
    NOT_RUNNING = 3
    COMPLETED_ERROR = 4

    def __init__(self, name, cmd, duration):
        self._process = None
        self.name = name
        self.cmd = cmd
        self.duration = duration
        self.terminate = False
        self._lastest_call_time = 0

    def run(self):
        status = self.get_run_status()
        if (status in [Job.COMPLETED_RECENTLY, Job.COMPLETED_LONG_TIME, Job.COMPLETED_ERROR]
            and self.duration <= time.clock() - self._lastest_call_time) or status == Job.NOT_RUNNING:
            self._process = subprocess.Popen(self.cmd, shell=True)
            self._lastest_call_time = time.clock()
            self.terminate = False
            logger.info(u'%s запущена' % self.name)

    def get_run_status(self):
        if not self._process:
            return Job.NOT_RUNNING
        elif self._process and self._process.poll() == 0:
            if self.terminate:
                return Job.COMPLETED_LONG_TIME
            else:
                logger.info(u'%s завершёна' % self.name)
                self.terminate = True
                return Job.COMPLETED_RECENTLY
        elif self._process and self._process.poll() is None:
            return Job.PERFORMED
        else:
            if not self.terminate:
                logger.error(u'%s завершёна аварийно' % self.name)
                self.terminate = True
            return Job.COMPLETED_ERROR


class SimpleScheduler:

    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def run(self):
        while True:
            for job in self.jobs:
                job.run()
            time.sleep(30)

scheduler = SimpleScheduler()
scheduler.add_job(Job(name='reg_import', cmd=u'C:/Python27/python.exe manage.py reg_import', duration=600))
scheduler.add_job(Job(name='mek', cmd=u'C:/Python27/python.exe manage.py new_mek', duration=600))
scheduler.add_job(Job(name='send_mek', cmd=u'C:/Python27/python.exe manage.py send_mek_to_mo', duration=300))
scheduler.add_job(Job(name='summary_report', cmd=u'C:/Python27/python.exe manage.py summary_report', duration=300))
scheduler.run()
