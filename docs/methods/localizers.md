# Localizers

```{admonition} Authoring TODO
:class: note
Lab-authored per localizer. Each section below is a template.
```

## pRF (population receptive field mapping)

- **Session label:** `ses-pRF`
- **Manifest:** `derivatives/localizers/prf/manifest.yaml`
- **Stimulus design:** describe the aperture sweep / bar protocol.
- **Run timing:** runs per session, run length, ISI.
- **Fits:** `prfpy`, models = `gauss`, `norm` (and `dog` — combined `.tsv` only).
- **Parameters:** see `params(model=…)`; also the noise-ceiling map.

## fLOC (planned)

- **Session label:** `ses-fLOC` *(to be confirmed)*
- **Stimulus design:** ?
- **Contrasts produced:** face / body / place / character / object …
- **Outputs:** GLM contrast maps under `derivatives/localizers/fLOC/`.

## Duration / time mapper (planned)

- **Session label:** `ses-time` *(to be confirmed)*
- **Stimulus design:** Harvey-style duration-tuning protocol.
- **Fits:** parametric (preferred duration, tuning width, …).
- **Outputs:** parameter maps under `derivatives/localizers/time/`.

## How a localizer becomes API-accessible

Drop the manifest at `derivatives/localizers/<name>/manifest.yaml` —
{class}`~AOTaccess.localizer_access.LocalizerAccess` picks it up
automatically. No code changes are needed for a new localizer. See
{doc}`../reference/manifest_schemas` for the schema and
`schemas/localizer-manifest.example.yaml` for the worked pRF example.
