"""Filesystem- and manifest-backed discovery for the AOT dataset.

Free functions that answer "what subjects / sessions / runs / videos /
atlases / ROIs / localizers are actually present?" without the caller having
to guess identifiers. Everything is read directly from the configured stores
(glmsingle / aot_prep / roi / localizers); manifests are consulted where they
exist.
"""

import re

from AOTaccess.config import Config
from AOTaccess.naming import fmt_sub, fmt_ses


_VIDEO_DESC_RE = re.compile(r"_desc-(\d{4})(?:betas|betaszscore)")
_RUN_RE = re.compile(r"_run-(\d+)_")
_SES_RE = re.compile(r"^ses-(.+)$")
_SUB_RE = re.compile(r"^sub-(\d+)$")


def _cfg(config):
    return config if config is not None else Config()


def subjects(config=None):
    """Subjects with main-task GLMsingle data, as a sorted list of ints."""
    cfg = _cfg(config)
    base = cfg.path("glmsingle") / "per_session"
    if not base.exists():
        return []
    out = []
    for p in base.iterdir():
        m = _SUB_RE.match(p.name)
        if m and p.is_dir():
            out.append(int(m.group(1)))
    return sorted(out)


def sessions(sub, config=None):
    """Sessions present for a subject's main-task GLMsingle outputs.

    Returns a sorted list — integers for AOT-task sessions (``1`` … ``10``)
    and strings for non-integer session labels (e.g. ``"pRF"``) if present.
    """
    cfg = _cfg(config)
    sub_dir = cfg.path("glmsingle") / "per_session" / f"sub-{fmt_sub(sub)}"
    if not sub_dir.exists():
        return []
    out = []
    for p in sub_dir.iterdir():
        if not p.is_dir():
            continue
        m = _SES_RE.match(p.name)
        if not m:
            continue
        token = m.group(1)
        out.append(int(token) if token.isdigit() else token)
    # ints sort before strings; partition then sort each
    ints = sorted(x for x in out if isinstance(x, int))
    strs = sorted(x for x in out if isinstance(x, str))
    return ints + strs


def runs(sub, ses, config=None):
    """Run indices present for (sub, ses) in the preprocessed-BOLD store."""
    cfg = _cfg(config)
    d = cfg.path("preproced") / f"sub-{fmt_sub(sub)}" / f"ses-{fmt_ses(ses)}" / "func"
    if not d.exists():
        return []
    found = set()
    for f in d.iterdir():
        m = _RUN_RE.search(f.name)
        if m:
            found.add(int(m.group(1)))
    return sorted(found)


def videos(sub, direction="fw", resolution="2p0mm", config=None):
    """Unique video ids with per-video GLMsingle betas for this subject."""
    cfg = _cfg(config)
    d = (
        cfg.path("glmsingle") / "per_video"
        / f"sub-{fmt_sub(sub)}" / f"space-T1w_res-{resolution}" / direction
    )
    if not d.exists():
        return []
    found = set()
    for f in d.iterdir():
        m = _VIDEO_DESC_RE.search(f.name)
        if m:
            found.add(int(m.group(1)))
    return sorted(found)


def atlases(config=None):
    """ROI atlases declared in the ROI manifest."""
    from AOTaccess.roi_access import ROIAccess
    return ROIAccess(config=_cfg(config)).atlases()


def rois(subject=None, config=None):
    """ROI names (all, or those available for a given subject)."""
    from AOTaccess.roi_access import ROIAccess
    return ROIAccess(config=_cfg(config)).rois(subject=subject)


def localizers(config=None):
    """Localizer names with a manifest in the localizers store."""
    from AOTaccess.localizer_access import LocalizerAccess
    return LocalizerAccess(config=_cfg(config)).localizers()
