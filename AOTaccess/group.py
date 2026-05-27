"""``AOTGroup`` — cross-subject access dispatching over a cohort.

Build from a list of subject ids (or pre-built ``AOTSubject`` instances) sharing
one ``Config``. Methods return per-subject dicts keyed by the subject id,
suitable for cross-subject encoding/decoding work. Brain masks and ROI voxel
counts differ across subjects, so the returned dict's values aren't
broadcastable; iterate per-subject or do your own alignment.
"""

from AOTaccess.config import Config
from AOTaccess.subject import AOTSubject


class AOTGroup:
    """A cohort of :class:`AOTSubject` objects sharing one Config."""

    def __init__(self, subjects, config=None, **subject_kwargs):
        """
        Parameters:
            subjects: Iterable of subject ids (``int`` / ``"sub-001"``) or
                already-built ``AOTSubject`` instances; mixed lists are fine.
            config (Config): Shared across the cohort; built fresh if omitted.
            **subject_kwargs: Forwarded to ``AOTSubject`` constructors
                (e.g. ``resolution``, ``glmtype``).
        """
        self.config = config if config is not None else Config()
        self.subjects = {}
        for s in subjects:
            if isinstance(s, AOTSubject):
                self.subjects[s.sub] = s
            else:
                self.subjects[s] = AOTSubject(
                    s, config=self.config, **subject_kwargs
                )

    # ------------------------------------------------------------------
    # cohort introspection
    # ------------------------------------------------------------------
    def __len__(self):
        return len(self.subjects)

    def __iter__(self):
        return iter(self.subjects.values())

    def __contains__(self, sub):
        return sub in self.subjects

    def __getitem__(self, sub):
        return self.subjects[sub]

    def keys(self):
        """Sorted-ish ordering preserved as inserted; use ``sorted(g.keys())``."""
        return list(self.subjects.keys())

    # ------------------------------------------------------------------
    # cross-subject discovery
    # ------------------------------------------------------------------
    def shared_videos(self, direction="fw"):
        """Videos with per-video betas in **every** subject of the cohort."""
        sets = [set(s.videos(direction=direction)) for s in self.subjects.values()]
        return sorted(set.intersection(*sets)) if sets else []

    def shared_sessions(self):
        """Main-task sessions present for every subject in the cohort."""
        sets = [set(s.sessions()) for s in self.subjects.values()]
        return sorted(set.intersection(*sets)) if sets else []

    # ------------------------------------------------------------------
    # broadcast getters — each returns {sub: per-subject result}
    # ------------------------------------------------------------------
    def get_brain_masks(self):
        """``{sub: brain_mask}`` for every subject."""
        return {sub: s.get_brain_mask() for sub, s in self.subjects.items()}

    def get_roi_masks(self, query, **kwargs):
        """``{sub: roi_mask}`` for one ROI query (passes ``**kwargs`` through)."""
        return {
            sub: s.get_roi_mask(query, **kwargs)
            for sub, s in self.subjects.items()
        }

    def get_betas(self, ses, roi=None, mask=None, nc_threshold=None,
                  nc_direction="fw"):
        """``{sub: (n_trials, n_voxels)}`` session betas across the cohort.

        Trial counts are the same per session across subjects; voxel counts
        differ (each subject has its own brain mask / ROI overlap).
        """
        return {
            sub: s.get_betas(ses, roi=roi, mask=mask,
                             nc_threshold=nc_threshold, nc_direction=nc_direction)
            for sub, s in self.subjects.items()
        }

    def get_video_betas(self, video, direction="fw", roi=None, mask=None,
                        average_repeats=True):
        """``{sub: betas}`` per-video betas across the cohort.

        Shape per subject: ``(2, n_voxels)`` or ``(n_voxels,)`` if
        ``average_repeats=True``.
        """
        return {
            sub: s.get_video_betas(
                video, direction=direction, roi=roi, mask=mask,
                average_repeats=average_repeats,
            )
            for sub, s in self.subjects.items()
        }

    def get_run_betas(self, ses, run, roi=None, mask=None):
        """``{sub: (n_stim_trials, n_voxels)}`` run-composed betas per subject."""
        return {
            sub: s.get_run_betas(ses, run, roi=roi, mask=mask)
            for sub, s in self.subjects.items()
        }

    def get_noise_ceiling(self, ses, direction="fw", roi=None, mask=None):
        """``{sub: (n_voxels,)}`` per-session noise ceiling per subject."""
        return {
            sub: s.get_noise_ceiling(
                ses, direction=direction, roi=roi, mask=mask,
            )
            for sub, s in self.subjects.items()
        }
