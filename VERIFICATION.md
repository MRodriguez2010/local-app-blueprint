# Public release verification

Verified on September 11, 2026 from a fresh Git checkout on Linux.
Runtime files, dependencies, caches, and generated reports are excluded from Git.
The repository includes an executable GitHub Actions workflow; local verification
below is distinct from the status of any hosted workflow run.

- Python 3.12.3; no third-party Python dependencies.
- All four unit tests passed, covering reopen persistence, 40 concurrent writes,
  HTTP health/increment, and rejected requests.
- All three Compose templates resolved with synthetic settings; source media
  remained read-only and the heavy worker published no port.
- The pinned Docker example built, became healthy, incremented, was recreated,
  and retained its count. Only its uniquely named test resources were removed.
- Browser review exercised the counter and inspected a narrow viewport.
- This does not establish acceptance on a physical NAS, phone, or other OS.

The public Git history was scanned with Gitleaks 8.30.1 with no findings. The
publication review also checked tracked files for private host paths, credentials,
operational data, and broken local documentation links. These checks do not
constitute an exhaustive security assessment. Reproduce the commands in README.md
and report any failure with the source revision and a synthetic example.
