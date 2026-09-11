# Local app architecture

## Architecture

```text
Laptop / PC / phone browsers
             |
         physical LAN
             |
NAS: app server + durable data + backups
             ^
             | outbound work and result traffic (heavy profile only)
             |
PC worker: CPU / GPU / local LLM / temporary scratch
```

The repository remains portable. Laptop and PC use ordinary local Git clones;
dependencies and build caches stay local to each machine. The NAS hosts the
running release, persistent data, mass storage, and backups. Do not develop in
an SMB/NFS-mounted worktree or edit a running NAS release.

## Standard profile

Use for normal websites, dashboards, databases, and lightweight background jobs.
The NAS runs the complete application. Laptop, PC, and phone need only a browser
for normal use.

## Heavy profile

Use when a feature needs substantially better CPU, GPU, RAM, media processing,
or a local LLM. The NAS still owns the UI, coordination, and durable data. The PC
worker connects outbound, processes a bounded task, and returns the result. The
app should remain safe when the PC is offline.

Models, package caches, intermediate files, and scratch space may be PC-local.
Source media should be mounted read-only by default. Before using GPU containers,
verify NVIDIA Container Toolkit; otherwise run the worker natively or on CPU.

## AI choices

| Need | Choice |
| --- | --- |
| Owner-guided development or one-off work | Codex/ChatGPT subscription on laptop or PC |
| Private repeatable inference | Local model on the PC worker |
| The running app calls a hosted model | OpenAI API with an explicit key and budget |
| No model is needed | No AI dependency |

A ChatGPT/Codex login is not an embedded application credential. Never silently
fall back from local or subscription work to paid API usage.

## Network boundary

- Bind the published service to the NAS physical-LAN IP.
- Do not add public tunnels, port forwarding, UPnP, public DNS, or cloud hosting.
- Treat Tailscale access as a separate opt-in decision.
- Keep real `.env` files and credentials outside Git.
