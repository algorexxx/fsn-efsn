import datetime
import copy
import json
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

    def test_resume_capacity_charges_only_remaining_growth(self):
        gib = 1024**3
        config = {'mode':'resume', 'limits':{'max_bytes':8*gib}}
        capacity = {'/home/rehearsal/results':29*gib, '/mnt/d':64*gib}
        required = monitor.require_starting_capacity(config, capacity, 4*gib)
        self.assertEqual({'/home/rehearsal/results':25*gib, '/mnt/d':60*gib}, required)

    def test_capacity_refuses_exhausted_margin_on_either_drive(self):
        gib = 1024**3
        config = {'mode':'resume', 'limits':{'max_bytes':8*gib}}
        for capacity in [{'/home/rehearsal/results':25*gib, '/mnt/d':64*gib}, {'/home/rehearsal/results':29*gib, '/mnt/d':60*gib}]:
            with self.assertRaisesRegex(ValueError, 'insufficient starting capacity'):
                monitor.require_starting_capacity(config, capacity, 4*gib)

    def test_copy_keeps_original_floors_and_refuses_existing_target(self):
        gib = 1024**3
        config = {'mode':'copy', 'limits':{'max_bytes':8*gib}}
        capacity = {'/home/rehearsal/results':31*gib, '/mnt/d':64*gib}
        self.assertEqual({'/home/rehearsal/results':30*gib, '/mnt/d':60*gib}, monitor.require_starting_capacity(config, capacity, 0))
        for size in [-1, 4*gib, 8*gib]:
            with self.assertRaises(ValueError):
                monitor.require_starting_capacity(config, capacity, size)

    def test_resume_refuses_unverified_or_wrong_prior_endpoint(self):
        config = {'start_height':2700000}
        completion = {'verified_pass':True, 'exit':0, 'requested_end':2700000}
        verification = {'pass':True, 'end_height':2700000}
        monitor.require_verified_prior(config, completion, verification)
        for changed in [dict(completion, verified_pass=False), dict(completion, exit=1), dict(completion, requested_end=2400000)]:
            with self.assertRaises(ValueError):
                monitor.require_verified_prior(config, changed, verification)
        for changed in [dict(verification, **{'pass':False}), dict(verification, end_height=2400000)]:
            with self.assertRaises(ValueError):
                monitor.require_verified_prior(config, completion, changed)


    def test_verified_stopped_checkpoint_keeps_failed_attempt_distinct(self):
        evidence = Path(__file__).resolve().parents[2]/'docs/evidence'
        prior = evidence/'restart-ticket-encoder-stopped-5331360-2026-10-10'
        attempt = evidence/'restart-ticket-encoder-job-5400000-2026-10-09'
        config = {'start_height':5331360, 'stopped_attempt':attempt.name}
        run = json.loads((prior/'qualification/run.json').read_bytes())
        verified = json.loads((prior/'verification.json').read_bytes())
        completion = json.loads((attempt/'completion.json').read_bytes())

        monitor.require_verified_stopped(config, run, verified, completion)

        self.assertFalse(completion['verified_pass'])
        self.assertEqual(5331360, verified['cold_verified_height'])
        self.assertEqual(5400000, completion['requested_end'])

    def test_stopped_resume_refuses_incomplete_or_mismatched_provenance(self):
        evidence = Path(__file__).resolve().parents[2]/'docs/evidence'
        prior = evidence/'restart-ticket-encoder-stopped-5331360-2026-10-10'
        attempt = evidence/'restart-ticket-encoder-job-5400000-2026-10-09'
        config = {'start_height':5331360, 'stopped_attempt':attempt.name}
        run = json.loads((prior/'qualification/run.json').read_bytes())
        verified = json.loads((prior/'verification.json').read_bytes())
        completion = json.loads((attempt/'completion.json').read_bytes())
        mutations = [
            (0, 'start_height', 5331361), (0, 'stopped_attempt', 'another-attempt'),
            (1, 'completed', False), (1, 'inspect_passed', False),
            (1, 'failures', ['incomplete']), (1, 'inspection_height', 5400000),
            (1, 'preservation_checks', {}), (1, 'target_before_cold_sha256', {}),
            (1, 'stop_sha256', ''), (1, 'requested_attempt_height', 5400001),
            (2, 'pass', False), (2, 'attempt_completed', True),
            (2, 'cold_verified_height', 5400000), (2, 'endpoint', {}),
            (2, 'requested_height', 5400001), (3, 'verified_pass', True),
            (3, 'exit', 0), (3, 'job', 'another-attempt'),
            (3, 'requested_end', 5400001)]
        for index, key, value in mutations:
            changed = copy.deepcopy([config, run, verified, completion])
            changed[index][key] = value
            with self.subTest(index=index, key=key), self.assertRaises(ValueError):
                monitor.require_verified_stopped(*changed)
        for key in run['preservation_checks']:
            changed = copy.deepcopy(run)
            changed['preservation_checks'][key] = False
            with self.subTest(preservation=key), self.assertRaises(ValueError):
                monitor.require_verified_stopped(config, changed, verified, completion)


if __name__ == '__main__':
    unittest.main()
