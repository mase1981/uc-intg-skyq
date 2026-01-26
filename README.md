# SkyQ Integration for Unfolded Circle Remote 2/3

Control your SkyQ satellite boxes directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive remote control functionality, **multi-device support**, and **real-time status monitoring**.

![SkyQ](https://img.shields.io/badge/SkyQ-Satellite%20TV-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-skyq?style=flat-square)](https://github.com/mase1981/uc-intg-skyq/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-skyq?style=flat-square)](https://github.com/mase1981/uc-intg-skyq/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-skyq/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides full remote control of your SkyQ satellite boxes directly from your Unfolded Circle Remote, with automatic multi-device detection and comprehensive remote functionality. **Production Ready**: Tested and verified working with real SkyQ devices across multiple households.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 📺 **Multi-Device Support**

- **Multi-Device Setup** - Configure up to 10 SkyQ devices in a single integration
- **Smart Naming** - Automatic entity naming using real device information (model, serial, location)
- **Device Models** - Supports all SkyQ models (ES130, ES200, etc.) with model-specific naming

#### **Per-Device Entities**
Each SkyQ device creates one remote entity:
- **Remote Entity**: `[Device Name] Remote ([Model])` - Full remote control with on-screen interface

### 🎮 **Remote Control Functionality**

#### **Comprehensive Button Support**
Real SkyQ protocol implementation with confirmed working buttons:

**Power Control** (4 commands):
- **Power Toggle**, **Power On**, **Standby**, **Off** - Complete power management

**Navigation** (8 commands):
- **D-Pad**: Up, Down, Left, Right, Select - Menu navigation
- **Control**: Back, Home, Services - Interface navigation

**Playback Control** (6 commands):
- **Transport**: Play, Pause, Stop, Record, Fast Forward, Rewind
- **Live TV**: Full control of live playback and recording

**Channel Control**:
- **Number Pad** (0-9) + Select - Direct channel entry
- **Channel Up** - Channel navigation
- **Guide**, **Info** - Program information and TV guide

**Volume Control** (3 commands):
- **Volume Up/Down**, **Mute Toggle** - Audio control

**Color Buttons** (4 commands):
- **Red**, **Green**, **Yellow**, **Blue** - Interactive TV functions

**Special Functions** (8 commands):
- **Sky Button**, **Search**, **Text/Teletext**, **Help**, **Services**, **Menu**, **Guide**, **Info**

#### **User Interface Features**
- **4 Comprehensive UI Pages**: Main Control, Numbers, Color Buttons, Special Functions
- **On-Screen Remote**: Full remote interface displayed on Remote screen
- **Button Mapping**: Physical Remote button mapping for core functions
- **Simple Commands**: All buttons available as simple command shortcuts

### **Device Requirements**

#### **SkyQ Device Compatibility**
- **SkyQ Models**: All SkyQ satellite boxes (ES130, ES200, etc.)
- **Firmware**: Any current SkyQ firmware version
- **Network**: Ethernet or Wi-Fi connected SkyQ device
- **API Access**: Standard SkyQ HTTP and TCP remote protocols (enabled by default)

### **Protocol Requirements**

- **Protocol**: SkyQ HTTP API + TCP Remote Control
- **HTTP Port**: 9006 (or 8080 for some devices)
- **Remote Port**: 49160 (default)
- **Network Access**: Device must be on same local network
- **Connection**: Real-time remote control commands

### **Network Requirements**

- **Local Network Access** - Integration requires same network as SkyQ devices
- **Port Access**: HTTP API (port 9006 or 8080) and Remote Control (port 49160)
- **Firewall**: No special configuration required for standard home networks
- **Static IP Recommended** - Device should have static IP or DHCP reservation

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-skyq/releases) page
2. Download the latest `uc-intg-skyq-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-skyq:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-skyq:
    image: ghcr.io/mase1981/uc-intg-skyq:latest
    container_name: uc-intg-skyq
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-skyq --restart unless-stopped --network host -v skyq-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-skyq:latest
```

## Configuration

### Step 1: Prepare Your SkyQ Devices

**IMPORTANT**: SkyQ devices must be powered on and connected to your network before adding the integration.

#### Verify Network Connection:
1. Ensure SkyQ devices are powered on and connected to network
2. Note the IP address for each device
3. Verify devices are accessible on network
4. Recommended: Give static IP addresses to your SkyQ devices

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow HTTP traffic on ports 9006/8080 and 49160
- **Network Isolation**: Must be on same subnet as Remote

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The SkyQ integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Device Count Selection:**
- Choose number of SkyQ devices to configure (1-10)

#### **Device Configuration:**
For each device:
- **Device IP Address**: SkyQ device IP (e.g., 192.168.1.100 or 192.168.1.100:9006)
- **Device Name**: Location-based name (e.g., "Living Room SkyQ", "Kitchen SkyQ")
- Click **Complete Setup**

#### **Connection Test:**
- Integration verifies device connectivity
- Tests HTTP API and remote control access
- Setup fails if device unreachable

4. Integration will create remote entities for each device:
   - **Remote**: `[Device Name] Remote ([Model])`

## Using the Integration

### Remote Entity

The remote entity provides comprehensive device control:

- **Power Control**: Power On/Off/Toggle/Standby
- **Navigation**: D-Pad and menu controls
- **Playback**: Transport controls and recording
- **Channel Control**: Number pad and channel navigation
- **Volume**: Volume and mute controls
- **Color Buttons**: Interactive TV functions
- **Special Functions**: Sky, Search, Text, Help, Services, Menu, Guide, Info
- **4 UI Pages**: Organized button layout for all functions

### Multi-Device Management

When using multiple devices:
- **Independent Control**: Each device operates independently
- **Room-Based Activities**: Create activities for each room/device
- **Centralized Overview**: All devices visible in integration settings
- **Model-Specific**: Automatic device model detection and naming

## Credits

- **Developer**: Meir Miyara
- **SkyQ**: Sky satellite TV platform
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **pyskyqremote**: Python library for SkyQ control
- **Protocol**: SkyQ HTTP API + TCP Remote Control
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-skyq/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Sky Support**: [Official Sky Support](https://www.sky.com/help)

---

**Made with ❤️ for the Unfolded Circle and SkyQ Communities**

**Thank You**: Meir Miyara
