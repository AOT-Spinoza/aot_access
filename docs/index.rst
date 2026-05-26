AOTaccess
=========

A read-only Python API for the AOT ("Arrow of Time") 7T fMRI dataset.
``AOTaccess`` resolves filesystem paths, applies BIDS-style filename
conventions, and exposes a single per-subject entry point —
:class:`~AOTaccess.subject.AOTSubject` — that returns betas, ROI masks,
brain coordinates, and round-trips back to NIfTI.

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: 🚀 Quickstart
      :link: getting_started/quickstart
      :link-type: doc

      One subject, one ROI, one ``get_betas`` call.

   .. grid-item-card:: 🧠 Subject API
      :link: user_guide/subject_api
      :link-type: doc

      The :class:`~AOTaccess.subject.AOTSubject` walkthrough.

   .. grid-item-card:: 🗺️ ROIs & groupings
      :link: user_guide/rois_and_groupings
      :link-type: doc

      Manifest-driven ROI access; per-atlas groupings.

   .. grid-item-card:: 📚 Examples gallery
      :link: auto_examples/index
      :link-type: doc

      Runnable scripts with output and figures.

.. toctree::
   :hidden:
   :caption: Getting started
   :maxdepth: 2

   getting_started/install
   getting_started/quickstart
   getting_started/dataset_at_a_glance

.. toctree::
   :hidden:
   :caption: User guide
   :maxdepth: 2

   user_guide/discovery
   user_guide/subject_api
   user_guide/brain_mask_and_flat_voxels
   user_guide/rois_and_groupings
   user_guide/localizers
   user_guide/config_and_paths
   user_guide/error_handling
   user_guide/naming_conventions

.. toctree::
   :hidden:
   :caption: Examples

   auto_examples/index

.. toctree::
   :hidden:
   :caption: Methods
   :maxdepth: 2

   methods/acquisition
   methods/preprocessing
   methods/glmsingle
   methods/rois
   methods/localizers

.. toctree::
   :hidden:
   :caption: Reference
   :maxdepth: 2

   api/index
   reference/folder_structure
   reference/manifest_schemas
   reference/faq
   reference/changelog
   reference/contributing
