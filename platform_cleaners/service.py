# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import sys
import time
import platform
import subprocess

from . import BasePlatformCleaner

import logging
log = logging.getLogger(__name__)


class LinuxServiceCleaner(BasePlatformCleaner):
    '''
    Manage services on Linux platforms via the 'service' utility.
    '''
    sub_parser_name = 'service_cleaner'

    def __init__(self, restart=None, ignore=False, if_exists=False, **kwargs):
        self.restart_services = restart or []
        self.ignore = ignore
        self.if_exists = if_exists

    @staticmethod
    def run_cmd(cmd, max_wait=2):
        start = time.time()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            if proc.poll is not None:
                break
            if time.time() - start > max_wait:
                log.warn('Command failed, took too long to finish: %s' % cmd)
                proc.terminate()
            else:
                time.sleep(1)
        proc.wait()
        return proc

    _cached_service_all = None  # To save on future service status lookups

    def _check_service_existence(self, service):
        '''
        Ensure that something like the passed in service name shows up in the
        service status list. chkconfig is a nice utility for getting the
        service list on CentOS, however, service --status-all is more universal
        and we can still get what we want from its output.
        '''
        if not self._cached_service_all:
            proc = self.run_cmd(['service', '--status-all'])
            self._cached_service_all = proc.stdout.read()
        return True if re.search(service, self._cached_service_all) else False

    def restart_service(self, service, if_exists=True):
        if self._check_service_existence(service) or not if_exists:
            proc = self.run_cmd(['service', service, 'restart'])
            rv = proc.returncode
            if rv != 0:
                log.warn('Failed to restart %s, returned: %i' % (service, rv))
            else:
                log.debug('Successfully restarted %s' % service)
            return rv
        log.debug('Service seems not to exist, skipping restart: %s' % service)
        return

    @staticmethod
    def check_platform():
        if platform.system() == 'Linux':
            return True
        return

    @classmethod
    def add_arguments(cls, parser, sub_parser):
        service_parser = sub_parser.add_parser(cls.sub_parser_name)
        service_parser.add_argument(
            '--restart',
            nargs='+',
            help='Restart system services by name.'
        )
        service_parser.add_argument(
            '--if-exists',
            dest='if_exists',
            action='store_const',
            const=True,
            help='Skip operations against services which appear to not exist.'
        )
        service_parser.add_argument(
            '--ignore',
            dest='ignore',
            action='store_const',
            const=True,
            help='Ignore errors default: False)'
        )

    def enforce(self, dryrun=False):
        for service in self.restart_services:
            log.debug('Attempting service restart: %s' % service)
            if dryrun:
                continue
            rv = self.restart_service(service, self.if_exists)
            if not self.ignore and rv is not None and rv != 0:
                sys.exit(rv)
