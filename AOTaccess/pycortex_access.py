"""Access to the pycortex database used for flatmap display.

The flatmap display tools need the precomputed quickflat caches under
``derivatives/pycortex/db/<sub>/cache`` plus the 2 mm volume reference and the
flatmap coordinate transform.  Rebuilding the caches from FreeSurfer GIFTI
surfaces is a *display-side* concern (see the ``quality_display`` package); this
module only resolves and validates the stored files.
"""

import json

import nibabel as nib
import numpy as np
from scipy import sparse

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.naming import fmt_sub

_SURFACE_KINDS = ("flat", "pia", "wm")
_HEMIS = ("lh", "rh")


class PycortexAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize the PycortexAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.root_pycortex_dir = self.config.path("pycortex")

    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    def db_root(self):
        """Root of the pycortex database (``<pycortex>/db``)."""
        return self.root_pycortex_dir / "db"

    def subject_dir(self, sub):
        """Directory of one subject inside the pycortex database."""
        return self.db_root() / f"sub-{fmt_sub(sub)}"

    def flatmask_path(self, sub):
        """Path to the flatmap mask cache (``cache/flatmask_1024.npz``)."""
        return self.subject_dir(sub) / "cache" / "flatmask_1024.npz"

    def flatpixel_path(self, sub, resolution="2p0mm", sampler="l32"):
        """Path to a flatmap pixel-mapping cache.

        ``sampler`` selects the cortical-depth sampling: ``"l32"`` is the
        32-depth average used by the delivered flatmap movies; ``"d0.8"`` is a
        single-depth variant.
        """
        return (
            self.subject_dir(sub) / "cache"
            / f"flatpixel_res-{resolution}_1024_nearest_{sampler}.npz"
        )

    def reference_path(self, sub, resolution="2p0mm"):
        """Path to the volume reference grid for the flatmap projection."""
        return (
            self.subject_dir(sub) / "transforms" / f"res-{resolution}" / "reference.nii.gz"
        )

    def matrices_path(self, sub, resolution="2p0mm"):
        """Path to the flatmap coordinate transform (``matrices.xfm``)."""
        return (
            self.subject_dir(sub) / "transforms" / f"res-{resolution}" / "matrices.xfm"
        )

    def surface_path(self, sub, kind, hemi):
        """Path to one GIFTI surface (``surfaces/{flat,pia,wm}_{lh,rh}.gii``)."""
        if kind not in _SURFACE_KINDS:
            raise ValueError(f"kind must be one of {_SURFACE_KINDS}, got {kind!r}")
        if hemi not in _HEMIS:
            raise ValueError(f"hemi must be one of {_HEMIS}, got {hemi!r}")
        return self.subject_dir(sub) / "surfaces" / f"{kind}_{hemi}.gii"

    def flatmap_cache_paths(self, sub, resolution="2p0mm", sampler="l32"):
        """All four files needed to project a volume onto the flatmap."""
        return dict(
            mask=self.flatmask_path(sub),
            mapper=self.flatpixel_path(sub, resolution=resolution, sampler=sampler),
            reference=self.reference_path(sub, resolution=resolution),
            matrices=self.matrices_path(sub, resolution=resolution),
        )

    def has_flatmap_cache(self, sub, resolution="2p0mm", sampler="l32"):
        """True when the flatmap pixel-mapping cache exists."""
        return self.flatpixel_path(sub, resolution=resolution, sampler=sampler).is_file()

    # ------------------------------------------------------------------
    # readers
    # ------------------------------------------------------------------
    def read_flatmask(self, sub):
        """Read the flatmap mask cache as a dict with ``mask`` and ``extents``."""
        path = self.flatmask_path(sub)
        if not path.is_file():
            raise DataNotFoundError(f"Pycortex flatmask cache not found: {path} (sub={sub})")
        with np.load(path) as cache:
            return dict(mask=cache["mask"], extents=np.asarray(cache["extents"]))

    def read_flatpixel_mapper(self, sub, resolution="2p0mm", sampler="l32"):
        """Read the sparse pixel-mapping cache as a CSR matrix."""
        path = self.flatpixel_path(sub, resolution=resolution, sampler=sampler)
        if not path.is_file():
            raise DataNotFoundError(
                f"Pycortex flatpixel cache not found: {path} "
                f"(sub={sub}, resolution={resolution}, sampler={sampler})"
            )
        with np.load(path) as cache:
            mapper = sparse.csr_matrix(
                (cache["data"], cache["indices"], cache["indptr"]),
                shape=tuple(cache["shape"]),
            )
        return mapper

    def read_reference(self, sub, resolution="2p0mm"):
        """Read the 3-D volume reference grid used by the projection."""
        path = self.reference_path(sub, resolution=resolution)
        if not path.is_file():
            raise DataNotFoundError(f"Pycortex reference grid not found: {path} (sub={sub})")
        return nib.load(str(path))

    def read_matrices(self, sub, resolution="2p0mm"):
        """Read the flatmap coordinate transform JSON (``matrices.xfm``)."""
        path = self.matrices_path(sub, resolution=resolution)
        if not path.is_file():
            raise DataNotFoundError(f"Pycortex matrices.xfm not found: {path} (sub={sub})")
        return json.loads(path.read_text())

    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------
    def validate_flatmap_cache(self, sub, resolution="2p0mm", sampler="l32"):
        """Check that mask/mapper/reference agree in shape; return an audit dict."""
        mask = self.read_flatmask(sub)
        mapper = self.read_flatpixel_mapper(sub, resolution=resolution, sampler=sampler)
        reference = self.read_reference(sub, resolution=resolution)
        expected = (int(mask["mask"].sum()), int(np.prod(reference.shape)))
        audit = dict(
            subject=f"sub-{fmt_sub(sub)}",
            sampler=sampler,
            resolution=resolution,
            flatmap_pixels=int(mask["mask"].sum()),
            mapper_rows=int(mapper.shape[0]),
            mapper_columns=int(mapper.shape[1]),
            reference_voxels=int(np.prod(reference.shape)),
            reference_shape=list(reference.shape),
            shape_ok=mapper.shape == expected,
            extents=[float(v) for v in mask["extents"]],
        )
        if not audit["shape_ok"]:
            raise ValueError(
                f"Pycortex flatmap cache dimensions disagree for {audit['subject']}: "
                f"mapper={mapper.shape}, expected={expected}"
            )
        return audit
