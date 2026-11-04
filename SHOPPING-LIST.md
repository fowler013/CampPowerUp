# 🛒 CampPowerUp Equipment Shopping List

> **Purpose:** Equipment needed for the retro gaming server project  
> **Last Updated:** March 29, 2026  
> **Status:** Planning

---

## 🎯 Deployment Strategy

**End Goal:** Host server at home, campers access remotely via internet  
**Starting Point:** Portable setup for testing and camp demos

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
| Home Router | Home Network | Has 4+ Ethernet ports |

---

## 🏕️ Setup 1: Portable (Camp/Demo)

For testing at camps, events, or anywhere without reliable network.

```
┌─────────────────────────────────────────────────────────────┐
│                    PORTABLE SETUP                           │
│                                                             │
│   GL.iNet Router ──► Ethernet Switch                        │
│        │                   │                                │
│        │                   ├──► MacBook Pro 2012 (server)   │
│        │                   └──► MacBook Air 2013 (backup)   │
│        │                                                    │
│        └──► WiFi ──► Camper phones/tablets/laptops          │
└─────────────────────────────────────────────────────────────┘
```

### Required for Portable Setup:

| Item | Purpose | Est. Price | Recommended |
|------|---------|------------|-------------|
| **GL.iNet Portable Router** | Creates WiFi network + VPN | $30-50 | GL-MT300N-V2 or GL-AXT1800 |
| **5-Port Ethernet Switch** | GL.iNet has only 1 LAN port | $15-18 | TP-Link TL-SG105 |
| **Ethernet Adapters (x2)** | Wired for both MacBooks | $36 | Anker USB 3.0 to Gigabit |
| **Cat6 Cables (short)** | 6-10ft for portable kit | $12-15 | Get 3x for flexibility |
| **USB Flash Drive** | OCLP recovery + ROM transfer | $10 | 16GB+ |
| **Cooling Pads (x2)** | Keep servers cool | $40-60 | Havit or TopMate |
| **Surge Protector** | Protect everything | $15-25 | Portable strip |

**Portable Setup Total: ~$160-210**

---

## 🏠 Setup 2: Home Hosted (End Goal)

Server runs 24/7 at home, campers access via internet.

```
┌─────────────────────────────────────────────────────────────┐
│                    HOME HOSTED SETUP                        │
│                                                             │
│   Home Router ──► MacBook Pro 2012 ──► ngrok/Cloudflare     │
│        │                   │                  │             │
│        │                   └── SurfShark VPN  │             │
│        │                                      │             │
│        └──► MacBook Air 2013 (backup)         ▼             │
│                                          Internet           │
│                                              │              │
│                                              ▼              │
│                                    Campers (anywhere!)      │
└─────────────────────────────────────────────────────────────┘
```

### Required for Home Hosting:

| Item | Purpose | Est. Price | Notes |
|------|---------|------------|-------|
| **Ethernet Adapters (x2)** | Wired for both MacBooks | $36 | Same as portable |
| **Cat6 Cables (longer)** | 25-50ft to reach router | $15-25 | Depends on home layout |
| **Cooling Pads (x2)** | 24/7 operation | $40-60 | Essential for always-on |
| **Surge Protector** | Protect equipment | $15-25 | |
| **UPS Battery Backup** | Keep running during outages | $80-150 | Optional but recommended |
| **ngrok Pro** | Custom domain, more tunnels | $8/month | Or use free tier |

**Home Setup Total: ~$100-150** (plus optional UPS)  
**Already Have:** Router, VPN, MacBooks

---

## 🔀 Items Needed for BOTH Setups

These work for portable AND home:

| Item | Est. Price | Recommended Product |
|------|------------|---------------------|
| **Anker USB 3.0 Ethernet Adapter** (x2) | $36 | [Amazon](https://www.amazon.com/dp/B00NPJP33M) |
| **Laptop Cooling Pads** (x2) | $40-60 | Havit HV-F2056 |
| **USB Flash Drive (32GB)** | $10 | SanDisk or Samsung |
| **Surge Protector** | $15-25 | 6+ outlets |
| **Cat6 Cables (10ft x2)** | $12 | Amazon Basics |

**Core Items Total: ~$115-145**

---

## 🛒 Complete Shopping List

### 🔴 High Priority (Get First)

| Item | Purpose | Est. Price | Link |
|------|---------|------------|------|
| **USB Flash Drive (32GB)** | OCLP recovery | $10 | [Amazon](https://www.amazon.com/s?k=usb+flash+drive+32gb) |
| **Anker Ethernet Adapters (x2)** | Wired server connection | $36 | [Amazon](https://www.amazon.com/dp/B00NPJP33M) |
| **Laptop Cooling Pads (x2)** | Prevent overheating | $50 | [Amazon](https://www.amazon.com/s?k=laptop+cooling+pad) |
| **TP-Link 5-Port Switch** | Connect multiple devices | $15 | [Amazon](https://www.amazon.com/dp/B00A128S24) |

### 🟡 Medium Priority (Portable Setup)

| Item | Purpose | Est. Price | Link |
|------|---------|------------|------|
| **GL.iNet Travel Router** | Portable network + VPN | $30-50 | [Amazon](https://www.amazon.com/s?k=gl.inet+travel+router) |
| **Cat6 Cables (10ft x3)** | Short for portable | $15 | [Amazon](https://www.amazon.com/s?k=cat6+10ft+3+pack) |
| **Surge Protector (portable)** | Protect gear | $20 | [Amazon](https://www.amazon.com/s?k=portable+surge+protector) |

### 🟢 Home Setup Additions

| Item | Purpose | Est. Price | Link |
|------|---------|------------|------|
| **Cat6 Cable (50ft)** | Reach home router | $15 | [Amazon](https://www.amazon.com/s?k=cat6+50ft) |
| **UPS Battery Backup** | Power outage protection | $80-150 | [Amazon](https://www.amazon.com/s?k=ups+battery+backup+600va) |

### 🎮 Xbox RetroArch Setup

| Item | Purpose | Est. Price | Link/Notes |
|------|---------|------------|------------|
| **Microsoft Dev Account** | Enable Dev Mode for RetroArch | $20 (one-time) | Required for sideloading |
| **USB Drives for ROMs (x2)** | ROM storage for each Xbox | $20 | 32GB+ recommended |

### 🎯 Nice to Have

| Item | Purpose | Est. Price |
|------|---------|------------|
| **External SSD (500GB+)** | ROM storage, backups | $50-80 |
| **8BitDo Controllers (x2-4)** | Better gaming | $40-80 |
| **USB-C to Thunderbolt 2** | Mac troubleshooting | $25 |

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

### By Setup Type:

| Setup | What You Get | Estimated Cost |
|-------|--------------|----------------|
| **Core Items** | USB, adapters, cooling pads, switch | ~$115-145 |
| **Portable Ready** | Core + GL.iNet router + short cables | ~$160-210 |
| **Home Hosted** | Core + long cables + UPS | ~$200-300 |
| **Full Everything** | Portable + Home + Xbox + Controllers | ~$400-500 |

### Shopping Priority Order:

| Priority | Items | Cost |
|----------|-------|------|
| 1️⃣ | USB drive + Ethernet adapters | ~$46 |
| 2️⃣ | Cooling pads + Switch | ~$65 |
| 3️⃣ | GL.iNet router + short cables | ~$50 |
| 4️⃣ | Surge protector + longer cables | ~$40 |
| 5️⃣ | UPS + Xbox dev account | ~$100-170 |

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
