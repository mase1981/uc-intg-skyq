# SkyQ Integration for Unfolded Circle Remote 2/3

Control your SkyQ satellite boxes directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive remote control functionality.

![SkyQ](https://img.shields.io/badge/SkyQ-Satellite%20TV-blue)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-skyq)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-skyq/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)

## Features

This integration provides full remote control of your SkyQ satellite boxes directly from your Unfolded Circle Remote, with automatic multi-device detection and comprehensive remote functionality.

**Production Ready**: Tested and verified working with real SkyQ devices across multiple households.

### 📺 **Multi-Device Support**

- **Multi-Device Setup**: Configure up to 10 SkyQ devices in a single integration
- **Smart Naming**: Automatic entity naming using real device information (model, serial, location)
- **Device Models**: Supports all SkyQ models (ES130, ES200, etc.) with model-specific naming

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

## Device Requirements

### **SkyQ Device Compatibility**
- **SkyQ Models**: All SkyQ satellite boxes (ES130, ES200, etc.)
- **Firmware**: Any current SkyQ firmware version
- **Network**: Ethernet or Wi-Fi connected SkyQ device
- **API Access**: Standard SkyQ HTTP and TCP remote protocols (enabled by default)

### **Network Requirements**
- **Local Network Access** - Integration requires same network as SkyQ devices
- **Port Access**: 
  - **HTTP API**: Port 9006 (or 8080 for some devices)
  - **Remote Control**: Port 49160
- **Firewall**: No special configuration required for standard home networks

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
    network_mode: host  # Required for SkyQ device discovery
    volumes:
      - ./data:/data
    environment:
      - UC_INTEGRATION_HTTP_PORT=9090
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name=uc-intg-skyq --network host -v </local/path>:/config --restart unless-stopped ghcr.io/mase1981/uc-intg-skyq:latest
```

## Configuration

### Step 1: Prepare Your SkyQ Devices

1. **Device Setup:**
   - Ensure SkyQ devices are powered on and connected to your network
   - Recommended: Give static IP addresses to your SkyQ devices
   - Verify devices are accessible via their web interface (if available)

2. **Network Discovery:**
   - Find SkyQ device IP addresses via router admin interface
   - Or use network scanning tools to locate devices
   - Default ports: 9006 (HTTP API), 49160 (Remote Control)

3. **Multiple Devices:**
   - Each SkyQ device should have a static or reserved IP address
   - Note the location/name for each device (Living Room, Bedroom, etc.)

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The SkyQ integration should appear in **Available Integrations**
3. Click **"Configure"** and follow the setup wizard:

   **Device Count Selection:**
   - Choose number of SkyQ devices to configure (1-10)

   **Device Configuration:**
   For each device:
   - **Device IP Address**: SkyQ device IP (e.g., 192.168.1.100 or 192.168.1.100:9006)
   - **Device Name**: Location-based name (e.g., "Living Room SkyQ", "Kitchen SkyQ")

4. Click **"Complete Setup"** when all devices are configured
5. Remote entities will be created for each successful device:
   - **[Device Name] Remote ([Model])** (Remote Entity)

### Step 3: Add Remote Entities to Activities

1. Go to **Activities** in your remote interface
2. Edit or create an activity for each room/device
3. Add SkyQ remote entities from the **Available Entities** list:
   - **SkyQ Remote** - Full remote control with comprehensive on-screen interface
4. Configure button mappings and UI layout as desired
5. Save your activity

## Usage Examples

### Single Device Setup
```
Setup Input:
- Device Count: 1
- IP Address: 192.168.1.100
- Name: "Living Room SkyQ"

Result:
- Remote: "Living Room SkyQ Remote (ES130)"
```

### Multi-Device Setup
```
Setup Input:
- Device Count: 3
- Device 1: 192.168.1.100, "Living Room SkyQ"
- Device 2: 192.168.1.101, "Kitchen SkyQ"  
- Device 3: 192.168.1.102, "Bedroom SkyQ"

Result:
- Living Room SkyQ Remote (ES130)
- Kitchen SkyQ Remote (ES200)
- Bedroom SkyQ Remote (ES130)
```

## Troubleshooting

### Common Issues

**Device Not Found:**
- Verify SkyQ device IP address is correct
- Check device is powered on and connected to network
- Try alternate port (8080 instead of 9006, or vice versa)
- Ensure Remote and SkyQ device are on same network subnet

**Connection Timeout:**
- Check firewall settings on router/network
- Verify SkyQ device is responding (try ping test)
- Some SkyQ devices may have HTTP API disabled - restart device

**Remote Not Working:**
- Check device power state (must be on, not standby)
- Verify network connectivity to device
- Review integration logs for error messages

**Some Buttons Not Working:**
- Some commands may not be supported by all SkyQ models
- Check logs for "Invalid command" errors from pyskyqremote
- Use the discovery script to verify supported commands for your device

### Debug Information

Enable detailed logging for troubleshooting:

**Docker Environment:**
```bash
# Add to docker-compose.yml environment section
- LOG_LEVEL=DEBUG

# View logs
docker logs uc-intg-skyq
```

**Integration Logs:**
- **Remote Interface**: Settings → Integrations → SkyQ → View Logs
- **Common Errors**: Connection timeouts, authentication failures, device detection issues

**Device Verification:**
- **HTTP Test**: Try accessing `http://device-ip:9006/as/services` in web browser
- **Remote Test**: Use `telnet device-ip 49160` to test remote control port
- **Network Scan**: Use network tools to verify device accessibility

**Discovery Script:**
If buttons don't work, run the discovery script to identify supported commands:
```bash
python skyq-discovery.py [your-skyq-ip]
```

## For Developers

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-skyq.git
   cd uc-intg-skyq
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   Integration uses local config files:
   ```bash
   # Configuration automatically created during setup
   # Located in project root: config.json
   ```

3. **Run development:**
   ```bash
   python uc_intg_skyq/driver.py
   # Integration runs on localhost:9090
   ```

4. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Configure integration with real SkyQ devices

### Project Structure

```
uc-intg-skyq/
├── uc_intg_skyq/              # Main package
│   ├── __init__.py            # Package info  
│   ├── client.py              # SkyQ API client (HTTP + TCP)
│   ├── config.py              # Configuration management
│   ├── driver.py              # Main integration driver
│   ├── remote.py              # Remote control entity
│   └── setup.py               # Integration setup flow (legacy)
├── .github/workflows/         # GitHub Actions CI/CD
│   └── build.yml              # Automated build pipeline
├── docker-compose.yml         # Docker deployment
├── Dockerfile                 # Container build instructions
├── docker-entry.sh            # Container entry point
├── driver.json               # Integration metadata
├── requirements.txt          # Dependencies
├── pyproject.toml            # Python project config
├── skyq-discovery.py         # Command discovery script
└── README.md                 # This file
```

### Development Features

#### **Real SkyQ Protocol**
Complete SkyQ protocol implementation:
- **Primary**: pyskyqremote library for real device communication
- **Fallback**: Direct HTTP/TCP communication for development/testing
- **Error Handling**: Robust connection management and retry logic
- **Device Detection**: Automatic model and capability detection

#### **Multi-Device Architecture**
Production-ready multi-device support:
- **Configuration Management**: Persistent multi-device configuration
- **Entity Lifecycle**: Independent entity management per device
- **Connection Monitoring**: Per-device health monitoring and reconnection
- **State Management**: Maintains device state across interruptions

#### **Command Verification**
All commands verified on real SkyQ hardware:
- **Discovery Testing**: Comprehensive command testing on real devices
- **Protocol Analysis**: Deep analysis of SkyQ communication protocols  
- **Error Mapping**: Proper handling of device-specific failures
- **Command Filtering**: Only working commands exposed to users

### Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run with real SkyQ devices
python uc_intg_skyq/driver.py

# Configure integration with SkyQ device IPs
# Test all remote functions on actual devices

# Discovery testing
python skyq-discovery.py [skyq-device-ip]
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with real SkyQ devices
4. Test with multiple SkyQ models if available
5. Verify commands work correctly with discovery script
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Architecture Notes

### **Current Implementation**
- **Remote-Only Design**: Focused on reliable remote control functionality
- **Production Tested**: Verified working with real SkyQ devices
- **Hybrid Communication**: pyskyqremote for real devices, HTTP fallback for development
- **Optimized Performance**: No heavy channel loading or unnecessary API calls

### **Why Remote-Only?**
- **Reliability**: Remote control is the primary use case for SkyQ devices
- **Performance**: Avoids loading 1000+ channels that can overwhelm the system
- **Compatibility**: Works consistently across all SkyQ models and firmware versions
- **User Experience**: Clean, focused interface without unnecessary complexity

## Credits

- **Developer**: Meir Miyara
- **SkyQ Protocol**: Built using pyskyqremote library and direct protocol analysis
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Community**: Testing and feedback from UC community with real SkyQ devices

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-skyq/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community** 

**Thank You**: Meir Miyara
