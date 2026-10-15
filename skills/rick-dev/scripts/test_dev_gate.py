"""Run: python scripts/test_dev_gate.py. Uses disposable Git repos, no real BD writes."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('dev_gate.py').resolve()
spec = importlib.util.spec_from_file_location('gate', SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class GateTests(unittest.TestCase):
    def setUp(self):
        self.old = Path.cwd()
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        os.chdir(self.tmp.name)
        subprocess.run(['git', 'init', '-q'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.invalid'], check=True)
        Path('scripts').mkdir()
        shutil.copyfile(SOURCE, 'scripts/dev_gate.py')
    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()
    def configure(self, code):
        gate.initialize([sys.executable, '-c', code])
    def test_pass_and_existing_preserved(self):
        self.configure('print("real check")')
        gate.check()
        before = Path('scripts/dev-check.json').read_bytes()
        with self.assertRaises(RuntimeError):
            gate.initialize(['bad'])
        self.assertEqual(before, Path('scripts/dev-check.json').read_bytes())
    def test_failure(self):
        self.configure('raise SystemExit(7)')
        with self.assertRaises(RuntimeError):
            gate.check()
    def test_source_change_rejected(self):
        self.configure('from pathlib import Path; Path("unexpected.txt").write_text("changed")')
        with self.assertRaises(RuntimeError):
            gate.check()
    def test_failed_hook_blocks_real_commit(self):
        self.configure('raise SystemExit(7)')
        subprocess.run(['git', 'add', '.'], check=True)
        result = subprocess.run(['git', 'commit', '-m', 'must fail'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], capture_output=True).returncode, 0)
    def test_done_with_mock_bd(self):
        self.configure('print("pass")')
        original = gate.run
        calls = []
        def fake(argv):
            if argv[0] != 'bd':
                return original(argv)
            calls.append(argv)
            closed = any(x[1] == 'close' for x in calls)
            return subprocess.CompletedProcess(argv, 0, json.dumps([{'id': 'demo-1', 'status': 'closed' if closed else 'in_progress'}]), '')
        with patch.object(gate, 'run', side_effect=fake):
            gate.check('demo-1')
        self.assertEqual([x[1] for x in calls], ['show', 'close', 'show'])
        self.assertIn('worktree_sha256=', calls[1][-1])

if __name__ == '__main__':
    unittest.main(verbosity=2)
