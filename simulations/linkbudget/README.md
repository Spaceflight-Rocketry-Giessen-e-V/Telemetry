# Link Budget Simulation

## Overview

This simulation calculates the link budget for a simple preset flight profile.
It can be used to verify a stable link during all flight phases.
For more informations about the link budget, please visit our dedicated [document](../../docs/linkbudget.md).

## Installation

1. Make sure you have Python 3.10+ installed.
2. Clone the repository or download the code.
3. Install dependencies: `pip install -r requirements.txt`

## Usage

1. Change the flight profile parameters in the [python script](linkbudget.py): `h_max`, `d_start`, `d_end`
2. Run the python script: `python linkbudget.py`
3. The program will output a plot with a visualisation of the preset flight profile, as well as a plot with the link margin during the flight. The minimal link margin is printed.