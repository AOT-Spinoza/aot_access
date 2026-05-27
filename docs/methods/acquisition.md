# MRI acquisition

```{admonition} Authoring TODO
:class: note
Lab-authored. Suggested sections below.
```

## Scanner & protocol

- Scanner make/model + field strength (7 T).
- Head coil; B0 shim approach.
- Software / pulse-sequence version.

## Functional acquisition

- Sequence (e.g. multi-band GE-EPI), TR, TE, MB factor, in-plane / through-plane
  acceleration, partial Fourier, flip angle, FoV, matrix, voxel size for both
  `res-1p25mm` and `res-2p0mm`.
- Slice prescription / coverage.
- Phase-encoding direction (`dir-`).
- NORDIC denoising at the scanner / offline (`rec-nordicstc`).
- Volumes per run, dummy scans.

## Anatomical acquisition

- T1w sequence (e.g. MP2RAGE) — TR, TI₁, TI₂, flip angles, voxel size.
- T2w sequence.
- AOT-anatomy session (`ses-AOTanat`) vs 3T-anatomy session (`ses-3Tanat`).

## Field maps

- Approach (PA/AP pair, etc.), schedule per session.

## Behavioural / eye tracking

- Response device.
- Eye-tracker make / sampling rate / calibration protocol.
- Synchronisation with the scanner (pulse logging).

## Stimulus delivery

- Display setup, viewing distance, refresh rate, gamma calibration.
- Software stack.

## Session structure

- Number of sessions per subject (10 AOT + localizers).
- Runs / session, run length.
- Inter-stimulus interval; blank distribution (12 blanks / 84 events / run).
