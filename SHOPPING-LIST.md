# 🛒 CampPowerUp Equipment Shopping List

> **Purpose:** Equipment needed for the retro gaming server project  
> **Last Updated:** March 29, 2026  
> **Status:** Planning

---

## ✅ Already Have

| Item | Role | Notes |
|------|------|-------|
| MacBook Pro 2012 (16GB/1TB) | Main Server | Running Sonoma via OCLP |
| MacBook Air 2013 (4GB/500GB) | Kiosk/Backup | Running Ventura via OCLP |
| MacBook Pro 2019 | Development | Mobile dev machine |
| Desktop PC (i7-9700K) | Dev/Testing | Primary development |
| Apple TV Gen 2 | AirPlay Hub | Spectator display |
| Xbox One x2 | Emulation Stations | RetroArch gaming |
| SurfShark VPN | Network Security | Already subscribed |

---

## 🛒 Need to Buy

### 🔴 High Priority (Get These First!)

| Item | Purpose | Est. Price | Why Priority |
|------|---------|------------|--------------|
| **USB Flash Drive (16GB+)** | OCLP recovery, ROM transfer | $8-15 | Learned this the hard way! |
| **Ethernet Adapters (x2)** | Wired connection for both MacBooks | $15-25 each | Most impactful for server performance |
| **Laptop Cooling Pads (x2)** | Keep servers cool 24/7 | $20-30 each | Prevents thermal throttling, extends lifespan |

### 🟡 Medium Priority (Recommended)

| Item | Purpose | Est. Price | Link/Notes |
|------|---------|------------|------------|
| **Ethernet Cables (Cat6)** | Reliable server connection | $10-20 | Get 2-3, various lengths |
| **Surge Protector/Power Strip** | Protect all equipment | $15-30 | 6+ outlets, essential! |
| **USB Hub (powered)** | Multiple peripherals | $20-35 | For MacBook Pro 2012 |
| **Portable Router (GL.iNet)** | Dedicated camp network + VPN | $30-50 | GL.iNet has built-in VPN support |
| **USB-C to Thunderbolt 2 Adapter** | Connect 2019 Mac to 2012 Mac | $20-35 | For troubleshooting/Target Disk Mode |

### 🟢 Nice to Have (Budget Permitting)

| Item | Purpose | Est. Price | Link/Notes |
|------|---------|------------|------------|
| **External SSD (500GB+)** | ROM storage, backups | $50-80 | Samsung T7 or similar |
| **HDMI Cable (6ft)** | Apple TV to TV | $8-15 | If not included with TV |
| **Bluetooth Controllers (8BitDo)** | Better gaming experience | $20-40 each | Get 2-4 for multiplayer |
| **UPS Battery Backup** | Power outage protection | $80-150 | APC or CyberPower |
| **TV/Monitor for Kiosk** | Display for Apple TV / Air | $100-200 | Or use existing camp TV |
| **Raspberry Pi 4 (4GB)** | Dedicated backup server | $55-60 | Future redundancy option |

### 🎮 Xbox RetroArch Setup

| Item | Purpose | Est. Price | Link/Notes |
|------|---------|------------|------------|
| **Microsoft Dev Account** | Enable Dev Mode for RetroArch | $20 (one-time) | Required for sideloading |
| **USB Drives for ROMs (x2)** | ROM storage for each Xbox | $15-20 each | 32GB+ recommended |

---

## 🆓 Free Software to Install

| Software | Purpose | Where to Get |
|----------|---------|--------------|
| **Amphetamine** | Keep Macs awake with lid closed | Mac App Store |
| **Stats** | Monitor CPU/RAM/temperature | Mac App Store |
| **Chrome** | Best browser for EmulatorJS | google.com/chrome |
| **Homebrew** | Package manager for Mac | brew.sh |

---

## 💰 Budget Summary

| Tier | What You Get | Estimated Cost |
|------|--------------|----------------|
| **Minimum** | USB drive + 2 Ethernet adapters | ~$50-65 |
| **Essential** | Above + 2 cooling pads + surge protector | ~$120-160 |
| **Recommended** | Above + router + cables + USB hub | ~$200-260 |
| **Full Setup** | All items including Xbox dev + controllers | ~$400-500 |

---

## 🔗 Quick Links

### Amazon Search Links
- [USB Flash Drives 16GB+](https://www.amazon.com/s?k=usb+flash+drive+16gb)
- [Thunderbolt to Ethernet Adapter](https://www.amazon.com/s?k=thunderbolt+ethernet+adapter)
- [Laptop Cooling Pad](https://www.amazon.com/s?k=laptop+cooling+pad+13+inch)
- [GL.iNet Travel Router](https://www.amazon.com/s?k=gl.inet+travel+router)
- [USB-C to Thunderbolt 2](https://www.amazon.com/s?k=usb-c+thunderbolt+2+adapter)
- [8BitDo Controllers](https://www.amazon.com/s?k=8bitdo+controller)
- [Cat6 Ethernet Cables](https://www.amazon.com/s?k=cat6+ethernet+cable)

### Recommended Brands
- **Adapters:** Apple, Anker, CalDigit
- **Networking:** GL.iNet, TP-Link, Netgear
- **Storage:** Samsung, SanDisk, Crucial
- **Controllers:** 8BitDo, PowerA
- **Cooling:** Havit, TopMate, Cooler Master

---

## ⚡ Performance Tips (Free!)

### On Both MacBooks:

**Reduce Visual Effects:**
```
System Preferences → Accessibility → Display
✅ Reduce motion
✅ Reduce transparency
```

**Disable Spotlight on Server Folders:**
```bash
sudo mdutil -i off /path/to/CampPowerUp
```

**Use Wired Ethernet:** WiFi adds latency — Ethernet is always faster for servers

**Close Unnecessary Apps:** Only run Docker, Chrome, Syncthing

---

## 📋 Priority Shopping Order

1. **🔴 USB Flash Drive** — Emergency OCLP recovery
2. **🔴 Ethernet Adapters (x2)** — Stable server connections
3. **🔴 Cooling Pads (x2)** — Protect hardware during 24/7 use
4. **🟡 Surge Protector** — Protect all equipment
5. **🟡 Portable Router** — Dedicated camp network
6. **🟢 Everything else** — As budget allows

---

## 📝 Camp-Specific Checklist

- [ ] Check if camp has WiFi or need to bring router
- [ ] Check available TVs/monitors at camp
- [ ] Count how many devices will connect (estimate bandwidth)
- [ ] Plan power outlet locations
- [ ] Bring extension cords if needed
- [ ] Test everything at home BEFORE camp!

---

*Part of the CampPowerUp project — Bringing retro gaming to camp!*
