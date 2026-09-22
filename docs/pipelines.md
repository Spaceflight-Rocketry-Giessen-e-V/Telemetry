# Pipelines
This document provides an overview of the automated workflows running through GitHub Actions and the manual processes used in this project.

# Table of Contents

- [Automatic](#automatic)
    - [Github-Actions](#github-actions)
        - [Firmware Documentation](#firmware-documentation)
- [Manuell](#manuell)
   - [Updating PCBs](#updating-pcbs)
   - [Updating Libraries](#updating-libraries)

# Automatic
## Github Actions
### Firmware Documentation

The firmware documentation workflow automatically builds and publishes the API
documentation for the onboard firmware, ground-station firmware, and
libraries. The documentation is generated from comments and declarations in the
C/C++ source files.

The source code uses Doxygen comment syntax to provide structured information
about functions, classes, and data structures. A documentation block starts
with `/**` and is placed directly before the declaration it describes. Doxygen
commands beginning with `@` identify the purpose and individual parts of the
API:

- `@brief` provides a short summary.
- `@param` describes a function parameter.
- `@return` describes the return value.
- `@defgroup` creates a documentation group.
- `@ingroup` assigns a declaration to a group, such as `onboard` or
  `groundstation`.

For example:

```cpp
/**
 * @brief Reads the latest command from the USB serial interface.
 *
 * @param serialUSB Serial interface used to receive the command.
 * @return The received command value.
 * @ingroup groundstation
 */
uint8_t commandReceive(HardwareSerial *serialUSB);
```

During the workflow, Doxygen converts these comments and the associated C/C++
declarations into Markdown/HTML files.
<p align="center"><img src="images/githubaction_workflow.png" /></p>


The workflow runs after a push to the `main` branch when files in one of the
following locations change:

- [`onboard/firmware/`](/onboard/firmware/)
- [`groundstation/firmware/`](/groundstation/firmware/)
- [`libraries/`](/libraries/)
- [`.github/mkdocs/`](/.github/mkdocs/)
- [`.github/workflows/ci.yml`](/.github/workflows/ci.yml)

The GitHub Actions job performs these steps:

1. Checks out the repository and configures the GitHub Actions bot as the Git
   user.
2. Installs Python 3.12, Doxygen, MkDocs, Material for MkDocs, and MkDoxy.
3. Builds the complete documentation using the configuration in
   [`.github/mkdocs/mkdocs.yml`](/.github/mkdocs/mkdocs.yml).
4. Runs the build in strict mode so that documentation warnings cause the job to
   fail instead of deploying an incomplete site.
5. Publishes the generated website to the
   [`gh-pages` branch](https://spaceflight-rocketry-giessen-e-v.github.io/Telemetry/).

The published firmware documentation is available at
[spaceflight-rocketry-giessen-e-v.github.io/Telemetry](https://spaceflight-rocketry-giessen-e-v.github.io/Telemetry/).
If another documentation workflow starts while one is already running, the
older run is cancelled so that only the newest version is deployed.

# Manuell

## Updating PCBs
When updating anything related to PCBs work through the follwing steps:

- [ ] regenerate gerber files 
- [ ] zip the gerber  files
- [ ] regenerate bom and ibom
- [ ] check if all rendering are still right

## Updating Libraries
When updating the libraries update the Version according to this scheme:
   - fix = x.x.0 -> x.x.1
   - feat (feature) = x.0.x -> x.1x
   - Release= 1.x.x -> 2.x.x
