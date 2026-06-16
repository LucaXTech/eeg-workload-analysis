from pathlib import Path
import os
from datetime import datetime

import gpype as gp
from PySide6.QtWidgets import QInputDialog
from gpype.frontend.widgets.base.widget import Widget  # wrapper for custom widget

# ---- Paths & parameters ----
parent_dir = os.path.dirname(os.path.abspath(__file__))
paradigms_dir = os.path.join(parent_dir, "paradigms")

# List of blocks in execution order
#  - first block is automatically selected in the Presenter
#  - the others are started via the control panel button
block_files = [
    "1-Back_train.xml",
    "3-Back_train.xml",
    "2-Back_train.xml",
]

sampling_rate = 250
channel_count = 8

# UDP markers (stimuli)
markers_udp = [
    (11, "1-Back Target",     "#00ff00"),
    (12, "1-Back NonTarget",  "#009900"),
    (21, "2-Back Target",     "#ff0000"),
    (22, "2-Back NonTarget",  "#990000"),
    (31, "3-Back Target",     "#0000ff"),
    (32, "3-Back NonTarget",  "#000099"),
]

# If you add extra markers in your XML files (e.g., block start/end),
# you can extend the list here, for example:
# markers_udp.extend([
#     (90, "start", "#444444"),
#     (91, "end 1", "#888888"),
#     (92, "end 2", "#aaaaaa"),
#     (93, "end 3", "#cccccc"),
# ])


def normalize_subject_id(text: str) -> str:
    """
    Normalize the subject ID to the format SXX if possible.
    Examples:
      - "s1"   -> "S01"
      - "01"   -> "S01"
      - "S12"  -> "S12"
    """
    text = (text or "").strip().upper()
    if text.startswith("S") and len(text) == 3 and text[1:].isdigit():
        return text
    # Try to force SXX if they only write the number
    if text.isdigit() and len(text) <= 2:
        return f"S{int(text):02d}"
    return text  # Fallback (we just warn later)


# =============== CONTROL PANEL as gpype Widget ===============
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ControlPanelWidget(Widget):
    """
    Operator control panel:
    - shows instructions
    - provides a 'Start next block' button to start the next paradigm block
      according to the predefined order in block_files.
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
        # Next block index:
        #   0 is already handled by the Presenter auto-selection,
        #   so we start from 1 (second element in block_files).
        self.next_block_idx = 1

        label = QLabel(
            "1) Press 'Start paradigm' in the Presenter for the first block.\n"
            "2) When the block ends, press 'Stop' and let the participant complete the NASA-TLX.\n"
            "3) After they finish, press 'Start next block' here.\n"
            "4) Repeat until all blocks are completed.\n"
        )
        label.setWordWrap(True)

        btn = QPushButton("Start next block")
        btn.clicked.connect(self.start_next_block)
        self.button = btn  # keep a reference to enable/disable

        self._layout.addWidget(label)
        self._layout.addWidget(btn)

    def start_next_block(self):
        """Select the next XML in the list and start the paradigm."""
        print(f"[INFO] Operator pressed: Start next block (idx = {self.next_block_idx})")

        if self.next_block_idx >= len(self.block_files):
            print("[INFO] No further blocks are available.")
            if hasattr(self, "button") and self.button is not None:
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
            print("[WARN] Presenter has no dropdown: cannot auto-select the block.")

        # Start the selected paradigm
        try:
            self.presenter._start_paradigm()
        except AttributeError:
            # Fallback for older Presenter implementations
            self.presenter.paradigm_presenter.start_paradigm()

        # Move to the next block index for the next button press
        self.next_block_idx += 1

        # If this was the last available block, disable the button
        if self.next_block_idx >= len(self.block_files):
            print("[INFO] Last block started. Disabling button.")
            if hasattr(self, "button") and self.button is not None:
                self.button.setEnabled(False)


if __name__ == "__main__":

    # Create main application & pipeline
    app = gp.MainApp()
    p = gp.Pipeline()

    # ==== Source: BCI Core-8 (or generator for testing) ====
    # For offline testing, you can use the generator:
    amp = gp.Generator(
        sampling_rate=sampling_rate,
        channel_count=channel_count,
        signal_frequency=10,
        signal_amplitude=15,
        signal_shape="sine",
        noise_amplitude=10,
    )

    # BCI Core-8 amplifier
    # amp = gp.BCICore8()

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

    # Keyboard marker (key "M" = ASCII 77) on an extra "channel"
    mk_list.append(
        mk(color="magenta", label="M Key", channel=channel_count + 1, value=77)
    )

    # Time series scope
    scope = gp.TimeSeriesScope(
        amplitude_limit=50,
        time_window=10,
        markers=mk_list,
    )

    # ROUTERs to merge streams
    router_scope = gp.Router(
        input_selector=[gp.Router.ALL, gp.Router.ALL, gp.Router.ALL]
    )
    router_raw = gp.Router(
        input_selector=[gp.Router.ALL, gp.Router.ALL, gp.Router.ALL]
    )

    # === Subject ID prompt and output path construction ===
    subject_text, ok = QInputDialog.getText(
        None,
        "Subject ID",
        "Enter subject ID (e.g. S01):",
    )
    if not ok:
        raise SystemExit("[ABORT] No subject ID provided. Exiting.")

    subject_id = normalize_subject_id(subject_text)
    if not (len(subject_id) == 3 and subject_id.startswith("S") and subject_id[1:].isdigit()):
        print(f"[WARN] Subject ID not in the required format SXX: '{subject_id}'. Proceeding anyway.")

    # Dataset root: local folder "dataset" next to this script
    base_root = Path(parent_dir) / "dataset"

    # Final structure: dataset/SXX/N-LEVELS/TRAIN
    save_dir = base_root / subject_id / "N-LEVELS" / "TRAIN"
    save_dir.mkdir(parents=True, exist_ok=True)

    # File name with timestamp to avoid overwrite
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"{subject_id}_NLevels_Train_{ts}.csv"
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

    # Merge data for scope (filtered EEG + triggers + keyboard)
    p.connect(notch50,       router_scope["in1"])
    p.connect(trig_receiver, router_scope["in2"])
    p.connect(key_capture,   router_scope["in3"])
    p.connect(router_scope,  scope)

    # Merge data for file writer (raw EEG + triggers + keyboard)
    p.connect(amp,           router_raw["in1"])
    p.connect(trig_receiver, router_raw["in2"])
    p.connect(key_capture,   router_raw["in3"])
    p.connect(router_raw,    writer)

    # === ParadigmPresenter with paradigms folder ===
    presenter = gp.ParadigmPresenter(paradigms_dir)

    # Automatically select the first block in the dropdown
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

    # === Add widgets to the main app ===
    app.add_widget(presenter)
    app.add_widget(scope)
    app.add_widget(control_panel)

    # Start pipeline and GUI
    p.start()
    app.run()
    p.stop()

    print("[INFO] Pipeline finished. Exiting.")
