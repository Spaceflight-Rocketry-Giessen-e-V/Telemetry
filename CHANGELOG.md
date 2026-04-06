# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Since our projects include multiple subsytems, which are developed more or less seperately (hardware, firmware, gui software), we decided to NOT use semantic versioning. The major versions of the whole project can be identified by their release date. However, the pcb designs include revision indications.

## [Unreleased]

### Added

- separate purpose-build groundstation electronics (motherboard/daughterboard approach)
- helix antenna design files for groundstation system
- GUI telemetry command transmission

### Changed

- onboard electronics with dual-band approach
- onboard and groundstation firmware update for new electronics

### Fixed

### Deprecated

### Removed

- flight data simulations

## 2026-01-04

### Added

- schematics and PCB design files for the onboard electronics system
- firmware for the onboard and ground station systems
- library for configuring and using Radiocrafts RC1780HP-RC232 radio modules
- library for encoding and decoding data packets
- graphical user interface for the ground station (receiving only)
- casing design files for the ground station
- 3d models and images of the system
- documentation for all systems