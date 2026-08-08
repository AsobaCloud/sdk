# Publishing the Asoba SDK

This repository publishes two artifacts from a GitHub Release (`vX.Y.Z`):

| Artifact | Registry | Workflow |
|----------|----------|----------|
| `@asobacloud/sdk` | npm | `.github/workflows/javascript-publish.yml` |
| `asoba` | PyPI (org `asobacloud`) | `.github/workflows/python-publish.yml` |

## Prerequisites

### npm

1. Add repository secret **`NPM_TOKEN`** on [`AsobaCloud/sdk`](https://github.com/AsobaCloud/sdk/settings/secrets/actions)
   with a token that can publish to the `@asobacloud` scope
   (`gh secret set NPM_TOKEN --repo AsobaCloud/sdk`).

### PyPI (Trusted Publisher / OIDC)

1. Ensure GitHub Environment **`pypi`** exists on the repo (already created).
2. On [pypi.org](https://pypi.org) as an `asobacloud` org owner, add a
   **pending publisher** (or trusted publisher) for project **`asoba`**:
   - Owner: `AsobaCloud`
   - Repository: `sdk`
   - Workflow: `python-publish.yml`
   - Environment: `pypi`
3. First successful release publish creates the `asoba` project under the org.

## Release steps

1. Confirm versions in `javascript/package.json` and `python/pyproject.toml`
   match the release tag (currently `1.0.0`).
2. Push to `main`, ensure CI is green.
3. Create a GitHub Release:

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
```

4. Verify:

```bash
npm view @asobacloud/sdk version
pip index versions asoba
```

## Python import migration

- Preferred: `from asoba import OnaClient`
- Temporary: `import ona_platform` still works and emits `DeprecationWarning`
