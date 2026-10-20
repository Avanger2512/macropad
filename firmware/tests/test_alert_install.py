import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('alert_install', Path(__file__).parents[1] / 'host/install_macos.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_preserves_existing_hooks_and_other_settings(self):
        settings = {'env': {'PRIVATE_SETTING': 'unchanged'}, 'hooks': {
            'Stop': [{'hooks': [{'type': 'command', 'command': 'existing-hook'}]}]}}
        actual = installer.build_settings(settings, '/usr/bin/python3', '/project/claude_alert.py')
        self.assertEqual(settings['hooks']['Stop'], actual['hooks']['Stop'][:1])
        self.assertEqual(settings['env'], actual['env'])
        self.assertNotIn('Notification', settings['hooks'])
        commands = [hook['command'] for item in actual['hooks']['PermissionRequest'] for hook in item['hooks']]
        self.assertEqual(commands, ['/usr/bin/python3 /project/claude_alert.py hook --source claude'])

    def test_install_is_idempotent_and_uninstall_preserves_other_hooks(self):
        original = {'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'keep'}]}]}}
        first = installer.build_settings(original, '/python with spaces', '/project/claude_alert.py')
        second = installer.build_settings(first, '/python with spaces', '/project/claude_alert.py')
        self.assertEqual(first, second)
        restored = installer.build_settings(second, '/python with spaces', '/project/claude_alert.py', enabled=False)
        self.assertEqual(restored, original)

    def test_codex_hooks_are_scoped_idempotent_and_removable(self):
        original = {'hooks': {'Stop': [{'hooks': [{'type':'command', 'command':'keep'}]}]}}
        first = installer.build_codex_settings(original, '/python', '/bridge.py')
        self.assertNotIn('Notification', first['hooks'])
        self.assertEqual(set(first['hooks']), {'PermissionRequest', 'PreToolUse', 'PostToolUse',
                                              'UserPromptSubmit', 'Stop', 'SessionEnd', 'Interrupt'})
        self.assertIn('Interrupt', first['hooks'])
        self.assertIn('--source codex', first['hooks']['PermissionRequest'][0]['hooks'][0]['command'])
        self.assertEqual(first, installer.build_codex_settings(first, '/python', '/bridge.py'))
        self.assertEqual(original, installer.build_codex_settings(first, '/python', '/bridge.py', False))

    def test_upgrades_only_our_legacy_command(self):
        original = {'hooks': {'Stop': [{'hooks': [
            {'type':'command','command':'/python /bridge.py hook'},
            {'type':'command','command':'some-other-hook'}]}]}}
        actual = installer.build_settings(original, '/python', '/bridge.py')
        commands = [hook['command'] for item in actual['hooks']['Stop'] for hook in item['hooks']]
        self.assertEqual(commands, ['some-other-hook', '/python /bridge.py hook --source claude'])


if __name__ == '__main__':
    unittest.main()
