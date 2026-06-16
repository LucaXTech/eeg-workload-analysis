# Analysis Examples

This folder will contain sanitized and representative analysis scripts adapted from the original MSc thesis workflow.

The goal is not to reproduce the full private analysis environment, but to document the main computational steps used for EEG-based mental workload analysis in a clean and reusable way.

No raw EEG recordings, participant-level files, questionnaire data or thesis output folders are included.

---

## Planned analysis modules

The analysis examples will cover the main components of the original workflow:

* EEG preprocessing and quality control;
* spectral feature extraction;
* baseline workload classification;
* observation-time analysis;
* time-on-task analysis;
* cross-paradigm transfer;
* ERP analysis.

Each script will be cleaned before publication by removing:

* local Windows paths;
* subject-specific output folders;
* private data references;
* unnecessary thesis-specific comments;
* duplicated or obsolete code sections.

---

## Data availability

The scripts are intended as portfolio examples.

To run them, users must provide their own EEG data following the expected structure, or use synthetic/demo data that may be added in the future.

This repository does not provide participant recordings.
