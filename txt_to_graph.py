import re
import shlex
from pathlib import Path
from typing import Tuple, Dict, List, Optional

import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# GLOBAL PLOTTING SETTINGS
# ---------------------------------------------------------

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "figure.dpi": 120,
    "savefig.dpi": 300,
})


# ---------------------------------------------------------
# CONSTANTS AND REGEX
# ---------------------------------------------------------

NUMBER_PATTERN = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
STEP_REGEX = re.compile(r"Run\s*=\s*(\d+)", re.IGNORECASE)

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def extract_number(text: str) -> Optional[float]:
    """Extracts the first floating-point number from a string."""
    match = re.search(NUMBER_PATTERN, text)
    return float(match.group()) if match else None


def get_axis_unit(label: str) -> str:
    """Returns the formatted label with the corresponding unit for axes."""
    label_lower = label.lower().strip()
    
    if "freq" in label_lower:
        return "Frequency [Hz]"
    if "time" in label_lower:
        return "Time [s]"
    if label_lower.startswith("v(") or label_lower == "voltage":
        return "Voltage [V]"
    if label_lower.startswith("i(") or label_lower == "current":
        return "Current [A]"
    if "temp" in label_lower:
        return "Temperature [°C]"
    return label


def get_signal_type(label: str) -> str:
    """Classifies the signal type to group subplots."""
    label_lower = label.lower().strip()
    
    if label_lower.startswith("v(") or label_lower == "voltage":
        return "Voltage"
    if label_lower.startswith("i(") or label_lower == "current":
        return "Current"
    if "temp" in label_lower:
        return "Temperature"
    return "Other"

def parse_file_paths(input_str: str) -> List[str]:
    """
    Splits the input string into a list of paths,
    correctly handling spaces enclosed in quotes.
    """
    try:
        return shlex.split(input_str)
    except ValueError:
        # Fallback in case of unmatched or unclosed quotes
        return [input_str.strip('"').strip("'")]

# ---------------------------------------------------------
# LTSPICE FILE READER
# ---------------------------------------------------------


def read_ltspice_file(filename: Path) -> Tuple[str, List[str], Dict[int, List], bool]:
    """Reads LTspice AC, Transient, and DC files."""

    with open(filename, "r", encoding="utf-8-sig", errors="replace") as file:
        lines = file.readlines()

    # Identify the header
    header_index = next(
        (
            i for i, line in enumerate(lines)
            if re.search(r"Freq\.?|Frequency|Time", line, re.IGNORECASE)
        ),
        None
    )

    if header_index is None:
        raise ValueError("Could not identify the file header.")

    header = lines[header_index].strip()

    # Column separation
    if "\t" in header:
        columns = [c.strip() for c in header.split("\t") if c.strip()]
    else:
        columns = re.split(r"\s{2,}", header)

    x_label = columns[0]
    y_labels = columns[1:]

    data = {}
    current_run = 1
    data[current_run] = []
    ac_mode = None

    for line in lines[header_index + 1:]:

        step_match = STEP_REGEX.search(line)

        if step_match:
            current_run = int(step_match.group(1))
            data.setdefault(current_run, [])
            continue

        line = line.strip()

        if not line:
            continue

        # -------------------------------------------------
        # AC FORMAT: multiple signals on the same line
        # -------------------------------------------------

        if "(" in line and ")" in line:

            try:
                # Extract all magnitude-phase pairs
                pairs = re.findall(r"\(([^()]*)\)", line)

                if not pairs:
                    continue

                # Extract frequency before the first parenthesis
                before_parenthesis = line.split("(", 1)[0]
                frequency = extract_number(before_parenthesis)

                if frequency is None:
                    continue

                # Check that there is a pair for each signal
                if len(pairs) != len(y_labels):
                    continue

                row = [frequency]

                for pair in pairs:

                    values = pair.split(",")

                    if len(values) != 2:
                        raise ValueError("Invalid AC format.")

                    magnitude = extract_number(values[0])
                    phase = extract_number(values[1])

                    if magnitude is None or phase is None:
                        raise ValueError("Invalid AC values.")

                    row.extend([magnitude, phase])

                if ac_mode is False:
                    raise ValueError(
                        "Mixed formats (AC and Transient) detected in the file."
                    )

                ac_mode = True
                data[current_run].append(row)

            except (ValueError, IndexError):
                continue

            continue

        # -------------------------------------------------
        # NORMAL NUMERIC FORMAT (Transient, DC)
        # -------------------------------------------------

        numbers = re.findall(NUMBER_PATTERN, line)

        if len(numbers) >= 2:

            if ac_mode is True:
                continue

            ac_mode = False
            data[current_run].append([float(v) for v in numbers])

    # Remove empty runs
    data = {
        run: rows
        for run, rows in data.items()
        if rows
    }

    if not data or ac_mode is None:
        raise ValueError("No valid numeric data found in the file.")

    return x_label, y_labels, data, ac_mode


# ---------------------------------------------------------
# PLOTTING FUNCTIONS
# ---------------------------------------------------------

def plot_bode(data: Dict[int, List], title: str,
              filename: Path, y_labels: List[str]):
    """Draws the Bode diagram for all signals."""

    fig, (ax_mag, ax_phase) = plt.subplots(
        2, 1, figsize=(11, 8), sharex=True
    )

    single_run = len(data) == 1

    # Identical palette to plot_normal()
    colors = plt.get_cmap("tab10").colors

    # Number of signals present
    num_signals = len(data[next(iter(data))][0]) // 2

    for run_index, (run, rows) in enumerate(data.items()):

        values = np.array(rows)

        # Frequency
        freq = values[:, 0]

        # Sort based on frequency
        order = np.argsort(freq)
        freq = freq[order]

        # Loop over all signals
        for signal_index in range(num_signals):

            mag = values[:, 1 + signal_index * 2][order]
            phase = values[:, 2 + signal_index * 2][order]

            # Remove discontinuities at ±180°
            phase = np.rad2deg(np.unwrap(np.deg2rad(phase)))

            # Reference color for the signal
            base_color = colors[signal_index % len(colors)]

            # Magnitude: original color
            color_mag = base_color

            # Phase: lighter shade
            color_phase = tuple(
                c + (1 - c) * 0.45 for c in base_color
            )

            if single_run:
                label = y_labels[signal_index] if len(y_labels) > signal_index else f"Signal {signal_index + 1}"
                lw, alpha = 1.5, 1.0
            else:
                color_mag, color_phase = None, None
                label = None
                lw, alpha = 0.9, 0.65

            # Magnitude
            ax_mag.semilogx(
                freq, mag,
                color=color_mag,
                linewidth=lw,
                alpha=alpha,
                label=label
            )

            # Phase
            ax_phase.semilogx(
                freq, phase,
                color=color_phase,
                linewidth=lw,
                alpha=alpha,
                label=label
            )

    ax_mag.set_title(title)
    ax_mag.set_ylabel("Magnitude [dB]")
    ax_mag.grid(True, which="both", linestyle="--", alpha=0.5)

    ax_phase.set_xlabel("Frequency [Hz]")
    ax_phase.set_ylabel("Phase [degrees]")
    ax_phase.grid(True, which="both", linestyle="--", alpha=0.5)

    if len(data) <= 10:
        ax_mag.legend(fontsize=8)
        ax_phase.legend(fontsize=8)

    fig.tight_layout()
    save_plot(fig, filename)

def plot_normal(data: Dict[int, List], title: str, x_label: str,
                y_labels: List[str], filename: Path):
    """Draws plots for transient or DC sweep analyses."""

    multiple_runs = len(data) > 1

    # In Monte Carlo: one subplot for each signal.
    # In other cases: grouping by signal type.
    if multiple_runs:
        plot_groups = [
            (get_signal_type(label), [(i + 1, label)])
            for i, label in enumerate(y_labels)
        ]
    else:
        signal_groups = {}

        for column, label in enumerate(y_labels):
            signal_type = get_signal_type(label)
            signal_groups.setdefault(signal_type, []).append(
                (column + 1, label)
            )

        plot_groups = list(signal_groups.items())

    num_plots = len(plot_groups)

    fig, axes = plt.subplots(
        num_plots, 1,
        figsize=(11, 4 * num_plots),
        sharex=True,
        squeeze=False
    )

    axes = axes.flatten()
    colors = plt.get_cmap("tab10").colors

    for ax, (signal_type, signals) in zip(axes, plot_groups):

        for run, rows in data.items():

            values = np.asarray(rows)

            if values.ndim != 2 or values.shape[1] < 2:
                continue

            x = values[:, 0]
            order = np.argsort(x)

            for signal_index, (column, label) in enumerate(signals):

                if column >= values.shape[1]:
                    continue

                y = values[:, column]

                if multiple_runs:
                    color = None
                    linewidth = 0.9
                    alpha = 0.55
                else:
                    color = colors[signal_index % len(colors)]
                    linewidth = 1.5
                    alpha = 1.0

                ax.plot(
                    x[order],
                    y[order],
                    color=color,
                    linewidth=linewidth,
                    alpha=alpha,
                    label=label
                )

        # Y-axis label: signal name + unit
        if multiple_runs:
            signal_name = signals[0][1]

            if signal_type == "Voltage":
                unit = "V"
            elif signal_type == "Current":
                unit = "A"
            elif signal_type == "Temperature":
                unit = "°C"
            else:
                unit = ""

            ylabel = f"{signal_name} [{unit}]" if unit else signal_name
            ax.set_ylabel(ylabel)

        else:
            if signal_type == "Voltage":
                ax.set_ylabel("Voltage [V]")
            elif signal_type == "Current":
                ax.set_ylabel("Current [A]")
            elif signal_type == "Temperature":
                ax.set_ylabel("Temperature [°C]")
            else:
                ax.set_ylabel(", ".join(lbl for _, lbl in signals))

            ax.legend(fontsize=8)

        ax.grid(True, linestyle="--", alpha=0.5)

    axes[-1].set_xlabel(get_axis_unit(x_label))

    fig.suptitle(title, fontsize=14)
    fig.tight_layout()

    save_plot(fig, filename)

def save_plot(fig: plt.Figure, filename: Path):
    """Saves the figure to disk (PNG and PDF) and displays it on screen."""

    output_dir = filename.parent
    output_name = filename.stem

    png_path = output_dir / "img" / f"{output_name}.png"
    pdf_path = output_dir / "pdf" / f"{output_name}.pdf"

    # Automatically create folders if they do not exist
    png_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")

    print("\nPlots saved in:")
    print(f"- {png_path}")
    print(f"- {pdf_path}")
    plt.show()

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    print("=" * 50)
    print("           LTspice Universal Plotter")
    print("=" * 50)

    script_dir = Path(__file__).resolve().parent
    file_input = input(
        "\nEnter the paths of the LTspice TXT files (separated by space,\n"
        "use quotes for paths containing spaces):\n> "
    ).strip()

    raw_paths = parse_file_paths(file_input)

    if not raw_paths:
        print("\nNo files provided.")
        input("Press ENTER to exit...")
        return

    # Global title option: asks for a general prefix/title or uses file names
    use_custom_title = input(
        "\nWould you like to enter a custom title for the plots? (y/N): "
    ).strip().lower() == 'y'
    
    custom_title = ""
    if use_custom_title:
        custom_title = input("Enter the base title for the plots: ").strip()

    total_files = len(raw_paths)

    for index, raw_path in enumerate(raw_paths, start=1):
        print("\n" + "-" * 50)
        print(f"Processing file {index}/{total_files}: {raw_path}")
        print("-" * 50)

        file_path = Path(raw_path)
        if not file_path.is_absolute():
            file_path = script_dir / file_path

        file_path = file_path.resolve()

        if not file_path.is_file():
            print(f"ERROR: File not found ({file_path}). Skipping to next.")
            continue

        try:
            x_label, y_labels, data, ac_mode = read_ltspice_file(file_path)

            print("File successfully analyzed.")
            print(f"Runs detected: {len(data)}")
            print(f"X-axis: {x_label}")
            print(f"Y-axis: {', '.join(y_labels)}")

            for run, rows in data.items():
                print(f" - Run {run}: {len(rows)} points")

            # Definition of the figure title
            if custom_title:
                title = f"{custom_title}\n{file_path.stem}" if total_files > 1 else custom_title
            else:
                title = file_path.stem

            if ac_mode:
                print("Format detected: AC / Bode Analysis")
                plot_bode(data, title, file_path, y_labels)
            else:
                print("Format detected: Normal numeric data (Transient/DC)")
                plot_normal(data, title, x_label, y_labels, file_path)

        except Exception as error:
            print(f"ERROR DURING EXECUTION on {file_path.name}: {error}")

    input("\nProcessing complete. Press ENTER to exit...")


if __name__ == "__main__":
    main()