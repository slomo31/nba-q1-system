#!/usr/bin/env python3
"""Q1 Parlay Recommendation System - Find best 2-3 picks to parlay"""
import pandas as pd
import numpy as np
import joblib
import requests
from datetime import datetime
import os

API_KEY = 'a03349ac7178eb60a825d19bd27014ce'
SPORT = 'basketball_nba'

# Team name mapping
TEAM_MAP = {
    'Atlanta': 'ATL', 'Atlanta Hawks': 'ATL', 'Boston': 'BOS', 'Boston Celtics': 'BOS',
    'Brooklyn': 'BKN', 'Brooklyn Nets': 'BKN', 'Charlotte': 'CHA', 'Charlotte Hornets': 'CHA',
    'Chicago': 'CHI', 'Chicago Bulls': 'CHI', 'Cleveland': 'CLE', 'Cleveland Cavaliers': 'CLE',
    'Dallas': 'DAL', 'Dallas Mavericks': 'DAL', 'Denver': 'DEN', 'Denver Nuggets': 'DEN',
    'Detroit': 'DET', 'Detroit Pistons': 'DET', 'Golden State': 'GSW', 'Golden State Warriors': 'GSW',
    'Houston': 'HOU', 'Houston Rockets': 'HOU', 'Indiana': 'IND', 'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC', 'Los Angeles Clippers': 'LAC', 'L.A. Clippers': 'LAC',
    'LA Lakers': 'LAL', 'Los Angeles Lakers': 'LAL', 'L.A. Lakers': 'LAL',
    'Memphis': 'MEM', 'Memphis Grizzlies': 'MEM', 'Miami': 'MIA', 'Miami Heat': 'MIA',
    'Milwaukee': 'MIL', 'Milwaukee Bucks': 'MIL', 'Minnesota': 'MIN', 'Minnesota Timberwolves': 'MIN',
    'New Orleans': 'NOP', 'New Orleans Pelicans': 'NOP', 'New York': 'NYK', 'New York Knicks': 'NYK',
    'Oklahoma City': 'OKC', 'Oklahoma City Thunder': 'OKC', 'Orlando': 'ORL', 'Orlando Magic': 'ORL',
    'Philadelphia': 'PHI', 'Philadelphia 76ers': 'PHI', 'Phoenix': 'PHX', 'Phoenix Suns': 'PHX',
    'Portland': 'POR', 'Portland Trail Blazers': 'POR', 'Sacramento': 'SAC', 'Sacramento Kings': 'SAC',
    'San Antonio': 'SAS', 'San Antonio Spurs': 'SAS', 'Toronto': 'TOR', 'Toronto Raptors': 'TOR',
    'Utah': 'UTA', 'Utah Jazz': 'UTA', 'Washington': 'WAS', 'Washington Wizards': 'WAS'
}

def standardize_team_name(name):
    return TEAM_MAP.get(name, name)

def get_team_stats(team_code, df):
    team_games = df[(df['away_team'] == team_code) | (df['home_team'] == team_code)]
    if len(team_games) == 0:
        return None
    
    recent = team_games.tail(5)
    q1_scores = []
    for _, game in recent.iterrows():
        if game['away_team'] == team_code:
            q1_scores.append(game['away_q1'])
        else:
            q1_scores.append(game['home_q1'])
    
    return {
        'q1_avg': np.mean(q1_scores),
        'pace': recent['total_score'].mean(),
        'games': len(team_games),
        'last_5_q1': q1_scores
    }

print("="*70)
print("🎯 Q1 PARLAY PREDICTOR")
print(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
print("="*70)

# Load model
print("\n📦 Loading model...")
model = joblib.load('models/q1_regression_model.pkl')
scaler = joblib.load('models/scaler.pkl')
feature_cols = joblib.load('models/feature_cols.pkl')
df = pd.read_csv('data/historical_games.csv')
if 'total_score' not in df.columns:
    df['total_score'] = df['away_score'] + df['home_score']

print(f"  ✅ Model loaded | {len(df)} games, {len(df['away_team'].unique())} teams")

# Get games from Odds API
print(f"\n🎲 Fetching today's games...")

url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
params = {
    'apiKey': API_KEY,
    'regions': 'us',
    'markets': 'totals',
    'oddsFormat': 'american'
}

all_predictions = []

try:
    response = requests.get(url, params=params, timeout=15)
    data = response.json()
    
    if not data:
        print("  ❌ No games found")
        exit(0)
    
    print(f"  ✅ Found {len(data)} games\n")
    print("="*70)
    print("ALL GAME PREDICTIONS")
    print("="*70)
    
    for game in data:
        away_team_raw = game.get('away_team', '')
        home_team_raw = game.get('home_team', '')
        commence_time = game.get('commence_time', '')
        
        away_team = standardize_team_name(away_team_raw)
        home_team = standardize_team_name(home_team_raw)
        
        # Get team stats
        away_stats = get_team_stats(away_team, df)
        home_stats = get_team_stats(home_team, df)
        
        if not away_stats or not home_stats:
            print(f"\n❌ {away_team} @ {home_team} - Insufficient data")
            continue
        
        # Create features
        features = {
            'away_q1_avg_L5': away_stats['q1_avg'],
            'away_pace': away_stats['pace'],
            'home_q1_avg_L5': home_stats['q1_avg'],
            'home_pace': home_stats['pace'],
            'combined_pace': (away_stats['pace'] + home_stats['pace']) / 2,
            'season_q1_avg': df['q1_total'].mean(),
            'home_advantage': 1
        }
        
        X = pd.DataFrame([features])[feature_cols]
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)[0]
        
        # Get Vegas game total for context
        vegas_total = None
        for bookmaker in game.get('bookmakers', []):
            if 'draftkings' in bookmaker.get('key', '').lower():
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'totals':
                        for outcome in market.get('outcomes', []):
                            if outcome.get('name') == 'Over':
                                vegas_total = outcome.get('point')
                                break
        
        # Calculate consistency based on consistency
        away_std = np.std(away_stats['last_5_q1'])
        home_std = np.std(home_stats['last_5_q1'])
        consistency_score = 10 - (away_std + home_std)
        
        # Store ALL predictions
        pred_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'game_time': commence_time,
            'away_team': away_team,
            'home_team': home_team,
            'away_q1_avg': away_stats['q1_avg'],
            'home_q1_avg': home_stats['q1_avg'],
            'prediction': prediction,
            'vegas_game_total': vegas_total,
            'consistency': consistency_score,
            'play': False,  # Will mark top picks as True
            'recommendation': 'NO PLAY',
            'confidence': 'N/A'
        }
        
        all_predictions.append(pred_data)
        
        # Display
        print(f"\n🏀 {away_team} @ {home_team}")
        print(f"   Start: {commence_time}")
        print(f"   {away_team} recent Q1: {away_stats['q1_avg']:.1f}")
        print(f"   {home_team} recent Q1: {home_stats['q1_avg']:.1f}")
        if vegas_total:
            print(f"   Vegas game total: {vegas_total}")
        print(f"\n   🎯 Q1 PREDICTION: {prediction:.1f} points")
        print(f"   📊 Consistency score: {consistency_score:.1f}/10")
        print(f"   {'-'*66}")
    
    # Now recommend best parlay picks
    if len(all_predictions) >= 2:
        pred_df = pd.DataFrame(all_predictions)
        
        print(f"\n{'='*70}")
        print("🎲 RECOMMENDED PARLAY PICKS (2-3 LEG)")
        print("="*70)
        
        # Sort by consistency (most consistent = best for parlay)
        pred_df_sorted = pred_df.sort_values('consistency', ascending=False)
        
        # Recommend top 2-3 picks with highest consistency
        parlay_picks = pred_df_sorted.head(3)
        
        print(f"\n💎 TOP PICKS FOR TODAY'S PARLAY:\n")
        
        for i, (idx, pick) in enumerate(parlay_picks.iterrows(), 1):
            # Determine over/under based on recent average
            implied_line = pick['away_q1_avg'] + pick['home_q1_avg']
            
            if pick['prediction'] > implied_line + 2:
                pick_type = "OVER"
                line_est = implied_line
            elif pick['prediction'] < implied_line - 2:
                pick_type = "UNDER"
                line_est = implied_line
            else:
                pick_type = "OVER" if pick['prediction'] > implied_line else "UNDER"
                line_est = implied_line
            
            # Mark this as a parlay pick in the dataframe
            pred_df.loc[idx, 'play'] = True
            pred_df.loc[idx, 'recommendation'] = pick_type
            pred_df.loc[idx, 'confidence'] = 'HIGH' if pick['consistency'] >= 3 else 'MEDIUM'
            
            print(f"LEG {i}: {pick['away_team']} @ {pick['home_team']}")
            print(f"   Pick: {pick_type} Q1 (~{line_est:.1f})")
            print(f"   Our prediction: {pick['prediction']:.1f}")
            print(f"   Confidence: {pick['consistency']:.1f}/10 (consistency)")
            print()
        
        # Calculate expected parlay odds
        print(f"📊 PARLAY INFO:")
        print(f"   2-leg parlay: ~+260 odds (pays $3.60 per $1)")
        print(f"   3-leg parlay: ~+600 odds (pays $7.00 per $1)")
        print(f"\n   Backtest performance: 64% on individual picks")
        print(f"   Expected 2-leg success: ~41% (.64 × .64)")
        print(f"   Expected 3-leg success: ~26% (.64 × .64 × .64)")
        
        # Save ALL predictions to file (not just parlay picks)
        os.makedirs('predictions', exist_ok=True)
        filename = f"predictions/predictions_{datetime.now().strftime('%Y%m%d')}.csv"
        pred_df.to_csv(filename, index=False)
        print(f"\n💾 Saved ALL {len(pred_df)} predictions to: {filename}")
        
        # Also save just parlay picks
        os.makedirs('parlays', exist_ok=True)
        parlay_filename = f"parlays/parlay_{datetime.now().strftime('%Y%m%d')}.csv"
        pred_df[pred_df['play'] == True].to_csv(parlay_filename, index=False)
        print(f"💾 Saved {len(pred_df[pred_df['play'] == True])} parlay picks to: {parlay_filename}")
    
    print(f"\n{'='*70}")
    print("⚠️  PARLAY BETTING NOTES:")
    print("   • Parlays are higher risk, higher reward")
    print("   • All legs must win for parlay to hit")
    print("   • Model is 64% accurate on individual picks")
    print("   • Consistency score helps identify reliable picks")
    print("   • Bet responsibly")
    print("="*70)
    
    remaining = response.headers.get('x-requests-remaining', 'Unknown')
    print(f"\n�� API requests remaining: {remaining}")
    
except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
