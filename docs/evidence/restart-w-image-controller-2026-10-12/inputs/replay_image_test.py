from pathlib import Path
import copy
import datetime
import json
import os
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import replay_image as image
import replay_monitor as monitor


def configuration():
    return {'mode':'resume','target':'candidate-ticket-encoding-w','limits':{'max_bytes':46*image.GIB},
            'storage':{'kind':'w-image','image':'/mnt/w/FusionRestart/replay-work-7170976-2026-10-12/replay.ext4',
                       'uuid':'2fb12ac9-9520-4cab-9414-f1041c4d25de','virtual_bytes':512*image.GIB,
                       'migration_bundle':'restart-w-checkpoint-copy-7170976-2026-10-12',
                       'migration_sha256':'ddd9718c8e61d4d31959ac130b6330655bc93750803dd5bd6d4ffc7b21c89f97'}}


class ReplayImageTests(unittest.TestCase):
    def setUp(self):
        self.config = configuration()
        self.target = image.ROOT/self.config['target']
        self.mounted = {'device_number':'7:0','directory_identity':[1792,42]}
        self.mount = {'target':str(self.target),'fstype':'ext4','fsroot':'/checkpoint','options':'rw,relatime','maj:min':'7:0'}
        self.share = {'target':'/mnt/w','source':'W:','fstype':'9p'}

    def test_resume_charges_growth_to_image_and_W_only(self):
        capacity = {p:500*image.GIB for p in image.capacity_paths(self.target)}
        capacity.update({'/home/rehearsal/results':22*image.GIB,'/mnt/d':57*image.GIB})
        expected = {'/home/rehearsal/results':21*image.GIB,'/mnt/d':51*image.GIB,'/mnt/w':103*image.GIB,str(self.target):23*image.GIB}
        self.assertEqual(expected, monitor.require_starting_capacity(self.config,capacity,44*image.GIB))
        for path,floor in expected.items():
            with self.subTest(path=path), self.assertRaisesRegex(ValueError,'insufficient starting capacity'):
                monitor.require_starting_capacity(self.config,dict(capacity,**{path:floor}),44*image.GIB)

    def test_wrong_image_identity_or_target_refuses(self):
        image.validate_storage(self.config)
        for key,value in [('image','/mnt/d/other.ext4'),('uuid','wrong'),('virtual_bytes',256*image.GIB),('kind','folder')]:
            changed = copy.deepcopy(self.config)
            changed['storage'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                image.validate_storage(changed)
        with self.assertRaises(ValueError):
            image.validate_storage(dict(self.config,target='candidate-ticket-encoding-working'))

    def test_mount_checks_refuse_fallback_wrong_subdirectory_and_replacement(self):
        image.require_mounts(self.target,self.mounted,self.mount,self.share,(1792,42))
        for mount in [dict(self.mount,target='/'),dict(self.mount,fsroot='/'),dict(self.mount,fstype='9p'),dict(self.mount,options='ro'),dict(self.mount,**{'maj:min':'7:1'})]:
            with self.subTest(mount=mount), self.assertRaises(ValueError):
                image.require_mounts(self.target,self.mounted,mount,self.share,(1792,42))
        with self.assertRaises(ValueError):
            image.require_mounts(self.target,self.mounted,self.mount,self.share,(1792,43))
        with self.assertRaises(ValueError):
            image.require_mounts(self.target,self.mounted,self.mount,dict(self.share,source='D:'),(1792,42))

    def test_each_runtime_reserve_refuses_at_its_floor(self):
        free = {p:500*image.GIB for p in image.capacity_paths(self.target)}
        for path,floor in [('/home/rehearsal/results',20),('/mnt/d',50),('/mnt/w',100),(str(self.target),20)]:
            values = dict(free,**{path:floor*image.GIB})
            with self.subTest(path=path), mock.patch.object(Path,'stat',return_value=SimpleNamespace(st_dev=1792,st_ino=42)), mock.patch.object(image,'read_mount',side_effect=[self.mount,self.share]), mock.patch.object(image.shutil,'disk_usage',side_effect=lambda p:SimpleNamespace(free=values[p])), self.assertRaisesRegex(ValueError,'storage reserve reached'):
                image.sample_storage(self.config,self.mounted)

    def test_wrong_UUID_detaches_without_mounting(self):
        with mock.patch.object(image,'command',side_effect=[json.dumps({'loopdevices':[]}),' /dev/loop0\n',json.dumps({'loopdevices':[{'name':'/dev/loop0','back-file':'/tmp/test.ext4','ro':False}]}),'wrong\n','']) as command:
            with self.assertRaisesRegex(ValueError,'UUID differs'):
                image.attach_image(Path('/tmp/test.ext4'),'expected')
            self.assertEqual(mock.call(['losetup','--detach','/dev/loop0']),command.call_args)

    def test_existing_attachment_refuses_before_attach(self):
        with mock.patch.object(image,'command',return_value=json.dumps({'loopdevices':[{'back-file':'/tmp/test.ext4'}]})) as command:
            with self.assertRaisesRegex(ValueError,'already attached'):
                image.attach_image(Path('/tmp/test.ext4'),'expected')
            self.assertEqual(1,command.call_count)

    def test_mount_refusal_prevents_child_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = self.helper(root)
            with mock.patch.object(image,'sample_storage',side_effect=ValueError('missing mount')), self.assertRaisesRegex(RuntimeError,'before replay'):
                monitor.run_monitored(helper,[sys.executable,'-c',"from pathlib import Path; Path('launched').touch()"],root,os.environ.copy(),self.limits())
            self.assertFalse((root/'launched').exists())
            self.assertIn('missing mount',(root/'STOP').read_text())

    def test_runtime_mount_loss_requests_clean_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = self.helper(root)
            script = "from pathlib import Path; import time\nwhile not Path('STOP').exists(): time.sleep(.01)"
            with mock.patch.object(image,'sample_storage',side_effect=[{'/mnt/w':200*image.GIB},ValueError('mount changed')]), self.assertRaisesRegex(RuntimeError,'no automatic retry'):
                monitor.run_monitored(helper,[sys.executable,'-c',script],root,os.environ.copy(),self.limits())
            self.assertEqual(0,helper.record['commands'][0]['exit'])
            self.assertIn('mount changed',helper.record['stop_reason'])

    def helper(self,root):
        return SimpleNamespace(RUN=root,STOP=root/'STOP',record={'commands':[],'configuration':self.config,'storage_mount':self.mounted},save=lambda:None,now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat(),allocated_size=lambda:1)

    def limits(self):
        return {'clean_seconds':3,'go_seconds':4,'outer_seconds':5,'max_bytes':100,'sample_seconds':.5}


if __name__ == '__main__':
    unittest.main()
