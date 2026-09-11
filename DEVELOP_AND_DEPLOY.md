# Repeatable development and deployment

## 1. Define the app

Record the chosen profile, repository, NAS host/IP, port, persistent directories,
backup target, health URL, AI choice, and rollback command. Reuse the app's
existing conventions instead of forcing a new platform onto it.

## 2. Develop on laptop or PC

1. Clone or pull the same repository revision locally.
2. Create a normal task branch such as `codex/feature-name`.
3. Install dependencies locally; do not share dependency folders over SMB/NFS.
4. Use test data and untracked local secrets.
5. Run the application's existing lint, type, unit, and browser smoke checks.
6. Commit and push the exact revision intended for deployment.

Laptop and PC should be interchangeable development clients. Neither becomes the
only copy of source code or application data.

## 3. Prepare the NAS

1. Choose `templates/standard` or `templates/heavy`.
2. Copy its Compose and `.env.example` files into the application.
3. Replace every `CHANGE_ME` value and store the real `.env` outside Git.
4. Confirm NAS paths, ownership, free space, LAN bind IP, and port availability.
5. Create a recoverable backup of persistent data.
6. Run `docker compose config` and inspect the resolved mounts and published port.

## 4. Deploy and verify

1. Pull/build the tested revision or immutable image.
2. Run the app-specific `docker compose up -d` command.
3. Check container status and bounded recent logs.
4. Check the health URL.
5. Open the main workflow from laptop and phone over the physical LAN.
6. Keep the prior working image/revision available for rollback.

A container start alone is not proof that the app works.

## 5. Heavy worker only

1. Verify the PC can reach the NAS app.
2. Use PC-local model, cache, and scratch paths.
3. Mount NAS source media read-only unless writes are explicitly required.
4. Publish no worker control port; the worker connects outbound.
5. Submit one small task and verify its durable result on the NAS.
6. Stop the worker and confirm the main app remains safe and usable.

## Rollback

Restore the previous Compose/image revision. Restore data only if the failed
release changed stored data; otherwise avoid overwriting newer user work.
