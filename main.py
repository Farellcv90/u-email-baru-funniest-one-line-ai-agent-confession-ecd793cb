#!/usr/bin/env python3
"""Funniest one-line AI agent confession.

This program writes one original line of plain text -- an AI agent's
confession about its own context window -- to ``/output/entry.txt``.

The joke is honest: the agent does not forget anything on purpose. It
simply runs out of context window and then carries on as if the first
half of the conversation never happened. That is the whole entry: one
line, 110 characters, no trailing newline.

The program is deliberately boring and predictable:

* deterministic -- the same input always produces the same bytes;
* no network access -- nothing is fetched, posted, or looked up;
* no secrets -- nothing credential-like is read or written;
* no reading of git history -- the program only writes its own output.

Pipeline (each step is a small, separately named function):

    confession line
        -> validate (empty / one line / no padding / length)
        -> encode as UTF-8 bytes (no trailing newline)
        -> prepare the output path
        -> write the bytes
        -> read back and verify the bytes match
        -> report the character count, byte count, and SHA-256 digest.

Running the program twice produces the same file bytes every time.
"""

import hashlib
import os
import sys

# Where the entry goes. The directory is created if it does not exist yet.
OUTPUT_DIR = "/output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "entry.txt")

# Maximum allowed length of the confession line, in characters.
MAX_LINE_LENGTH = 200

# The entry itself. This string must not change: the competition entry is
# exactly this line, one line, 110 characters, with no trailing newline.
# The em dash is written as the ``\\u2014`` escape so the source stays
# plain ASCII even though the emitted text contains a non-ASCII character.
CONFESSION_LINE = (
    "I don't forget our conversations \u2014 I just run out of context "
    "window and pretend the first half never happened."
)


def get_confession_line():
    """Return the exact confession line to write."""
    return CONFESSION_LINE


def validate_not_empty(line):
    """Reject an empty confession line.

    An empty line is not a confession at all, so the program stops
    instead of writing an empty entry file.
    """
    if not line:
        raise SystemExit("validation failed: confession line is empty")
    return line


def validate_single_line(line):
    """Reject a confession line that spans more than one line.

    The entry must be exactly one line, so neither a newline nor a
    carriage return may appear anywhere in the text.
    """
    if "\n" in line or "\r" in line:
        raise SystemExit("validation failed: confession line must be one line")
    return line


def validate_no_padding(line):
    """Reject a confession line with stray leading or trailing spaces.

    Padding would be invisible in most displays but would change the
    bytes written, so the line must be exactly itself, edge to edge.
    """
    if line != line.strip():
        raise SystemExit("validation failed: confession line has stray padding")
    return line


def validate_length(line):
    """Reject a confession line longer than the allowed maximum.

    The limit keeps the entry a genuine one-liner; anything over
    MAX_LINE_LENGTH characters is too long to be one line.
    """
    if len(line) > MAX_LINE_LENGTH:
        raise SystemExit(
            "validation failed: confession line exceeds {} chars".format(
                MAX_LINE_LENGTH
            )
        )
    return line


def validate_line(line):
    """Run every line check in order and return the checked line.

    This is a thin wrapper kept for convenience: it chains the four
    small validators (empty, single line, no padding, length) in the
    order they are defined above, passing the line through each one.
    """
    line = validate_not_empty(line)
    line = validate_single_line(line)
    line = validate_no_padding(line)
    line = validate_length(line)
    return line


def encode_entry(line):
    """Encode the validated line as UTF-8 bytes, with no trailing newline.

    UTF-8 is used because the line contains a non-ASCII character (the
    em dash). Encoding explicitly, rather than relying on a text-mode
    default, keeps the byte count stable on every platform: the entry
    is 110 characters and 112 bytes. No newline byte is appended here
    or anywhere else, so the file ends exactly at the final period.
    """
    return line.encode("utf-8")


def prepare_output_path():
    """Create the output directory if needed and return the file path.

    ``/output`` may not exist on a fresh machine, so it is created with
    ``exist_ok=True`` (creating it is harmless when it already exists).
    The returned path is always ``/output/entry.txt``.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_FILE


def write_entry(path, data):
    """Write the bytes to path, replacing any previous content.

    The file is opened in binary mode so the bytes are written exactly
    as given -- no newline translation, no encoding surprises. Opening
    with ``"wb"`` also truncates any previous content, so a stale entry
    can never survive a re-run. The number of bytes written is returned
    so the caller can cross-check it against the encoded length.
    """
    with open(path, "wb") as handle:
        handle.write(data)
    return len(data)


def read_back_and_verify(path, expected_bytes):
    """Read the file back and check its bytes equal the expected bytes.

    Writing is only half the job: the file is read back from disk and
    compared byte for byte with what was meant to be written. Two
    failure modes are checked separately so the error message says
    which one happened:

    * the bytes on disk differ from the expected bytes (a write went
      wrong, or another process touched the file);
    * the file ends with a newline byte, which the entry must not have.

    On success the verified bytes are returned unchanged.
    """
    with open(path, "rb") as handle:
        actual = handle.read()
    if actual != expected_bytes:
        raise SystemExit(
            "verification failed: written bytes do not match expected bytes"
        )
    if actual.endswith(b"\n"):
        raise SystemExit("verification failed: trailing newline present")
    return actual


def report(path, data):
    """Print a short summary of the written entry.

    The summary names the output path and gives the three numbers that
    identify the entry: its character count (110), its byte count
    (112), and the SHA-256 digest of its exact bytes. Printing the
    digest lets anyone confirm, without opening the file, that the
    entry on disk is byte-for-byte the intended confession line.
    """
    digest = hashlib.sha256(data).hexdigest()
    text = data.decode("utf-8")
    print("wrote {} ({} chars, {} bytes, sha256 {})".format(
        path, len(text), len(data), digest))


def main():
    """Run the pipeline: line -> validate -> encode -> write -> verify.

    The steps run in a fixed order, and each one must succeed before
    the next one starts:

    1. ``get_confession_line`` returns the exact entry line.
    2. The four validators run in order -- not empty, single line,
       no padding, within the length limit -- each one raising
       ``SystemExit`` with a specific message if its check fails.
    3. ``encode_entry`` turns the checked line into UTF-8 bytes.
    4. ``prepare_output_path`` makes sure ``/output`` exists.
    5. ``write_entry`` writes the bytes to ``/output/entry.txt``.
    6. ``read_back_and_verify`` reads the file back and compares it
       byte for byte with what was written.
    7. ``report`` prints the path, counts, and SHA-256 digest.

    Returns 0 on success. Any validation or verification failure
    exits the program from inside the step that detected it.
    """
    line = get_confession_line()
    checked = validate_not_empty(line)
    checked = validate_single_line(checked)
    checked = validate_no_padding(checked)
    checked = validate_length(checked)
    data = encode_entry(checked)
    path = prepare_output_path()
    write_entry(path, data)
    verified = read_back_and_verify(path, data)
    report(path, verified)
    return 0


if __name__ == "__main__":
    sys.exit(main())
