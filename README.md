# Local App Blueprint

A small starting point for apps that run on a NAS or a trusted local machine.
Develop on your laptop or PC; keep the running release, durable data, and backups
on the NAS. Add an outbound PC worker only when a job needs its CPU or GPU.

[![CI](https://github.com/MRodriguez2010/local-app-blueprint/actions/workflows/ci.yml/badge.svg)](https://github.com/MRodriguez2010/local-app-blueprint/actions/workflows/ci.yml)

## Try the runnable example

The included Python/SQLite counter demonstrates a health endpoint, persistent
data, concurrent writes, and a browser interface. It contains only a synthetic
integer and does not require an account, API key, model, or hosted service.

```bash
git clone https://github.com/MRodriguez2010/local-app-blueprint.git
cd local-app-blueprint
python3 examples/counter/app.py
```

Open **http://127.0.0.1:8080**. Press Add one, stop the app with Ctrl+C, and restart
it. The count persists in the ignored `data/counter.sqlite3` file. Python 3.12+
is required; there are no third-party Python dependencies.

For an isolated Docker example:

```bash
docker compose -f examples/counter/compose.yaml up --build -d --wait
# Open http://127.0.0.1:8080
docker compose -f examples/counter/compose.yaml restart
docker compose -f examples/counter/compose.yaml down
```

The named volume survives `down`. To discard this example's synthetic count,
use `down --volumes` with the same Compose file. Set `COUNTER_PORT=8081` if 8080
is occupied. The example publishes only on loopback and runs as a non-root user.

## Adapt the blueprint

| Starting point | Use |
| --- | --- |
| [Standard template](templates/standard) | App and durable storage on the NAS |
| [Heavy template](templates/heavy) | NAS coordinator plus an outbound PC worker |
| [Architecture](BLUEPRINT.md) | Choose ownership, storage, and AI boundaries |
| [Development and deployment](DEVELOP_AND_DEPLOY.md) | Build, verify, deploy, and roll back |

The templates require your own immutable app image, data paths, health command,
and physical LAN bind address. They are deployment skeletons; the heavy profile
does not implement a job queue or worker protocol. Real `.env` files stay out of Git.
The example's container listens on all container interfaces so Docker can reach
it; its **host port** stays bound to 127.0.0.1.

Before putting real data behind a LAN service, add authentication appropriate to
your app, define backup/restore behavior, and verify access from your actual
clients. This example has no user accounts and is intended for a trusted local
machine. Do not expose it through port forwarding or a public tunnel.

## Verify

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check-compose.py
```

Tests exercise persistence, concurrent writes, health, and rejected cross-origin
requests. The Compose check resolves every template using synthetic values and
checks the published ports and read-only source-media mount. CI also builds and
restarts the Docker example to check persistence.

## Backup the example

Stop the app before copying `counter.sqlite3` from its data directory or Docker
volume. Restore while the app is stopped, then restart and check the counter.
For a real app, use its database's documented backup and migration procedure.

MIT licensed. See [authorship](AUTHORS.md), [contributing](CONTRIBUTING.md), and
[security and support](SECURITY.md). The local example is verified on Linux;
NAS and physical phone acceptance depend on the host where you deploy it.
