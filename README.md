# ASCENT II Experimental Rocket Telemetry System

<img src="https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetrie/blob/main/media/images/Onboard_PCB_Front.png" width="400">
<img src="https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetrie/blob/main/media/images/Onboard_PCB_Back.png" width="400">

## 868 MHz telemetry system with a range of >10 km for bidirectional data exchange between an experimental rocket and a ground station

The telemetry system is part of the ASCENT II flight computer of the student rocketry association *Spaceflight Rocketry Gießen e.V.*, developed for the ARCHER experimental rocket.  
With this system, the ASCENT II flight computer can transmit sensor and status data in high quantity to the ground station as well as reliably receive and execute telecommands.

### Features

- 868 MHz radio transceiver  
- Minimum range of 18 km  
- Minimum data rate of 1.2 kbps  
- QFH antenna adapted to requirements  
- L-network for antenna matching  
- Software with a custom command library  

## Documentation

Information about the theoretical background, the components used, and more can be found [here](docs/literatur.md).  

Links to the software solutions we use are listed [here](docs/apps.md).  

The software documentation, including the command library, can be found [here](docs/documentation.md).  

## Usage

### Clone repository locally:
- Download and install Git: [Download](https://git-scm.com/downloads)  
- Open Git CMD (e.g., via Windows Search)  
- Configure Git username and email  
```
git config --global user.name "First Last"
git config --global user.email "Email address"
```
- Clone repository locally  
```
cd folderpath
git clone https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry
```

### Edit and synchronize files:
- Update local repository clone to the latest version  
```
git pull
```
- Edit/add/delete files  
- Synchronize updates online  
```
git add filename / git add --all
git commit -m "Short description of the update"
git push
```
