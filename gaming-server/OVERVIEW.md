# 🎮 CampPowerUp Retro Gaming Server

## Project Overview

 Here's what we're building for the camp's gaming program.

---

## 🎯 What Is This?

A **self-hosted retro gaming server** that lets campers play classic video games from the 80s, 90s, and 2000s right in their web browser - no downloads or installs needed!

Think of it as our own private "Netflix for retro games" that runs on camp's network.

---

## 🕹️ Games We Can Offer

| Era | Systems | Popular Games |
|-----|---------|---------------|
| **80s** | NES, Arcade | Mario Bros, Pac-Man, Tetris, Contra |
| **90s** | SNES, Genesis, N64, PS1 | Mario Kart, Sonic, GoldenEye, Crash Bandicoot |
| **2000s** | GBA, PS1 | Pokémon, Tony Hawk, Final Fantasy |

**Total: 8+ classic gaming systems**, hundreds of potential games!

---

## ✨ Key Benefits for Camp

### 1. **Zero Setup for Campers**
- Open a web browser → Pick a game → Play
- Works on any computer, tablet, or Chromebook
- No downloads, no installations, no accounts needed

### 2. **Multiplayer Ready**
- Campers can play together on the same screen
- Future: Online multiplayer across camp network

### 3. **Nostalgia + New Experiences**
- Kids discover classics their parents played
- Great for gaming history lessons
- Tournaments and competitions

### 4. **Safe & Controlled**
- We choose which games are available
- No internet required (runs on camp network)
- No ads, no in-app purchases, no surprises

### 5. **Cost Effective**
- All software is free and open-source
- Runs on hardware we already have
- One-time setup, works forever

---

## 🖥️ What We Need

### Hardware (One-Time)
| Item | Purpose | Est. Cost |
|------|---------|-----------|
| Linux Server or PC | Hosts the games | Already have? |
| Raspberry Pi 4 (optional) | Dedicated gaming stations | ~$60 each |
| USB Controllers (optional) | Better than keyboard | ~$15 each |

### Software (Free)
- ✅ Docker (container platform)
- ✅ EmulatorJS (browser-based emulation)
- ✅ Nginx (file server)
- ✅ All open-source, no licensing fees

---

## 📸 What It Looks Like

When campers visit the gaming server, they see:

```
┌─────────────────────────────────────────────────┐
│  🎮 CampPowerUp Game Library                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  [NES]  [SNES]  [Genesis]  [N64]  [PS1]        │
│                                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│  │Mario│ │Sonic│ │Zelda│ │Tetris│ │Kirby│      │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘      │
│                                                 │
│  Click any game to play instantly!              │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Rollout Plan

### Phase 1: Foundation (This PR) ✅
- [x] Server infrastructure
- [x] Browser-based game player
- [x] ROM organization system
- [x] ROM organization script (`scripts/organize_roms.py`)
- [x] Curated homebrew games list (`HOMEBREW_GAMES.md`)
- [ ] Download and add initial games from list

### Phase 2: Client Stations
- [ ] Set up Raspberry Pi gaming stations
- [ ] USB controller support
- [ ] Dedicated screens around camp

### Phase 3: Multiplayer & Social
- [ ] Online multiplayer support
- [ ] Tournament system
- [ ] High score leaderboards
- [ ] Achievement tracking

### Phase 4: Game Streaming
- [ ] Stream newer games (PS2, GameCube, Wii)
- [ ] Low-latency streaming to any device

---

## 💡 Activity Ideas

1. **Retro Game Tournament** - Mario Kart, Street Fighter brackets
2. **Gaming History Day** - Evolution of games from 1980-2010
3. **Speedrun Challenge** - Who can beat Mario fastest?
4. **Cooperative Gaming** - Beat games together as a team
5. **Game Design Intro** - "These old games had 8 colors and 3 buttons..."

---

## ⚖️ Legal Note

We'll only use:
- Games we legally own (backup copies)
- Free homebrew games
- Public domain games
- Open-source games

There are tons of legal free retro games available!

---

## 🤔 Questions?

Let me know what you think! We can adjust the scope based on:
- Budget available
- Timeline for camp
- Which systems/games are priorities

---

**Ready to bring retro gaming to camp! 🕹️**
