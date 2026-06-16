# Analysis Examples

This folder contains sanitized and representative analysis scripts adapted from the original MSc thesis workflow on EEG-based mental workload decoding.

The goal is not to reproduce the full private analysis environment, but to document the main computational steps in a clean, reusable and privacy-preserving way.

No raw EEG recordings, participant-level files, questionnaire data or thesis output folders are included.

---

## Available scripts

### `spectral_features_example.py`

Self-contained example for spectral EEG feature extraction.

Main components:

* fixed-length EEG windowing;
* Welch PSD estimation;
* delta, theta, alpha and beta bandpower extraction;
* log-bandpower features;
* theta/alpha ratio;
* alpha/theta ratio;
* engagement index;
* optional synthetic EEG-like data generation.

The script can run without real participant data by generating synthetic EEG-like signals.

---

### `baseline_classification_example.py`

Self-contained example for baseline EEG workload classification.

Main components:

* synthetic EEG feature table generation;
* leakage-aware machine-learning pipelines;
* train/test holdout evaluation;
* leave-one-subject-out validation;
* Logistic Regression;
* shrinkage Linear Discriminant Analysis;
* accuracy, balanced accuracy, macro F1-score, confusion matrix and classification report.

The script demonstrates how scaling and model fitting should be kept inside the training pipeline to avoid data leakage.

---

## Planned additional modules

Additional sanitized examples may include:

* time-on-task analysis;
* observation-time analysis;
* cross-paradigm transfer;
* ERP feature extraction and classification;
* behavioral and questionnaire integration.

Each script will be cleaned before publication by removing:

* local Windows paths;
* subject-specific output folders;
* private data references;
* unnecessary thesis-specific comments;
* duplicated or obsolete code sections.

---

## Data availability

The scripts are intended as portfolio examples.

To run them with real data, users must provide their own EEG data following the expected structure. This repository does not provide participant recordings.
