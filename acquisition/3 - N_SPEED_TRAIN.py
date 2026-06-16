from pathlib import Path
import os
from datetime import datetime

import gpype as gp
from PySide6.QtWidgets import QInputDialog, QWidget, QVBoxLayout
from gpype.frontend.widgets.base.widget import Widget  # wrapper for custom widgets

# ---- Paths & parameters ----
parent_dir = os.path.dirname(os.path.abspath(__file__))
paradigms_dir = os.path.join(parent_dir, "paradigms")

# List of paradigm XML files in the desired order
block_files = [
    "2-Back_fast_train.xml",
    "2-Back_slow_train.xml",
    "2-Back_medium_train.xml",
]

sampling_rate = 250
channel_count = 8

# UDP markers (stimuli)
markers_udp = [
    (41, "slow Target",      "#00ff00"),
    (42, "slow NonTarget",   "#009900"),
    (51, "medium Target",    "#ff0000"),
    (52, "medium NonTarget", "#990000"),
    (61, "fast Target",      "#0000ff"),
    (62, "fast NonTarget",   "#000099"),
]

# If you add block-start/end markers to your XML paradigms,
# you can extend the list here, e.g.:
# markers_udp.extend([
#     (90, "block start", "#444444"),
#     (91, "block end 1", "#888888"),
#     (92, "block end 2", "#aaaaaa"),
#     (93, "block end 3", "#cccccc"),
# ])


def normalize_subject_id(text: str) -> str:
    """
    Normalize the subject ID to the format SXX when possible.

    Examples:
        "s01"  -> "S01"
        "1"    -> "S01"
        "12"   -> "S12"
    """
    text = (text or "").strip().upper()

    # Already in the desired format SXX
    if text.startswith("S") and len(text) == 3 and text[1:].isdigit():
        return text

    # If only a number (e.g. "1" or "12"), convert to SXX
    if text.isdigit() and len(text) <= 2:
        return f"S{int(text):02d}"

    # Fallback: return as is (we will just warn later)
    return text


# =============== CONTROL PANEL as gpype Widget ===============
class ControlPanelWidget(Widget):
    """
    Operator panel:
    - shows instructions for the operator
    - provides a "Start next block" button to start the next paradigm block
      according to the order defined in `block_files`.
    """

    def __init__(self, presenter: gp.ParadigmPresenter, block_files: list[str]):
        super().__init__(
            widget=QWidget(),
            name="Control panel",
            layout=QVBoxLayout,
        )

        from PySide6.QtWidgets import QLabel, QPushButton  # local import for clarity

        self.presenter = presenter
        self.block_files = block_files

        # Index of the next block in self.block_files to be started
        self.next_block_idx = 1  # index 0 is assumed to be started first via the Presenter

        label = QLabel(
            "1) Press 'Start paradigm' in the Presenter for the first block.\n"
            "2) When a block ends, press 'Stop' and let the participant complete the NASA-TLX.\n"
            "3) After they finish, press 'Start next block' here.\n"
            "4) Repeat until all blocks are completed.\n"
        )
        label.setWordWrap(True)

        self.btn = QPushButton("Start next block")
        self.btn.clicked.connect(self.start_next_block)

        self._layout.addWidget(label)
        self._layout.addWidget(self.btn)


    def start_next_block(self):
        """Start the next block and disable the button once all blocks are used."""
        print(f"[INFO] Operator pressed: Start next block (idx = {self.next_block_idx})")

        # No more blocks available → disable button
        if self.next_block_idx >= len(self.block_files):
            print("[INFO] No further blocks available. Disabling button.")
            self.btn.setEnabled(False)
            return

        target_file = self.block_files[self.next_block_idx]
        print(f"[INFO] Attempting to select: {target_file}")

        # Auto-select in Presenter dropdown if available
        if hasattr(self.presenter, "dropdown") and self.presenter.dropdown is not None:
            idx = -1
            for i in range(self.presenter.dropdown.count()):
                text = self.presenter.dropdown.itemText(i)
                if target_file in text:
                    idx = i
                    break
            if idx != -1:
                self.presenter.dropdown.setCurrentIndex(idx)
                print(f"[INFO] Selected {target_file} in Presenter dropdown.")
            else:
                print(f"[WARN] {target_file} not found in Presenter dropdown.")
        else:
            print("[WARN] Presenter has no dropdown; cannot auto-select the next block.")

        # Start paradigm
        try:
            self.presenter._start_paradigm()
        except AttributeError:
            self.presenter.paradigm_presenter.start_paradigm()

        # Increment block counter
        self.next_block_idx += 1

        # If after incrementing there are no more blocks, disable the button
        if self.next_block_idx >= len(self.block_files):
            print("[INFO] Last block started. Disabling button.")
            self.btn.setEnabled(False)



if __name__ == "__main__":

    # Create main application and pipeline
    app = gp.MainApp()
    p = gp.Pipeline()

    # ==== Source: BCI Core-8 amplifier (real EEG) ====
    # If you want to test with a synthetic generator, you can replace this with gp.Generator.
    
    amp = gp.BCICore8()
    # amp = gp.Generator(
    #     sampling_rate=sampling_rate,
    #     channel_count=channel_count,
    #     signal_frequency=10,
    #     signal_amplitude=15,
    #     signal_shape="sine",
    #     noise_amplitude=10,
    # )   

    # Filters
    bandpass = gp.Bandpass(f_lo=1, f_hi=30)
    notch50 = gp.Bandstop(f_lo=48, f_hi=52)

    # Presenter trigger receiver (UDP from ParadigmPresenter)
    trig_receiver = gp.UDPReceiver(port=1000)

    # Keyboard input capture
    key_capture = gp.Keyboard()

    # Time series scope markers
    mk = gp.TimeSeriesScope.Markers
    mk_list = [
        mk(color=color, label=label, channel=channel_count, value=value)
        for value, label, color in markers_udp
    ]

    # Marker for keyboard (key "M" = ASCII 77)
    mk_list.append(
        mk(color="magenta", label="M Key", channel=channel_count + 1, value=77)
    )

    # Time series scope
    scope = gp.TimeSeriesScope(
        amplitude_limit=50,
        time_window=10,
        markers=mk_list,
    )

    # ROUTER to merge data streams (for visualization)
    router_scope = gp.Router(
        input_selector=[gp.Router.ALL, gp.Router.ALL, gp.Router.ALL]
    )
    # ROUTER to merge data streams (for file writing)
    router_raw = gp.Router(
        input_selector=[gp.Router.ALL, gp.Router.ALL, gp.Router.ALL]
    )

    # === Subject ID dialog and save path construction ===
    subject_text, ok = QInputDialog.getText(
        None,
        "Subject ID",
        "Enter subject ID (e.g. S01):",
    )
    if not ok:
        raise SystemExit("[ABORT] No subject ID provided. Exiting.")

    subject_id = normalize_subject_id(subject_text)
    if not (len(subject_id) == 3 and subject_id.startswith("S") and subject_id[1:].isdigit()):
        print(
            f"[WARN] Subject ID is not in the SXX format: '{subject_id}'. "
            "Continuing anyway."
        )

    # Base folder = directory where this script is located
    script_dir = Path(__file__).resolve().parent

    # Dataset folder inside the script directory
    base_root = script_dir / "dataset"

    # Required structure: dataset/SXX/N-SPEED/TRAIN
    save_dir = base_root / subject_id / "N-SPEED" / "TRAIN"
    save_dir.mkdir(parents=True, exist_ok=True)


    # Filename with timestamp to avoid overwriting
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"{subject_id}_NSpeed_Train_{ts}.csv"
    save_path = save_dir / csv_name

    print(f"[INFO] Output CSV will be saved as:\n{save_path}")

    # File writer (raw data + triggers + keyboard)
    writer = gp.FileWriter(file_name=str(save_path))

    # === Connections ===
    # Main signal chain
    p.connect(amp, bandpass)
    p.connect(bandpass, notch50)

    # Merge data for scope
    p.connect(notch50,       router_scope["in1"])
    p.connect(trig_receiver, router_scope["in2"])
    p.connect(key_capture,   router_scope["in3"])
    p.connect(router_scope,  scope)

    # Merge data for file writer (raw)
    p.connect(amp,           router_raw["in1"])
    p.connect(trig_receiver, router_raw["in2"])
    p.connect(key_capture,   router_raw["in3"])
    p.connect(router_raw,    writer)

    # === ParadigmPresenter with paradigms folder ===
    presenter = gp.ParadigmPresenter(paradigms_dir)

    # Automatic selection of the first block in block_files
    if hasattr(presenter, "dropdown") and presenter.dropdown is not None:
        idx1 = -1
        first_file = block_files[0]
        for i in range(presenter.dropdown.count()):
            text = presenter.dropdown.itemText(i)
            if first_file in text:
                idx1 = i
                break

        if idx1 != -1:
            presenter.dropdown.setCurrentIndex(idx1)
            print(f"[INFO] Automatically selected {first_file} in the Presenter.")
        else:
            print(f"[WARN] {first_file} not found in the Presenter dropdown.")
    else:
        print("[WARN] Presenter has no dropdown: cannot auto-select the first block.")

    # === Control panel for the operators ===
    control_panel = ControlPanelWidget(
        presenter=presenter,
        block_files=block_files,
    )

    # === Add widgets to the main app ===
    app.add_widget(presenter)
    app.add_widget(scope)
    app.add_widget(control_panel)

    print(f"[INFO] Recording path:\n{save_path}")

    # Run pipeline and GUI
    p.start()
    app.run()
    p.stop()

    print("[INFO] Pipeline finished. Exiting.")
