# CampPowerUp Retro Gaming Server

A self-hosted retro gaming server for camp, providing browser-based emulation, ROM management, and save file synchronization.

## 🎮 Features

- **EmulatorJS** - Play classic games directly in your web browser
- **ROM Server** - Centralized storage and distribution of game files
- **Save Sync** - Automatic save file synchronization across devices via Syncthing

## 📋 Supported Systems

| System | Extensions | Notes |
|--------|------------|-------|
| NES | `.nes` | Nintendo Entertainment System |
| SNES | `.sfc`, `.smc` | Super Nintendo |
| Genesis/Mega Drive | `.md`, `.gen` | Sega Genesis |
| Game Boy | `.gb`, `.gbc` | Original & Color |
| Game Boy Advance | `.gba` | Requires BIOS |
| Nintendo 64 | `.n64`, `.z64`, `.v64` | |
| PlayStation | `.bin/.cue`, `.iso`, `.chd` | Requires BIOS |
| Arcade | `.zip` | MAME ROMs |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Linux server (Ubuntu/Debian recommended) or Windows with WSL2

### 1. Start the Server

```bash
cd gaming-server
docker-compose up -d
```

### 2. Add Your ROMs

Copy ROM files into the appropriate subdirectories:

```
gaming-server/
├── roms/
│   ├── nes/          # NES games (.nes)
│   ├── snes/         # SNES games (.sfc, .smc)
│   ├── genesis/      # Genesis games (.md, .gen)
│   ├── n64/          # N64 games (.n64, .z64)
│   ├── psx/          # PlayStation games (.bin/.cue, .chd)
│   ├── gba/          # GBA games (.gba)
│   ├── gb/           # Game Boy games (.gb, .gbc)
│   └── arcade/       # MAME arcade ROMs (.zip)
└── bios/
    └── psx/          # PlayStation BIOS (scph1001.bin, etc.)
```

### 3. Access the Services

| Service | URL | Description |
|---------|-----|-------------|
| EmulatorJS Player | http://localhost:3000 | Play games in browser |
| EmulatorJS Manager | http://localhost:8080 | Manage ROM library |
| ROM Server | http://localhost:8888 | Browse/download ROMs |
| Save Sync (Syncthing) | http://localhost:8384 | Configure save sync |

## 🎯 Usage at Camp

### For Campers

1. Open a web browser and go to `http://[server-ip]:3000`
2. Browse the game library
3. Click a game to play
4. Use keyboard or USB controller

### Controller Mapping (EmulatorJS)

| Action | Keyboard | Controller |
|--------|----------|------------|
| D-Pad | Arrow Keys | D-Pad/Left Stick |
| A Button | X | A |
| B Button | Z | B |
| Start | Enter | Start |
| Select | Shift | Select |

### For Raspberry Pi Stations

Pi clients can download ROMs directly from the ROM server:

```bash
# Example: Download all NES ROMs
wget -r -np http://[server-ip]:8888/roms/nes/
```

Or configure RetroArch to use network paths.

## 🔧 Configuration

### Environment Variables

Edit the `docker-compose.yml` to customize:

```yaml
environment:
  - TZ=America/New_York     # Your timezone
  - PUID=1000               # User ID for file permissions
  - PGID=1000               # Group ID for file permissions
```

### Adding BIOS Files

Some systems require BIOS files for emulation:

**PlayStation:**
- Place `scph1001.bin` (or similar) in `bios/psx/`

**Game Boy Advance:**
- Place `gba_bios.bin` in `bios/gba/`

### Save File Location

Save files are stored in:
- EmulatorJS: Browser local storage (per-device)
- Syncthing: `saves/` directory (synced across devices)

## 🛠️ Maintenance

### View Logs

```bash
docker-compose logs -f emulatorjs
docker-compose logs -f rom-server
docker-compose logs -f save-sync
```

### Stop Services

```bash
docker-compose down
```

### Update Containers

```bash
docker-compose pull
docker-compose up -d
```

### Backup Saves

```bash
# Backup all save files
tar -czvf saves-backup-$(date +%Y%m%d).tar.gz saves/
```

## 📁 Directory Structure

```
gaming-server/
├── docker-compose.yml      # Main orchestration file
├── README.md               # This file
├── rom-server/
│   ├── nginx.conf          # Nginx configuration
│   └── index.html          # ROM server landing page
├── emulatorjs/
│   └── config/             # EmulatorJS configuration (auto-created)
├── save-sync/
│   └── config/             # Syncthing configuration (auto-created)
├── roms/                   # ROM files organized by system
│   ├── nes/
│   ├── snes/
│   ├── genesis/
│   ├── n64/
│   ├── psx/
│   ├── gba/
│   ├── gb/
│   └── arcade/
├── bios/                   # System BIOS files
│   └── psx/
└── saves/                  # Synchronized save files
```

## ⚖️ Legal Notice

**Important:** Only use ROMs for games you legally own. This server is intended for:
- Backup copies of games you own
- Homebrew games
- Public domain games
- Games with appropriate licensing

### 📚 Documentation

| Guide | Description |
|-------|-------------|
| **[HOMEBREW_GAMES.md](HOMEBREW_GAMES.md)** | Curated list of free, legal homebrew games + recommended commercial games to purchase |
| **[CARTRIDGE_DUMPING.md](CARTRIDGE_DUMPING.md)** | How to legally dump cartridges you own using devices like Epilogue or Retrode |
| **[OVERVIEW.md](OVERVIEW.md)** | Non-technical overview for stakeholders |

### Resources
- [Homebrew Hub](https://hh.gbdev.io/) - Game Boy homebrew
- [PDRoms](https://pdroms.de/) - Public domain ROMs
- [itch.io](https://itch.io/games/tag-retro) - Indie retro games

## 🔮 Future Enhancements

- [ ] RetroArch Netplay relay server for multiplayer
- [ ] Moonlight/Sunshine for game streaming
- [ ] User authentication and profiles
- [ ] High score leaderboards
- [ ] Tournament system

---

Part of the [CampPowerUp](../) project.
