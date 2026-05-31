"""Send a prompt to an agent's tmux pane via `tmux send-keys`."""

from __future__ import annotations

import subprocess
import time


def send(pane_id: str, message: str) -> None:
    """Type `message` into the pane, then press Enter.

    The literal text and the Enter keypress are sent as two separate calls with
    a small delay. tmux (and Claude's input box) use bracketed-paste mode; if
    Enter rides in the same send-keys call it can be swallowed as part of the
    paste, so the prompt is typed but never submitted.
    """
    # -l = literal: do not interpret the text as key names.
    subprocess.run(
        ["tmux", "send-keys", "-t", pane_id, "-l", message],
        check=True,
        capture_output=True,
        text=True,
    )
    time.sleep(0.15)
    subprocess.run(
        ["tmux", "send-keys", "-t", pane_id, "Enter"],
        check=True,
        capture_output=True,
        text=True,
    )
