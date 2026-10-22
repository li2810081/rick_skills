"""Isolated tests; no live GitHub writes."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import retrospective as retro


class RetrospectiveTests(unittest.TestCase):
    def setUp(self):
        self.report = dict(key='delivery-scope-drift', title='交付范围偏移', body='脱敏证据：用户要求完整流程，实际只有局部。')

    def test_validate_rejects_invalid_and_leak(self):
        for report in ({}, dict(self.report, key='../oops'), dict(self.report, body='sk-' + 'x' * 30),
                       dict(self.report, title='x' * 181), dict(self.report, title='sk-' + 'x' * 30)):
            with self.assertRaises(ValueError):
                retro.validate(report)

    def test_offline_preview_and_write_requires_review(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            path = Path(directory) / 'report.json'
            path.write_text(json.dumps(self.report), encoding='utf-8')
            for argv, expected in (([str(path)], 0), ([str(path), '--publish'], 2)):
                result = subprocess.run([sys.executable, str(Path(retro.__file__)), *argv],
                                        capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected == 0:
                    self.assertEqual(json.loads(result.stdout)['action'], 'preview')

    def test_create_and_exact_readback(self):
        _, _, title, body = retro.prepare(self.report)
        saved = dict(number=7, html_url='https://example.invalid/7', title=title, body=body)
        with patch.object(retro, 'pages', return_value=[]), patch.object(retro, 'gh', side_effect=[saved, saved]) as api:
            self.assertEqual(retro.publish('owner/repo', self.report)['action'], 'created')
            self.assertEqual(api.call_args_list[0].kwargs['payload']['labels'], [])
            self.assertEqual(api.call_args_list[1].args, ('repos/owner/repo/issues/7',))

    def test_append_existing_and_readback(self):
        pattern, _, _, body = retro.prepare(self.report)
        target = dict(number=8, title='[rick-dev] existing', body=pattern, state='closed', html_url='https://example.invalid/8')
        saved = dict(id=10, body=body, html_url='https://example.invalid/comment/10')
        with patch.object(retro, 'pages', side_effect=[[target], []]), patch.object(retro, 'gh', side_effect=[saved, saved]) as api:
            result = retro.publish('owner/repo', self.report)
            self.assertEqual(result['action'], 'commented')
            self.assertEqual(result['state'], 'closed')
            self.assertEqual(api.call_args_list[-1].args, ('repos/owner/repo/issues/comments/10',))

    def test_same_report_is_idempotent(self):
        _, event, _, _ = retro.prepare(self.report)
        target = dict(number=8, title='[rick-dev] existing', body='old', html_url='https://example.invalid/8')
        comment = dict(body=event, html_url='https://example.invalid/comment/1')
        with patch.object(retro, 'pages', side_effect=[[], [comment]]), patch.object(retro, 'gh', return_value=target) as api:
            self.assertEqual(retro.publish('owner/repo', self.report, 8)['action'], 'already_present')
            self.assertEqual(api.call_count, 1)

    def test_retry_finds_pattern_in_comments_without_issue_flag(self):
        pattern, event, _, _ = retro.prepare(self.report)
        target = dict(number=8, title='[rick-dev] existing', body='another mechanism',
                      comments=1, html_url='https://example.invalid/8')
        comment = dict(body=pattern + event, html_url='https://example.invalid/comment/1')
        with patch.object(retro, 'pages', side_effect=[[target], [comment], [comment]]), patch.object(retro, 'gh') as api:
            self.assertEqual(retro.publish('owner/repo', self.report)['action'], 'already_present')
            api.assert_not_called()

    def test_readback_mismatch_fails(self):
        with patch.object(retro, 'pages', return_value=[]), patch.object(retro, 'gh', side_effect=[{'number': 7}, {}]):
            with self.assertRaises(RuntimeError):
                retro.publish('owner/repo', self.report)

    def test_pagination_and_duplicate_pattern(self):
        with patch.object(retro, 'gh', return_value=[[{'number': 1}], [{'number': 2}]]):
            self.assertEqual(len(retro.pages('endpoint')), 2)
        pattern, _, _, _ = retro.prepare(self.report)
        with patch.object(retro, 'pages', return_value=[{'body': pattern}, {'body': pattern}]):
            with self.assertRaises(ValueError):
                retro.publish('owner/repo', self.report)

    def test_network_failure_nonzero_and_no_receipt(self):
        result = subprocess.CompletedProcess([], 1, stdout='', stderr='private transport failure')
        with patch.object(retro.subprocess, 'run', return_value=result):
            with self.assertRaises(RuntimeError):
                retro.gh('endpoint')


if __name__ == '__main__':
    unittest.main(verbosity=2)
