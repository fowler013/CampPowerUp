# 🎮 Game Library Management System

This branch adds a comprehensive game library management system to Camp Power-Up, allowing camp organizers to track games owned by campers and manage camp inventory.

## 🚀 New Features

### Game Tracking
- **Camper Game Ownership**: Track which games each camper owns and brings to camp
- **Popularity Analysis**: Visual representation of game popularity among campers
- **Camp Inventory**: Manage camp-owned game copies and availability status
- **Real-time Updates**: Interactive interface to update inventory on the fly

### Dashboard Interface
- **Statistics Overview**: Total games, ownership instances, camp copies, and averages
- **Interactive Table**: Sortable, searchable game library with visual popularity indicators
- **Inventory Management**: Direct editing of camp copies and availability status
- **Export Functionality**: Download game library data as CSV for camp planning

## 📁 Files Added/Modified

### New Files
- `game_library.py`: Core game library processing and database logic
- `templates/game_library.html`: Responsive game library dashboard interface

### Modified Files
- `app.py`: Added game library API endpoints and routes
- `templates/index.html`: Added navigation links to game library

## 🗄️ Database Schema

### `games` Table
```sql
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    normalized_name TEXT NOT NULL,
    platform TEXT DEFAULT 'Nintendo Switch',
    genre TEXT,
    rating TEXT,
    total_owned INTEGER DEFAULT 0,
    camp_copies INTEGER DEFAULT 0,
    availability_status TEXT DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `camper_games` Table
```sql
CREATE TABLE camper_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camper_id INTEGER,
    game_id INTEGER,
    owns_game BOOLEAN DEFAULT 0,
    brings_to_camp BOOLEAN DEFAULT 0,
    skill_level TEXT DEFAULT 'Beginner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games (id)
);
```

## 🌐 API Endpoints

- `GET /game_library` - Game library dashboard page
- `GET /api/game_library/stats` - Get library statistics and game data
- `GET /api/game_library/process` - Process camper data to populate library
- `POST /api/game_library/update` - Update game inventory and availability

## 🎯 Usage

1. **Access the Game Library**: Navigate to the main dashboard and click "🎮 Game Library"
2. **Process Data**: Click "📊 Process Camper Game Data" to extract games from registration data
3. **Manage Inventory**: 
   - Update camp copies using the input fields
   - Change availability status using the dropdown menus
4. **Export Data**: Click "📋 Export Library" to download CSV for planning

## 📊 Sample Data

The system includes sample game data to demonstrate functionality:
- Mario Kart 8 Deluxe (45 campers, 5 camp copies)
- Super Smash Bros Ultimate (38 campers, 3 camp copies)
- Animal Crossing New Horizons (32 campers, 2 camp copies)
- Minecraft (28 campers, 4 camp copies)
- And more...

## 🔮 Future Enhancements

- Integration with registration form for direct game capture
- Automated game recommendation system
- Tournament bracket generation based on popular games
- Integration with Nintendo Switch game library APIs
- Advanced analytics and reporting features

## 🛠️ Technical Notes

- Game names are normalized for consistent matching
- Supports multiple platforms (Nintendo Switch, Multiple, etc.)
- Responsive design works on desktop and mobile
- Real-time updates without page refresh
- Comprehensive error handling and user feedback

This feature significantly enhances camp planning capabilities by providing visibility into camper game preferences and camp resource allocation.
