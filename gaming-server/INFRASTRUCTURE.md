# 🏗️ CampPowerUp Infrastructure Plan

> **Last Updated:** March 28, 2026  
> **Status:** Phase 2 Planning  
> **Purpose:** Hardware deployment strategy for the retro gaming server

---

## 📋 Overview

CampPowerUp uses a multi-device infrastructure to provide reliable retro gaming services at camp. This document outlines the hardware assignments, roles, and deployment strategy.

---

## 🖥️ Available Hardware

### Device Inventory

| Device | CPU | RAM | Storage | OS | Power Level |
|--------|-----|-----|---------|-----|-------------|
| **Desktop PC** | Intel i7-9700K (8C/8T) | 16GB DDR4 | 119GB SSD + 2TB + 4TB | Windows 10 Pro | 🔥🔥🔥🔥🔥 |
| **MacBook Pro 2019** | Intel i9-9880H (8C/16T) | 16GB DDR4 | 1TB NVMe SSD | macOS Sonoma | 🔥🔥🔥🔥🔥 |
| **MacBook Pro 2012** | Intel i5/i7 | 16GB DDR4 | 1TB SSD | macOS Ventura (OCLP) | 🔥🔥🔥 |
| **MacBook Air 2013** | Intel i5 | 4GB DDR4 | 500GB SSD | macOS Ventura (OCLP) | 🔥 |
| **Apple TV Gen 2** | Apple A4 | 256MB | 8GB | iOS 6.2.1 (tvOS) | 📺 |

### Detailed Specs

#### Desktop PC (Primary Workstation)
- **Motherboard:** ASUS ROG STRIX Z370-E GAMING
- **GPU:** NVIDIA GeForce GTX 1070 (8GB) + Intel UHD 630
- **Storage Breakdown:**
  - C: 119GB NVMe SSD (Boot)
  - D: 2TB HDD (Projects/VMs)
  - E: 4TB HDD (Backups/Media)
- **Network:** Intel I219-V Gigabit + Realtek 802.11ac WiFi

#### MacBook Pro 16" (2019)
- **GPU:** AMD Radeon Pro 5500M (4GB) + Intel UHD 630
- **Display:** 16" Retina (3072x1920)
- **Security:** T2 Chip, Touch ID, FileVault
- **Ports:** 4x Thunderbolt 3 (USB-C)

#### MacBook Pro 13" (Mid 2012)
- **Upgrades:** RAM upgraded to 16GB, 1TB SSD installed
- **Running:** macOS Ventura via OpenCore Legacy Patcher
- **Best For:** Dedicated server role (low power, reliable)

#### MacBook Air 13" (2013)
- **Limitation:** 4GB RAM (soldered, non-upgradeable)
- **Running:** macOS Ventura via OpenCore Legacy Patcher
- **Best For:** Light support tasks, kiosk display

#### Apple TV Gen 2 (2010)
- **Chip:** Apple A4 (single-core ARM, 1GHz)
- **RAM:** 256MB (severely limited)
- **Storage:** 8GB internal
- **Output:** 720p HDMI
- **Network:** Ethernet + WiFi 802.11n
- **Best For:** AirPlay display hub, status dashboard

---

## 🗺️ Role Assignments

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CAMPOWERUP INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    🏠 HOME / DEVELOPMENT                            │   │
│  │                                                                     │   │
│  │   Desktop PC (i7-9700K)          MacBook Pro 2019 (i9)             │   │
│  │   ┌─────────────────────┐        ┌─────────────────────┐           │   │
│  │   │ • Code Development  │        │ • Mobile Dev        │           │   │
│  │   │ • Testing Server    │        │ • Code on the go    │           │   │
│  │   │ • VM Labs           │        │ • Design/UI work    │           │   │
│  │   │ • Build & Deploy    │        │ • Backup Dev        │           │   │
│  │   │ • 4TB Backup Store  │        │                     │           │   │
│  │   └─────────────────────┘        └─────────────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ Deploy                                 │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         🏕️ CAMP DEPLOYMENT                          │   │
│  │                                                                     │   │
│  │   MacBook Pro 2012 (16GB)        MacBook Air 2013 (4GB)            │   │
│  │   ┌─────────────────────┐        ┌─────────────────────┐           │   │
│  │   │ 👑 MAIN SERVER      │        │ 📺 KIOSK/SUPPORT    │           │   │
│  │   │                     │        │                     │           │   │
│  │   │ • EmulatorJS        │◄──────►│ • Game Menu Display │           │   │
│  │   │ • ROM Server        │  Sync  │ • Syncthing Node    │           │   │
│  │   │ • Syncthing Hub     │        │ • Monitoring UI     │           │   │
│  │   │ • Save Management   │        │ • Backup Server     │           │   │
│  │   │ • User Auth         │        │ • Emergency Backup  │           │   │
│  │   └─────────────────────┘        └─────────────────────┘           │   │
│  │              │                              │                       │   │
│  │              │                              │ AirPlay               │   │
│  │              │                              ▼                       │   │
│  │              │         ┌─────────────────────────────────┐         │   │
│  │              │         │ 📺 APPLE TV GEN 2               │         │   │
│  │              │         │ • AirPlay Display Hub           │         │   │
│  │              │         │ • Mirror gameplay to big TV     │         │   │
│  │              │         │ • Spectator mode for groups     │         │   │
│  │              │         └─────────────────────────────────┘         │   │
│  │              ▼                                                      │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │                    📱 CAMPER DEVICES                        │  │   │
│  │   │        Phones, Tablets, Laptops, Chromebooks                │  │   │
│  │   │              (Connect via WiFi to play)                     │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Device Responsibilities

#### 🖥️ Desktop PC — Development & Testing Hub

| Task | Description |
|------|-------------|
| Code Development | Primary workspace with VS Code, Git, Docker |
| Testing Server | Test Docker containers before deploying |
| VM Labs | Run cybersecurity labs and test environments |
| Build & Deploy | Push releases to GitHub for camp devices |
| Backup Storage | 4TB BarraCuda for ROM backups and saves |

#### 💻 MacBook Pro 2019 — Mobile Development

| Task | Description |
|------|-------------|
| Mobile Dev | Code on the go, travel-ready |
| macOS Testing | Test Docker on Mac before camp deployment |
| Design/UI Work | 16" Retina display for design tasks |
| Emergency Backup | Can replace any other device if needed |

#### 💻 MacBook Pro 2012 — Camp Main Server 👑

| Task | Description |
|------|-------------|
| EmulatorJS | Serve browser-based gaming to all devices |
| ROM Server | nginx hosting game files |
| Syncthing Hub | Central save file synchronization |
| User Auth | Manage camper accounts (Phase 2) |
| 24/7 Operation | Runs in clamshell mode, low power |

#### 💻 MacBook Air 2013 — Kiosk & Support

| Task | Description |
|------|-------------|
| Game Menu Display | Connect to TV, browse game library |
| Syncthing Node | Redundant save file backup |
| Monitoring UI | Display server health dashboard |
| Failover Server | Emergency backup if main server fails |

#### 📺 Apple TV Gen 2 — AirPlay Display Hub

| Task | Description |
|------|-------------|
| AirPlay Receiver | Mirror iOS/Mac screens to big TV |
| Spectator Mode | Let groups watch gameplay together |
| Game Demos | Show off games on large display |
| Status Display | (Future) Show server status/QR codes |

**Setup Instructions:**
1. Connect Apple TV to HDMI TV/monitor
2. Connect to camp WiFi network
3. Enable AirPlay in Settings → AirPlay
4. Campers use AirPlay from their devices to share screen

**Future Enhancement (Jailbreak):**
- Use Seas0nPass to jailbreak Apple TV 2
- Install nitoTV + lightweight browser
- Display server status dashboard or QR codes

---

## 🚀 Deployment Phases

### Phase 1: Foundation ✅ (Complete)
- [x] Docker Compose setup for gaming server
- [x] EmulatorJS container configuration
- [x] ROM Server (nginx) with web UI
- [x] Syncthing save file sync
- [x] Standalone emulator test page
- [x] Quick-play demo functionality

### Phase 2: Infrastructure (Current)
- [ ] Document hardware assignments
- [ ] Set up Docker on MacBook Pro 2012
- [ ] Set up Docker on MacBook Air 2013
- [ ] Configure Syncthing mesh between devices
- [ ] Test failover scenarios
- [ ] Create deployment scripts

### Phase 3: Features (Planned)
- [ ] RetroArch Netplay relay (multiplayer)
- [ ] User authentication system
- [ ] Camper profiles and save management
- [ ] Leaderboards and tournaments

### Phase 4: Advanced (Future)
- [ ] Moonlight/Sunshine game streaming
- [ ] Mobile app for game browsing
- [ ] Automated ROM organization
- [ ] Analytics dashboard

---

## 🔧 Setup Instructions

### MacBook Pro 2012 (Main Server)

1. **Install Docker Desktop for Mac**
   ```bash
   # Download from https://www.docker.com/products/docker-desktop/
   # Or use Homebrew:
   brew install --cask docker
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/fowler013/CampPowerUp.git
   cd CampPowerUp/gaming-server
   ```

3. **Start the gaming server**
   ```bash
   docker-compose up -d
   ```

4. **Configure for clamshell mode**
   - System Preferences → Energy Saver
   - Prevent sleep when display is off: ✅
   - Connect to power adapter

### MacBook Air 2013 (Kiosk)

1. **Install Docker Desktop** (same as above)

2. **Clone repository** (same as above)

3. **Start only the kiosk services**
   ```bash
   docker-compose up -d rom-server save-sync
   ```

4. **Connect to external display**
   - Open browser to `http://localhost:8888`
   - Enter fullscreen mode (Cmd+Shift+F)

---

## 📊 Network Configuration

### Camp Network Setup

```
Internet ──► Camp Router ──┬──► MacBook Pro 2012 (192.168.1.100)
                           │         Main Server
                           │
                           ├──► MacBook Air 2013 (192.168.1.101)
                           │         Kiosk/Backup
                           │
                           └──► Camper Devices (DHCP)
                                     Players
```

### Recommended Static IPs

| Device | IP Address | Ports |
|--------|------------|-------|
| MacBook Pro 2012 | 192.168.1.100 | 3000, 8080, 8384, 8888 |
| MacBook Air 2013 | 192.168.1.101 | 8384, 8888 |

### Firewall Rules

Allow inbound on main server:
- TCP 3000 (EmulatorJS web frontend)
- TCP 8080 (ROM manager)
- TCP 8384 (Syncthing web UI)
- TCP 8888 (ROM file server)
- TCP 22000 (Syncthing sync)
- UDP 21027 (Syncthing discovery)

---

## 💰 Cost Analysis

| Item | Cost |
|------|------|
| Desktop PC | Already owned |
| MacBook Pro 2019 | Already owned |
| MacBook Pro 2012 | Already owned |
| MacBook Air 2013 | Already owned |
| Apple TV Gen 2 | Already owned |
| Additional hardware | **$0** |
| **Total** | **$0** |

---

## 📝 Maintenance Checklist

### Before Camp
- [ ] Update macOS on both camp MacBooks
- [ ] Pull latest code from GitHub
- [ ] Test Docker containers locally
- [ ] Verify Syncthing is syncing
- [ ] Backup ROM library to Desktop PC
- [ ] Charge all devices

### During Camp
- [ ] Monitor server health daily
- [ ] Check Syncthing sync status
- [ ] Backup saves to Air nightly
- [ ] Document any issues

### After Camp
- [ ] Export save files
- [ ] Backup to Desktop PC (4TB drive)
- [ ] Document lessons learned
- [ ] Update this plan as needed

---

## 🆘 Troubleshooting

### Server Not Accessible
1. Check if Docker is running: `docker ps`
2. Verify IP address: `ifconfig | grep inet`
3. Test locally: `curl http://localhost:8888`
4. Check firewall settings

### Syncthing Not Syncing
1. Check Syncthing UI: `http://localhost:8384`
2. Verify both devices are online
3. Check folder paths match
4. Restart Syncthing container

### EmulatorJS Slow/Laggy
1. Close unnecessary browser tabs
2. Use Chrome for best performance
3. Reduce number of simultaneous players
4. Check server RAM usage

---

*Part of the CampPowerUp project — Bringing retro gaming to camp!*
