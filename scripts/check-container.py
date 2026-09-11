"""Build and verify only a uniquely named disposable counter example."""
import json
import os
import socket
import subprocess
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
project = "blueprint-check-" + uuid.uuid4().hex[:12]
with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
environment = dict(os.environ, COUNTER_PORT=str(port))
command = ["docker", "compose", "--project-name", project, "-f", str(ROOT / "examples/counter/compose.yaml")]


def compose(*args):
    result = subprocess.run(command + list(args), env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(result.stdout)


def request(path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}" + path, data=body,
                                 headers={"Content-Type": "application/json"} if body else {})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


try:
    compose("up", "--build", "-d", "--wait", "--wait-timeout", "60")
    assert request("/health")["value"] == 0
    assert request("/api/increment", b"{}")["value"] == 1
    compose("up", "--force-recreate", "-d", "--wait", "--wait-timeout", "60")
    assert request("/api/counter")["value"] == 1
    print("Container health and persistence after recreation passed.")
finally:
    compose("down", "--volumes", "--remove-orphans")
