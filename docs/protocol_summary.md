# Protocol Summary

This document summarizes the experimental protocol used for the EEG-based mental workload project.

The protocol was developed to investigate changes in EEG activity during N-back tasks under different cognitive workload conditions. Two complementary paradigms were used:

* **N-LEVELS**, manipulating working-memory load.
* **N-SPEED**, manipulating stimulus presentation speed while keeping working-memory load fixed.

No participant data are included in this repository.

---

## Experimental setup

EEG data were acquired using a g.tec BCI Core-8 system with 8 EEG channels and a sampling rate of 250 Hz.

The experiment was implemented using the g.Pype framework and ParadigmPresenter. Stimuli were presented as single letters, and event markers were sent through UDP during stimulus presentation.

The acquisition scripts were designed to support:

* predefined block orders;
* TRAIN and TEST session separation;
* UDP event marker labeling;
* participant ID handling;
* operator-controlled block progression;
* post-block questionnaire completion.

---

## EEG channel configuration

The EEG montage included the following channels:

| Channel | Electrode |
| ------- | --------- |
| Ch01    | Fz        |
| Ch02    | C3        |
| Ch03    | Cz        |
| Ch04    | C4        |
| Ch05    | Pz        |
| Ch06    | PO7       |
| Ch07    | POz       |
| Ch08    | PO8       |

The reference/ground electrodes were placed over the right mastoid region (P10/TP10).

In the exported CSV files, `Ch01`–`Ch08` correspond to EEG channels. Additional columns such as `Ch09` and `Ch10` may be used for experimental markers and should not be treated as EEG channels.

---

## N-LEVELS paradigm

The N-LEVELS paradigm manipulated working-memory load by varying the N-back level.

Conditions:

* 1-back
* 2-back
* 3-back

Each condition was presented as a separate block.

### TRAIN block order

1. 1-back
2. 3-back
3. 2-back

### TEST block order

1. 2-back
2. 1-back
3. 3-back

### Event markers

| Condition | Event type | UDP marker |
| --------- | ---------- | ---------- |
| 1-back    | Target     | 11         |
| 1-back    | Non-target | 12         |
| 2-back    | Target     | 21         |
| 2-back    | Non-target | 22         |
| 3-back    | Target     | 31         |
| 3-back    | Non-target | 32         |

---

## N-SPEED paradigm

The N-SPEED paradigm manipulated stimulus presentation speed while keeping the task fixed at 2-back.

Conditions:

* slow
* medium
* fast

Each condition was presented as a separate block.

### TRAIN block order

1. fast
2. slow
3. medium

### TEST block order

1. slow
2. fast
3. medium

### Event markers

| Condition | Event type | UDP marker |
| --------- | ---------- | ---------- |
| slow      | Target     | 41         |
| slow      | Non-target | 42         |
| medium    | Target     | 51         |
| medium    | Non-target | 52         |
| fast      | Target     | 61         |
| fast      | Non-target | 62         |

---

## Block handling

Each block included a pre-block period followed by the N-back stimulus sequence. After each block, the participant completed a simplified NASA-TLX questionnaire before the next block was started.

The acquisition scripts included a custom operator control panel to advance through the predefined block sequence. This allowed the operator to start the first block from ParadigmPresenter and then move through the remaining blocks in a controlled order.

---

## Analysis rationale

The protocol was designed to support several levels of analysis:

* spectral EEG feature extraction;
* ERP analysis based on target and non-target events;
* within-subject TRAIN-to-TEST validation;
* leave-one-subject-out validation;
* observation-time analysis;
* time-on-task and temporal drift analysis;
* cross-paradigm transfer between N-LEVELS and N-SPEED.

The separation between TRAIN and TEST sessions was used to support more realistic validation of EEG-based workload decoding and to reduce the risk of overly optimistic performance estimates.

---

## Privacy note

This repository contains only protocol and code documentation. It does not include raw EEG recordings, behavioral responses, questionnaire results, participant identifiers or sensitive data.
