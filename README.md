# SkyQ Integration for Unfolded Circle Remote 2/3

Control your SkyQ satellite boxes directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player and remote control functionality.

![SkyQ](https://img.shields.io/badge/SkyQ-Satellite%20TV-blue)
![Version](https://img.shields.io/badge/version-1.0.0-green)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)

## Features

This integration provides comprehensive control of your SkyQ satellite boxes directly from your Unfolded Circle Remote, with automatic multi-device detection and full remote functionality.

### 📺 **Multi-Device Support**

#### **Automatic Device Detection**
- **Multi-Device Setup**: Configure up to 10 SkyQ devices in a single integration
- **Smart Naming**: Automatic entity naming using real device information (model, serial, location)
- **Device Models**: Supports all SkyQ models (ES130, ES200, etc.) with model-specific naming

#### **Per-Device Entities**
Each SkyQ device creates two entities:
- **Media Player Entity**: `[Device Name] ([Model])` - Playback and Basic Controls
- **Remote Entity**: `[Device Name] Remote ([Model])` - Full remote control functionality

### 🎮 **Remote Control Functionality**

#### **Comprehensive Button Support** (43 verified commands)
Real SkyQ protocol implementation with only confirmed working buttons:

**Power Control** (4 commands):
- **Power Toggle**, **Power On**, **Standby**, **Off** - Complete power management

**Navigation** (8 commands):
- **D-Pad**: Up, Down, Left, Right, Select - Menu navigation
- **Control**: Back, Home, Menu - Interface navigation

**Playback Control** (6 commands):
- **Transport**: Play, Pause, Stop, Record, Fast Forward, Rewind
- **Live TV**: Full control of live playback and recording

**Channel Control**:
- **Number Pad** (0-9) + Select - Direct channel entry
- **Guide**, **Info** - Program information and TV guide

**Volume Control** (3 commands):
- **Volume Up/Down**, **Mute Toggle** - Audio control

**Color Buttons** (4 commands):
- **Red**, **Green**, **Yellow**, **Blue** - Interactive TV functions

**Special Functions** (5 commands):
- **Sky Button**, **Search**, **Text/Teletext**, **Help**, **Services**

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
   - Best to give static IP addresses to your SkyQ devices
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
5. Entities will be created for each successful device:
   - **[Device Name] ([Model])** (Media Player Entity)
   - **[Device Name] Remote ([Model])** (Remote Entity)

### Step 3: Add Entities to Activities

1. Go to **Activities** in your remote interface
2. Edit or create an activity for each room/device
3. Add SkyQ entities from the **Available Entities** list:
   - **SkyQ Media Player** - Channel control and media information
   - **SkyQ Remote** - Full remote control with on-screen interface
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
- Media Player: "Living Room SkyQ (ES130)"
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
- Living Room SkyQ (ES130) + Living Room SkyQ Remote (ES130)
- Kitchen SkyQ (ES200) + Kitchen SkyQ Remote (ES200)
- Bedroom SkyQ (ES130) + Bedroom SkyQ Remote (ES130)
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

**Entities Not Working:**
- Check device power state (must be on, not standby)
- Verify network connectivity to device
- Review integration logs for error messages

**Volume Controls Not Working:**
- Volume control available only on Remote entity, not Media Player
- Use VOL+, VOL-, MUTE buttons on remote interface
- Some SkyQ models may have limited volume control support

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
│   ├── media_player.py        # Media player entity
│   ├── remote.py              # Remote control entity
│   └── setup.py               # Integration setup flow
├── .github/workflows/         # GitHub Actions CI/CD
│   └── build.yml              # Automated build pipeline
├── docker-compose.yml         # Docker deployment
├── Dockerfile                 # Container build instructions
├── docker-entry.sh            # Container entry point
├── driver.json               # Integration metadata
├── requirements.txt          # Dependencies
├── pyproject.toml            # Python project config
└── README.md                 # This file
```

### Development Features

#### **Real SkyQ Protocol**
Complete SkyQ protocol implementation:
- **HTTP API**: Official SkyQ REST endpoints for device info and services
- **TCP Remote**: Native remote control protocol with proper command formatting
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
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with real SkyQ devices
4. Test with multiple SkyQ models if available
5. Verify all 43 commands work correctly
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Credits

- **Developer**: Meir Miyara
- **SkyQ Protocol**: Reverse-engineered from real SkyQ device behavior
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Community**: Testing and feedback from UC community

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-skyq/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community** 

**Thank You**: Meir Miyara