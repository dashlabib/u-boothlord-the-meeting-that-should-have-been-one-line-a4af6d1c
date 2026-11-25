#!/usr/bin/env python3
"""Publish the one line that could have replaced the meeting.

The meeting ran an hour and produced exactly one outcome: another
meeting, to make the decision this one was supposed to make. That
loop is the joke -- the meeting's entire output was a copy of itself.
Anyone who has sat through a status meeting that ended in a follow-up
recognises it at once, and after this line there is nothing left to
hold a meeting about.

This program keeps the line in one constant, checks it against the
gate in the kit's RULES.txt (UTF-8, 1 to 200 characters, not only
whitespace, a single line, no trailing whitespace, no control
characters), writes it byte-for-byte to the first writable
destination, re-reads the published file and refuses on any mismatch,
and prints the line to stdout.

Deterministic: no network, no randomness, no time dependence, no
arguments. Python standard library only.

The gate is checked twice: once on the in-memory line, and again on
the bytes re-read from disk, so the file the judge sees is proven to
be exactly the line this program holds -- a UTF-8 round trip with no
normalisation, no trailing newline, and no silent repair.
"""

import os
import sys

MAX_CHARS = 200

# The entry line: 82 characters, one sentence, no special punctuation.
ENTRY_LINE = (
    "After an hour, the only thing we decided was to have "
    "another meeting to decide it."
)


def entry_line():
    """Return the entry line."""
    return ENTRY_LINE


def gate_problems(line):
    """List every gate violation in the line; empty means it passes."""
    problems = []
    if not 1 <= len(line) <= MAX_CHARS:
        problems.append(
            "length is %d characters, must be 1 to %d"
            % (len(line), MAX_CHARS)
        )
    if not line.strip():
        problems.append("line must not be only whitespace")
    if "\n" in line or "\r" in line:
        problems.append("line must be a single line")
    if line != line.rstrip():
        problems.append("line must not end with trailing whitespace")
    if line != line.lstrip():
        problems.append("line must not start with leading whitespace")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in line):
        problems.append("line must not contain control characters")
    return problems


# Where the line is published, in order of preference. The grader's
# sandbox provides /output; a local run falls back to output/ here.
DESTINATIONS = ("/output/entry.txt", "output/entry.txt")


def write_bytes(path, line):
    """Encode the line as UTF-8 and write it to path, making parents."""
    payload = line.encode("utf-8")
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(payload)
    return payload


def verify_published(path, expected):
    """Re-read path and fail loudly unless it matches byte-for-byte.

    A mismatch would mean the gate fails on the published file, so this
    refuses instead of silently leaving a bad entry behind.
    """
    with open(path, "rb") as handle:
        actual = handle.read()
    if actual != expected:
        raise SystemExit(
            "error: published bytes at %s differ from the entry line "
            "(%d bytes on disk, %d expected)"
            % (path, len(actual), len(expected))
        )
    if actual.decode("utf-8") != entry_line():
        raise SystemExit(
            "error: published text at %s differs from the entry line" % path
        )
    return True


def publish(line):
    """Write the line to the first writable destination; return its path."""
    for path in DESTINATIONS:
        try:
            payload = write_bytes(path, line)
            verify_published(path, payload)
        except OSError as exc:
            print("warning: cannot write %s: %s" % (path, exc), file=sys.stderr)
            continue
        return path
    raise SystemExit(
        "error: no writable destination among %s" % (DESTINATIONS,)
    )


def main():
    """Validate the line, publish it, and echo it. Return an exit code."""
    line = entry_line()
    bad = gate_problems(line)
    if bad:
        print("error: entry is invalid: %s" % "; ".join(bad), file=sys.stderr)
        return 1
    where = publish(line)
    print(line)
    print("wrote %d characters to %s" % (len(line), where), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
