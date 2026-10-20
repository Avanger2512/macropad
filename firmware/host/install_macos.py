#!/usr/bin/env python3
"""Merge notification-only Claude hooks and prepare a per-user bridge LaunchAgent."""
import argparse
import copy
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import tempfile
import time

LABEL = 'local.macropad.claude-alerts'
EVENTS = {
    'PermissionRequest': '*',
    'PreToolUse': 'AskUserQuestion|ExitPlanMode',
    'Notification': 'permission_prompt|elicitation_dialog|elicitation_url_dialog|agent_needs_input',
    'PostToolUse': '*',
    'PostToolUseFailure': '*',
    'UserPromptSubmit': None,
    'Stop': None,
    'SessionEnd': None,
}

CODEX_EVENTS = {**{key: value for key, value in EVENTS.items() if key not in ('Notification', 'PostToolUseFailure')},
    'PreToolUse': r'(^|.*[.]|.*__)request_user_input(_async)?$', 'Interrupt': None}


def build_settings(settings, python, script, enabled=True, source="claude"):
    result = copy.deepcopy(settings)
    hooks = result.setdefault('hooks', {})
    command = shlex.join([str(python), str(script), 'hook', '--source', source])
    old_command = shlex.join([str(python), str(script), 'hook'])
    owned = (command, old_command) if source == 'claude' else (command,)
    events = EVENTS if source == 'claude' else CODEX_EVENTS
    cleanup_events = {**events, 'PostToolUseFailure': '*'} if source == 'codex' else events
    for event, matcher in cleanup_events.items():
        entries = []
        for entry in hooks.get(event, []):
            remaining = [hook for hook in entry.get('hooks', [])
                         if not (hook.get('type') == 'command' and hook.get('command') in owned)]
            if remaining:
                entries.append({**entry, 'hooks': remaining})
        if enabled and event in events:
            entry = {'hooks': [{'type': 'command', 'command': command, 'timeout': 2}]}
            if matcher is not None:
                entry['matcher'] = matcher
            entries.append(entry)
        if entries:
            hooks[event] = entries
        else:
            hooks.pop(event, None)
    return result


def build_codex_settings(settings, python, script, enabled=True):
    return build_settings(settings, python, script, enabled, source='codex')


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.macropad-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True, type=Path)
    parser.add_argument('--clients', choices=('claude', 'codex', 'both'), default='both')
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    # Keep the virtual environment executable path: resolve() would bypass its packages.
    python = args.python.absolute()
    script = Path(__file__).with_name('claude_alert.py').resolve()
    if not python.is_file() or not script.is_file():
        parser.error('Python interpreter or hook script is missing')
    clients = ('claude', 'codex') if args.clients == 'both' else (args.clients,)
    prepared = []
    for client in clients:
        settings_path = Path.home() / ('.claude/settings.json' if client == 'claude' else '.codex/hooks.json')
        original = settings_path.read_bytes() if settings_path.exists() else b'{}'
        settings = json.loads(original)
        if not isinstance(settings, dict) or not isinstance(settings.get('hooks', {}), dict):
            parser.error(f'{client} settings must contain a JSON object and a hooks object')
        updated = build_settings(settings, python, script, enabled=not args.uninstall, source=client)
        prepared.append((settings_path, original, updated))
    for settings_path, original, updated in prepared:
        backup = settings_path.with_name(f'{settings_path.name}.before-macropad-{time.time_ns()}.bak')
        atomic_write(backup, original)
        atomic_write(settings_path, (json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode())
        print(f'Settings backup: {backup}')
    agent = Path.home() / f'Library/LaunchAgents/{LABEL}.plist'
    if args.uninstall:
        # Unloading a running agent is deliberately a separate launchctl command.
        if agent.exists():
            shutil.move(agent, agent.with_suffix(f'.disabled-{time.time_ns()}'))
    else:
        state = Path.home() / 'Library/Application Support/Macropad/state'
        state.mkdir(parents=True, mode=0o700, exist_ok=True)
        os.chmod(state, 0o700)
        configuration = {
            'Label': LABEL,
            'ProgramArguments': [str(python), str(script), 'bridge'],
            'RunAtLoad': True,
            'KeepAlive': True,
            'ThrottleInterval': 10,
            'StandardOutPath': str(state / 'bridge.stdout.log'),
            'StandardErrorPath': str(state / 'bridge.stderr.log'),
        }
        atomic_write(agent, plistlib.dumps(configuration))
    print(f'LaunchAgent: {agent}')
    print('Hooks only send local notifications; no approval or answer decisions are returned.')


if __name__ == '__main__':
    main()
