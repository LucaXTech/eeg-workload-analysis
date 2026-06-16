from pathlib import Path
import os
from datetime import datetime

import gpype as gp
from PySide6.QtWidgets import QInputDialog
from gpype.frontend.widgets.base.widget import Widget  # wrapper for custom widgets

# ---- Paths & parameters ----
parent_dir = os.path.dirname(os.path.abspath(__file__))
paradigms_dir = os.path.join(parent_dir, "paradigms")

# Block order for N-SPEED TEST
block_files = [
    "2-Back_slow_test.xml",
    "2-Back_fast_test.xml",
    "2-Back_medium_test.xml",
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


def normalize_subject_id(text: str) -> str:
    """
    Normalize subject ID to the SXX format if possible.

    Examples:
    - "s1"   -> "S01"
    - "1"    -> "S01"
    - "S12"  -> "S12"
    """
    text = (text or "").strip().upper()
    if text.startswith("S") and len(text) == 3 and text[1:].isdigit():
        return text
    # Try to force SXX format if they type only the number
    if text.isdigit() and len(text) <= 2:
        return f"S{int(text):02d}"
    return text  # fallback, keep as-is and just warn later


# =============== CONTROL PANEL (gpype Widget) ===============
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ControlPanelWidget(Widget):
    """
    Operator control panel:
    - displays short instructions
    - provides a 'Start next block' button to run the subsequent N-back blocks.
    """

    def __init__(self, presenter: gp.ParadigmPresenter, block_files: list[str]):
        Widget.__init__(
            self,
            widget=QWidget(),
            name="Control panel",
            layout=QVBoxLayout,
        )

        from PySide6.QtWidgets import QLabel, QPushButton  # local import for clarity

        self.presenter = presenter
        self.block_files = block_files
        # next block index in the list (we start from 1, as the first one is auto-selected)
        self.next_block_idx = 1

        label = QLabel(
            "1) Press 'Start Paradigm' in the Presenter.\n"
            "2) When the block ends, press 'Stop' and have the participant complete the NASA-TLX.\n"
            "3) After they finish, press 'Start next block' here.\n"
            "4) Repeat until all blocks are completed.\n"
        )
        label.setWordWrap(True)

        btn = QPushButton("Start next block")
        btn.clicked.connect(self.start_next_block)
        self.button = btn  # keep a reference so we can disable it

        self._layout.addWidget(label)
        self._layout.addWidget(btn)

    def start_next_block(self):
        """Select the next XML in the list and start the paradigm."""
        print(f"[INFO] Operator pressed: Start next block (idx = {self.next_block_idx})")

        if self.next_block_idx >= len(self.block_files):
            print("[INFO] No further blocks are available.")
            # Extra safety: disable the button if somehow still enabled
            if hasattr(self, "button"):
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
            print("[WARN] Presenter without dropdown: cannot auto-select the block.")

        # Start the selected paradigm
        try:
            self.presenter._start_paradigm()
        except AttributeError:
            # Fallback if presenter API differs
            self.presenter.paradigm_presenter.start_paradigm()

        # Move to the next block index
        self.next_block_idx += 1

        # If we just started the last block, disable the button
        if self.next_block_idx >= len(self.block_files):
            print("[INFO] Last block started. Disabling button.")
            if hasattr(self, "button"):
                self.button.setEnabled(False)


if __name__ == "__main__":

    # Main application & pipeline
    app = gp.MainApp()
    p = gp.Pipeline()

    # ==== Source: BCI Core-8 (or Generator as fallback) ====
    # Example generator (for testing without hardware):
    # amp = gp.Generator(
    #     sampling_rate=sampling_rate,
    #     channel_count=channel_count,
    #     signal_frequency=10,
    #     signal_amplitude=15,
    #     signal_shape="sine",
    #     noise_amplitude=10,
    # )

    # BCI Core-8
    amp = gp.BCICore8()

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

    # Marker for keyboard (key "M" = ASCII 77) on an extra channel
    mk_list.append(
        mk(color="magenta", label="M Key", channel=channel_count + 1, value=77)
    )

    # Time series scope
    scope = gp.TimeSeriesScope(
        amplitude_limit=50,
        time_window=10,
        markers=mk_list,
    )

    # Routers to merge flows
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
        "Enter subject ID (e.g. S01):"
    )
    if not ok:
        raise SystemExit("[ABORT] No subject ID provided. Exiting.")

    subject_id = normalize_subject_id(subject_text)
    if not (len(subject_id) == 3 and subject_id.startswith("S") and subject_id[1:].isdigit()):
        print(f"[WARN] Subject ID not in the required SXX format: '{subject_id}'. Proceeding anyway.")

    # Base directory = folder where this script is located
    script_dir = Path(__file__).resolve().parent

    # Dataset root inside the script directory
    base_root = script_dir / "dataset"

    # Required structure: dataset/SXX/N-SPEED/TEST
    save_dir = base_root / subject_id / "N-SPEED" / "TEST"
    save_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped filename to avoid overwriting
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"{subject_id}_NSpeed_Test_{ts}.csv"
    save_path = save_dir / csv_name

    print("[INFO] Output CSV will be saved as:")
    print(save_path)
    print("[INFO] Recording path:")
    print(save_path)

    # File writer (raw stream: EEG + triggers + keyboard)
    writer = gp.FileWriter(file_name=str(save_path))

    # === Connections ===
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

    # Automatically select the first block (e.g. slow) in the dropdown
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
        print("[WARN] Presenter without dropdown: cannot auto-select first block.")

    # === Operator control panel ===
    control_panel = ControlPanelWidget(presenter=presenter, block_files=block_files)

    # === Add widgets to the main app ===
    app.add_widget(presenter)
    app.add_widget(scope)
    app.add_widget(control_panel)

    # Start pipeline + UI
    p.start()
    app.run()
    p.stop()

    print("[INFO] Pipeline finished. Exiting.")
