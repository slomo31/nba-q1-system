#!/usr/bin/env python3
"""Train Q1 Total Regression Model - Predict actual point total"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os

print("="*60)
print("TRAINING Q1 TOTAL REGRESSION MODEL")
print("Predicting Actual Q1 Point Total")
print("="*60)

# Load data from historical_games.csv (not training_data.csv)
print("\n📊 Loading training data...")
df = pd.read_csv('data/historical_games.csv')

# Add total_score if missing
if 'total_score' not in df.columns:
    df['total_score'] = df['away_score'] + df['home_score']

# Create features
print(f"  Creating features from {len(df)} games...")

training_data = []
for idx, row in df.iterrows():
    # Get history before this game
    hist = df[df['date'] < row['date']]
    
    if len(hist) < 10:  # Need at least 10 games of history
        continue
    
    # Away team stats
    away_games = hist[(hist['away_team'] == row['away_team']) | (hist['home_team'] == row['away_team'])]
    if len(away_games) >= 5:
        recent_away = away_games.tail(5)
        away_q1 = np.mean([g['away_q1'] if g['away_team'] == row['away_team'] else g['home_q1'] 
                          for _, g in recent_away.iterrows()])
        away_pace = recent_away['total_score'].mean()
    else:
        continue
    
    # Home team stats  
    home_games = hist[(hist['away_team'] == row['home_team']) | (hist['home_team'] == row['home_team'])]
    if len(home_games) >= 5:
        recent_home = home_games.tail(5)
        home_q1 = np.mean([g['home_q1'] if g['home_team'] == row['home_team'] else g['away_q1'] 
                          for _, g in recent_home.iterrows()])
        home_pace = recent_home['total_score'].mean()
    else:
        continue
    
    training_data.append({
        'away_q1_avg_L5': away_q1,
        'away_pace': away_pace,
        'home_q1_avg_L5': home_q1,
        'home_pace': home_pace,
        'combined_pace': (away_pace + home_pace) / 2,
        'season_q1_avg': hist['q1_total'].mean(),
        'home_advantage': 1,
        'q1_total': row['q1_total']
    })

training_df = pd.DataFrame(training_data)

print(f"  Samples: {len(training_df)}")

# Features
feature_cols = ['away_q1_avg_L5', 'away_pace', 'home_q1_avg_L5', 
                'home_pace', 'combined_pace', 'season_q1_avg', 'home_advantage']

X = training_df[feature_cols]
y = training_df['q1_total']

print(f"  Features: {len(feature_cols)}")

# Show target distribution
print(f"\n🎯 Target: Q1 Total Points")
print(f"  Mean: {y.mean():.1f}")
print(f"  Median: {y.median():.1f}")
print(f"  Std Dev: {y.std():.1f}")
print(f"  Range: {y.min()} - {y.max()}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\n📂 Data split:")
print(f"  Training: {len(X_train)} samples")
print(f"  Testing: {len(X_test)} samples")

# Scale features
print(f"\n⚙️  Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train XGBoost Regressor
print(f"\n🤖 Training XGBoost Regressor...")
model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    objective='reg:squarederror'
)

model.fit(X_train_scaled, y_train)

# Predictions
y_train_pred = model.predict(X_train_scaled)
y_test_pred = model.predict(X_test_scaled)

# Evaluate
train_mae = mean_absolute_error(y_train, y_train_pred)
test_mae = mean_absolute_error(y_test, y_test_pred)
train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
train_r2 = r2_score(y_train, y_train_pred)
test_r2 = r2_score(y_test, y_test_pred)

print(f"\n📈 Results:")
print(f"  Training MAE:  {train_mae:.2f} points")
print(f"  Test MAE:      {test_mae:.2f} points")
print(f"  Training RMSE: {train_rmse:.2f} points")
print(f"  Test RMSE:     {test_rmse:.2f} points")
print(f"  Training R²:   {train_r2:.3f}")
print(f"  Test R²:       {test_r2:.3f}")

print(f"\n💡 Interpretation:")
print(f"  On average, predictions are off by {test_mae:.1f} points")
print(f"  Model explains {test_r2*100:.1f}% of variance in Q1 totals")

# Feature importance
importances = model.feature_importances_
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': importances
}).sort_values('importance', ascending=False)

print(f"\n🔍 Feature Importance:")
for _, row in feature_importance.iterrows():
    print(f"  {row['feature']:<20} {row['importance']:.3f}")

# Save model
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/q1_regression_model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')
joblib.dump(feature_cols, 'models/feature_cols.pkl')

print(f"\n💾 Saved:")
print(f"  ✅ models/q1_regression_model.pkl")
print(f"  ✅ models/scaler.pkl")
print(f"  ✅ models/feature_cols.pkl")

# Sample predictions
print(f"\n🎲 Sample predictions on test set:")
print(f"  {'Predicted':<12} {'Actual':<10} {'Error':<10} {'Status'}")
print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")

for i in range(min(15, len(y_test))):
    pred = y_test_pred[i]
    actual = y_test.iloc[i]
    error = pred - actual
    status = "✅" if abs(error) < 5 else "⚠️"
    print(f"  {pred:>6.1f}       {actual:>6.0f}      {error:>+5.1f}      {status}")

print("\n" + "="*60)
print("✅ REGRESSION MODEL TRAINED!")
print(f"Using {len(df)} games from {df['date'].min()} to {df['date'].max()}")
print("="*60)
