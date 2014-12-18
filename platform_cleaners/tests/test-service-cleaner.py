# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import platform

if platform.system() == 'Linux':
    from platform_cleaners.service import LinuxServiceCleaner as ServiceCleaner
else:
    # No other platforms are currently available
    sys.exit()


def test_check_service_existence():
    service_cleaner = ServiceCleaner()
    service_cleaner._cached_service_all = 'something 1ya\n yadda yadda\n bing'
    assert service_cleaner._check_service_existence('something') is True
    assert service_cleaner._check_service_existence('nada') is False


def test_run_cmd():
    proc = ServiceCleaner.run_cmd(['echo', 'test'])
    assert proc.stdout.read().strip() == 'test'
    assert proc.returncode == 0
