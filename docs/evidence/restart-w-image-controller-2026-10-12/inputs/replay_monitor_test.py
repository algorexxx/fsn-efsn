import datetime
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

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

    def test_native_reserve_stop_uses_verified_failure_records_without_fabricated_stop(self):
        fixture = self.load_native_reserve_fixture()

        monitor.require_verified_stopped(**fixture)

        self.assertFalse(fixture['attempt_completion']['verified_pass'])
        self.assertNotIn('stop_sha256', fixture['run'])
        self.assertEqual('host-reserve', fixture['verification']['stop_kind'])

    def test_native_reserve_resume_refuses_missing_or_mixed_stop_provenance(self):
        fixture = self.load_native_reserve_fixture()
        mutations = [
            ('run', 'stop_kind', 'unknown'), ('run', 'stop_kind', None),
            ('run', 'stop_sha256', 'a' * 64),
            ('run', 'stop_evidence_sha256', {}),
            ('run', 'discovery_expected_refusal', False),
            ('verification', 'stop_kind', 'stop-file'),
            ('verification', 'discovery_expected_refusal', False),
        ]
        evidence = fixture['run']['stop_evidence_sha256']
        for name in evidence:
            mutations.append(('run', 'stop_evidence_sha256', {key:value for key,value in evidence.items() if key != name}))
            mutations.append(('run', 'stop_evidence_sha256', dict(evidence, **{name:'invalid'})))
            mutations.append(('run', 'stop_evidence_sha256', dict(evidence, **{name:None})))
        mutations.append(('run', 'stop_evidence_sha256', dict(evidence, **{'STOP':'a' * 64})))

        for section, key, value in mutations:
            changed = copy.deepcopy(fixture)
            changed[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                monitor.require_verified_stopped(**changed)

    def load_native_reserve_fixture(self):
        evidence = Path(__file__).resolve().parents[2]/'docs/evidence'
        prior = evidence/'restart-ticket-encoder-stopped-reserve-2026-10-10'
        attempt = evidence/'restart-ticket-encoder-job-6300000-v2-2026-10-10'
        verified = json.loads((prior/'verification.json').read_bytes())
        return {
            'config':{'start_height':verified['cold_verified_height'], 'stopped_attempt':attempt.name},
            'run':json.loads((prior/'qualification/run.json').read_bytes()),
            'verification':verified,
            'attempt_completion':json.loads((attempt/'completion.json').read_bytes()),
        }

    def load_followup_fixture(self, copy_files=False):
        evidence = Path(__file__).resolve().parents[2]/'docs/evidence'
        prior = evidence/'restart-ticket-encoder-job-6600000-2026-10-11'
        followup = evidence/'restart-ticket-encoder-6600000-verification-followup-2026-10-12'
        if copy_files:
            prior = Path(shutil.copytree(prior, self.root/prior.name))
            followup = Path(shutil.copytree(followup, self.root/followup.name))
        config = {'prior_bundle':prior.name, 'start_height':6600000,
                  'prior_verification_bundle':followup.name,
                  'prior_verification_sha256':hashlib.sha256((followup/'SHA256SUMS').read_bytes()).hexdigest()}
        return {'config':config, 'prior_directory':prior}

    def test_followup_accepts_sealed_evidence_without_reclassifying_original_failure(self):
        fixture = self.load_followup_fixture()
        original = (fixture['prior_directory']/'completion.json').read_bytes()
        expected = {fixture['config']['prior_verification_bundle']:fixture['config']['prior_verification_sha256']}

        result = monitor.require_completed_prior(**fixture)

        self.assertEqual(expected, result)
        self.assertEqual(original, (fixture['prior_directory']/'completion.json').read_bytes())
        self.assertFalse(json.loads(original)['verified_pass'])

    def test_followup_refuses_missing_identity_wrong_endpoint_and_mixed_stop_path(self):
        fixture = self.load_followup_fixture()
        changes = [dict(fixture['config'], start_height=6600001),
                   dict(fixture['config'], prior_verification_sha256='0'*64),
                   dict(fixture['config'], prior_verification_bundle='../escape'),
                   dict(fixture['config'], stopped_attempt='other-attempt'),
                   {key:value for key,value in fixture['config'].items() if key != 'prior_verification_sha256'}]

        for changed in changes:
            with self.subTest(configuration=changed), self.assertRaises(ValueError):
                monitor.require_completed_prior(changed, fixture['prior_directory'])

    def test_followup_refuses_changed_evidence_bytes(self):
        fixture = self.load_followup_fixture(copy_files=True)
        completion = fixture['prior_directory']/'completion.json'
        completion.write_bytes(completion.read_bytes()+b'\n')

        with self.assertRaisesRegex(ValueError, 'evidence file identity differs'):
            monitor.require_completed_prior(**fixture)

    def test_followup_refuses_incomplete_semantic_proof_even_with_manifest_check_stubbed(self):
        fixture = self.load_followup_fixture(copy_files=True)
        prior = fixture['prior_directory']
        followup = prior.parent/fixture['config']['prior_verification_bundle']
        mutations = [(followup/'review.json', 'original_evidence_unchanged', False),
                     (followup/'review.json', 'all_original_verifier_assertions_retained', False),
                     (followup/'review.json', 'original_completion', {}),
                     (followup/'verification.json', 'endpoint', {}),
                     (followup/'verification.json', 'replay_binary_sha256', '0'*64),
                     (prior/'qualification/run.json', 'completed', False),
                     (prior/'qualification/run.json', 'failures', ['failed']),
                     (prior/'qualification/run.json', 'target_before_cold_sha256', {}),
                     (prior/'qualification/run.json', 'additional_preservation_checks', {'bad':False})]

        for path, key, value in mutations:
            original = path.read_bytes()
            changed = json.loads(original)
            changed[key] = value
            path.write_text(json.dumps(changed), encoding='utf-8')
            with self.subTest(path=path.name, key=key), mock.patch.object(monitor, 'require_manifest_files'), self.assertRaises(ValueError):
                monitor.require_completed_prior(**fixture)
            path.write_bytes(original)

    def test_followup_refuses_added_stop_or_replacement_verification(self):
        fixture = self.load_followup_fixture(copy_files=True)
        prior = fixture['prior_directory']

        for path in [prior/'qualification/STOP', prior/'verification.json']:
            path.write_text('{}', encoding='utf-8')
            with self.subTest(path=path.name), self.assertRaisesRegex(ValueError, 'cannot replace or reinterpret'):
                monitor.require_completed_prior(**fixture)
            path.unlink()

    def test_observer_patch_is_checked_before_replay(self):
        prior, changed = self.root/'prior', self.root/'inputs'
        prior.mkdir()
        changed.mkdir()
        config = {'start_height':1, 'end_height':2}
        (prior/'details_test.go').write_bytes(b'const height = uint64(1)\n')
        (changed/'details_test.go').write_bytes(b'const height = uint64(2)\n')
        patch = b'--- a/details_test.go\n+++ b/details_test.go\n@@ -1 +1 @@\n-const height = uint64(1)\n+const height = uint64(2)\n'
        (changed/'observer-change.patch').write_bytes(patch)

        monitor.require_observer_change(config, prior, changed)
        (changed/'observer-change.patch').write_bytes(patch.replace(b'a/details', b'prior/details'))
        with self.assertRaisesRegex(ValueError, 'canonical filenames'):
            monitor.require_observer_change(config, prior, changed)
        (changed/'details_test.go').write_bytes(b'const height = uint64(3)\n')
        with self.assertRaisesRegex(ValueError, 'exactly one height literal'):
            monitor.require_observer_change(config, prior, changed)

    @unittest.skipUnless(os.name == 'posix', 'allocated blocks require Linux')
    def test_quiescent_allocation_matches_du_with_sparse_files_and_hardlinks(self):
        (self.root/'123.ldb').write_bytes(b'x'*8192)
        os.link(self.root/'123.ldb',self.root/'456.ldb')
        with (self.root/'789.log').open('wb') as file:
            file.truncate(8*1024**2)
        expected = int(subprocess.check_output(['du','-sB1',str(self.root)],text=True).split()[0])

        actual = monitor.allocated_blocks(self.root)

        self.assertEqual({'path':str(self.root),'allocated_bytes':expected,'vanished_entries':[]}, actual)

    @unittest.skipUnless(os.name == 'posix', 'allocated blocks require Linux')
    def test_vanished_table_does_not_discard_remaining_allocation(self):
        (self.root/'retained.ldb').write_bytes(b'x'*8192)
        expected = int(subprocess.check_output(['du','-sB1',str(self.root)],text=True).split()[0])
        with os.scandir(self.root) as iterator:
            entries = list(iterator)
        missing = mock.Mock()
        missing.name = '123.ldb'
        missing.stat.side_effect = FileNotFoundError('removed between enumeration and stat')
        iterator = mock.MagicMock()
        iterator.__enter__.return_value = entries+[missing]

        with mock.patch.object(monitor.os,'scandir',return_value=iterator):
            actual = monitor.allocated_blocks(self.root)

        self.assertEqual({'path':str(self.root),'allocated_bytes':expected,'vanished_entries':['123.ldb']},actual)

    @unittest.skipUnless(os.name == 'posix', 'allocated blocks require Linux')
    def test_allocation_refuses_unknown_missing_entries_permissions_and_io_errors(self):
        cases = [('replay-identity.json',FileNotFoundError),('123.ldb',PermissionError),('123.ldb',OSError)]

        for name,error in cases:
            entry = mock.Mock()
            entry.name = name
            entry.stat.side_effect = error('measurement unavailable')
            iterator = mock.MagicMock()
            iterator.__enter__.return_value = [entry]
            with self.subTest(name=name,error=error), mock.patch.object(monitor.os,'scandir',return_value=iterator), self.assertRaises(error):
                monitor.allocated_blocks(self.root)

    @unittest.skipUnless(os.name == 'posix', 'allocated blocks require Linux')
    def test_allocation_refuses_nested_directory_and_symlink(self):
        child = self.root/'child'
        child.mkdir()

        with self.assertRaisesRegex(ValueError,'regular files'):
            monitor.allocated_blocks(self.root)
        child.rmdir()
        child.symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'regular files'):
            monitor.allocated_blocks(self.root)

    @unittest.skipUnless(os.name == 'posix', 'bounded worker requires Linux')
    def test_live_allocation_worker_records_raw_result_and_finite_command(self):
        self.helper.TARGET = self.root
        self.helper.record['size_measurements'] = []
        expected = int(subprocess.check_output(['du','-sB1',str(self.root)],text=True).split()[0])

        actual = monitor.measure_live_allocation(self.helper)

        self.assertEqual(expected,actual)
        self.assertEqual(1,len(self.helper.record['size_measurements']))
        entry = self.helper.record['size_measurements'][0]
        self.assertEqual(['timeout','--kill-after=2s','15s'],entry['argv'][:3])
        self.assertEqual('stat-blocks-v1',entry['method'])
        self.assertEqual(expected,json.loads(entry['scanner_stdout'])['allocated_bytes'])

    def test_live_allocation_timeouts_stop_after_three_attempts(self):
        self.helper.TARGET = self.root
        self.helper.record['size_measurements'] = []
        unavailable = subprocess.CompletedProcess([],124,stdout='',stderr='timeout')

        with mock.patch.object(monitor.subprocess,'run',return_value=unavailable) as child, mock.patch.object(monitor.time,'sleep'):
            actual = monitor.measure_live_allocation(self.helper)

        self.assertIsNone(actual)
        self.assertEqual(3,child.call_count)
        self.assertEqual([1,2,3],[m['attempt'] for m in self.helper.record['size_measurements']])

    def test_live_allocation_rejects_malformed_or_wrong_target_worker_output(self):
        self.helper.TARGET = self.root
        self.helper.record['size_measurements'] = []
        outputs = ['not json',json.dumps({'path':'wrong','allocated_bytes':4096,'vanished_entries':[]}),json.dumps({'path':str(self.root),'allocated_bytes':True,'vanished_entries':[]})]

        for output in outputs:
            child = subprocess.CompletedProcess([],0,stdout=output,stderr='')
            with self.subTest(output=output), mock.patch.object(monitor.subprocess,'run',return_value=child), mock.patch.object(monitor.time,'sleep'):
                actual = monitor.measure_live_allocation(self.helper)
            self.assertIsNone(actual)

    def test_replay_failure_restores_closed_measurement_function(self):
        self.helper.TARGET = self.root
        original = self.helper.allocated_size

        with mock.patch.object(monitor,'run_monitored',side_effect=RuntimeError('stopped')), self.assertRaisesRegex(RuntimeError,'stopped'):
            monitor.run_replay(self.helper,{},self.limits)

        self.assertIs(original,self.helper.allocated_size)


if __name__ == '__main__':
    unittest.main()
