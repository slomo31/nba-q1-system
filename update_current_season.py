#!/usr/bin/env python3
"""Incrementally update with only NEW games since last scrape"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import os

print("="*70)
print("📊 INCREMENTAL DATA UPDATE - 2025-26 SEASON")
print("Only scrapes NEW games since last update")
print("="*70)

# Load existing data
data_file = 'data/historical_games.csv'

if os.path.exists(data_file):
    existing_df = pd.read_csv(data_file)
    existing_df['date'] = pd.to_datetime(existing_df['date'])
    
    # Get last game date
    last_date = existing_df['date'].max()
    print(f"\n✅ Existing data: {len(existing_df)} games")
    print(f"📅 Last game: {last_date.strftime('%Y-%m-%d')}")
    
    # Start scraping from day AFTER last game
    start_date = last_date + timedelta(days=1)
    print(f"🔍 Scraping from: {start_date.strftime('%Y-%m-%d')} to today")
else:
    print("\n⚠️  No existing data found - will scrape full season")
    existing_df = pd.DataFrame()
    start_date = datetime(2025, 10, 22)  # 2025-26 season start

# Team name standardization
TEAM_MAP = {
    'ATL': 'ATL', 'BOS': 'BOS', 'BKN': 'BKN', 'CHA': 'CHA', 'CHI': 'CHI', 'CLE': 'CLE',
    'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GSW': 'GSW', 'GS': 'GSW', 'HOU': 'HOU',
    'IND': 'IND', 'LAC': 'LAC', 'LAL': 'LAL', 'MEM': 'MEM', 'MIA': 'MIA', 'MIL': 'MIL',
    'MIN': 'MIN', 'NOP': 'NOP', 'NO': 'NOP', 'NYK': 'NYK', 'NY': 'NYK', 'OKC': 'OKC',
    'ORL': 'ORL', 'PHI': 'PHI', 'PHX': 'PHX', 'POR': 'POR', 'SAC': 'SAC', 'SAS': 'SAS',
    'SA': 'SAS', 'TOR': 'TOR', 'UTA': 'UTA', 'WAS': 'WAS'
}

# Use ESPN API
def get_games_from_espn(start_date):
    """Get games from ESPN API"""
    new_games = []
    
    current = start_date
    today = datetime.now()
    
    print(f"\n📥 Using ESPN API for games from {start_date.strftime('%Y-%m-%d')} to today...")
    
    # Check each day
    while current <= today:
        date_str = current.strftime('%Y%m%d')
        
        print(f"\n📆 Checking {current.strftime('%Y-%m-%d')}...")
        
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            params = {'dates': date_str}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'events' not in data or len(data['events']) == 0:
                print(f"   No games found")
                current += timedelta(days=1)
                continue
            
            for event in data['events']:
                # Check if game is completed
                status = event.get('status', {}).get('type', {}).get('completed', False)
                if not status:
                    print(f"   ⏭️  Game not completed yet")
                    continue
                
                competitions = event.get('competitions', [])
                if not competitions:
                    continue
                    
                comp = competitions[0]
                competitors = comp.get('competitors', [])
                
                if len(competitors) < 2:
                    continue
                
                # Get teams
                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                
                if not home or not away:
                    continue
                
                # Get team names and scores
                home_team = home.get('team', {}).get('abbreviation', '')
                away_team = away.get('team', {}).get('abbreviation', '')
                home_score = int(home.get('score', 0))
                away_score = int(away.get('score', 0))
                
                # Get Q1 scores from linescores
                away_ls = away.get('linescores', [])
                home_ls = home.get('linescores', [])
                
                if not away_ls or not home_ls:
                    print(f"   ⚠️  No Q1 data for {away_team} @ {home_team}")
                    continue
                
                away_q1 = int(away_ls[0].get('value', 0))
                home_q1 = int(home_ls[0].get('value', 0))
                
                # Standardize team names
                away_team_std = TEAM_MAP.get(away_team, away_team)
                home_team_std = TEAM_MAP.get(home_team, home_team)
                
                new_games.append({
                    'date': current.strftime('%Y-%m-%d'),  # Keep as string
                    'away_team': away_team_std,
                    'away_score': away_score,
                    'away_q1': away_q1,
                    'home_team': home_team_std,
                    'home_score': home_score,
                    'home_q1': home_q1,
                    'q1_total': away_q1 + home_q1,
                    'total_score': away_score + home_score
                })
                
                print(f"   ✅ {away_team_std} @ {home_team_std}: Q1 = {away_q1 + home_q1}")
            
            time.sleep(1)  # Be nice to API
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        current += timedelta(days=1)
    
    return new_games

# Scrape new games
new_games = get_games_from_espn(start_date)

if len(new_games) == 0:
    print("\n⚠️  No new games found!")
    print(f"   Current data: {len(existing_df)} games through {existing_df['date'].max() if len(existing_df) > 0 else 'N/A'}")
else:
    print(f"\n{'='*70}")
    print(f"📊 ADDING {len(new_games)} NEW GAMES")
    print(f"{'='*70}")
    
    # Convert to DataFrame
    new_df = pd.DataFrame(new_games)
    
    # Combine with existing data
    if len(existing_df) > 0:
        # Convert existing dates back to string for consistency
        existing_df['date'] = existing_df['date'].dt.strftime('%Y-%m-%d')
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['date', 'away_team', 'home_team'], keep='last')
    
    # Sort by date (string sorting works for YYYY-MM-DD format)
    combined_df = combined_df.sort_values('date')
    
    # Save
    combined_df.to_csv(data_file, index=False)
    
    print(f"\n✅ SUCCESS!")
    print(f"   Previous: {len(existing_df)} games")
    print(f"   Added: {len(new_games)} games")
    print(f"   Total: {len(combined_df)} games")
    print(f"   Latest: {combined_df['date'].max()}")
    print(f"\n💾 Saved to: {data_file}")

print("\n" + "="*70)
print("✅ DATA UPDATE COMPLETE!")
print("\nNext steps:")
print("   1. python train_regression_model.py  (retrain with new data)")
print("   2. python parlay_predictor.py        (get today's picks)")
print("="*70)
