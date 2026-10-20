# Claude Code and Codex notifications on the Macropad

Installed and hardware-tested on macOS, October 20, 2026, with Claude Code
2.1.304. The owner confirmed the question screen, smooth LED pulse and automatic
return to the regular display. The installed hook command also passed simulated
PermissionRequest/PostToolUse payloads with device ACKs for both alert and clear.
The owner also confirmed a real question notification from a new local Codex
desktop session after trusting the hooks. A chat opened before installation did
not load the new definitions; use a fresh chat for initial validation.

## Behavior

- Question: source logo and `CLAUDE` or `CODEX`, with `QUESTION / FOR YOU`; dim yellow breathing LEDs.
- Permission request: source logo/name and `APPROVAL / NEEDED`; dim orange breathing LEDs.
- When both clients wait, both logos and `CLAUDE + CODEX` appear.
- Response/tool completion, turn stop or session end: remove that session's alert.
- Other sessions' pending alerts remain; approvals take priority over questions.
- Missing event cleanup expires after ten minutes. A disconnected/stopped bridge
  stops refreshing the device, and its alert expires within five seconds.
- Vial key mappings, layer switching and the regular OLED/RGB behavior remain
  available. Normal layer colors return after alert clearance/expiry.

The hooks only notify. They never approve tools, answer questions, send keys,
read transcripts or return Claude permission decisions. Plain prose questions
without a supported hook/tool event cannot be detected reliably.

## Architecture

Claude/Codex hooks write private per-source, per-session state → a per-user launchd bridge → a
dedicated USB HID interface → RAM-only display/RGB overlay. No network service,
Hammerspoon or serial port is required.

The interface uses VID `FEED`, PID `6061`, vendor usage page `FF61`, usage `61`.
Vial uses a separate `FF60` interface, which the bridge never opens. It sends
32-byte, zero-padded ASCII output reports, prefixed by report-ID byte zero on
the host. Commands: `MP2 CLAUDE Q 5\n`, `MP2 CODEX A 5\n`, `MP2 BOTH Q 5\n`,
`MP2 NONE C 0\n`; responses echo source/kind, e.g. `MP2 OK CODEX A\n`,
zero-padded to 32 bytes. Heartbeats refresh every two seconds. The firmware
retains MP1 compatibility, interpreting legacy notifications as Claude.
The device validates version, fields and TTL; unknown/oversized input is ignored.

An initial CDC transport received commands but could not return acknowledgements.
It exceeded the ESP32-S3's concurrent IN-endpoint budget (including EP0). The
dedicated HID interface reduces the total to five and passed real ACK tests.
See [Espressif's endpoint limit](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html).

## Installation

From the repository root, after flashing the matching RMK application:

```sh
python3 -m venv build/host-venv
build/host-venv/bin/python -m pip install -r firmware/host/requirements.txt
build/host-venv/bin/python firmware/host/install_macos.py --python "$PWD/build/host-venv/bin/python"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.macropad.claude-alerts.plist"
```

The installer backs up `~/.claude/settings.json` next to the original before
merging hooks for both clients, preserves existing hooks/settings, and prepares a login agent.
Codex definitions go in `~/.codex/hooks.json`; its unrelated config.toml is not modified.
Choose `--clients claude`, `--clients codex`, or the default `--clients both`.
Running it again does not duplicate identical Macropad hooks. Paths are absolute:
moving the repository or deleting `build/host-venv` requires reinstalling.

Claude events configured:

| Event | Scope |
|---|---|
| PermissionRequest | All tools; question/plan approval distinguished |
| PreToolUse | AskUserQuestion, ExitPlanMode |
| Notification | permission_prompt, elicitation_dialog, elicitation_url_dialog, agent_needs_input |
| PostToolUse / PostToolUseFailure | Clear matching pending tool |
| UserPromptSubmit / Stop / SessionEnd | Clear only that session |

`idle_prompt` is intentionally ignored: finishing a response is not necessarily
a request for an answer. Notification timing depends on Claude's terminal-away
rules and version; the direct tool hooks provide immediate question/permission
signals. See [Claude's hooks reference](https://code.claude.com/docs/en/hooks).

## Test and troubleshoot

```sh
build/host-venv/bin/python firmware/host/claude_alert.py test --kind question --duration 15
build/host-venv/bin/python firmware/host/claude_alert.py test --kind approval --duration 15
launchctl print "gui/$(id -u)/local.macropad.claude-alerts"
```

Open a new Claude Code session and use `/hooks` to check the configured events.
Ask Claude to ask a question using `AskUserQuestion`; answer in the terminal and
check that the alert clears. This tests actual Claude event delivery in addition
to the hardware and synthetic-hook checks already performed.

State and logs: `~/Library/Application Support/Macropad/state/`. Session IDs are
hashed. Stored fields are only kind, timestamps and bounded tool identity; full
messages, tool inputs and transcript paths are not retained. ACK logs contain
only A/Q/C state changes. State directory is mode 700; state files are mode 600.

If the board is unplugged, the bridge reconnects automatically. Multiple matching
boards require explicit `bridge --serial-number ...` configuration. The bridge
never falls back to a keyboard or Vial HID interface.

After editing bridge code, restart it:

```sh
launchctl kickstart -k "gui/$(id -u)/local.macropad.claude-alerts"
```

## Disable / uninstall

```sh
launchctl bootout "gui/$(id -u)/local.macropad.claude-alerts"
build/host-venv/bin/python firmware/host/install_macos.py --python "$PWD/build/host-venv/bin/python" --uninstall
```

Uninstall removes only the matching Macropad hook command and archives the
LaunchAgent plist. Other Claude hooks remain. No firmware rollback is necessary:
without the bridge, the alert overlay expires and the normal display returns.

## Recovery and validation

Full flash before this feature: `build/recovery/rmk-before-alerts-2026-10-20.bin`,
with SHA-256 alongside it. The previous ELF is
`build/rmk/macropad-vial-before-alerts.elf`. Binary backups are git ignored.
Flash only application address `0x10000`; the settings region starts `0x3F0000`.
RMK revision/features/storage framing were retained to preserve Vial schema.
Vial export after flashing matched `firmware/backup/denis_macropad_current_2026-10-20.vil`
exactly, including tab controls and encoder layer switching.

Host tests: `python3 -m unittest discover -s firmware/tests -p 'test_*.py'`.
Firmware protocol tests:

```sh
rustc --edition 2024 --test firmware/tests/test_alert_policy.rs -o /tmp/macropad-alert-tests
/tmp/macropad-alert-tests
```


## Codex desktop setup and hook trust

The installed desktop backend was `codex-cli 0.163.0-alpha.10.2`, with hooks
supported and enabled. Its read-only `hooks/list` returned no load errors and
all seven Macropad definitions as trusted after the owner approved them.

Codex hooks installed: PermissionRequest, PreToolUse, PostToolUse,
UserPromptSubmit, Stop, SessionEnd and Interrupt. Unlike Claude, Codex does not
have Notification or PostToolUseFailure hooks in this configuration. The
PreToolUse matcher targets request_user_input/request_user_input_async, allowing
namespace prefixes. Hooks are silent and never return approval decisions.

Review new hooks through `/hooks` in the Codex CLI. Trust only the handlers
pointing to this bridge with `hook --source codex`; the user must approve the
exact definitions through Codex's normal trust UI. The installer does not forge
trust hashes or bypass trust. Start a **new local chat in the desktop app** after
installing/trusting. The owner confirmed this fresh-chat path works.

Async questions immediately return an accepted response before the user answers.
Their alerts therefore survive PostToolUse and Stop. UserPromptSubmit, Interrupt,
SessionEnd, a matching failure, or the ten-minute fallback clears them. Ordinary
prose questions are not observable through these tool hooks. Remote/cloud
execution is not covered by this local command-hook setup.

Claude and Codex session IDs are namespaced before hashing. One client cannot
clear the other's pending request, even if their session IDs happen to match.

## Quick notification switch

Double-click **Macropad Notifications.command** on the Desktop. It prints `OFF`
or `ON` and persists the choice across bridge restarts/login. A portable copy
is `firmware/host/notifications-toggle.command` in this repository.

From the repository root:

```sh
build/host-venv/bin/python firmware/host/claude_alert.py off
build/host-venv/bin/python firmware/host/claude_alert.py on
build/host-venv/bin/python firmware/host/claude_alert.py toggle
build/host-venv/bin/python firmware/host/claude_alert.py status
```

OFF clears pending alerts and ignores new hooks, but leaves the assistants,
Vial, keyboard inputs and normal layer LEDs running. ON waits for new events;
it does not resurrect cleared alerts. The bridge sends clear within its normal
polling delay; if disconnected, the board's five-second TTL still applies.

Client-specific tests:

```sh
build/host-venv/bin/python firmware/host/claude_alert.py test --source codex --kind question --duration 15
build/host-venv/bin/python firmware/host/claude_alert.py test --source claude --kind approval --duration 15
```

Both source states, multi-client aggregation, independent clearing, Desktop
OFF/ON and no resurrection were tested through real HID ACKs. The owner confirmed
Codex question notification in a fresh app session. Official monochrome logos
come from installed app artwork; provenance/reproduction are documented in
`../rmk_macropad/assets/README.md`.

Before the dual-source firmware update, a full flash backup and SHA-256 were
saved as `build/recovery/rmk-before-codex-2026-10-20.bin` and `.bin.sha256`.
