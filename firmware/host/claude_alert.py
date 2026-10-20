#!/usr/bin/env python3
"""Private Claude hook state and reconnecting Macropad USB notification bridge."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time

MAX_INPUT = 65536
STATE_TTL = 600
DEFAULT_STATE = Path.home() / 'Library/Application Support/Macropad/state'
SAFE_TOOL = re.compile(r'^[A-Za-z0-9_:. /-]{1,128}$')


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.directory, 0o700)

    @contextlib.contextmanager
    def locked(self):
        fd = os.open(self.directory / 'state.lock', os.O_CREAT | os.O_RDWR, 0o600)
        with os.fdopen(fd, 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def _read(self, now):
        try:
            data = json.loads((self.directory / 'pending.json').read_text())
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {key: value for key, value in data.items()
                if isinstance(key, str) and re.fullmatch('[0-9a-f]{64}', key)
                and isinstance(value, dict) and value.get('kind') in ('A', 'Q')
                and value.get('source', 'claude') in ('claude', 'codex')
                and isinstance(value.get('expires'), (float, int))
                and now < value['expires'] <= now + STATE_TTL}

    def _write(self, data, filename='pending.json'):
        fd, name = tempfile.mkstemp(prefix='.pending-', dir=self.directory)
        try:
            with os.fdopen(fd, 'w') as target:
                json.dump(data, target, separators=(',', ':'))
                target.flush()
                os.fsync(target.fileno())
            os.replace(name, self.directory / filename)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def enabled(self):
        try:
            return json.loads((self.directory / 'config.json').read_text()).get('enabled', True) is not False
        except (OSError, ValueError, AttributeError):
            return True

    def set_enabled(self, action):
        with self.locked():
            previous = self.enabled()
            enabled = not previous if action == 'toggle' else action == 'on'
            if enabled != previous or not enabled:
                self._write({})
            self._write({'enabled': enabled}, 'config.json')
            return enabled

    def update(self, payload, now=None, source='claude'):
        now = time.time() if now is None else now
        if not isinstance(payload, dict):
            return
        session = payload.get('session_id')
        event = payload.get('hook_event_name')
        if not isinstance(session, str) or not 0 < len(session) <= 1024 or not isinstance(event, str):
            return
        if source not in ('claude', 'codex'):
            return
        key = digest(source + ':' + session)
        tool = payload.get('tool_name')
        tool = tool if isinstance(tool, str) and SAFE_TOOL.fullmatch(tool) else None
        use_id = payload.get('tool_use_id')
        use_id = digest(use_id) if isinstance(use_id, str) and len(use_id) <= 1024 else None
        with self.locked():
            if not self.enabled():
                return
            states = self._read(now)
            kind = None
            pending = states.get(key, {})
            pending_tool = pending.get('tool')
            async_question = (pending.get('source') == 'codex' and pending.get('kind') == 'Q'
                              and isinstance(pending_tool, str)
                              and re.split(r'\.|__', pending_tool)[-1] == 'request_user_input_async')
            question = (tool in ('AskUserQuestion', 'ExitPlanMode') if source == 'claude'
                        else bool(tool) and re.split(r'\.|__', tool)[-1] in
                        ('request_user_input', 'request_user_input_async'))
            if event == 'PermissionRequest':
                kind = 'Q' if question else 'A'
            elif event == 'PreToolUse' and question:
                kind = 'Q'
            elif event == 'Notification' and source == 'claude':
                notification = payload.get('notification_type')
                if notification == 'permission_prompt':
                    kind = 'A'
                elif notification in ('elicitation_dialog', 'elicitation_url_dialog', 'agent_needs_input'):
                    kind = 'Q'
                # Notification payload has no reliable tool identity.
                tool, use_id = None, None
            if kind:
                states[key] = {'kind': kind, 'source': source, 'tool': tool, 'use_id': use_id,
                               'created': now, 'expires': now + STATE_TTL}
            elif event in ('UserPromptSubmit', 'Stop', 'SessionEnd', 'Interrupt'):
                if event != 'Stop' or not async_question:
                    states.pop(key, None)
            elif event in ('PostToolUse', 'PostToolUseFailure') and key in states:
                pending = states[key]
                matches = (pending.get('use_id') == use_id if pending.get('use_id')
                           else pending.get('tool') is None or pending.get('tool') == tool)
                if matches and not (event == 'PostToolUse' and async_question):
                    states.pop(key, None)
            self._write(states)

    def test(self, kind, duration, source="claude"):
        now = time.time()
        with self.locked():
            if not self.enabled():
                return
            states = self._read(now)
            states[digest(source + ':macropad-local-test')] = {'kind': kind, 'source': source, 'tool': None,
                'created': now, 'expires': now + duration}
            self._write(states)

    def current_alert(self, now=None):
        now = time.time() if now is None else now
        with self.locked():
            states = self._read(now) if self.enabled() else {}
        kinds = {value['kind'] for value in states.values()}
        sources = {value.get('source', 'claude') for value in states.values()}
        source = 'BOTH' if len(sources) > 1 else next(iter(sources)).upper() if sources else 'NONE'
        return source, 'A' if 'A' in kinds else 'Q' if 'Q' in kinds else 'C'

    def current(self, now=None):
        return self.current_alert(now)[1]


def frame(kind, source='CLAUDE'):
    if kind not in ('A', 'Q', 'C') or source not in ('CLAUDE', 'CODEX', 'BOTH', 'NONE'):
        raise ValueError('Unknown alert state')
    source = 'NONE' if kind == 'C' else source
    return f'MP2 {source} {kind} {0 if kind == "C" else 5}\n'.encode('ascii')


def send(device, kind, source='CLAUDE'):
    source = 'NONE' if kind == 'C' else source
    report = b'\0' + frame(kind, source).ljust(32, b'\0')
    if device.write(report) != len(report):
        return False
    reply = bytes(device.read(32, 200)).rstrip(b'\0')
    return reply == f'MP2 OK {source} {kind}\n'.encode('ascii')


def choose_port(ports, serial_number=None):
    """Select only our dedicated HID interface; never open the Vial interface."""
    matches = [port for port in ports if port.get('vendor_id') == 0xFEED
               and port.get('product_id') == 0x6061
               and port.get('usage_page') == 0xFF61 and port.get('usage') == 0x61
               and (serial_number is None or port.get('serial_number') == serial_number)]
    if len(matches) > 1:
        raise ValueError('Multiple Macropads found; specify --serial-number')
    return matches[0]['path'] if matches else None


def bridge(store, serial_number=None, once=False):
    import hid
    lock_fd = os.open(store.directory / 'bridge.lock', os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(lock_fd, 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('A Macropad bridge is already running') from None
        device, previous, sent_at, retry_at = None, None, 0, 0
        try:
            while True:
                now = time.monotonic()
                try:
                    if device is None and now >= retry_at:
                        path = choose_port(hid.enumerate(0xFEED, 0x6061), serial_number)
                        if path:
                            device = hid.device()
                            device.open_path(path)
                            previous = None
                        retry_at = now + 2
                    source, kind = store.current_alert()
                    current = (source, kind)
                    if device and (previous != current or now - sent_at >= 2):
                        if not send(device, kind, source):
                            raise OSError('Macropad acknowledgement missing')
                        if previous != current:
                            print(f'Macropad state {source} {kind}: acknowledged', file=sys.stderr, flush=True)
                        previous, sent_at = current, now
                except (OSError, ValueError):
                    if device:
                        device.close()
                    device, previous, retry_at = None, None, now + 2
                    print('Macropad bridge: device unavailable or acknowledgement missing', file=sys.stderr)
                if once:
                    return
                time.sleep(0.25)
        finally:
            if device:
                device.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', default=os.environ.get('MACROPAD_STATE_DIR', str(DEFAULT_STATE)))
    sub = parser.add_subparsers(dest='command', required=True)
    hook = sub.add_parser('hook')
    hook.add_argument('--source', choices=('claude', 'codex'), default='claude')
    for action in ('on', 'off', 'toggle', 'status'):
        sub.add_parser(action)
    daemon = sub.add_parser('bridge')
    daemon.add_argument('--serial-number')
    daemon.add_argument('--once', action='store_true')
    test = sub.add_parser('test')
    test.add_argument('--source', choices=('claude', 'codex'), default='claude')
    test.add_argument('--kind', choices=('approval', 'question'), required=True)
    test.add_argument('--duration', type=int, choices=range(1, 601), default=8, metavar='1..600')
    args = parser.parse_args()
    try:
        store = Store(args.state_dir)
        if args.command == 'hook':
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
            if len(raw) > MAX_INPUT:
                raise ValueError('Hook payload exceeds 64 KiB')
            store.update(json.loads(raw), source=args.source)
        elif args.command == 'test':
            store.test('A' if args.kind == 'approval' else 'Q', args.duration, args.source)
        elif args.command in ('on', 'off', 'toggle', 'status'):
            enabled = store.enabled() if args.command == 'status' else store.set_enabled(args.command)
            print('ON' if enabled else 'OFF')
        else:
            bridge(store, args.serial_number, args.once)
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        # Never expose hook content or block Claude on unavailable hardware.
        print(f'Macropad: {type(error).__name__}', file=sys.stderr)
        return 0 if args.command == 'hook' else 1
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        if args.command != 'hook':
            raise
        print(f'Macropad hook: {type(error).__name__}', file=sys.stderr)
        return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
