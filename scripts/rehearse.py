"""Rehearse previous -> candidate -> previous on one temporary localhost port."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

from release import check_server, package, running_server


def unpack(archive, directory):
    expected = archive.with_suffix(archive.suffix + ".sha256").read_text().split()[0]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Release checksum mismatch")
    directory.mkdir()
    with tarfile.open(archive) as source:
        source.extractall(directory, filter="data")
    return json.loads((directory / "release.json").read_text())["commit"]


def rehearse(previous, candidate):
    with tempfile.TemporaryDirectory(prefix="service-status-rehearsal-") as temporary:
        root = Path(temporary)
        old = root / "previous"
        new = root / "candidate"
        old_commit = unpack(package(previous, root / "old-packages"), old)
        new_commit = unpack(package(candidate, root / "new-packages"), new)
        if old_commit == new_commit:
            raise ValueError("Previous and candidate must resolve to different commits")
        port = 0
        for label, directory, commit in (
            ("Deploy previous", old, old_commit),
            ("Deploy candidate", new, new_commit),
            ("Roll back", old, old_commit),
        ):
            with running_server(directory, port) as port:
                check_server(port)
                print(f"{label}: {commit[:12]} healthy at http://127.0.0.1:{port}", flush=True)
        print("Rehearsal passed; temporary servers and files cleaned up.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", default="HEAD~1")
    parser.add_argument("--candidate", default="HEAD")
    args = parser.parse_args()
    try:
        rehearse(args.previous, args.candidate)
    except (subprocess.CalledProcessError, OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Rehearsal failed: {error}\n")


if __name__ == "__main__":
    main()
