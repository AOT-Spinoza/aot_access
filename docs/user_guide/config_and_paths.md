# Configuration and paths

Every store the API touches is resolved through one central
{class}`~AOTaccess.config.Config`. Each access class holds a `Config` and
asks it for paths — there's no `settings.yml` reading or `root_dir`
branching scattered across modules.

## Three ways to point at data

**1. Default — packaged `settings.yml`.** Absolute cluster paths; works
out-of-the-box on the lab's filesystem.

```python
from AOTaccess.config import Config
cfg = Config()
cfg.path("glmsingle")
cfg.path("roi")
```

**2. Override the settings file.** Two equivalent ways:

```bash
export AOT_SETTINGS=/path/to/my_settings.yml
```

```python
cfg = Config(settings_path="/path/to/my_settings.yml")
```

**3. `root_dir` — relocated / copied dataset.** Resolve every store
relative to one dataset root, using the canonical layout in
{data}`AOTaccess.config._RELATIVE_LAYOUT`:

```python
cfg = Config(root_dir="/scratch/me/aot_copy")
cfg.path("glmsingle")    # /scratch/me/aot_copy/derivatives/glmsingle
cfg.path("roi")          # /scratch/me/aot_copy/derivatives/roi
```

## Sharing a Config

Pass it explicitly to every access class so they share parsed settings:

```python
from AOTaccess.subject import AOTSubject

cfg = Config()
subs = [AOTSubject(i, config=cfg) for i in (1, 2, 3, 4, 5, 7, 8)]
```

{class}`~AOTaccess.aot_access.AOTAccess` builds one `Config` internally
and shares it with every sub-accessor.

## Adding a new store

When a new derivative folder appears under the dataset:

1. Add a `paths.<key>` entry to `AOTaccess/settings.yml` (absolute path).
2. Add the same key to `AOTaccess/config._RELATIVE_LAYOUT` (relative path under
   the dataset root, for `root_dir` mode).
3. The access class for the new store calls `self.config.path("<key>")` —
   no module-level `yaml.safe_load`, ever.

## The `parameters:` section

Numeric / scalar settings (e.g. `run_number: 10`) live under
`settings.yml`'s `parameters:` section and are read via
{meth}`~AOTaccess.config.Config.param`:

```python
cfg.param("run_number")           # 10
cfg.param("missing", default=7)   # 7
```

## Anatomy roots — dual-cluster fallback

{meth}`~AOTaccess.config.Config.anatomy_root` returns the first existing
candidate from the VU `/research/...` and Snellius `/projects/prjs1914/...`
roots, so `read_affine` / `read_header` work from either cluster.
