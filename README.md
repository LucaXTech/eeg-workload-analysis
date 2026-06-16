# EEG Workload Analysis Portfolio

This repository contains a sanitized portfolio version of an EEG-based mental workload project developed during my MSc thesis and Erasmus+ research traineeship at g.tec medical engineering.

The project focused on EEG recordings acquired during N-back tasks designed to manipulate cognitive workload through working-memory load and stimulus presentation speed. The repository includes protocol documentation, N-back paradigm files, acquisition scripts, and representative material for reproducible EEG signal-processing and machine-learning workflows.

No participant data are included in this repository.

---

## Project overview

The experimental protocol included two main paradigms:

* **N-LEVELS**: manipulation of working-memory load using 1-back, 2-back and 3-back tasks.
* **N-SPEED**: manipulation of stimulus presentation speed at fixed 2-back load using slow, medium and fast conditions.

Each paradigm included separate TRAIN and TEST sessions with predefined block orders. The experimental design was used to investigate EEG markers of mental workload, including spectral features, ERP responses, classification performance, time-on-task effects and cross-paradigm generalization.

---

## Repository contents

```text
eeg-workload-analysis-portfolio/
├── acquisition/
│   ├── n_level_train.py
│   ├── n_level_test.py
│   ├── n_speed_train.py
│   └── n_speed_test.py
├── analysis_examples/
│   ├── README.md
│   ├── run_examples.md
│   ├── spectral_features_example.py
│   ├── baseline_classification_example.py
│   ├── time_on_task_example.py
│   └── cross_paradigm_transfer_example.py
├── docs/
│   ├── BCICore8_Electrode_Positions.png
│   ├── protocol_summary.md
│   └── reproducibility_notes.md
├── paradigms/
│   ├── nlevels/
│   └── nspeed/
├── requirements.txt
├── requirements_acquisition.txt
├── NOTICE.md
├── .gitignore
└── README.md

```
## Installation

The repository separates analysis dependencies from acquisition dependencies.

For the analysis examples, install:

```bash
pip install -r requirements.txt
```

This includes the main scientific Python packages used for EEG feature extraction, machine learning and visualization.

For the acquisition scripts, install:

```bash
pip install -r requirements_acquisition.txt
```

This includes `gpype` and `PySide6`, which are required for the g.Pype-based acquisition scripts and the operator control panel.

The analysis examples can run without the acquisition dependencies.

---

## EEG acquisition setup

EEG was acquired using a g.tec BCI Core-8 system with 8 EEG channels and a sampling rate of 250 Hz.

The channel configuration was:

| Channel | Electrode |
| ------- | --------- |
| 1       | Fz        |
| 2       | C3        |
| 3       | Cz        |
| 4       | C4        |
| 5       | Pz        |
| 6       | PO7       |
| 7       | POz       |
| 8       | PO8       |

Ground/reference electrodes were placed below P10 and TP10.

![BCI Core-8 electrode layout](docs/BCICore8_Electrode_Positions.png)

---

## Paradigm files

The `paradigms/` folder contains XML files used to define deterministic N-back task blocks in the g.Pype/ParadigmPresenter environment.

The XML files define:

* task condition;
* stimulus sequence;
* stimulus duration;
* target and non-target events;
* UDP markers sent during stimulus presentation.

The N-LEVELS paradigm includes 1-back, 2-back and 3-back conditions.
The N-SPEED paradigm includes slow, medium and fast 2-back conditions.

---

## Acquisition scripts

The `acquisition/` folder contains Python scripts used to configure and run the experimental sessions in g.Pype.

The scripts define:

* block order for TRAIN and TEST sessions;
* sampling rate and number of channels;
* UDP marker labels;
* participant ID handling;
* operator control panel for advancing through experimental blocks.

These scripts are provided as documentation of the experimental acquisition workflow and require the dependencies listed in `requirements_acquisition.txt`. The scripts use the g.Pype SDK and PySide6 for the operator control panel.

---

## Documentation

The `docs/` folder contains additional documentation about the experimental protocol and reproducibility principles.

### Protocol summary

The file `docs/protocol_summary.md` summarizes the experimental structure, including:

* EEG acquisition setup;
* channel configuration;
* N-LEVELS and N-SPEED paradigms;
* TRAIN and TEST block orders;
* UDP event markers;
* analysis rationale.

### Reproducibility notes

The file `docs/reproducibility_notes.md` summarizes the main validation and reproducibility principles followed in the workflow, including:

* data privacy;
* data leakage prevention;
* within-subject validation;
* leave-one-subject-out validation;
* observation-time analysis;
* time-on-task analysis;
* cross-paradigm transfer;
* limitations of the public portfolio repository.

---

## Analysis workflow

The repository includes four sanitized and self-contained analysis examples. Example commands for running the scripts are provided in `analysis_examples/run_examples.md`.

### Spectral feature extraction

The script `analysis_examples/spectral_features_example.py` demonstrates fixed-length EEG windowing and spectral feature extraction using Welch PSD estimation.

It includes:

* delta, theta, alpha and beta bandpower extraction;
* log-bandpower features;
* theta/alpha and alpha/theta ratios;
* engagement index;
* optional synthetic EEG-like data generation.

### Baseline classification

The script `analysis_examples/baseline_classification_example.py` demonstrates a leakage-aware machine-learning workflow for EEG workload classification.

It includes:

* synthetic EEG feature table generation;
* train/test holdout evaluation;
* leave-one-subject-out validation;
* Logistic Regression;
* shrinkage Linear Discriminant Analysis;
* accuracy, balanced accuracy, macro F1-score, confusion matrix and classification report.

Scaling and model fitting are handled inside scikit-learn pipelines to avoid data leakage.

### Time-on-task analysis

The script `analysis_examples/time_on_task_example.py` demonstrates temporal analysis of EEG features across task segments.

It includes:

* temporal segment handling;
* within-subject feature normalization;
* early, middle and late phase comparison;
* Spearman trend analysis;
* Kruskal-Wallis testing across temporal phases;
* simple time-course plot generation.

This module documents how EEG workload markers can be analyzed dynamically rather than only as static block-level averages.

### Cross-paradigm transfer

The script `analysis_examples/cross_paradigm_transfer_example.py` demonstrates cross-paradigm workload decoding.

It includes:

* synthetic feature generation for two related EEG workload paradigms;
* within-paradigm evaluation;
* cross-paradigm transfer evaluation;
* leakage-aware scikit-learn pipelines;
* Logistic Regression;
* shrinkage Linear Discriminant Analysis;
* accuracy, balanced accuracy, macro F1-score and confusion matrix.

This module documents how a classifier trained on one workload manipulation can be tested on another paradigm. It is useful for assessing whether EEG workload markers are task-specific or partially transferable across experimental conditions.

---

## Privacy and data availability

This repository does not include:

* raw EEG recordings;
* participant identifiers;
* questionnaire data;
* behavioral response files;
* clinical or sensitive data.

The repository is intended as a technical portfolio demonstrating experimental design, acquisition workflow documentation, and reproducible EEG analysis structure.

---

## License and notice

No open-source license is currently provided. This repository is shared as a sanitized technical portfolio for academic and research application purposes.

The acquisition scripts depend on g.Pype, which is distributed separately by g.tec medical engineering under its own license. This repository does not redistribute g.Pype.

See `NOTICE.md` for copyright, privacy and third-party dependency notes.


---

## Author

**Luca Serioli**<br>
Biomedical Engineer<br>
EEG signal processing, computational neurophysiology and biomedical data analysis
