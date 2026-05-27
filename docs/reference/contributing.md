# Contributing

## Local development

```bash
pip install -e ".[dev,docs]"
pytest                     # full suite; cluster-marked tests skip off-cluster
pytest -m "not cluster"    # only the synthetic-fixture tests
black AOTaccess/ tests/    # formatter
flake8 AOTaccess/ tests/   # linter
```

## Building the docs

```bash
cd docs && sphinx-build -b html . _build/html
open _build/html/index.html
```

On the cluster, the examples gallery executes against the real data
(set `SPHINX_GALLERY_EXECUTE=0` to skip — that's what RTD does).

## Where to put things

| What | Where |
|---|---|
| New access class | `AOTaccess/<name>_access.py` + a test file `tests/test_<name>_access.py` |
| New derivative store path | `AOTaccess/settings.yml` + `AOTaccess/config.py:_RELATIVE_LAYOUT` |
| New user-guide page | `docs/user_guide/<page>.md`, add to `docs/index.rst` toctree |
| New example | `docs/examples/plot_NN_<topic>.py` (Sphinx-Gallery picks it up automatically) |
| New manifest type | `docs/reference/manifest_schemas.md` + an example under `schemas/` |

## Docstring style

Google-style (`Args:` / `Returns:` / `Raises:`), parsed by Napoleon and
rendered through the autosummary API reference. Keep them short — one
clear sentence summarising what the function does is more useful than a
long preamble.

## Path conventions

Every filename built or parsed by the API follows the BIDS conventions
documented in {doc}`../user_guide/naming_conventions`. Never inline
`f"ses-{ses:02d}"` or similar — use the helpers in
{mod}`AOTaccess.naming` (`fmt_sub`, `fmt_ses`, `fmt_run`, `fmt_video`),
which handle integer- and string-session cases uniformly.

## Error contract

`read_*` methods raise {class}`~AOTaccess.errors.DataNotFoundError` (a
`FileNotFoundError` subclass) with the resolved path and the identifiers
that produced it. Never return `None` for missing data.
