from pathlib import Path
import os
from datetime import datetime

import gpype as gp
from PySide6.QtWidgets import QInputDialog, QWidget, QVBoxLayout

from gpype.frontend.widgets.base.widget import Widget  # wrapper for custom widgets


# ---- Paths & parameters ----
parent_dir = os.path.dirname(os.path.abspath(__file__))
paradigms_dir = os.path.join(parent_dir, "paradigms")

# Block list in execution order
block_files = [
    "2-Back_test.xml",
    "1-Back_test.xml",
    "3-Back_test.xml",
]

sampling_rate = 250
channel_count = 8

# UDP markers (stimuli)
markers_udp = [
    (11, "1-Back Target",    "#00ff00"),
    (12, "1-Back NonTarget", "#009900"),
    (21, "2-Back Target",    "#ff0000"),
    (22, "2-Back NonTarget", "#990000"),
    (31, "3-Back Target",    "#0000ff"),
    (32, "3-Back NonTarget", "#000099"),
]

# If needed, you can add extra markers (e.g., block start/end) here:
# markers_udp.extend([
#     (90, "block start", "#444444"),
#     (91, "block end 1", "#888888"),
#     (92, "block end 2", "#aaaaaa"),
#     (93, "block end 3", "#cccccc"),
# ])


def normalize_subject_id(text: str) -> str:
    """Normalize user input to format SXX when possible."""
    text = (text or "").strip().upper()
    if text.startswith("S") and len(text) == 3 and text[1:].isdigit():
        return text
    # Try to enforce SXX if they only type the number
    if text.isdigit() and len(text) <= 2:
        return f"S{int(text):02d}"
    return text  # fallback (we warn later but do not block)


# =============== Control Panel Widget ===============
class ControlPanelWidget(Widget):
    """
    Operator control panel:
    - shows instructions
    - provides a 'Start next block' button to start the next N-back block
      according to the order defined in `block_files`.
    """

    def __init__(self, presenter: gp.ParadigmPresenter, block_files: list[str]):
        from PySide6.QtWidgets import QLabel, QPushButton  # local import for clarity

        super().__init__(
            widget=QWidget(),
            name="Control panel",
            layout=QVBoxLayout,
        )

        self.presenter = presenter
        self.block_files = block_files

        # Next block index to start (0 is auto-selected at startup)
        self.next_block_idx = 1

        label = QLabel(
            "1) Press 'Start Paradigm' in the Paradigm Presenter.\n"
            "2) When the block ends, press 'Stop' and let the participant fill in the NASA-TLX.\n"
            "3) After they finish, press 'Start next block' here.\n"
            "4) Repeat until all blocks are completed.\n"
        )
        label.setWordWrap(True)

        self.button = QPushButton("Start next block")
        self.button.clicked.connect(self.start_next_block)

        self._layout.addWidget(label)
        self._layout.addWidget(self.button)

    def start_next_block(self):
        """Select the next XML in the list and start the corresponding block."""
        print(f"[INFO] Operator pressed: Start next block (idx = {self.next_block_idx})")

        if self.next_block_idx >= len(self.block_files):
            print("[INFO] No further blocks are available.")
            self.button.setEnabled(False)
            return

        target_file = self.block_files[self.next_block_idx]
        print(f"[INFO] Attempting to select: {target_file}")

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
            print("[WARN] Presenter has no dropdown: cannot auto-select block.")

        # Start the selected paradigm
        try:
            self.presenter._start_paradigm()
        except AttributeError:
            # Fallback for older API
            self.presenter.paradigm_presenter.start_paradigm()

        # Move to the next block for the next button press
        self.next_block_idx += 1

        # If we just started the last block, disable the button
        if self.next_block_idx >= len(self.block_files):
            print("[INFO] Last block started. Disabling button.")
            self.button.setEnabled(False)


if __name__ == "__main__":

    # Create main application & pipeline
    app = gp.MainApp()
    p = gp.Pipeline()

    # ==== Source: BCI Core-8 (real EEG) ====
    # If needed, you can switch to the Generator for testing:
    #
    # amp = gp.Generator(
    #     sampling_rate=sampling_rate,
    #     channel_count=channel_count,
    #     signal_frequency=10,
    #     signal_amplitude=15,
    #     signal_shape="sine",
    #     noise_amplitude=10,
    # )

    amp = gp.BCICore8()

    # Filters
    bandpass = gp.Bandpass(f_lo=1, f_hi=30)
    notch50 = gp.Bandstop(f_lo=48, f_hi=52)

    # UDP trigger receiver (from ParadigmPresenter)
    trig_receiver = gp.UDPReceiver(port=1000)

    # Keyboard input capture
    key_capture = gp.Keyboard()

    # Time series scope markers
    mk = gp.TimeSeriesScope.Markers
    mk_list = [
        mk(color=color, label=label, channel=channel_count, value=value)
        for value, label, color in markers_udp
    ]

    # Keyboard marker ("M" key = ASCII 77)
    mk_list.append(
        mk(color="magenta", label="M Key", channel=channel_count + 1, value=77)
    )

    # Time series scope
    scope = gp.TimeSeriesScope(
        amplitude_limit=50,
        time_window=10,
        markers=mk_list,
    )

    # Routers to merge data streams
    router_scope = gp.Router(
        input_selector=[gp.Router.ALL, gp.Router.ALL, gp.Router.ALL]
    )
    router_raw = gp.Router(
        input_selector=[gp.Router.ALL, gp.Router.ALL, gp.Router.ALL]
    )

    # === Subject ID prompt and output path ===
    subject_text, ok = QInputDialog.getText(
        None,
        "Subject ID",
        "Enter subject ID (e.g. S01):"
    )
    if not ok:
        raise SystemExit("[ABORT] No subject ID provided. Exiting.")

    subject_id = normalize_subject_id(subject_text)
    if not (len(subject_id) == 3 and subject_id.startswith("S") and subject_id[1:].isdigit()):
        print(f"[WARN] Subject ID not in the required SXX format: '{subject_id}'. Proceeding anyway.")

    # Dataset root next to this script
    base_root = Path(parent_dir) / "dataset"

    # Folder structure: dataset/SXX/N-LEVELS/TEST
    save_dir = base_root / subject_id / "N-LEVELS" / "TEST"
    save_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped file name to avoid overwriting
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"{subject_id}_NLevels_Test_{ts}.csv"
    save_path = save_dir / csv_name

    print("[INFO] Output CSV will be saved as:")
    print(save_path)
    print("[INFO] Recording path:")
    print(save_path)

    # File writer
    writer = gp.FileWriter(file_name=str(save_path))

    # === Connections ===
    p.connect(amp, bandpass)
    p.connect(bandpass, notch50)

    # Merge data for visualization scope
    p.connect(notch50,       router_scope["in1"])
    p.connect(trig_receiver, router_scope["in2"])
    p.connect(key_capture,   router_scope["in3"])
    p.connect(router_scope,  scope)

    # Merge raw data for file writer
    p.connect(amp,           router_raw["in1"])
    p.connect(trig_receiver, router_raw["in2"])
    p.connect(key_capture,   router_raw["in3"])
    p.connect(router_raw,    writer)

    # === ParadigmPresenter with paradigms folder ===
    presenter = gp.ParadigmPresenter(paradigms_dir)

    # Auto-select the first block (2-Back_test.xml) in the dropdown
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
            print(f"[INFO] Automatically selected {first_file} in Paradigm Presenter.")
        else:
            print(f"[WARN] {first_file} not found in Presenter dropdown.")
    else:
        print("[WARN] Presenter has no dropdown: cannot auto-select first block.")

    # === Operator control panel ===
    control_panel = ControlPanelWidget(presenter=presenter, block_files=block_files)

    # === Add widgets to main app ===
    app.add_widget(presenter)
    app.add_widget(scope)
    app.add_widget(control_panel)

    p.start()
    app.run()
    p.stop()

    print("[INFO] Pipeline finished. Exiting.")
