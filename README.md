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
├── docs/
│   └── BCICore8_Electrode_Positions.png
├── paradigms/
│   ├── nlevels/
│   └── nspeed/
├── .gitignore
└── README.md
```

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

These scripts are provided as documentation of the experimental acquisition workflow and require the g.Pype SDK. g.Pype is publicly available as a Python SDK for neuroscience and BCI applications and can be installed with `pip install gpype`. Some scripts also use PySide6 for the operator control panel.

---

## Analysis workflow

The complete thesis analysis included:

* EEG preprocessing and quality control;
* event-based segmentation;
* spectral feature extraction;
* bandpower and ratio-based features;
* ERP analysis;
* behavioral and questionnaire integration;
* within-subject and leave-one-subject-out validation;
* feature-set comparison;
* time-on-task analysis;
* temporal generalization;
* cross-paradigm transfer.

Representative analysis examples will be added in a sanitized form. No raw EEG recordings, participant-level files or sensitive data will be included.

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

## Author

Luca Serioli
Biomedical Engineer
EEG signal processing, computational neurophysiology and biomedical data analysis
