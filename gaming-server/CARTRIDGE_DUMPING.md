# 🎮 Cartridge Dumping Guide

How to legally create ROM backups from cartridges you own for the CampPowerUp gaming server.

---

## 📋 What You Need

### Hardware

Pick ONE dumper based on your systems:

| Device | Price | Systems | Best For |
|--------|-------|---------|----------|
| **[Epilogue GB Operator](https://www.epilogue.co/)** | ~$50 | GB, GBC, GBA | Game Boy family only |
| **[Retrode 2](https://www.retrode.com/)** | ~$85 | NES, SNES, Genesis, N64, GB | Multi-system collection |
| **[Open Source Cartridge Reader](https://github.com/sanni/cartreader)** | ~$50 DIY | Most systems | Tinkerers, best value |
| **[INLretro Dumper](https://www.infiniteneslives.com/)** | ~$60 | NES, SNES, GB | NES focus |
| **[Submodule](https://submodule.co/)** | ~$70 | GB, GBC, GBA | Alternative to Epilogue |

**Recommendation:** Start with **Epilogue GB Operator** ($50) for Pokémon/Game Boy games, then add **Retrode 2** ($85) if you expand to SNES/Genesis/N64.

### Software

Most dumpers include their own software. You'll also want:
- File manager to organize ROMs
- Our `organize_roms.py` script

---

## 🔧 Step-by-Step: Epilogue GB Operator

The most common choice for Pokémon games.

### 1. Initial Setup

```bash
# Download Epilogue software from https://www.epilogue.co/downloads
# Install on Mac/Windows/Linux
```

### 2. Connect & Insert Cartridge

1. Plug GB Operator into USB port
2. Insert your cartridge (label facing you)
3. Open Epilogue software
4. Wait for cartridge to be detected

### 3. Dump the ROM

1. Click **"Backup Game"** or **"Read ROM"**
2. Choose save location (e.g., `~/Downloads/roms/`)
3. Wait for dump to complete (30 seconds to 2 minutes)
4. ROM file appears as `GameName.gb`, `.gbc`, or `.gba`

### 4. Backup Save File (Important!)

If the cartridge has a save file you want to keep:
1. Click **"Backup Save"**
2. Save the `.sav` file alongside the ROM
3. This preserves any existing game progress

### 5. Add to Gaming Server

```bash
# Navigate to gaming-server directory
cd gaming-server

# Option A: Use the organize script
python scripts/organize_roms.py ~/Downloads/roms/

# Option B: Manual copy
cp ~/Downloads/roms/*.gb roms/gb/
cp ~/Downloads/roms/*.gbc roms/gb/
cp ~/Downloads/roms/*.gba roms/gba/
```

### 6. Verify

```bash
# Check the files are in place
python scripts/organize_roms.py --report

# Restart the server to pick up new games
docker-compose down && docker-compose up -d
```

---

## 🔧 Step-by-Step: Retrode 2

Best for multi-system collections (SNES, Genesis, N64).

### 1. Setup

The Retrode appears as a USB mass storage device - no special software needed!

### 2. Connect & Insert

1. Plug Retrode into USB port
2. Insert cartridge into appropriate slot
3. Retrode mounts as a drive (like a USB stick)

### 3. Copy ROM

1. Open the Retrode drive in Finder/Explorer
2. You'll see the ROM file directly (e.g., `SONIC2.BIN`)
3. Copy to your downloads folder
4. **Important:** Safely eject before removing cartridge

### 4. Add to Gaming Server

```bash
cd gaming-server

# Use organize script (recommended)
python scripts/organize_roms.py ~/Downloads/retrode-dumps/

# Or manual:
cp ~/Downloads/*.sfc roms/snes/
cp ~/Downloads/*.md roms/genesis/
cp ~/Downloads/*.n64 roms/n64/
```

---

## 🔧 Step-by-Step: Open Source Cart Reader (Sanni)

Best value, requires some assembly.

### 1. Build/Buy

- Buy pre-assembled from various sellers (~$50-80)
- Or build yourself from [GitHub instructions](https://github.com/sanni/cartreader)

### 2. Setup

1. Insert SD card into reader
2. Power via USB
3. Use the on-device menu or connect to PC

### 3. Dump

1. Insert cartridge
2. Select system type on LCD menu
3. Choose "Read ROM"
4. ROM saves to SD card

### 4. Transfer

```bash
# Copy from SD card
cp /Volumes/SDCARD/*.nes ~/Downloads/roms/
cp /Volumes/SDCARD/*.sfc ~/Downloads/roms/

# Then organize
cd gaming-server
python scripts/organize_roms.py ~/Downloads/roms/
```

---

## 📁 File Naming Best Practices

### Clean Up Names

ROMs dump with various naming conventions. For consistency:

```
# Bad (but functional)
POKEMON_YELLOW_USA.gbc
Pokemon Yellow (U) [C][!].gbc

# Good (clean, readable)
Pokemon Yellow.gbc
Super Mario World.sfc
Sonic the Hedgehog 2.md
```

### Renaming Script

```bash
# Quick rename examples (run from roms directory)

# Remove region tags
rename 's/ \(U\)//g' *.gb *.gbc *.gba *.sfc *.md
rename 's/ \(USA\)//g' *.gb *.gbc *.gba *.sfc *.md

# Remove [!] verified dumps tag
rename 's/ \[\!\]//g' *.gb *.gbc *.gba *.sfc *.md
```

Or just rename manually - you won't have that many files.

---

## 🎮 System-Specific Notes

### Game Boy / GBC / GBA
- **Epilogue GB Operator** is the easiest option
- GBA games are larger (8-32MB), take longer to dump
- Some reproduction carts won't dump correctly (that's how you know they're fake!)

### NES
- Many cartridges use different "mappers"
- Retrode 2 or INLretro handle most common ones
- A few rare games need specialized equipment

### SNES
- Straightforward with Retrode 2
- Some games have enhancement chips (SuperFX, SA-1)
- Most work fine, a few need specific dumper support

### Genesis / Mega Drive
- Very straightforward
- Retrode 2 handles these perfectly
- Sonic games dump in seconds

### N64
- Larger files (8-64MB)
- Retrode 2 with N64 adapter works well
- Takes a few minutes per game

### PlayStation
- **Different process** - you need to rip CDs, not cartridges
- Use **ImgBurn** (Windows) or **Disc Image Mounter** (Mac)
- Create `.bin/.cue` or `.iso` files
- Convert to `.chd` format to save space (optional)

---

## 📂 Complete Workflow Example

Let's say you bought: Pokémon Yellow, Sonic 2, and Super Mario World.

```bash
# 1. Dump with your device(s)
#    - Pokémon Yellow → Epilogue → pokemon_yellow.gbc
#    - Sonic 2 → Retrode → sonic2.md  
#    - SMW → Retrode → smw.sfc

# 2. Collect dumps in one folder
mkdir ~/camp-roms
mv ~/Downloads/*.gbc ~/camp-roms/
mv /Volumes/RETRODE/*.md ~/camp-roms/
mv /Volumes/RETRODE/*.sfc ~/camp-roms/

# 3. Organize into gaming server
cd ~/Documents/GitHub/CampPowerUp/gaming-server
python scripts/organize_roms.py ~/camp-roms/

# Output:
#   MOVE: pokemon_yellow.gbc -> roms/gb/
#   MOVE: sonic2.md -> roms/genesis/
#   MOVE: smw.sfc -> roms/snes/
#   Total organized: 3

# 4. Verify
python scripts/organize_roms.py --report

# 5. Restart server
docker-compose restart emulatorjs

# 6. Test at http://localhost:3000
#    Your games should appear!
```

---

## ❓ Troubleshooting

### "Cartridge not detected"
- Clean cartridge contacts with isopropyl alcohol
- Try reinserting
- Check USB connection

### "ROM won't play in EmulatorJS"
- Verify file extension is correct
- Some games need BIOS files (GBA, PSX)
- Try a different core/emulator setting

### "Dumped file is wrong size"
- Cartridge might be fake/reproduction
- Try dumping again
- Compare hash to known good dumps (google "[game] ROM hash")

### "Save file not working"
- Make sure you dumped the `.sav` file too
- Place `.sav` in same folder as ROM with same name
- EmulatorJS uses browser storage by default

---

## ⚖️ Legal Reminder

This process is legal when:
- ✅ You own the physical cartridge
- ✅ You're creating a personal backup
- ✅ The backup is for your own use (camp = your organization)
- ✅ You're not distributing the ROMs

This is NOT legal:
- ❌ Downloading ROMs for games you don't own
- ❌ Sharing your dumps publicly
- ❌ Using someone else's dump instead of making your own

**Keep your cartridges!** They're your proof of ownership.

---

## 🛒 Quick Shopping List

### Minimum Setup (Game Boy games)
| Item | Price |
|------|-------|
| Epilogue GB Operator | $50 |
| **Total** | **$50** |

### Recommended Setup (Multi-system)
| Item | Price |
|------|-------|
| Epilogue GB Operator | $50 |
| Retrode 2 | $85 |
| **Total** | **$135** |

### Budget Setup (DIY)
| Item | Price |
|------|-------|
| Open Source Cart Reader (Sanni) kit | $50 |
| Soldering iron (if needed) | $20 |
| **Total** | **$70** |

---

## 📚 Additional Resources

- [Epilogue Documentation](https://support.epilogue.co/)
- [Retrode Wiki](https://www.retrode.com/wiki/)
- [Sanni Cart Reader GitHub](https://github.com/sanni/cartreader)
- [No-Intro DAT files](https://no-intro.org/) - verify your dumps
- [Redump](http://redump.org/) - disc verification
