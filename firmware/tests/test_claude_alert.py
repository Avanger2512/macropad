import importlib.util
import pathlib
import tempfile
import unittest
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('claude_alert', pathlib.Path(__file__).parents[1] / 'host/claude_alert.py')
alert = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(alert)

class AlertTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = alert.Store(self.tmp.name)
    def event(self, event, session='one', **extra):
        return {'hook_event_name': event, 'session_id': session, **extra}
    def test_source_isolation_and_both_priority(self):
        self.store.update(self.event('PermissionRequest', tool_name='Bash'), now=1, source='claude')
        self.store.update(self.event('PreToolUse', tool_name='functions.request_user_input_async'), now=2, source='codex')
        self.assertEqual(self.store.current_alert(3), ('BOTH', 'A'))
        self.store.update(self.event('Interrupt'), now=4, source='codex')
        self.assertEqual(self.store.current_alert(4), ('CLAUDE', 'A'))
        self.store.update(self.event('Stop'), now=5, source='claude')
        self.assertEqual(self.store.current_alert(5), ('NONE', 'C'))

    def test_codex_async_question_survives_acceptance_and_stop(self):
        event = self.event('PreToolUse', tool_name='functions.request_user_input_async', tool_use_id='question')
        self.store.update(event, now=1, source='codex')
        self.store.update({**event, 'hook_event_name':'PostToolUse'}, now=2, source='codex')
        self.store.update(self.event('Stop'), now=3, source='codex')
        self.assertEqual(self.store.current_alert(4), ('CODEX', 'Q'))
        self.store.update(self.event('UserPromptSubmit'), now=5, source='codex')
        self.assertEqual(self.store.current_alert(5), ('NONE', 'C'))
        self.store.update(event, now=6, source='codex')
        self.store.update({**event, 'hook_event_name':'PostToolUseFailure'}, now=7, source='codex')
        self.assertEqual(self.store.current_alert(7), ('NONE', 'C'))

    def test_disable_is_persistent_and_drops_requests(self):
        self.store.update(self.event('PermissionRequest'), now=1)
        self.assertFalse(self.store.set_enabled('off'))
        other = alert.Store(self.tmp.name)
        other.update(self.event('PermissionRequest'), now=2)
        self.assertEqual(other.current_alert(3), ('NONE', 'C'))
        self.assertTrue(other.set_enabled('on'))
        self.assertEqual(other.current(4), 'C')
        self.assertFalse(other.set_enabled('toggle'))

    def test_codex_tool_allowlist(self):
        for tool in ('request_user_input', 'functions.request_user_input_async', 'mcp__x__request_user_input'):
            self.store.update(self.event('PreToolUse', tool_name=tool), now=1, source='codex')
            self.assertEqual(self.store.current_alert(2), ('CODEX','Q'))
            self.store.update(self.event('Stop'), now=3, source='codex')
        self.store.update(self.event('PreToolUse', tool_name='fake_request_user_input'), now=4, source='codex')
        self.assertEqual(self.store.current(5), 'C')

    def test_private_state_and_matching_completion(self):
        self.store.update(self.event('PermissionRequest', tool_name='Bash', tool_input={'secret':'NO'}), now=10)
        data = pathlib.Path(self.tmp.name, 'pending.json').read_text()
        self.assertNotIn('secret', data)
        self.assertNotIn('one', data)
        self.store.update(self.event('PostToolUse', tool_name='Read'), now=11)
        self.assertEqual(self.store.current(11), 'A')
        self.store.update(self.event('PostToolUse', tool_name='Bash'), now=12)
        self.assertEqual(self.store.current(12), 'C')
    def test_multi_session_priority_clear_and_expiry(self):
        self.store.update(self.event('PreToolUse', tool_name='AskUserQuestion'), now=10)
        self.store.update(self.event('PermissionRequest', session='two', tool_name='Bash'), now=11)
        self.assertEqual(self.store.current(12), 'A')
        self.store.update(self.event('Stop', session='two'), now=12)
        self.assertEqual(self.store.current(13), 'Q')
        self.assertEqual(self.store.current(611), 'C')
    def test_notifications_and_ignored_idle(self):
        self.store.update(self.event('Notification', notification_type='idle_prompt'), now=1)
        self.assertEqual(self.store.current(2), 'C')
        self.store.update(self.event('Notification', notification_type='permission_prompt'), now=3)
        self.store.update(self.event('PostToolUse', tool_name='Read'), now=4)
        self.assertEqual(self.store.current(4), 'C')
    def test_invalid_payload(self):
        for value in [None, [], {}, {'session_id': []}, {'session_id': 'x', 'hook_event_name': []}]:
            self.store.update(value, now=1)
        self.assertEqual(self.store.current(1), 'C')
    def test_protocol_ack_and_bounded_ttl(self):
        self.assertEqual(alert.frame('A'), b'MP2 CLAUDE A 5\n')
        self.assertEqual(alert.frame('C'), b'MP2 NONE C 0\n')
        self.assertEqual(alert.frame('Q', 'CODEX'), b'MP2 CODEX Q 5\n')
        self.assertEqual(alert.frame('A', 'BOTH'), b'MP2 BOTH A 5\n')
        class Hid:
            def write(self, value):
                self.written = value
                return len(value)
            def read(self, count, timeout):
                self.args = (count, timeout)
                return list(b'MP2 OK CLAUDE A\n'.ljust(32, b'\0'))
        device = Hid()
        self.assertTrue(alert.send(device, 'A'))
        self.assertEqual(device.written, b'\0MP2 CLAUDE A 5\n'.ljust(33, b'\0'))
        self.assertEqual(device.args, (32, 200))
        self.assertFalse(alert.send(device, 'Q'))
    def test_tool_id_prevents_wrong_completion(self):
        self.store.update(self.event('PreToolUse', tool_name='AskUserQuestion', tool_use_id='first'), now=10)
        self.store.update(self.event('PostToolUse', tool_name='AskUserQuestion', tool_use_id='other'), now=11)
        self.assertEqual(self.store.current(11), 'Q')
        self.store.update(self.event('PostToolUseFailure', tool_name='AskUserQuestion', tool_use_id='first'), now=12)
        self.assertEqual(self.store.current(12), 'C')

    def test_hook_cli_is_silent_and_fails_open(self):
        for raw in (b'{broken', b'x' * 65537, b'[' * 2000 + b']' * 2000, b'{"hook_event_name":"Stop","session_id":"x"}'):
            result = subprocess.run([sys.executable, str(SPEC.origin), '--state-dir', self.tmp.name, 'hook'],
                                    input=raw, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'')

    def test_bridge_closes_on_bad_ack(self):
        class FakeHid:
            closed = False
            def open_path(self, path): self.path = path
            def write(self, value): return len(value)
            def read(self, count, timeout): return list(b'bad ACK\n')
            def close(self): self.closed = True
        instance = FakeHid()
        port = {'vendor_id':0xFEED, 'product_id':0x6061, 'usage_page':0xFF61,
                'usage':0x61, 'path':b'private-path', 'serial_number':'abc'}
        hid = SimpleNamespace(device=lambda: instance, enumerate=lambda vid,pid: [port])
        with patch.dict(sys.modules, {'hid': hid}):
            with patch('builtins.print'):
                alert.bridge(self.store, once=True)
        self.assertTrue(instance.closed)
        self.assertEqual(instance.path, b'private-path')

    def test_port_selection_fails_closed_and_excludes_vial(self):
        port = {'vendor_id':0xFEED, 'product_id':0x6061, 'usage_page':0xFF61,
                'usage':0x61, 'path':b'private-path', 'serial_number':'abc'}
        vial = {**port, 'usage_page':0xFF60}
        self.assertEqual(alert.choose_port([vial, port]), b'private-path')
        self.assertIsNone(alert.choose_port([vial]))
        self.assertIsNone(alert.choose_port([port], 'different'))
        with self.assertRaises(ValueError): alert.choose_port([port,port])

if __name__ == '__main__': unittest.main()
