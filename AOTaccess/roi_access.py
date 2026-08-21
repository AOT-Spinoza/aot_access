"""Manifest-driven access to the AOT ROI derivatives.

Every path is resolved from the ROI library's ``MANIFEST.yaml`` (its
``path_templates`` section) rather than hard-coded here, so this module follows
the ROI toolchain's layout automatically whenever the manifest is regenerated.

The ROI library propagates hand-drawn and published-atlas ROIs into several
spaces. The ``fsnative`` volumetric space is the same voxel grid as the EPI
space used by GLMsingle and aot_prep, so an ``fsnative`` mask at a matching
resolution indexes a betas/BOLD array directly (see ``extract_betas_in_roi``
on ``AOTAccess``).
"""

import yaml
import numpy as np
import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError


# User-facing volume-space label -> ROI manifest template-key prefix.
# Following the project convention adopted 2026-05-22: `T1w` is the canonical
# label for the subject-native volume, `MNI` for the standard volume; bare
# `fsnative` and `fsaverage` are reserved for cortical surfaces.
#
# The current ROI manifest still uses the legacy template-key prefixes
# `fsnative_volume_*` and `mni_volume_*`; this map routes the canonical
# user-facing labels to them transitionally. When the aot_rois toolchain
# regenerates the store with BIDS-canonical entity ordering and the new
# template keys (`T1w_volume_*`, `MNI_volume_*`, surfaces under
# `space-fsnative`/`space-fsaverage`), flip this map to identity:
#
#     _VOLUME_SPACE_ALIASES = {"T1w": "T1w", "MNI": "MNI"}
#
# Everything else (defaults, surface methods, _resolve_volume_space) is
# already canonical and needs no further change.
_VOLUME_SPACE_ALIASES = {
    "T1w": "fsnative",
    "MNI": "mni",
    "MNI152NLin2009cAsym": "mni",   # BIDS-canonical alias
    "epi": "fsnative",              # legacy alias, kept transitionally
}

# Spaces accepted by surface methods.
_SURFACE_SPACES = {"fsnative", "fsaverage"}

# Preferred defaults, used when a space/atlas offers them. Volumetric methods
# take `res=None` / `cons=None` and resolve against the manifest and the store
# (see _resolve_res / _resolve_cons) — the spaces are not built at the same
# resolutions, nor the atlases at the same conservativeness levels, so a single
# hardcoded default cannot be right everywhere.
_PREFERRED_RES = "2p0mm"
_PREFERRED_CONS = "balanced"


def _resolve_volume_space(space):
    """Validate a volume-method `space` arg and return its manifest prefix.

    Rejects surface labels (`fsnative`, `fsaverage`) with a clear hint.
    """
    if space in _SURFACE_SPACES:
        raise ValueError(
            f"{space!r} is a surface space; for volumetric ROI masks use "
            f"space='T1w' (subject-native) or space='MNI'. Surface methods "
            f"(read_surface_label) take {space!r}."
        )
    if space not in _VOLUME_SPACE_ALIASES:
        raise ValueError(
            f"Unknown volume space {space!r}. "
            f"Valid: {sorted(_VOLUME_SPACE_ALIASES)}."
        )
    return _VOLUME_SPACE_ALIASES[space]


class ROIAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize a ROIAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.roi_dir = self.config.path("roi")
        self.manifest_path = self.roi_dir / "MANIFEST.yaml"
        self._manifest = None
        self._cons_cache = {}

    # ------------------------------------------------------------------
    # manifest
    # ------------------------------------------------------------------
    @property
    def manifest(self):
        """The parsed MANIFEST.yaml (lazy-loaded and cached)."""
        if self._manifest is None:
            if not self.manifest_path.exists():
                raise DataNotFoundError(
                    f"ROI manifest not found: {self.manifest_path}"
                )
            with open(self.manifest_path) as f:
                self._manifest = yaml.safe_load(f)
        return self._manifest

    def refresh(self):
        """Drop the cached manifest and directory listings.

        The ROI store is rebuilt in place, so a long-running process that
        first read it mid-build would otherwise keep serving what it saw
        then. Call this after a build lands to pick up the new state.
        """
        self._manifest = None
        self._cons_cache.clear()

    # ------------------------------------------------------------------
    # discovery
    # ------------------------------------------------------------------
    def atlases(self):
        """List atlas names, e.g. 'manual', 'wang_2015', 'glasser_2016'."""
        return list(self.manifest["atlases"])

    def atlas_info(self, atlas: str):
        """Return manifest metadata for an atlas (citation, source files, ...)."""
        return self.manifest["atlases"][atlas]

    def spaces(self):
        """List the spaces ROIs are propagated to."""
        return list(self.manifest["spaces"])

    def conservativeness_levels(self):
        """List conservativeness levels, e.g. 'strict', 'balanced', 'liberal'.

        Not every level is built for every atlas — ``fs_aseg`` ships only
        ``'labels'``, the others ship the remaining eight. Use
        :meth:`available_cons` for the levels actually present for one
        (subject, atlas, space, resolution), and :meth:`cons_info` for a
        level's description, threshold and sampling.
        """
        return list(self.manifest["conservativeness_levels"])

    def cons_info(self, cons: str):
        """Return manifest metadata for a conservativeness level.

        Mirrors :meth:`atlas_info` / :meth:`roi_info`: a dict with the
        level's ``description``, ``threshold`` and ``sampling``.
        """
        return self.manifest["conservativeness_levels"][cons]

    def resolutions(self, space: str = "T1w"):
        """List available resolutions for a volumetric space ('T1w' / 'MNI').

        The spaces differ: subject-native volumes are built at both
        ``2p0mm`` and ``1p25mm``, MNI volumes at ``1p25mm`` only.
        """
        key = _resolve_volume_space(space)
        return list(self.manifest["resolutions"][key])

    def subjects(self):
        """List subjects present in the ROI library, e.g. 'sub-001'."""
        return list(self.manifest["subjects"])

    def rois(self, subject=None):
        """List ROI names.

        With ``subject`` given, returns the ROIs available for that subject;
        otherwise returns every ROI defined in the library.
        """
        if subject is not None:
            return list(self._sub_entry(subject)["rois"])
        return list(self.manifest["rois"])

    def roi_info(self, roi: str):
        """Return manifest metadata for an ROI (full_name, source)."""
        return self.manifest["rois"][roi]

    def atlas_rois(self, atlas: str):
        """ROI names belonging to one atlas.

        :meth:`rois` pools every ROI in the library (or every ROI built for
        a subject) across all atlases, so a name from it is not necessarily
        readable with a given ``atlas=``. This is the per-atlas list.
        """
        return list(self.atlas_info(atlas).get("rois", []))

    def missing_rois(self, subject):
        """ROIs the manifest reports as not produced for a subject."""
        return self._sub_entry(subject).get("missing_rois", {})

    def template_keys(self):
        """List the path-template names defined in the manifest."""
        return list(self.manifest["path_templates"])

    # ------------------------------------------------------------------
    # provenance and build status
    # ------------------------------------------------------------------
    def provenance(self):
        """Who built this ROI library, when, and against which schema.

        A dict with ``manifest_schema_version``, ``toolchain_version``,
        ``generated_at``, ``generated_by``, ``dataset`` and ``schema_url``
        — the "what am I reading" story in one call.
        """
        m = self.manifest
        return {
            "manifest_schema_version": m.get("manifest_schema_version"),
            "toolchain_version": m.get("toolchain_version"),
            "generated_at": m.get("generated_at"),
            "generated_by": m.get("generated_by"),
            "dataset": m.get("dataset"),
            "schema_url": m.get("$schema"),
        }

    def schema_version(self):
        """Manifest schema version as an ``(major, minor, patch)`` tuple.

        Callers can branch on capability without string-munging; ``None``
        if the manifest predates the version key.
        """
        raw = self.manifest.get("manifest_schema_version")
        if raw is None:
            return None
        parts = str(raw).split(".")
        return tuple(int(p) if p.isdigit() else 0 for p in parts[:3])

    def build_status(self):
        """The toolchain's own report on the last build.

        A dict with ``completed``, ``hashes_computed``, ``failed_outputs``
        and ``warnings``. Empty dict for manifests that predate the key.
        """
        return self.manifest.get("build_status", {})

    def build_warnings(self):
        """Warnings recorded by the last build, as ``{code, message}`` dicts."""
        return list(self.build_status().get("warnings", []))

    def failed_outputs(self):
        """Products the last build failed to write.

        The per-file counterpart to :meth:`missing_rois`, which reports
        per-subject ROI gaps the toolchain knew about in advance.
        """
        return list(self.build_status().get("failed_outputs", []))

    def is_complete(self):
        """Whether the toolchain reported the last build as completed.

        ``False`` is a real signal that reads may hit missing files: the
        store is rebuilt in place, so a manifest can also be *older* than
        the tree it describes while a build is in flight.
        """
        return bool(self.build_status().get("completed", False))

    # ------------------------------------------------------------------
    # subject token helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sub_token(sub):
        """Zero-padded subject token: 1 -> '001', 'sub-001' -> '001'."""
        if isinstance(sub, int):
            return f"{sub:03d}"
        s = str(sub)
        return s[len("sub-"):] if s.startswith("sub-") else s

    def _sub_key(self, sub):
        """Subject key as used in the manifest 'subjects' mapping, 'sub-001'."""
        return f"sub-{self._sub_token(sub)}"

    def _sub_entry(self, sub):
        """Manifest entry for a subject; DataNotFoundError if absent.

        Subjects can exist in other stores (e.g. GLMsingle) before the ROI
        library has been regenerated for them.
        """
        key = self._sub_key(sub)
        entry = self.manifest["subjects"].get(key)
        if entry is None:
            raise DataNotFoundError(
                f"Subject {key} is not in the ROI library manifest "
                f"(available: {sorted(self.manifest['subjects'])}); "
                f"the ROI store may not have been regenerated for it yet."
            )
        return entry

    # ------------------------------------------------------------------
    # availability — what is actually on disk for one (sub, atlas, ...)
    # ------------------------------------------------------------------
    def _volume_dir(self, sub, atlas, space_key, res=None):
        """Directory holding one atlas's volumetric products for a subject."""
        d = (
            self.roi_dir
            / self._sub_key(sub)
            / f"{space_key}_volume"
            / f"atlas-{atlas}"
        )
        return d if res is None else d / f"res-{res}"

    def available_atlases(self, sub, space: str = "T1w"):
        """Atlases with volumetric products on disk for one subject."""
        return self._available_atlases(sub, _resolve_volume_space(space))

    def _available_atlases(self, sub, space_key):
        """:meth:`available_atlases` keyed by a resolved space prefix."""
        base = self.roi_dir / self._sub_key(sub) / f"{space_key}_volume"
        if not base.exists():
            return []
        return sorted(
            p.name[len("atlas-"):]
            for p in base.iterdir()
            if p.is_dir() and p.name.startswith("atlas-")
        )

    def available_resolutions(self, sub, atlas="wang_2015", space="T1w"):
        """Resolutions on disk for one (subject, atlas, space)."""
        key = _resolve_volume_space(space)
        base = self._volume_dir(sub, atlas, key)
        if not base.exists():
            return []
        return sorted(
            p.name[len("res-"):]
            for p in base.iterdir()
            if p.is_dir() and p.name.startswith("res-")
        )

    def available_cons(self, sub, atlas="wang_2015", space="T1w", res=None):
        """Conservativeness levels on disk for one (subject, atlas, space, res).

        Not every level is built for every atlas — ``fs_aseg`` ships only
        ``'labels'`` (a labels-preserving resample), the surface-sampled
        atlases ship the other eight. Cached per lookup.
        """
        return self._available_cons(sub, atlas, _resolve_volume_space(space), res)

    def _available_cons(self, sub, atlas, space_key, res):
        """:meth:`available_cons` keyed by an already-resolved space prefix.

        Empty listings are not cached: the store is rebuilt in place, so an
        atlas directory can be momentarily absent and must not be
        remembered as empty for the life of the object.
        """
        res = self._resolve_res(space_key, res)
        cache_key = (self._sub_key(sub), atlas, space_key, res)
        if cache_key not in self._cons_cache:
            base = self._volume_dir(sub, atlas, space_key, res)
            levels = (
                sorted(
                    p.name[len("cons-"):]
                    for p in base.iterdir()
                    if p.is_dir() and p.name.startswith("cons-")
                )
                if base.exists()
                else []
            )
            if not levels:
                return []
            self._cons_cache[cache_key] = levels
        return list(self._cons_cache[cache_key])

    def _atlas_cons(self, sub, atlas, space_key):
        """Conservativeness levels for an atlas, unioned over its resolutions.

        A single resolution's listing can be *partial* while the store is
        rebuilt in place. Corroborating across the atlas's resolutions
        keeps a half-written directory from looking like an atlas that
        ships exactly one level, which is what
        :meth:`_resolve_cons` keys its fallback on.
        """
        base = self._volume_dir(sub, atlas, space_key)
        if not base.exists():
            return []
        levels = set()
        for res_dir in base.iterdir():
            if res_dir.is_dir() and res_dir.name.startswith("res-"):
                levels.update(
                    self._available_cons(
                        sub, atlas, space_key, res_dir.name[len("res-"):]
                    )
                )
        return sorted(levels)

    # ------------------------------------------------------------------
    # default resolution / conservativeness
    # ------------------------------------------------------------------
    def _resolve_res(self, space_key, res):
        """Fill in a ``res=None`` default from the manifest, per space.

        The spaces are built at different resolutions (subject-native at
        2p0mm and 1p25mm, MNI at 1p25mm only), so a single hardcoded
        default cannot be right for both.
        """
        if res is not None:
            return res
        available = self.manifest.get("resolutions", {}).get(space_key) or []
        if _PREFERRED_RES in available:
            return _PREFERRED_RES
        return available[0] if available else _PREFERRED_RES

    def _resolve_cons(self, sub, atlas, space_key, res, cons):
        """Fill in a ``cons=None`` default from what is on disk.

        Prefers ``'balanced'`` where it exists; falls back to the sole
        level when an atlas ships exactly one (``fs_aseg`` → ``'labels'``).
        If nothing can be listed — an unbuilt subject, or a rebuild in
        flight — defers to ``'balanced'`` so the caller gets the familiar
        path-not-found error rather than a confusing one from here.

        Never guesses between several non-preferred levels: silently
        picking one would hand back a real, readable mask sampled at a
        conservativeness the caller did not ask for.
        """
        if cons is not None:
            return cons
        levels = self._atlas_cons(sub, atlas, space_key)
        if _PREFERRED_CONS in levels or not levels:
            return _PREFERRED_CONS
        if len(levels) == 1:
            if self._cons_is_exclusive(sub, space_key, res, levels[0]):
                return levels[0]
            # An ordinary level standing alone means the directory is still
            # being written — fall back so the caller gets a path-not-found
            # rather than a mask at a conservativeness they did not ask for.
            return _PREFERRED_CONS
        raise ValueError(
            f"No '{_PREFERRED_CONS}' conservativeness for atlas {atlas!r} "
            f"(sub={sub}, space={space_key}); pass cons= explicitly. "
            f"Available: {levels}."
        )

    def _cons_is_exclusive(self, sub, space_key, res, level):
        """Whether ``level`` is special-purpose rather than interchangeable.

        The manifest lists conservativeness levels globally, not per atlas,
        so the store itself has to say which are exclusive. A level that
        appears *alongside* the preferred one for some other atlas of this
        subject is an ordinary alternative (``strict``, ``liberal``,
        ``thick``, the ``pyc_*`` samplers) — seeing it alone means the
        directory is mid-write. A level that never co-occurs with it, as
        ``fs_aseg``'s ``labels`` never does, really is its atlas's only
        level.
        """
        for other in self._available_atlases(sub, space_key):
            levels = self._available_cons(sub, other, space_key, res)
            if level in levels and _PREFERRED_CONS in levels:
                return False
        return True

    # ------------------------------------------------------------------
    # generic path resolution
    # ------------------------------------------------------------------
    def resolve(self, template_key: str, **params):
        """Resolve a manifest path template to an absolute Path.

        ``template_key`` is one of :meth:`template_keys`; keyword arguments
        supply the template's ``{...}`` placeholders and are validated against
        the template's declared parameter list. ``sub`` may be an int or a
        'sub-XXX' string and is normalised to the bare token.
        """
        templates = self.manifest["path_templates"]
        if template_key not in templates:
            raise KeyError(
                f"Unknown path template '{template_key}'. "
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
                f"Template '{template_key}' expects parameters {sorted(required)}; "
                f"missing={sorted(missing)}, unexpected={sorted(unexpected)}."
            )
        return self.roi_dir / spec["template"].format(**params)

    # ------------------------------------------------------------------
    # volumetric masks (single ROI)
    # ------------------------------------------------------------------
    def mask_path(self, sub, roi, atlas="wang_2015", space="T1w",
                  res=None, cons=None, hemi=None):
        """Path to a single-ROI binary mask.

        ``hemi`` None resolves the bilateral mask (union of L and R);
        'L'/'R' resolves the per-hemisphere mask. ``space`` is 'T1w'
        (the EPI grid) or 'MNI'. ``res`` and ``cons`` default to what the
        store actually offers for this space and atlas — 2p0mm/balanced
        where available, otherwise the sole built alternative (MNI is
        1p25mm-only; ``fs_aseg`` is ``cons='labels'``-only).
        """
        sp = _resolve_volume_space(space)
        res = self._resolve_res(sp, res)
        cons = self._resolve_cons(sub, atlas, sp, res, cons)
        kind = "per_hemi" if hemi is not None else "bilateral"
        params = dict(sub=sub, atlas=atlas, roi=roi, res=res, cons=cons)
        if hemi is not None:
            params["hemi"] = hemi
        return self.resolve(f"{sp}_volume_mask_{kind}", **params)

    def read_mask(self, sub, roi, atlas="wang_2015", space="T1w",
                  res=None, cons=None, hemi=None):
        """Load a single-ROI mask as a boolean ndarray.

        With ``space='T1w'`` at a matching resolution the result indexes
        GLMsingle betas / preprocessed BOLD directly (same voxel grid).
        """
        path = self.mask_path(sub, roi, atlas, space, res, cons, hemi)
        if not path.exists():
            raise DataNotFoundError(
                f"ROI mask not found: {path}\n"
                f"(sub={sub}, roi={roi}, atlas={atlas}, space={space}, "
                f"res={res}, cons={cons}, hemi={hemi})"
            )
        return np.asarray(nib.load(path).get_fdata()) > 0

    # ------------------------------------------------------------------
    # volumetric parcellations (all ROIs of an atlas)
    # ------------------------------------------------------------------
    def dseg_path(self, sub, atlas="wang_2015", space="T1w",
                  res=None, cons=None, hemi=None):
        """Path to an atlas discrete segmentation (integer-labelled volume).

        ``res`` and ``cons`` default as in :meth:`mask_path`.
        """
        sp = _resolve_volume_space(space)
        res = self._resolve_res(sp, res)
        cons = self._resolve_cons(sub, atlas, sp, res, cons)
        kind = "per_hemi" if hemi is not None else "bilateral"
        params = dict(sub=sub, atlas=atlas, res=res, cons=cons)
        if hemi is not None:
            params["hemi"] = hemi
        return self.resolve(f"{sp}_volume_dseg_{kind}", **params)

    def read_dseg(self, sub, atlas="wang_2015", space="T1w",
                  res=None, cons=None, hemi=None):
        """Load an atlas discrete segmentation as an integer ndarray."""
        path = self.dseg_path(sub, atlas, space, res, cons, hemi)
        if not path.exists():
            raise DataNotFoundError(f"ROI dseg not found: {path}")
        return np.asarray(nib.load(path).get_fdata()).astype(int)

    # ------------------------------------------------------------------
    # surface labels
    # ------------------------------------------------------------------
    def surface_label_path(self, sub, roi, hemi, atlas="wang_2015",
                           space="fsnative"):
        """Path to a per-ROI surface label (.label.gii).

        ``space`` is 'fsnative' (atlas-specific) or 'fsaverage'. The
        fsaverage template is hardcoded to the hand-drawn ``manual``
        atlas, which carries no ROIs in the current build — so fsaverage
        labels do not resolve for any subject yet, and ``atlas`` is
        ignored for that space.
        """
        if space == "fsaverage":
            return self.resolve("fsaverage_surface_label",
                                sub=sub, roi=roi, hemi=hemi)
        return self.resolve("fsnative_surface_label",
                            sub=sub, roi=roi, hemi=hemi, atlas=atlas)

    def read_surface_label(self, sub, roi, hemi, atlas="wang_2015",
                           space="fsnative"):
        """Load a per-ROI surface label as a per-vertex ndarray."""
        path = self.surface_label_path(sub, roi, hemi, atlas, space)
        if not path.exists():
            raise DataNotFoundError(f"ROI surface label not found: {path}")
        return nib.load(path).agg_data()

    # ------------------------------------------------------------------
    # group probabilistic maps
    # ------------------------------------------------------------------
    def group_probseg_path(self, roi, hemi, atlas="wang_2015",
                           res="1p25mm", cons="balanced"):
        """Path to a group probabilistic segmentation (MNI) for one ROI."""
        return self.resolve("group_mni_probseg_per_hemi",
                            atlas=atlas, roi=roi, hemi=hemi, res=res, cons=cons)

    def read_group_probseg(self, roi, hemi, atlas="wang_2015",
                           res="1p25mm", cons="balanced"):
        """Load a group probabilistic segmentation (MNI) as a float ndarray."""
        path = self.group_probseg_path(roi, hemi, atlas, res, cons)
        if not path.exists():
            raise DataNotFoundError(f"Group probseg not found: {path}")
        return np.asarray(nib.load(path).get_fdata())

    # ------------------------------------------------------------------
    # group majority-vote (MNI) masks
    # ------------------------------------------------------------------
    def group_majority_path(self, roi, hemi, atlas="wang_2015",
                            res="1p25mm", cons="balanced"):
        """Path to a group majority-voted mask (MNI) for one ROI."""
        return self.resolve(
            "group_mni_majority_per_hemi",
            atlas=atlas, roi=roi, hemi=hemi, res=res, cons=cons,
        )

    def read_group_majority(self, roi, hemi, atlas="wang_2015",
                            res="1p25mm", cons="balanced"):
        """Load a group majority-voted mask (MNI) as a boolean ndarray."""
        path = self.group_majority_path(roi, hemi, atlas, res, cons)
        if not path.exists():
            raise DataNotFoundError(f"Group majority mask not found: {path}")
        return np.asarray(nib.load(path).get_fdata()) > 0

    # ------------------------------------------------------------------
    # group fsaverage surface products
    # ------------------------------------------------------------------
    def group_fsaverage_probseg_path(self, roi, hemi, atlas="wang_2015"):
        """Path to a group fsaverage-surface probabilistic map for one ROI."""
        return self.resolve(
            "group_fsaverage_probseg_per_hemi",
            atlas=atlas, roi=roi, hemi=hemi,
        )

    def read_group_fsaverage_probseg(self, roi, hemi, atlas="wang_2015"):
        """Load a group fsaverage-surface probseg as a per-vertex ndarray."""
        path = self.group_fsaverage_probseg_path(roi, hemi, atlas)
        if not path.exists():
            raise DataNotFoundError(f"Group fsaverage probseg not found: {path}")
        return nib.load(path).agg_data()

    def group_fsaverage_mpm_path(self, hemi, atlas="wang_2015"):
        """Path to the group fsaverage maximum-probability-map annot."""
        return self.resolve("group_fsaverage_mpm_annot", atlas=atlas, hemi=hemi)

    # ------------------------------------------------------------------
    # CIFTI grayordinate dlabel files (fsLR)
    # ------------------------------------------------------------------
    def cifti_dlabel_path(self, atlas="wang_2015", den="32k"):
        """Path to a CIFTI dlabel for one atlas at one fsLR density.

        ``den`` is ``"32k"`` or ``"170k"``.
        """
        key = f"cifti_{den}_dlabel"
        if key not in self.template_keys():
            raise ValueError(
                f"Unknown CIFTI density {den!r}; "
                f"available: {[k.replace('cifti_', '').replace('_dlabel', '') for k in self.template_keys() if k.startswith('cifti_')]}"
            )
        return self.resolve(key, atlas=atlas)

    def read_cifti_dlabel(self, atlas="wang_2015", den="32k"):
        """Load a CIFTI dlabel as a ``nibabel.cifti2.Cifti2Image``."""
        path = self.cifti_dlabel_path(atlas, den)
        if not path.exists():
            raise DataNotFoundError(f"CIFTI dlabel not found: {path}")
        return nib.load(path)
