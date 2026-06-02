# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Since our projects include multiple subsytems, which are developed more or less seperately (hardware, firmware, gui software), we decided to NOT use semantic versioning. The major versions of the whole project can be identified by their release date. However, the pcb designs include revision indications.


## [UNRELEASED]:

### Added
### Changed
### Removed
### Fixed
### Deprecated


## 2026-06-02:

### Added
- New purpose-built groundstation electronics (motherboard/daughterboard design)
- Helix antenna for the groundstation: design files, drilling template, renderings, and assembly manual
- GUI command transmission - send commands to the rocket, not just receive telemetry
- New GUI windows: commands, connection, settings (with persistence), time, and acceleration
- run.bat launcher for the GUI and new Arduino simulation sketches (v2, v3, CSV replay)
- New design overview documentation covering the electronics and groundstation architecture

### Changed
- Onboard electronics redesigned for dual-band operation (new schematic, PCB, BOM, 3D model, renderings)
- Onboard and groundstation firmware updated for the new electronics
- Major GUI rework, including the map/location view and a new COM controller
- Reorganized libraries: common/lib renamed to common/libraries; RC1780HP renamed to Radiocrafts_RC17xxHP_RC232
- Reworked READMEs and documentation structure; added Digikey purchase links for the boards

### Removed
- Flight data simulations
- Deprecated GUI receiver and old system overview docs


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
