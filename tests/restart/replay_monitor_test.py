import datetime
import os
from pathlib import Path
import sys
import shutil
import tempfile
from types import SimpleNamespace
import unittest

import replay_monitor as monitor


class ReplayMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.helper = SimpleNamespace(RUN=self.root, STOP=self.root/'STOP', record={'commands':[]}, save=lambda:None, now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat(), allocated_size=lambda:1)
        self.limits = {'clean_seconds':2, 'go_seconds':3, 'outer_seconds':4, 'max_bytes':100, 'sample_seconds':0.02}

    def run_child(self, body):
        return monitor.run_monitored(self.helper, [sys.executable, '-c', body], self.root, os.environ.copy(), self.limits)

    def wait_for_stop(self):
        return "from pathlib import Path; import time,sys\np=Path('STOP')\nend=time.monotonic()+5\nwhile not p.exists() and time.monotonic()<end: time.sleep(.01)\nsys.exit(1 if p.exists() else 9)"

    def test_success_keeps_stop_absent(self):
        self.run_child("print('successful child')")
        self.assertEqual(0, self.helper.record['commands'][0]['exit'])
        self.assertFalse(self.helper.STOP.exists())

    def test_child_failure_is_preserved_without_retry(self):
        with self.assertRaisesRegex(RuntimeError, 'no automatic retry'):
            self.run_child("import sys; print('child failure'); sys.exit(7)")
        self.assertEqual([7], [item['exit'] for item in self.helper.record['commands']])
        self.assertIn('child failure', (self.root/'replay.stdout.txt').read_text(encoding='utf-8'))

    def test_time_limit_requests_clean_child_exit(self):
        self.limits['clean_seconds'] = 0.1
        with self.assertRaises(RuntimeError):
            self.run_child(self.wait_for_stop())
        self.assertEqual('declared clean-stop allowance reached', self.helper.record['stop_reason'])
        self.assertEqual(1, self.helper.record['commands'][0]['exit'])

    @unittest.skipUnless(shutil.which('timeout') and os.name == 'posix', 'GNU timeout requires Linux')
    def test_outer_timeout_bounds_child_that_ignores_stop(self):
        self.limits.update(clean_seconds=0.05, go_seconds=0.15, outer_seconds=0.25)
        command = ['timeout', '--kill-after=0.1s', '0.25s', sys.executable, '-c', 'import time; time.sleep(5)']
        with self.assertRaises(RuntimeError):
            monitor.run_monitored(self.helper, command, self.root, os.environ.copy(), self.limits)
        self.assertEqual(124, self.helper.record['commands'][0]['exit'])
        self.assertEqual('declared clean-stop allowance reached', self.helper.record['stop_reason'])

    def test_allocation_limit_requests_stop(self):
        self.helper.allocated_size = lambda:100
        with self.assertRaises(RuntimeError):
            self.run_child(self.wait_for_stop())
        self.assertEqual('declared target allocation allowance reached', self.helper.record['stop_reason'])

    def test_unavailable_measurement_stops_without_ignoring_error(self):
        self.helper.allocated_size = lambda:None
        with self.assertRaises(RuntimeError):
            self.run_child(self.wait_for_stop())
        self.assertEqual('size monitor failed all three bounded attempts', self.helper.record['stop_reason'])

    def test_external_stop_cannot_be_reported_as_success(self):
        with self.assertRaises(RuntimeError):
            self.run_child("from pathlib import Path; Path('STOP').write_text('operator stop\\n', encoding='utf-8')")
        self.assertEqual(0, self.helper.record['commands'][0]['exit'])
        self.assertEqual('operator stop\n', self.helper.STOP.read_text(encoding='utf-8'))

    def test_existing_stop_refuses_before_child_creation(self):
        self.helper.STOP.write_text('preserved failure\n', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            self.run_child("from pathlib import Path; Path('child-started').touch()")
        self.assertFalse((self.root/'child-started').exists())
        self.assertEqual([], self.helper.record['commands'])

    def test_timeout_order_refuses_before_child_creation(self):
        self.limits['go_seconds'] = 1
        with self.assertRaises(ValueError):
            self.run_child("from pathlib import Path; Path('child-started').touch()")
        self.assertFalse((self.root/'child-started').exists())

    def test_copy_and_resume_cannot_overwrite_recovery_or_escape_paths(self):
        config = {'job':'new-job', 'prior_bundle':'old-job', 'recovery_bundle':'old-job', 'checkpoint':'saved-checkpoint', 'target':'working-target', 'recovery_checkpoint':'saved-checkpoint', 'start_height':2400000, 'end_height':2700000, 'mode':'copy', 'limits':self.limits}
        monitor.validate_configuration(config)
        monitor.validate_configuration(dict(config, mode='resume', checkpoint='working-target'))
        for changed in [dict(config, target='saved-checkpoint'), dict(config, target='../escaped'), dict(config, mode='resume'), dict(config, end_height=2400000)]:
            with self.assertRaises(ValueError):
                monitor.validate_configuration(changed)


if __name__ == '__main__':
    unittest.main()
