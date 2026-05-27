# Localizers

A *localizer* is an auxiliary functional-mapping experiment with its own
session — pRF retinotopy (current), an fLOC category-selective localizer
(planned), and a Harvey-style duration / time mapper (planned). Localizer
sessions go through the *shared* pipelines (`aot_prep`, `glmsingle`); only
the final analysis products are localizer-specific and live in
`derivatives/localizers/<name>/`.

Same idiom as ROIs: each localizer carries its own `manifest.yaml`. Localizers
are diverse, so manifests stay separate.
{class}`~AOTaccess.localizer_access.LocalizerAccess` reads any of them.

## Discovery

```python
from AOTaccess.localizer_access import LocalizerAccess
la = LocalizerAccess()

la.localizers()                # ['prf', ...]
la.kind("prf")                 # 'parametric'
la.subjects("prf")
la.maps("prf", model="gauss")  # parameter names produced by the gauss model
la.models("prf")               # ['gauss', 'norm']
```

## Reading a map

`read_map(localizer, sub, map_name, **params)` — free parameters default from
the manifest's `defaults:` block; override per call:

```python
ecc = la.read_map("prf", 1, "ecc")                         # 3-D ndarray, gauss/2p0mm
surr = la.read_map("prf", 1, "surr_size", model="norm")
nc   = la.read_map("prf", 1, "noiseceiling")
```

Unknown maps, models, or paths raise
{class}`~AOTaccess.errors.DataNotFoundError` with the full resolved path
and the params used.

## PrfAccess — the convenience wrapper

For pRF specifically there's a thin
{class}`~AOTaccess.prf_access.PrfAccess` that keeps the familiar
`read_param` / `read_noiseceiling` names and adds optional R² masking:

```python
from AOTaccess.prf_access import PrfAccess
p = PrfAccess()

p.params(model="gauss")
ecc = p.read_param(sub=1, param="ecc")
ecc_masked = p.read_param(sub=1, param="ecc", mask=True, mask_r2_threshold=0.1)
nc = p.read_noiseceiling(sub=1)
```

Under the hood it just calls
{meth}`~AOTaccess.localizer_access.LocalizerAccess.read_map`. New code can use
`LocalizerAccess(localizer="prf")` directly.

## Authoring a new localizer manifest

See {doc}`../reference/manifest_schemas` for the schema; the worked pRF
example lives in the repo at `schemas/localizer-manifest.example.yaml`.

Once the manifest is dropped at `derivatives/localizers/<name>/manifest.yaml`,
`LocalizerAccess(localizer="<name>")` works with zero code change.
