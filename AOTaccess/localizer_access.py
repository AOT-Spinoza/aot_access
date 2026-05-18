"""Manifest-driven access to the AOT localizer derivatives.

A "localizer" is an auxiliary functional-mapping experiment — pRF retinotopy,
an fLOC category localizer, a Harvey-style duration mapper, and so on.
Localizer sessions are preprocessed and modelled through the *shared* pipelines
(``aot_prep``, ``glmsingle``); only the final analysis products are
localizer-specific and live under ``derivatives/localizers/<name>/``.

Each localizer carries its own ``manifest.yaml`` — localizers are diverse, so
manifests are kept separate. A manifest declares the localizer's subjects,
result maps, default parameters, and path templates. ``LocalizerAccess``
resolves every path from those manifests; no per-localizer layout is hard-coded
here, so a new localizer is added by dropping its folder + manifest, with no
code change. See ``schemas/localizer-manifest.example.yaml`` for the structure.
"""

import yaml
import numpy as np
import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError


class LocalizerAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize a LocalizerAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.localizers_dir = self.config.path("localizers")
        self._manifests = {}

    # ------------------------------------------------------------------
    # manifest
    # ------------------------------------------------------------------
    def manifest_path(self, localizer: str):
        """Path to a localizer's manifest.yaml."""
        return self.localizers_dir / localizer / "manifest.yaml"

    def manifest(self, localizer: str):
        """Parsed manifest.yaml for a localizer (lazy-loaded, cached)."""
        if localizer not in self._manifests:
            path = self.manifest_path(localizer)
            if not path.exists():
                raise DataNotFoundError(
                    f"Localizer manifest not found: {path}. "
                    f"Known localizers: {self.localizers()}"
                )
            with open(path) as f:
                self._manifests[localizer] = yaml.safe_load(f)
        return self._manifests[localizer]

    # ------------------------------------------------------------------
    # discovery
    # ------------------------------------------------------------------
    def localizers(self):
        """List localizers in the store (subfolders carrying a manifest.yaml)."""
        if not self.localizers_dir.exists():
            return []
        return sorted(
            p.name
            for p in self.localizers_dir.iterdir()
            if (p / "manifest.yaml").exists()
        )

    def kind(self, localizer: str):
        """The localizer's output kind, e.g. 'parametric' or 'contrast'."""
        return self.manifest(localizer).get("kind")

    def description(self, localizer: str):
        """Free-text description of a localizer."""
        return self.manifest(localizer).get("description")

    def subjects(self, localizer: str):
        """List subjects available for a localizer."""
        return list(self.manifest(localizer).get("subjects", []))

    def models(self, localizer: str):
        """List fit models for a parametric localizer (empty if it has none)."""
        return list(self.manifest(localizer).get("models", {}))

    def maps(self, localizer: str, model: str = None):
        """List result-map names for a localizer.

        With ``model`` given, returns only maps that model produces (plus any
        model-independent maps).
        """
        all_maps = self.manifest(localizer).get("maps", {})
        if model is None:
            return sorted(all_maps)
        return sorted(
            m
            for m, info in all_maps.items()
            if not info.get("models") or model in info["models"]
        )

    def map_info(self, localizer: str, map: str):
        """Manifest metadata for one result map."""
        return self.manifest(localizer)["maps"][map]

    def template_keys(self, localizer: str):
        """List path-template names defined in a localizer's manifest."""
        return list(self.manifest(localizer).get("path_templates", {}))

    # ------------------------------------------------------------------
    # path resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _sub_token(sub):
        """Zero-padded subject token: 1 -> '001', 'sub-001' -> '001'."""
        if isinstance(sub, int):
            return f"{sub:03d}"
        s = str(sub)
        return s[len("sub-"):] if s.startswith("sub-") else s

    def resolve(self, localizer: str, template_key: str, **params):
        """Resolve a manifest path template to an absolute Path.

        Keyword arguments supply the template's ``{...}`` placeholders and are
        validated against the template's declared parameter list.
        """
        templates = self.manifest(localizer).get("path_templates", {})
        if template_key not in templates:
            raise KeyError(
                f"Localizer '{localizer}' has no path template '{template_key}'. "
                f"Available: {sorted(templates)}"
            )
        spec = templates[template_key]
        required = set(spec["parameters"])
        params = dict(params)
        if "sub" in params:
            params["sub"] = self._sub_token(params["sub"])
        missing = required - set(params)
        unexpected = set(params) - required
        if missing or unexpected:
            raise ValueError(
                f"Template '{template_key}' of localizer '{localizer}' expects "
                f"{sorted(required)}; missing={sorted(missing)}, "
                f"unexpected={sorted(unexpected)}."
            )
        return self.localizers_dir / localizer / spec["template"].format(**params)

    def map_path(self, localizer: str, sub, map: str, **params):
        """Path to a localizer result map.

        Free parameters (model, resolution, ...) default to the manifest's
        ``defaults`` and may be overridden via keyword arguments.
        """
        manifest = self.manifest(localizer)
        info = manifest.get("maps", {}).get(map)
        if info is None:
            raise ValueError(
                f"Localizer '{localizer}' has no map '{map}'. "
                f"Available: {self.maps(localizer)}"
            )
        merged = {**manifest.get("defaults", {}), **params}
        if info.get("models") and "model" in merged:
            if merged["model"] not in info["models"]:
                raise ValueError(
                    f"Map '{map}' of localizer '{localizer}' is not produced by "
                    f"model '{merged['model']}'; available: {info['models']}."
                )
        template_key = info.get("template", "default")
        spec = manifest.get("path_templates", {}).get(template_key)
        if spec is None:
            raise KeyError(
                f"Map '{map}' of localizer '{localizer}' references unknown "
                f"path template '{template_key}'."
            )
        # Supply sub + map, then keep only what this template declares.
        candidate = {"sub": sub, "map": map, **merged}
        wanted = {k: v for k, v in candidate.items() if k in spec["parameters"]}
        return self.resolve(localizer, template_key, **wanted)

    def read_map(self, localizer: str, sub, map: str, **params):
        """Read a localizer result map as an ndarray."""
        path = self.map_path(localizer, sub, map, **params)
        if not path.exists():
            raise DataNotFoundError(
                f"Localizer map not found: {path}\n"
                f"(localizer={localizer}, sub={sub}, map={map}, params={params})"
            )
        return np.asarray(nib.load(path).get_fdata())
