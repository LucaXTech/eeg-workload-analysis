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

### `time_on_task_example.py`

Self-contained example for time-on-task and temporal drift analysis.

Main components:

* temporal segment handling;
* within-subject feature normalization;
* early, middle and late phase comparison;
* Spearman trend analysis across task segments;
* Kruskal-Wallis testing across temporal phases;
* simple time-course plot generation;
* optional synthetic feature data generation.

The script demonstrates how EEG features can be analyzed dynamically rather than only as static block-level averages. This is useful for studying temporal changes related to workload, fatigue, arousal and task duration.

---

### `cross_paradigm_transfer_example.py`

Self-contained example for cross-paradigm workload decoding.

Main components:

* synthetic feature generation for two related EEG workload paradigms;
* within-paradigm evaluation;
* cross-paradigm transfer evaluation;
* leakage-aware scikit-learn pipelines;
* Logistic Regression;
* shrinkage Linear Discriminant Analysis;
* accuracy, balanced accuracy, macro F1-score and confusion matrix.

The script demonstrates how a classifier trained on one workload manipulation can be tested on another paradigm. This is useful for assessing whether EEG workload markers are task-specific or partially transferable across experimental conditions.

---

## Planned additional modules

Additional sanitized examples may include:

* observation-time analysis;
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
