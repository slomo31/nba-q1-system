#!/usr/bin/env python3
"""Track ALL predictions - WIN if Q1 > 52.5"""
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
import time

Q1_THRESHOLD = 52.5  # Win if actual Q1 goes OVER this

print("="*70)
print("🤖 AUTOMATIC RESULTS TRACKER")
print(f"📊 Win = Q1 Total > {Q1_THRESHOLD}")
print("="*70)

# Load today's predictions
today_str = datetime.now().strftime('%Y%m%d')
pred_file = f"predictions/predictions_{today_str}.csv"

if not os.path.exists(pred_file):
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    pred_file = f"predictions/predictions_{yesterday_str}.csv"
    
if not os.path.exists(pred_file):
    print("\n❌ No recent predictions found")
    exit(1)

pred_df = pd.read_csv(pred_file)

if len(pred_df) == 0:
    print("\n❌ No predictions to track")
    exit(0)

print(f"\n📋 Tracking {len(pred_df)} predictions from {pred_file}")

def get_actual_q1_espn(away_team, home_team, game_date):
    """Get actual Q1 total from ESPN API"""
    try:
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%Y%m%d')
        
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        params = {'dates': formatted_date}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'events' in data:
            for event in data['events']:
                competitions = event.get('competitions', [])
                if competitions:
                    comp = competitions[0]
                    competitors = comp.get('competitors', [])
                    
                    if len(competitors) >= 2:
                        home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                        away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                        
                        if home and away:
                            home_abbr = home.get('team', {}).get('abbreviation', '')
                            away_abbr = away.get('team', {}).get('abbreviation', '')
                            
                            if (away_abbr in away_team or away_team in away_abbr) and \
                               (home_abbr in home_team or home_team in home_abbr):
                                
                                away_ls = away.get('linescores', [])
                                home_ls = home.get('linescores', [])
                                
                                if away_ls and home_ls:
                                    away_q1 = int(away_ls[0].get('value', 0))
                                    home_q1 = int(home_ls[0].get('value', 0))
                                    return away_q1 + home_q1
        
        return None
        
    except Exception as e:
        return None

# Load or create results file
results_file = 'predictions/results.csv'
if os.path.exists(results_file):
    results_df = pd.read_csv(results_file)
else:
    results_df = pd.DataFrame()

print(f"\n{'='*70}")
print(f"FETCHING RESULTS - WIN = Q1 > {Q1_THRESHOLD}")
print(f"{'='*70}\n")

updated_count = 0

for idx, pred in pred_df.iterrows():
    # Check if already tracked
    if not results_df.empty:
        already_tracked = ((results_df['away_team'] == pred['away_team']) & 
                          (results_df['home_team'] == pred['home_team']) & 
                          (results_df['date'] == pred['date']) &
                          (results_df['result'].notna())).any()
        if already_tracked:
            print(f"✅ {pred['away_team']} @ {pred['home_team']} - Already tracked")
            continue
    
    print(f"🏀 {pred['away_team']} @ {pred['home_team']}")
    print(f"   Prediction: {pred['prediction']:.1f}")
    
    # Get actual Q1
    actual_q1 = get_actual_q1_espn(pred['away_team'], pred['home_team'], pred['date'])
    
    if actual_q1 is None:
        print(f"   ⏳ Game not finished yet\n")
        continue
    
    print(f"   Actual Q1: {actual_q1}")
    
    # WIN/LOSS based on 52.5 threshold
    won = actual_q1 > Q1_THRESHOLD
    result = 'WIN' if won else 'LOSS'
    
    # Margin from threshold
    margin = actual_q1 - Q1_THRESHOLD
    
    # Add to results
    result_row = pred.to_dict()
    result_row['actual_q1'] = actual_q1
    result_row['result'] = result
    result_row['margin'] = margin
    result_row['threshold'] = Q1_THRESHOLD
    
    results_df = pd.concat([results_df, pd.DataFrame([result_row])], ignore_index=True)
    
    status = "✅ WIN" if won else "❌ LOSS"
    parlay_marker = "🎯" if pred.get('play', False) else "📊"
    print(f"   {status} {parlay_marker} (Actual: {actual_q1} vs {Q1_THRESHOLD}, Margin: {margin:+.1f})\n")
    
    updated_count += 1
    time.sleep(1)

# Save results
if updated_count > 0:
    results_df.to_csv(results_file, index=False)
    print(f"💾 Saved {updated_count} new results\n")
else:
    print(f"ℹ️  No new results\n")

# Show stats
print(f"{'='*70}")
print(f"📊 PERFORMANCE SUMMARY (Q1 > {Q1_THRESHOLD})")
print(f"{'='*70}\n")

tracked = results_df[results_df['result'].notna()]

if len(tracked) == 0:
    print("No completed games yet")
else:
    # Overall stats
    all_games = tracked[tracked['result'].isin(['WIN', 'LOSS'])]
    if len(all_games) > 0:
        all_wins = len(all_games[all_games['result'] == 'WIN'])
        all_wr = all_wins / len(all_games) * 100
        print(f"📈 ALL GAMES: {all_wins}-{len(all_games)-all_wins} ({all_wr:.1f}%)")
        print(f"   Average Q1: {all_games['actual_q1'].mean():.1f} pts")
    
    # Parlay picks performance
    parlay_picks = tracked[tracked.get('play', False) == True]
    if len(parlay_picks) > 0:
        p_wins = len(parlay_picks[parlay_picks['result'] == 'WIN'])
        p_losses = len(parlay_picks) - p_wins
        p_wr = p_wins / len(parlay_picks) * 100
        
        profit = (p_wins * 0.91) - p_losses
        roi = (profit / len(parlay_picks)) * 100
        
        print(f"\n🎯 PARLAY PICKS:")
        print(f"   Record: {p_wins}-{p_losses} ({p_wr:.1f}%)")
        print(f"   Profit: {profit:+.2f} units")
        print(f"   ROI: {roi:+.1f}%")
        print(f"   Avg Q1: {parlay_picks['actual_q1'].mean():.1f} pts")
    
    # Recent results
    print(f"\n📋 Last 5 Results:")
    for _, game in tracked.tail(5).iterrows():
        status = "✅" if game['result'] == 'WIN' else "❌"
        parlay = "🎯" if game.get('play', False) else "📊"
        print(f"   {status} {parlay} {game['away_team']}@{game['home_team']}: "
              f"Pred {game['prediction']:.1f} | Actual {game.get('actual_q1', 0):.0f}")

print(f"\n{'='*70}")
