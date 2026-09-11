"""Resolve deployment templates using synthetic configuration, without deployment."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALUES = {
    "APP_IMAGE": "example/app:0.1.0", "WORKER_IMAGE": "example/worker:0.1.0",
    "LAN_BIND_IP": "127.0.0.1", "APP_PORT": "8080", "CONTAINER_PORT": "8080",
    "APP_DATA_DIR": "/tmp/blueprint-check/data", "APP_JOBS_DIR": "/tmp/blueprint-check/jobs",
    "HEALTHCHECK_COMMAND": "true", "COORDINATOR_URL": "http://127.0.0.1:8080",
    "PC_MODEL_DIR": "/tmp/blueprint-check/models", "PC_CACHE_DIR": "/tmp/blueprint-check/cache",
    "PC_SCRATCH_DIR": "/tmp/blueprint-check/scratch", "NAS_MEDIA_MOUNT": "/tmp/blueprint-check/media",
}

with tempfile.TemporaryDirectory(prefix="blueprint-config-") as directory:
    target = Path(directory)
    (target / ".env").write_text("".join(f"{key}={value}\n" for key, value in VALUES.items()))
    for source in sorted((ROOT / "templates").rglob("*.yaml")):
        shutil.copyfile(source, target / "compose.yaml")
        result = subprocess.check_output(["docker", "compose", "--project-name", "blueprint-config-check", "-f", str(target / "compose.yaml"), "config", "--format", "json"], text=True)
        config = json.loads(result)
        for name, service in config["services"].items():
            if name == "worker":
                assert not service.get("ports"), "worker must connect outbound"
                media = next(volume for volume in service["volumes"] if volume["target"] == "/worker/media")
                assert media["read_only"], "source media must be read-only"
            else:
                assert all(port["host_ip"] == "127.0.0.1" for port in service["ports"]), "explicit bind lost"
        print(f"Verified {source.relative_to(ROOT)}")
