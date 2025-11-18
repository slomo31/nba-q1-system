# 🏀 NBA Q1 Parlay System - Daily Workflow

## 📋 Quick Reference

**Dashboard URL:** https://nba-q1-system.onrender.com  
**Login:** slomo / parlay2025  
**Win Threshold:** Q1 > 52.5 points

---

## 🌅 MORNING ROUTINE (Get Today's Picks)

### Step 1: Generate Predictions
```bash
cd ~/Documents/nba_q1_system
python parlay_predictor.py
```

### Step 2: Push to Dashboard
```bash
git add predictions/*.csv parlays/*.csv
git commit -m "Today's picks"
git push
```

**⏱️ Time:** 2 minutes  
**Result:** Dashboard updates in 2-3 minutes with today's parlay picks

---

## 🌙 NIGHT ROUTINE (Track Results)

### Step 1: Update Results (After games finish)
```bash
cd ~/Documents/nba_q1_system
python auto_track_results.py
```

### Step 2: Push to Dashboard
```bash
git add predictions/results.csv
git commit -m "Update results"
git push
```

**⏱️ Time:** 2 minutes  
**Result:** Dashboard updates with W/L and performance stats

---

## 📅 WEEKLY MAINTENANCE (Every Sunday)

### Step 1: Update Data (Get new games)
```bash
cd ~/Documents/nba_q1_system
python update_current_season.py
```

### Step 2: Retrain Model
```bash
python train_regression_model.py
```

### Step 3: Push Everything
```bash
git add data/*.csv models/*.pkl
git commit -m "Weekly update - $(date +%Y-%m-%d)"
git push
```

**⏱️ Time:** 5 minutes  
**Result:** Model trained on latest data, dashboard fully updated

---

## 📱 ACCESSING DASHBOARD

**From Any Device:**
1. Go to: https://nba-q1-system.onrender.com
2. Login when prompted
3. View picks, results, and stats

**Add to iPhone Home Screen:**
1. Open Safari → Go to dashboard URL
2. Tap Share button
3. Tap "Add to Home Screen"
4. Now it works like an app!

---

## ⚡ OPTIONAL: Command Aliases

Add these to `~/.zshrc` for one-command workflows:
```bash
# Edit your .zshrc
nano ~/.zshrc

# Add these lines:
alias picks="cd ~/Documents/nba_q1_system && python parlay_predictor.py && git add predictions/*.csv parlays/*.csv && git commit -m 'Today picks' && git push"

alias results="cd ~/Documents/nba_q1_system && python auto_track_results.py && git add predictions/results.csv && git commit -m 'Update results' && git push"

alias weekly="cd ~/Documents/nba_q1_system && python update_current_season.py && python train_regression_model.py && git add data/*.csv models/*.pkl && git commit -m 'Weekly update' && git push"

# Save and reload
source ~/.zshrc
```

**Then just type:**
- `picks` → Get today's picks and update dashboard
- `results` → Track results and update dashboard  
- `weekly` → Full weekly update

---

## 📊 WHAT THE DASHBOARD SHOWS

### Stats Cards
- Total picks tracked
- Win rate % (W-L record)
- Profit in units
- ROI %

### Today's Parlay
- Top 2-3 picks for parlay
- Predicted Q1 totals
- Team matchups

### All Games Today
- Every game's Q1 prediction
- Scroll through all options

### Results by Date
- Last 5 days of picks
- Color coded: Green = WIN, Red = LOSS
- Actual Q1 scores vs predictions

---

## ⏱️ TIME COMMITMENT

| Task | Frequency | Time |
|------|-----------|------|
| Morning picks | Daily | 2 min |
| Night results | Daily | 2 min |
| Weekly update | Weekly | 5 min |
| **Total per week** | | **~30 min** |

---

## 🎯 SYSTEM PERFORMANCE (As of Nov 16, 2025)

- **Total Picks:** 9
- **Win Rate:** 89% (8-1)
- **Profit:** +6.3 units
- **ROI:** +70%

---

## 🔧 TROUBLESHOOTING

### Dashboard not updating?
- Wait 2-3 minutes after push
- Check Render dashboard for deploy status
- Clear browser cache and refresh

### Render sleeping?
- Free tier sleeps after 15 min inactivity
- First load takes ~30 seconds to wake up
- Subsequent loads are instant

### Can't access dashboard?
- Check you're using correct password
- Try incognito/private browsing mode
- Verify URL: https://nba-q1-system.onrender.com

### Script errors?
```bash
# Make sure you're in the right directory
cd ~/Documents/nba_q1_system

# Activate virtual environment
source venv/bin/activate

# Check Python version
python --version  # Should be 3.12+
```

---

## 📞 IMPORTANT FILES

| File | Purpose |
|------|---------|
| `parlay_predictor.py` | Generate daily picks |
| `auto_track_results.py` | Track game results |
| `update_current_season.py` | Get new games (incremental) |
| `train_regression_model.py` | Retrain ML model |
| `dashboard_parlay.py` | Web dashboard code |
| `data/historical_games.csv` | All game data |
| `predictions/results.csv` | Tracked results |
| `models/*.pkl` | Trained ML models |

---

## �� FUTURE AUTOMATION (Coming Soon)

Once system is proven (2-3 weeks), we'll automate:
- ✅ Auto-generate picks every morning at 9am
- ✅ Auto-track results every night at midnight
- ✅ No manual commands needed
- ✅ Dashboard always up-to-date

---

## �� BETTING STRATEGY

**Recommended:**
- Use 2-3 leg parlays (not individual bets)
- 1 unit per parlay ($10-50 depending on bankroll)
- Only bet games with high consistency scores
- Track everything through the system

**DO NOT:**
- Chase losses
- Increase bet size after losses
- Bet games without running predictions first
- Ignore the data/gut feeling bets

---

## 📝 NOTES

- Dashboard auto-refreshes every 60 seconds
- Render free tier: Unlimited hours, but sleeps after 15 min
- All times in your local timezone
- System uses DraftKings odds exclusively
- Q1 = First Quarter only (not cumulative)

---

**Last Updated:** November 16, 2025  
**System Status:** ✅ Operational  
**Current Season:** 2025-26 NBA
