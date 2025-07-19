# 🏕️ Camp Power-Up Dashboard

A comprehensive data management and visualization system for Camp Power-Up, designed to analyze camper registration data and provide insights for camp planning.

## 📊 Features

- **Clean Data Processing**: Automatically removes duplicates and standardizes messy CSV data
- **Interactive Dashboard**: Beautiful web-based dashboard with charts and statistics
- **Game Analytics**: Analyzes favorite games and gaming behavior
- **Special Needs Tracking**: Highlights campers with allergies and sensory issues
- **Real-time Updates**: Live data processing and visualization

## 🎮 Key Insights

The dashboard provides insights into:
- Age and grade distribution
- Returning vs new campers
- Most popular games (Mario, Fortnite, Minecraft, etc.)
- Nintendo Switch ownership
- Special dietary and sensory considerations
- Gaming behavior and social skills

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CampPowerUp
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install flask pandas
   ```

4. **Add your data**
   - Place your CSV file in the `data/` folder
   - Update the `CSV_FILE_PATH` in `app.py` if needed
   - A `sample_data.csv` is provided for testing

5. **Run the application**
   ```bash
   python app.py
   ```

6. **View the dashboard**
   Open your browser to `http://127.0.0.1:5000`

## 📁 Project Structure

```
CampPowerUp/
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Dashboard HTML template
├── data/
│   └── *.csv          # CSV data files (not tracked in git)
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js
- **Data Processing**: Pandas
- **Database**: SQLite

## 📈 Statistics Overview

Current dataset provides insights on:
- 138 total campers (after deduplication)
- 65 returning campers (47% return rate)
- 14 campers with allergies
- 5 campers with sensory needs
- 97 campers bringing Nintendo Switch (70%)

## 🎯 Popular Games

Top games mentioned by campers:
1. Mario (15 mentions)
2. Fortnite (14 mentions) 
3. Minecraft (12 mentions)
4. Roblox (8 mentions)
5. Zelda (6 mentions)

## 🔧 Customization

The system is designed to be flexible:
- Modify game detection in `app.py` to track different games
- Update the HTML template for different styling
- Add new API endpoints for additional data analysis
- Extend the CSV processing for different data formats

## 📝 Data Privacy

This system processes camp registration data. Ensure you:
- Follow local data protection regulations
- Obtain proper consent for data processing
- Keep sensitive data secure
- Don't commit actual registration data to version control

## 🤝 Contributing

This is a camp management tool. Feel free to:
- Report issues
- Suggest improvements
- Add new features
- Improve documentation

## 📄 License

This project is for educational and camp management purposes.

---

**Built for Camp Power-Up 2025** 🎮✨
