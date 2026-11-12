# LTspice Universal Plotter

**LTspice Universal Plotter** is a Python script designed to read, analyze, and automatically visualize simulation data exported from LTspice in `.txt` format.

The program automatically detects different types of analyses (AC, Transient, and DC), organizes signals into dedicated plots, and saves the results in both PNG and PDF formats, making simulation results easier to inspect, analyze, and document.

## Key Features

- **Automatic format detection:** identifies AC, Transient, and DC analysis data.
- **AC Analysis:** automatically generates Bode plots, displaying magnitude and phase in two separate graphs.
- **Transient and DC Analysis:** generates plots of signals as a function of time or sweep variable.
- **Automatic signal grouping:** organizes subplots by signal type, distinguishing between voltages, currents, temperatures, and other signals.
- **Monte Carlo and multiple-run support:** detects multiple simulation runs within the same file and overlays their results.
- **Batch processing:** allows multiple TXT files to be processed in a single execution.
- **Custom titles:** allows users to assign a general title to the generated plots.
- **Automatic export:** saves each plot in both PNG and PDF formats.
- **Path handling:** supports file paths containing spaces through quotation marks.
- **Data sorting:** automatically sorts data points according to the independent variable.

## Requirements

The project requires **Python 3.9 or later** and the following external libraries:

- NumPy
- Matplotlib

The modules `re`, `shlex`, `pathlib`, and `typing` are part of the Python standard library and do not require additional installation.

## Installation

## Requirements

The project requires **Python 3.9 or later** and the following external libraries:

- NumPy
- Matplotlib

The modules `re`, `shlex`, `pathlib`, and `typing` are part of the Python standard library and do not require additional installation.

---

## Installation

1. Download or clone the repository:

   ```bash
   git clone https://github.com/dario0603/LTspiceUniversalPlotter.git
   ```

2. Navigate to the project directory:

   ```bash
   cd LTspiceUniversalPlotter
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Place the LTspice simulation files (.txt) in the project directory.

5. Run the Python script:

   ```bash
   python txt_to_graph.py
   ```


## Exporting Data from LTspice

To use the program, simulation results must be exported from LTspice in text (`.txt`) format.

General procedure:

1. Run the desired simulation in LTspice.
2. Open the simulation results window.
3. Select the signals to be exported.
4. Export the data in TXT format.
5. Save the file in the project directory or in an accessible location.

The program uses the headers and numerical data contained in the exported file to automatically identify the columns and interpret the simulation results.

### Supported Analysis Types

| Analysis Type | Data Format | Visualization |
|---|---|---|
| AC Analysis | Magnitude and phase | Bode plots |
| Transient Analysis | Time and signals | Time-domain plots |
| DC Sweep | Sweep variable and signals | XY plots |
| Monte Carlo / Multiple Runs | Multiple simulation runs | Overlaid curves |


## Usage

Run the script from the terminal:

```bash
python txt_to_graph.py
```

The program will display a guided command-line interface.

### 1. File Input

You will be prompted to enter the paths of the TXT files to be processed.

Multiple files can be entered, separated by spaces.

Example:

```text
simulation1.txt simulation2.txt simulation3.txt
```

For file paths containing spaces, quotation marks must be used:

```text
"simulation test 1.txt" "simulation test 2.txt"
```

Relative paths are interpreted with respect to the directory containing the Python script.

## Testing the Program

To test the program, open `All files name.txt` and simply copy and paste its entire content into the program when prompted to enter the simulation file paths.

The file contains the names of all the test files available in the project directory, allowing you to test the different supported analysis types.

When asked whether you want to enter a custom title, type `n` (no) and press ENTER.

The program will then automatically process all the selected files and generate the corresponding plots.

### 2. Custom Plot Title

The program will then ask whether you want to assign a custom title to the generated plots.

- Entering `y` allows you to specify a custom title.
- Entering `n` or pressing ENTER uses the file name as the plot title.

When multiple files are processed, the corresponding file name is appended to the custom title to distinguish the results.

### 3. Automatic Processing

For each file, the program:

1. Identifies the header.
2. Extracts the signal column names.
3. Detects the data format.
4. Identifies any multiple simulation runs.
5. Generates the corresponding plots.
6. Automatically exports the figures.


## Plot Types

### AC Analysis – Bode Plots

For AC analysis, two subplots are generated:

- **Magnitude [dB]:** magnitude response as a function of frequency.
- **Phase [degrees]:** phase response as a function of frequency.

Both plots use a logarithmic frequency axis.

The phase data is processed using `numpy.unwrap()` to reduce discontinuities caused by transitions between +180° and -180°.

Each signal is assigned a distinctive color, while its phase response is displayed using a lighter shade of the same color.

### Transient Analysis and DC Sweep

For standard numerical analyses, the program automatically generates subplots by grouping signals into the following categories:

- Voltage
- Current
- Temperature
- Other

Signal classification is performed by analyzing the signal name.

For example:

| Signal Name | Category |
|---|---|
| V(out) | Voltage |
| V(in) | Voltage |
| I(R1) | Current |
| I(L1) | Current |
| Temp | Temperature |

When multiple simulation runs are present, each signal is displayed in a separate subplot, with the different simulation results overlaid.

## Output Organization

Plots are automatically saved in the same directory as the processed TXT file.

The program automatically creates two subdirectories:

```text
project/
│
├── txt_to_graph.py
│
├── simulation.txt
│
├── img/
│   └── simulation.png
│
└── pdf/
    └── simulation.pdf
```

### Export Formats

| Format | Description |
|---|---|
| PNG | High-resolution raster image (300 DPI) |
| PDF | Vector-based document, suitable for technical documentation |

After saving the files, the plots are also displayed on screen using Matplotlib.

## Plot Customization

Plot settings can be modified directly at the beginning of the script using `matplotlib.rcParams`.

The default settings include:

- Serif font family.
- Default font size of 11 pt.
- Axis title size of 13 pt.
- Legend font size of 10 pt.
- Display resolution of 120 DPI.
- Export resolution of 300 DPI.

The `tab10` Matplotlib color palette is used to distinguish between signals.
