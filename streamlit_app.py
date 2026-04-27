import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from predictive_engine import get_odds, identify_ev_opportunities, run_monte_carlo_simulation
from config import STARTING_BALANCE, GOAL_BALANCE

# Configure Streamlit page
st.set_page_config(
    page_title="Project 100k - Wallet Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
    <style>
        * {
            margin: 0;
            padding: 0;
        }
        body {
            background-color: #F8F9FB;
        }
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #262730;
        }
        .metric-subtext {
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }
        .header {
            text-align: center;
            padding: 20px 0;
            margin-bottom: 20px;
        }
        .header-title {
            font-size: 32px;
            font-weight: bold;
            color: #262730;
        }
        .header-subtitle {
            font-size: 14px;
            color: #999;
            margin-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_equity' not in st.session_state:
    st.session_state.current_equity = STARTING_BALANCE
if 'locked_vault' not in st.session_state:
    st.session_state.locked_vault = 0
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None

# Header
st.markdown("""
    <div class="header">
        <div class="header-title">Project 100k</div>
        <div class="header-subtitle">Scaling ₦5,000 to ₦100,000 via +EV Predictive Modeling</div>
    </div>
""", unsafe_allow_html=True)

# Main KPIs Section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Equity</div>
            <div class="metric-value">₦{st.session_state.current_equity:,.0f}</div>
            <div class="metric-subtext">Current Balance</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Locked Vault</div>
            <div class="metric-value">₦{st.session_state.locked_vault:,.0f}</div>
            <div class="metric-subtext">Discipline Savings</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    liquid_capital = st.session_state.current_equity - st.session_state.locked_vault
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Liquid Capital</div>
            <div class="metric-value">₦{liquid_capital:,.0f}</div>
            <div class="metric-subtext">Available for Betting</div>
        </div>
    """, unsafe_allow_html=True)

# Progress Bar
progress_percentage = (st.session_state.current_equity / GOAL_BALANCE) * 100
st.progress(min(progress_percentage / 100, 1.0), text=f"{progress_percentage:.1f}% to Goal")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "+EV Signals", "Simulation", "Settings"])

with tab1:
    st.subheader("Wallet Overview")
    
    # Summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Starting Balance", f"₦{STARTING_BALANCE:,}")
    with col2:
        st.metric("Goal Balance", f"₦{GOAL_BALANCE:,}")
    
    # Remaining to goal
    remaining = GOAL_BALANCE - st.session_state.current_equity
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Remaining to Goal", f"₦{remaining:,}")
    with col2:
        growth_percentage = ((st.session_state.current_equity - STARTING_BALANCE) / STARTING_BALANCE) * 100
        st.metric("Growth %", f"{growth_percentage:.1f}%")

with tab2:
    st.subheader("+EV Opportunities")
    
    if st.button("Fetch +EV Signals"):
        with st.spinner("Fetching odds from The Odds API..."):
            odds = get_odds()
            if odds:
                ev_opportunities = identify_ev_opportunities(odds)
                if ev_opportunities:
                    st.success(f"Found {len(ev_opportunities)} +EV opportunities!")
                    
                    # Display opportunities as a table
                    df_opportunities = pd.DataFrame(ev_opportunities)
                    # Select relevant columns for display
                    display_cols = ['home_team', 'away_team', 'outcome_name', 'odds', 'implied_probability', 'model_probability', '+EV_edge']
                    if all(col in df_opportunities.columns for col in display_cols):
                        st.dataframe(df_opportunities[display_cols], use_container_width=True)
                    else:
                        st.dataframe(df_opportunities, use_container_width=True)
                else:
                    st.info("No +EV opportunities found at the moment.")
            else:
                st.error("Failed to fetch odds. Please check your API key.")

with tab3:
    st.subheader("Monte Carlo Simulation")
    
    if st.button("Run Simulation"):
        with st.spinner("Running 1,000-iteration Monte Carlo simulation..."):
            simulation_results = run_monte_carlo_simulation(
                st.session_state.current_equity,
                num_simulations=1000,
                num_days=30,
                avg_daily_return=0.02,
                daily_volatility=0.03
            )
            st.session_state.simulation_results = simulation_results
            
            # Display results
            col1, col2, col3 = st.columns(3)
            with col1:
                prob_of_ruin = simulation_results['probability_of_ruin']
                st.metric("Probability of Ruin", f"{prob_of_ruin:.2%}")
            with col2:
                if simulation_results['estimated_completion_date']:
                    est_date = datetime.now() + timedelta(days=simulation_results['estimated_completion_date'])
                    st.metric("Est. Completion Date", est_date.strftime("%Y-%m-%d"))
                else:
                    st.metric("Est. Completion Date", "Not reached")
            with col3:
                lower, upper = simulation_results['confidence_interval']
                st.metric("90% CI (Final Balance)", f"₦{lower:,.0f} - ₦{upper:,.0f}")
            
            # Plot confidence interval
            st.subheader("Balance Forecast (30 Days)")
            simulated_balances = simulation_results['simulated_balances']
            
            fig, ax = plt.subplots(figsize=(12, 6))
            days = np.arange(simulated_balances.shape[1])
            
            # Calculate percentiles
            p5 = np.percentile(simulated_balances, 5, axis=0)
            p25 = np.percentile(simulated_balances, 25, axis=0)
            p50 = np.percentile(simulated_balances, 50, axis=0)
            p75 = np.percentile(simulated_balances, 75, axis=0)
            p95 = np.percentile(simulated_balances, 95, axis=0)
            
            # Plot
            ax.fill_between(days, p5, p95, alpha=0.2, color='blue', label='90% Confidence Interval')
            ax.fill_between(days, p25, p75, alpha=0.3, color='blue', label='50% Confidence Interval')
            ax.plot(days, p50, color='darkblue', linewidth=2, label='Median')
            ax.axhline(y=GOAL_BALANCE, color='green', linestyle='--', linewidth=2, label='Goal (₦100k)')
            ax.set_xlabel('Days')
            ax.set_ylabel('Balance (₦)')
            ax.set_title('Projected Balance Over 30 Days')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)

with tab4:
    st.subheader("Settings")
    
    # Update balances
    st.write("Update your current balances:")
    new_equity = st.number_input("Total Equity (₦)", value=st.session_state.current_equity, min_value=0)
    new_vault = st.number_input("Locked Vault (₦)", value=st.session_state.locked_vault, min_value=0)
    
    if st.button("Save Settings"):
        st.session_state.current_equity = new_equity
        st.session_state.locked_vault = new_vault
        st.success("Settings saved!")

# Footer
st.markdown("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #999; font-size: 12px;">
        <p>Project 100k | Autonomous Full-Stack Quant Developer | Powered by Streamlit</p>
    </div>
""", unsafe_allow_html=True)
