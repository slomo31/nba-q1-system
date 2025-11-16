#!/usr/bin/env python3
"""Interactive Dashboard for Q1 Parlay System - Password Protected"""
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_auth
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import os

Q1_THRESHOLD = 52.5

app = dash.Dash(__name__)
app.title = "Q1 Parlay System Dashboard"
server = app.server

# PASSWORD PROTECTION
# Change these credentials!
VALID_USERNAME_PASSWORD_PAIRS = {
    'slomo': 'parlay2025'  # Change this!
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# Load data function
def load_data():
    hist_df = pd.read_csv('data/historical_games.csv')
    
    results_file = 'predictions/results.csv'
    if os.path.exists(results_file):
        results_df = pd.read_csv(results_file)
        results_df = results_df[results_df['result'].notna()]
        
        if 'actual_q1' in results_df.columns:
            results_df['result'] = results_df['actual_q1'].apply(
                lambda x: 'WIN' if x > Q1_THRESHOLD else 'LOSS'
            )
            results_df['margin'] = results_df['actual_q1'] - Q1_THRESHOLD
    else:
        results_df = pd.DataFrame()
    
    today_str = datetime.now().strftime('%Y%m%d')
    pred_file = f"predictions/predictions_{today_str}.csv"
    if os.path.exists(pred_file):
        pred_df = pd.read_csv(pred_file)
    else:
        pred_df = pd.DataFrame()
    
    parlay_file = f"parlays/parlay_{today_str}.csv"
    if os.path.exists(parlay_file):
        parlay_df = pd.read_csv(parlay_file)
    else:
        parlay_df = pd.DataFrame()
    
    return hist_df, results_df, pred_df, parlay_df

# Layout
app.layout = html.Div([
    html.Div([
        html.H1("🏀 Q1 PARLAY SYSTEM", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 10}),
        html.P(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}", 
               style={'textAlign': 'center', 'fontSize': 18, 'color': '#7f8c8d', 'marginBottom': 5}),
        html.P(f"🎯 WIN = Q1 > {Q1_THRESHOLD} points", 
               style={'textAlign': 'center', 'fontSize': 16, 'color': '#e74c3c', 'fontWeight': 'bold'})
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px'}),
    
    html.Div([
        html.Button('🔄 Refresh', id='refresh-button', n_clicks=0,
                   style={'padding': '10px 20px', 'fontSize': '16px', 'cursor': 'pointer',
                          'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                          'borderRadius': '5px'})
    ], style={'textAlign': 'center', 'margin': '20px'}),
    
    html.Div(id='stats-cards', style={'marginBottom': 30}),
    
    html.Div([
        html.Div([
            html.H2("🎯 TODAY'S PARLAY", style={'color': '#2c3e50'}),
            html.Div(id='parlay-picks')
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'}),
        
        html.Div([
            html.H2("📊 ALL GAMES", style={'color': '#2c3e50'}),
            html.Div(id='all-predictions')
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'})
    ]),
    
    html.Div([
        html.H2("📈 PERFORMANCE", style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': 40}),
        html.Div([
            dcc.Graph(id='q1-distribution', style={'width': '100%'})
        ])
    ]),
    
    html.Div([
        html.H2("📋 RESULTS BY DATE", style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': 40}),
        html.Div(id='results-by-date')
    ]),
    
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0)
], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f8f9fa'})

@app.callback(
    [Output('stats-cards', 'children'),
     Output('parlay-picks', 'children'),
     Output('all-predictions', 'children'),
     Output('q1-distribution', 'figure'),
     Output('results-by-date', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard(n_clicks, n_intervals):
    hist_df, results_df, pred_df, parlay_df = load_data()
    
    # Stats Cards
    if len(results_df) > 0:
        wins = len(results_df[results_df['result'] == 'WIN'])
        losses = len(results_df) - wins
        win_rate = wins / len(results_df) * 100
        profit = (wins * 0.91) - losses
        roi = (profit / len(results_df)) * 100
    else:
        wins, losses, win_rate, profit, roi = 0, 0, 0, 0, 0
    
    stats_cards = html.Div([
        html.Div([
            html.H3(f"{len(results_df)}", style={'fontSize': 40, 'margin': 0}),
            html.P("Picks", style={'margin': 0})
        ], style={'textAlign': 'center', 'padding': 20, 'backgroundColor': '#3498db', 
                 'color': 'white', 'borderRadius': 10, 'width': '22%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(f"{win_rate:.0f}%", style={'fontSize': 40, 'margin': 0}),
            html.P(f"{wins}-{losses}", style={'margin': 0})
        ], style={'textAlign': 'center', 'padding': 20, 'backgroundColor': '#2ecc71', 
                 'color': 'white', 'borderRadius': 10, 'width': '22%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(f"{profit:+.1f}u", style={'fontSize': 40, 'margin': 0}),
            html.P("Profit", style={'margin': 0})
        ], style={'textAlign': 'center', 'padding': 20, 
                 'backgroundColor': '#27ae60' if profit > 0 else '#e74c3c', 
                 'color': 'white', 'borderRadius': 10, 'width': '22%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(f"{roi:+.0f}%", style={'fontSize': 40, 'margin': 0}),
            html.P("ROI", style={'margin': 0})
        ], style={'textAlign': 'center', 'padding': 20, 'backgroundColor': '#9b59b6', 
                 'color': 'white', 'borderRadius': 10, 'width': '22%', 'display': 'inline-block', 'margin': '1%'})
    ])
    
    # Parlay picks
    if len(parlay_df) > 0:
        parlay_items = []
        for i, row in parlay_df.iterrows():
            parlay_items.append(html.Div([
                html.H4(f"LEG {i+1}: {row['away_team']} @ {row['home_team']}", 
                       style={'marginBottom': 5, 'color': '#2c3e50', 'fontSize': 16}),
                html.P(f"Q1: {row['prediction']:.1f} pts", style={'fontSize': 14, 'margin': 0})
            ], style={'backgroundColor': '#ecf0f1', 'padding': 10, 'borderRadius': 10, 'marginBottom': 10}))
        parlay_picks = html.Div(parlay_items)
    else:
        parlay_picks = html.P("No picks yet", style={'color': '#7f8c8d'})
    
    # All predictions
    if len(pred_df) > 0:
        pred_items = []
        for _, row in pred_df.iterrows():
            pred_items.append(html.Div([
                html.P(f"{row['away_team']} @ {row['home_team']}: {row['prediction']:.1f}", 
                      style={'fontSize': 14, 'margin': 5})
            ], style={'backgroundColor': '#fff', 'padding': 8, 'borderRadius': 5, 'marginBottom': 5}))
        all_predictions = html.Div(pred_items, style={'maxHeight': '400px', 'overflowY': 'auto'})
    else:
        all_predictions = html.P("No games today", style={'color': '#7f8c8d'})
    
    # Q1 Distribution
    fig_q1 = px.histogram(hist_df, x='q1_total', nbins=30, title='Q1 Total Distribution')
    fig_q1.add_vline(x=Q1_THRESHOLD, line_dash="dash", line_color="red")
    
    # Results by date
    if len(results_df) > 0:
        results_sorted = results_df.sort_values('date', ascending=False)
        results_sorted['Game'] = results_sorted['away_team'] + ' @ ' + results_sorted['home_team']
        
        date_tables = []
        for date in results_sorted['date'].unique()[:5]:
            date_games = results_sorted[results_sorted['date'] == date]
            daily_wins = len(date_games[date_games['result'] == 'WIN'])
            
            date_tables.append(html.Div([
                html.H3(f"{date} - {daily_wins}/{len(date_games)}", 
                       style={'color': '#2c3e50', 'marginTop': 15, 'fontSize': 18})
            ]))
            
            table = dash_table.DataTable(
                data=date_games[['Game', 'prediction', 'actual_q1', 'result']].to_dict('records'),
                columns=[{'name': c.title(), 'id': c} for c in ['Game', 'prediction', 'actual_q1', 'result']],
                style_cell={'textAlign': 'center', 'padding': '8px', 'fontSize': 12},
                style_header={'backgroundColor': '#34495e', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'filter_query': '{result} = WIN'}, 'backgroundColor': '#d4edda'},
                    {'if': {'filter_query': '{result} = LOSS'}, 'backgroundColor': '#f8d7da'}
                ]
            )
            date_tables.append(table)
        
        results_by_date = html.Div(date_tables)
    else:
        results_by_date = html.P("No results yet", style={'textAlign': 'center', 'color': '#7f8c8d'})
    
    return stats_cards, parlay_picks, all_predictions, fig_q1, results_by_date

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=False, host='0.0.0.0', port=port)
