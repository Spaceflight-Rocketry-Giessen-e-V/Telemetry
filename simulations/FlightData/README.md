# Flight Simulation UI README

## Overview
This UI allows you to simulate flight data with customizable parameters. The simulation generates time series data, saves it, and displays it as a plot to mitigate CSV I/O issues.

## Features
- Input constants such as gravity, ascent velocity (`V_ASCENT`), and other parameters.
- Start the simulation with a single button.
- Saves outputs in a timestamped folder:
  - `simulation.csv` – the flight data
  - `parameters.json` – the constants used
  - `plot.png` – a graphical representation of the simulation
- Displays the generated plot in the UI for immediate feedback.

## Installation
1. Make sure you have Python 3.10+ installed.
2. Clone the repository or download the code.
3. Install dependencies:
`bash
pip install -r requirements.txt
`

## Usage
1. Run the Python script:
`bash
python flight_simulation_ui.py
`
2. In the UI:
   - Enter your desired values for simulation constants.
   - Click **Run Simulation**.
3. The program will:
   - Create a timestamped folder in the `flight_data` directory.
   - Save a CSV of the simulation and a JSON of parameters.
   - Generate a PNG plot from the CSV and display it in the UI.

## Output Structure
`flight_data/
└── YYYY-MM-DD_HH-MM-SS/
    ├── flight_data_YYYY-MM-DD_HH-MM-SS.csv
    ├── flight_data_YYYY-MM-DD_HH-MM-SS.json
    └── flight_data_YYYY-MM-DD_HH-MM-SS.png
`

## Notes
- The PNG is regenerated from the CSV to avoid read/write conflicts.
- Default simulation constants are:
  - Gravity: 10.0 m/s²
  - Velocity ascent: 30.0 m/s
  - Velocity descent: 20.0 m/s
  - Wind: 20.0 m/s
  - Battery drain rate: 0.11 V/s
  - Time step: 0.125 s
  - Starting latitude: 50.587249
  - Starting longitude: 8.683231
  - Initial position: 100 m
  - Initial battery: 8.4 V

## License
This project is open-source and free to use.
