# Error handling

Every error the API raises derives from
{class}`~AOTaccess.errors.AOTAccessError`, so callers can catch the whole
family with one `except`. Two specialised subclasses cover the common cases.

```python
from AOTaccess.errors import AOTAccessError, ConfigError, DataNotFoundError
```

## `DataNotFoundError`

Raised when a requested file or directory doesn't exist on disk — by the
`read_*` methods on every access class, and by manifest lookups. It's
*also* a subclass of the builtin `FileNotFoundError`, so legacy
`except FileNotFoundError` handlers keep catching it unchanged.

The message names the **resolved path** and the **identifiers that produced
it**:

```text
DataNotFoundError: GLMsingle session betas not found:
  /research/.../glmsingle/per_session/sub-099/ses-01/space-T1w_res-2p0mm/...
  (sub=99, ses=1, glmtype=TYPED_FITHRF_GLMDENOISE_RR, resolution=2p0mm)
```

So you always see *what* was looked for, not just *that something* was
missing.

```python
from AOTaccess.subject import AOTSubject
from AOTaccess.errors import DataNotFoundError

sub = AOTSubject(1)
try:
    betas = sub.get_betas(ses=99)
except DataNotFoundError as e:
    print("missing data:", e)
```

## `ConfigError`

Raised when something is wrong with the configuration itself —
`settings.yml` not found, an unknown store key, a `root_dir`-mode lookup for
a key that isn't in `_RELATIVE_LAYOUT`. Never `FileNotFoundError`-derived
because it's not "the data is missing", it's "the config asked for the wrong
thing".

```python
from AOTaccess.errors import ConfigError

cfg = Config()
try:
    cfg.path("not-a-store")
except ConfigError as e:
    print("bad config:", e)
```

## `read_*` does not return `None`

The API never silently returns `None` for missing data; missing always
raises with context. Callers don't need null checks — wrap with
`try/except DataNotFoundError` if you want skip-on-missing behaviour.

## ValueError / TypeError

These are for bad *arguments*, not missing data. Examples:

- `read_mask(space="fsnative")` — `fsnative` is a surface space; pass
  `space="T1w"` (or use `read_surface_label`).
- `read_map("prf", 1, "surr_size", model="gauss")` — `surr_size` isn't a
  gauss-model parameter.
- `get_roi_mask(query=123)` — query must be a string or a list.
