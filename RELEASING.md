# Releasing `astrolinkers-sdk`

This SDK is published to PyPI via **Trusted Publishing** — the
GitHub Actions workflow at `.github/workflows/release.yml` exchanges
a one-shot OIDC token for an upload credential. No PyPI API token
ever lives in the repo or in CI secrets.

## One-time setup (already done — listed for posterity)

1. The project owner enabled 2FA on the PyPI account.
2. On https://pypi.org/manage/account/publishing/ a **pending
   publisher** was registered with these exact values:

   | Field              | Value                       |
   | ------------------ | --------------------------- |
   | PyPI Project Name  | `astrolinkers-sdk`          |
   | Owner              | `fedorello`                 |
   | Repository name    | `astrolinkers-sdk-python`   |
   | Workflow filename  | `release.yml`               |
   | Environment name   | `pypi`                      |

3. A `pypi` environment was created in the GitHub repo (Settings →
   Environments → New environment). Optional: enable
   "Required reviewers" so a release upload needs a human approval.

## Cutting a release

1. **Bump the version** in `pyproject.toml` and `src/astrolinkers/_version.py`
   (both must match).
2. **Update `CHANGELOG.md`** with the new version's section.
3. **Run the quality gates locally**:

   ```bash
   uv run ruff check src tests
   uv run mypy
   uv run pytest -q
   uv build
   ```

   `uv build` emits a wheel + sdist into `dist/` so you can sanity-
   check the contents (`tar tf dist/*.tar.gz | head` is a good
   smoke test).

4. **Commit + push** the version bump:

   ```bash
   git add pyproject.toml src/astrolinkers/_version.py CHANGELOG.md
   git commit -m "Release v0.X.Y"
   git push
   ```

5. **Tag and push the tag**:

   ```bash
   git tag -a v0.X.Y -m "v0.X.Y"
   git push origin v0.X.Y
   ```

   The tag push triggers `release.yml`. Watch the run at
   https://github.com/fedorello/astrolinkers-sdk-python/actions.

6. **Verify on PyPI**:

   ```bash
   pip index versions astrolinkers-sdk
   ```

   The new version should appear within ~1 minute of the workflow
   completing. `pip install astrolinkers-sdk==0.X.Y` should work
   immediately afterwards.

## What happens on a tag push

```
git push origin v0.X.Y
        │
        ▼
GitHub Actions: release.yml
        │
        ├── Check out the tag
        ├── Install uv, pin Python 3.13
        ├── Verify tag == pyproject version
        ├── ruff + mypy + pytest
        ├── uv build  (→ dist/*.tar.gz, dist/*.whl)
        ├── Request OIDC token (id-token: write)
        └── pypa/gh-action-pypi-publish
                │
                ▼
            PyPI exchanges OIDC token for upload creds
                │
                ▼
            Wheel + sdist uploaded with PEP 740 attestations
```

## If something goes wrong

- **Tag-version mismatch** → the workflow exits early before
  publish. Push a new tag matching `pyproject.toml`.
- **PyPI rejects the upload** → the most common cause is that the
  pending publisher was never converted to active. Check
  https://pypi.org/manage/project/astrolinkers-sdk/settings/publishing/
  and confirm the GitHub config matches.
- **A version was published with a bug** → PyPI does not allow
  re-using a version number. Yank the bad release
  (`pypi.org/manage/project/astrolinkers-sdk/release/0.X.Y/` →
  "Yank release") and ship `0.X.(Y+1)`.

## Why Trusted Publishing instead of a token

* No long-lived credential to leak, rotate, or accidentally commit.
* Every upload is tied to a specific tag on a specific repo via
  OIDC + PEP 740 attestations.
* Compromising a CI secret no longer compromises PyPI access — the
  attacker also needs to push to the repo.
