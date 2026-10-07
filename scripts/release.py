"""Package a committed application revision and smoke-test the extracted release."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import select
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def package(ref, output):
    commit = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    archive = git("archive", "--format=tar", commit, "app")
    manifest = json.dumps({"commit": commit}, indent=2).encode() + b"\n"
    # Verify the exact archived files before publishing the package.
    with tempfile.TemporaryDirectory(prefix="service-status-") as temporary:
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(temporary, filter="data")
        smoke_test(Path(temporary))
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"service-status-{commit}.tar.gz"
    with target.open("xb") as destination:
        with tarfile.open(fileobj=destination, mode="w:gz") as release:
            with tarfile.open(fileobj=io.BytesIO(archive)) as source:
                for member in source:
                    release.addfile(member, source.extractfile(member) if member.isfile() else None)
            info = tarfile.TarInfo("release.json")
            info.size = len(manifest)
            release.addfile(info, io.BytesIO(manifest))
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix + ".sha256").write_text(f"{checksum}  {target.name}\n")
    return target


def smoke_test(directory):
    command = (
        "from app.server import StatusServer, RequestHandler; "
        "server = StatusServer(('127.0.0.1', 0), RequestHandler); "
        "print(server.server_port, flush=True); server.serve_forever()"
    )
    process = subprocess.Popen(
        [sys.executable, "-u", "-c", command], cwd=directory,
        stdout=subprocess.PIPE, text=True,
    )
    try:
        if not select.select([process.stdout], [], [], 5)[0]:
            raise RuntimeError("Release server did not start within five seconds")
        port = int(process.stdout.readline())
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            if response.status != 200 or json.load(response) != {"status": "ok"}:
                raise RuntimeError("Release health check failed")
        with urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
            if b"<h1>Service Status</h1>" not in response.read():
                raise RuntimeError("Release homepage check failed")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ref", nargs="?", default="HEAD", help="Committed Git revision (default: HEAD)")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        print(package(args.ref, args.output))
    except (subprocess.CalledProcessError, OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Release failed: {error}\n")


if __name__ == "__main__":
    main()
