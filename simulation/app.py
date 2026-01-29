"""
Streamlit Dashboard for Hellas ABM Simulator

Run with: streamlit run simulation/app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
from typing import Dict, Any
import sys
import os

# Handle imports whether running from project root or simulation directory
try:
    from simulation.config import (
        SimulationConfig, ProtocolParameters, ReputationParameters,
        BASELINE_CONFIG, WEAK_ENFORCEMENT_CONFIG, NO_STAKE_FLOOR_CONFIG,
    )
    from simulation.core.engine import SimulationEngine, SimulationResult
    from simulation.attacks.scenarios import (
        ReputationFarmingAttack, SybilAttack, CollusionAttack,
        GriefingAttack, NoStakeFloorAttack, CensorshipAttack,
        run_all_attacks,
    )
    from simulation.analysis.visualization import (
        plot_simulation_results, plot_attack_comparison,
        plot_equilibrium_analysis, plot_parameter_sensitivity,
        plot_reputation_farming_analysis,
    )
    from simulation.analysis.metrics import (
        compute_theoretical_equilibrium, compute_welfare_metrics,
        parameter_sensitivity_analysis, analyze_attack_profitability,
    )
except ImportError:
    # Running from within simulation directory
    from config import (
        SimulationConfig, ProtocolParameters, ReputationParameters,
        BASELINE_CONFIG, WEAK_ENFORCEMENT_CONFIG, NO_STAKE_FLOOR_CONFIG,
    )
    from core.engine import SimulationEngine, SimulationResult
    from attacks.scenarios import (
        ReputationFarmingAttack, SybilAttack, CollusionAttack,
        GriefingAttack, NoStakeFloorAttack, CensorshipAttack,
        run_all_attacks,
    )
    from analysis.visualization import (
        plot_simulation_results, plot_attack_comparison,
        plot_equilibrium_analysis, plot_parameter_sensitivity,
        plot_reputation_farming_analysis,
    )
    from analysis.metrics import (
        compute_theoretical_equilibrium, compute_welfare_metrics,
        parameter_sensitivity_analysis, analyze_attack_profitability,
    )


# Page configuration
st.set_page_config(
    page_title="Hellas ABM Simulator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("🎮 Hellas Fraud Game ABM Simulator")
st.markdown("""
**Agent-Based Model for analyzing incentive compatibility in off-chain computation.**

Based on: *"Fraud Game Analysis for Hellas Protocol"* (CryptoEconLab, 2026)
""")

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# Protocol parameters
st.sidebar.subheader("Protocol Parameters")

col1, col2 = st.sidebar.columns(2)

with col1:
    S_P_min = st.number_input("S_P (min stake)", value=100.0, min_value=0.0, step=10.0)
    c_H = st.number_input("c_H (honest cost)", value=5.0, min_value=0.1, step=0.5)
    C_safe = st.number_input("C_safe (verify cost)", value=8.0, min_value=0.1, step=1.0)
    beta = st.slider("β (slash reward)", 0.0, 1.0, 0.5, 0.05)

with col2:
    P_set = st.number_input("P_set (payment)", value=50.0, min_value=1.0, step=5.0)
    c_F = st.number_input("c_F (cheat cost)", value=0.5, min_value=0.0, step=0.1)
    p_w = st.slider("p_w (enforcement)", 0.5, 1.0, 0.95, 0.01)
    lambda_ = st.slider("λ (payment route)", 0.0, 1.0, 1.0, 0.1)

L = st.sidebar.number_input("L (client loss)", value=50.0, min_value=1.0, step=5.0)
B_C = st.sidebar.number_input("B_C (challenge bond)", value=5.0, min_value=0.0, step=1.0)

# Simulation parameters
st.sidebar.subheader("Simulation Parameters")
n_periods = st.sidebar.slider("Periods", 100, 2000, 500, 100)
n_providers = st.sidebar.slider("Providers", 10, 200, 50, 10)
n_clients = st.sidebar.slider("Clients", 20, 500, 100, 20)
seed = st.sidebar.number_input("Random Seed", value=42, min_value=0)

# Agent distributions
st.sidebar.subheader("Agent Distributions")
honest_frac = st.sidebar.slider("Honest Providers %", 0, 100, 60, 5) / 100
adversarial_frac = st.sidebar.slider("Adversarial Providers %", 0, 100, 10, 5) / 100
rational_frac = 1.0 - honest_frac - adversarial_frac

if rational_frac < 0:
    st.sidebar.error("Agent fractions must sum to 100%")
    rational_frac = 0

st.sidebar.text(f"Rational Providers: {rational_frac*100:.0f}%")

# Create protocol config
protocol = ProtocolParameters(
    S_P_min=S_P_min,
    c_H=c_H,
    c_F=c_F,
    C_safe=C_safe,
    beta=beta,
    lambda_=lambda_,
    p_w=p_w,
    B_C=B_C,
    L_base=L,
)

config = SimulationConfig(
    n_providers=n_providers,
    n_clients=n_clients,
    n_periods=n_periods,
    seed=seed,
    job_value_mean=P_set,
    provider_honest_frac=honest_frac,
    provider_rational_frac=rational_frac,
    provider_adversarial_frac=adversarial_frac,
    protocol=protocol,
)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Theoretical Analysis",
    "🎲 Run Simulation",
    "⚔️ Attack Scenarios",
    "📈 Parameter Sensitivity",
    "📖 Documentation",
])

# Tab 1: Theoretical Analysis
with tab1:
    st.header("Theoretical Equilibrium Analysis")

    # Compute equilibrium
    eq = compute_theoretical_equilibrium(protocol, P_set, S_P_min, L)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("v* (audit prob)", f"{eq.v_star:.4f}")
        st.metric("θ (IC threshold)", f"{eq.theta:.4f}")

    with col2:
        st.metric("q* (cheat prob)", f"{eq.q_star:.4f}")
        st.metric("Δ (dispute surplus)", f"{eq.Delta:.2f}")

    with col3:
        st.metric("S_P^min (viable stake)", f"{eq.S_P_min:.2f}")
        status = "✅ Viable" if eq.is_enforcement_viable else "❌ Not Viable"
        st.metric("Enforcement Status", status)

    with col4:
        st.metric("E[U_P] (provider)", f"{eq.expected_provider_utility:.2f}")
        st.metric("E[U_C] (client)", f"{eq.expected_client_utility:.2f}")

    # Equilibrium analysis plot
    st.subheader("Incentive Compatibility Region")
    fig_eq = plot_equilibrium_analysis(protocol, L=L)
    st.plotly_chart(fig_eq, use_container_width=True)

    # Key equations
    st.subheader("Key Equilibrium Equations")

    st.latex(r"v^* = \frac{c_H - c_F}{P_{set} + S_P} = " + f"{eq.v_star:.4f}")
    st.latex(r"q^* = \frac{C_{safe}}{L + \Delta} = " + f"{eq.q_star:.4f}")
    st.latex(r"\Delta = p_w(\beta S_P + \lambda P_{set}) - (c_{proof} + c_{tx}) - (1-p_w)B_C = " + f"{eq.Delta:.2f}")
    st.latex(r"S_P^{min} = \max\left\{0, \frac{C_{disp} + (1-p_w)B_C - p_w\lambda P_{set}}{p_w\beta}\right\} = " + f"{eq.S_P_min:.2f}")

# Tab 2: Run Simulation
with tab2:
    st.header("Run ABM Simulation")

    if st.button("🚀 Run Simulation", type="primary"):
        with st.spinner(f"Running {n_periods} periods..."):
            engine = SimulationEngine(config)
            result = engine.run(show_progress=False)

        st.success(f"Simulation completed! Processed {result.total_jobs} jobs.")

        # Store result in session state
        st.session_state["simulation_result"] = result

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Jobs", result.total_jobs)
            st.metric("Total Frauds", result.total_frauds)

        with col2:
            st.metric("Fraud Rate", f"{result.fraud_rate:.2%}")
            st.metric("Detection Rate", f"{result.detection_rate:.2%}")

        with col3:
            st.metric("Stake Slashed", f"${result.total_stake_slashed:.2f}")
            st.metric("Client Losses", f"${result.total_client_losses:.2f}")

        with col4:
            st.metric("Social Welfare", f"${result.social_welfare:.2f}")
            st.metric("Attack Success", f"{result.attack_metrics.get('attack_success_ratio', 0):.2f}x")

        # Visualization
        st.subheader("Simulation Results")
        fig = plot_simulation_results(result)
        st.plotly_chart(fig, use_container_width=True)

        # Attack metrics
        if result.attack_metrics:
            st.subheader("Attack Detection")
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Reputation Farming Suspects:**")
                suspects = result.attack_metrics.get("reputation_farming_suspects", [])
                if suspects:
                    st.write(suspects)
                else:
                    st.write("None detected")

            with col2:
                st.write("**Self-Buying Suspects:**")
                self_buy = result.attack_metrics.get("self_buy_suspects", [])
                if self_buy:
                    for suspect, details in self_buy[:5]:
                        st.write(f"- {suspect}: {details}")
                else:
                    st.write("None detected")

# Tab 3: Attack Scenarios
with tab3:
    st.header("Adversarial Attack Analysis")

    st.markdown("""
    Analyze how different attack strategies exploit protocol vulnerabilities.
    Each attack is compared against a baseline honest scenario.
    """)

    attack_type = st.selectbox(
        "Select Attack Type",
        [
            "Reputation Farming",
            "No Stake Floor",
            "Sybil Attack",
            "Collusion",
            "Griefing",
            "Censorship",
            "Run All Attacks",
        ]
    )

    attack_periods = st.slider("Attack Simulation Periods", 100, 1000, 300, 50)

    if st.button("⚔️ Run Attack Analysis", type="primary"):
        with st.spinner(f"Running {attack_type} analysis..."):

            if attack_type == "Reputation Farming":
                attack = ReputationFarmingAttack(config, min_stake_enforced=False)
                attack_result = attack.run(n_periods=attack_periods, show_progress=False)

                st.subheader("Reputation Farming Attack Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Fraud Rate Increase", f"{attack_result.fraud_rate_increase:+.2%}")
                with col2:
                    st.metric("Attacker Profit", f"${attack_result.attacker_profit:.2f}")
                with col3:
                    st.metric("Welfare Loss", f"${attack_result.social_welfare_loss:.2f}")

                fig = plot_reputation_farming_analysis(
                    attack_result.attack_result,
                    attack_result.attack_result.attack_metrics
                )
                st.plotly_chart(fig, use_container_width=True)

            elif attack_type == "No Stake Floor":
                attack = NoStakeFloorAttack(config, min_stake_override=1.0)
                attack_result = attack.run(n_periods=attack_periods, show_progress=False)

                st.subheader("No Stake Floor Attack Results")
                st.markdown("""
                **Attack Vector:** When minimum stake is not enforced, providers can use
                minimal stake, making slashing penalties economically insignificant.
                """)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Baseline Fraud Rate", f"{attack_result.baseline_result.fraud_rate:.2%}")
                    st.metric("Attack Fraud Rate", f"{attack_result.attack_result.fraud_rate:.2%}")
                with col2:
                    st.metric("Fraud Rate Increase", f"{attack_result.fraud_rate_increase:+.2%}")
                    st.metric("Victim Losses", f"${attack_result.victim_losses:.2f}")

            elif attack_type == "Censorship":
                attack = CensorshipAttack(config, censorship_rate=0.3)
                attack_result = attack.run(n_periods=attack_periods, show_progress=False)

                st.subheader("Censorship Attack Results")
                st.markdown("""
                **Attack Vector:** Attacker censors dispute transactions, reducing effective
                enforcement probability p_w.
                """)

                profitability = analyze_attack_profitability(protocol, P_set, S_P_min, L, "censorship")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Original q*", f"{profitability['original_q_star']:.4f}")
                    st.metric("Original Δ", f"{profitability['original_Delta']:.2f}")
                with col2:
                    st.metric("New q* (with censorship)", f"{profitability['new_q_star']:.4f}")
                    st.metric("New Δ (with censorship)", f"{profitability['new_Delta']:.2f}")

            elif attack_type == "Run All Attacks":
                all_results = run_all_attacks(config, n_periods=attack_periods, show_progress=False)

                st.subheader("All Attack Scenarios Comparison")
                fig = plot_attack_comparison(all_results)
                st.plotly_chart(fig, use_container_width=True)

                # Summary table
                summary_data = []
                for name, result in all_results.items():
                    summary_data.append({
                        "Attack": name,
                        "Fraud Rate Δ": f"{result.fraud_rate_increase:+.2%}",
                        "Detection Δ": f"{result.detection_rate_change:+.2%}",
                        "Attacker Profit": f"${result.attacker_profit:.0f}",
                        "Victim Losses": f"${result.victim_losses:.0f}",
                        "Welfare Loss": f"${result.social_welfare_loss:.0f}",
                    })

                st.dataframe(pd.DataFrame(summary_data))

            else:
                st.info(f"Attack type '{attack_type}' analysis coming soon...")

# Tab 4: Parameter Sensitivity
with tab4:
    st.header("Parameter Sensitivity Analysis")

    param_to_analyze = st.selectbox(
        "Select Parameter to Analyze",
        ["S_P_min", "p_w", "C_safe", "beta", "lambda_", "B_C", "L_base"]
    )

    param_range = st.slider(
        f"Range for {param_to_analyze}",
        0.1, 500.0, (10.0, 200.0), 10.0
    )

    if st.button("📈 Run Sensitivity Analysis"):
        param_values = np.linspace(param_range[0], param_range[1], 30).tolist()

        fig = plot_parameter_sensitivity(
            protocol, param_to_analyze, param_values,
            P_set=P_set, S_P=S_P_min, L=L,
            title=f"Sensitivity to {param_to_analyze}"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Key insights
        st.subheader("Key Insights")

        if param_to_analyze == "S_P_min":
            st.markdown("""
            **Effect of Minimum Stake:**
            - ↑ S_P → ↓ q* (lower cheating rate)
            - ↑ S_P → ↓ v* (less auditing needed)
            - Provider participation cost increases with stake (opportunity cost)
            """)

        elif param_to_analyze == "p_w":
            st.markdown("""
            **Effect of Enforcement Reliability:**
            - ↑ p_w → ↓ q* (more reliable punishment deters cheating)
            - ↑ p_w → ↑ Δ (higher expected dispute surplus)
            - Critical threshold: p_w must exceed θ for IC
            """)

        elif param_to_analyze == "C_safe":
            st.markdown("""
            **Effect of Verification Cost:**
            - ↑ C_safe → ↑ q* (less auditing → more cheating)
            - Reducing C_safe through trusted fallback providers improves outcomes
            - This is the primary lever for protocol optimization
            """)

# Tab 5: Documentation
with tab5:
    st.header("📖 Documentation")

    st.markdown("""
    ## Hellas Fraud Game ABM Simulator

    This simulator implements the economic model from *"Fraud Game Analysis for
    Hellas Protocol"* (CryptoEconLab, 2026).

    ### Model Overview

    The Hellas fraud game secures off-chain computation through economic incentives:
    1. **Providers** post stake that can be slashed if fraud is proven
    2. **Clients** request computation and decide whether to audit
    3. **Challengers** can dispute and submit fraud proofs

    ### Key Equilibrium Results

    **Mixed Strategy Nash Equilibrium (Theorem 2):**

    Under conditions where $0 < c_H - c_F < P_{set} + S_P$ and $0 < C_{safe} < L + \Delta$:

    $$v^* = \\frac{c_H - c_F}{P_{set} + S_P}$$

    $$q^* = \\frac{C_{safe}}{L + \Delta}$$

    **Minimum Viable Stake (Proposition 2):**

    $$S_P^{min} = \\max\\left\\{0, \\frac{C_{disp} + (1-p_w)B_C - p_w\\lambda P_{set}}{p_w\\beta}\\right\\}$$

    ### Attack Vectors Analyzed

    1. **Reputation Farming**: Build reputation with low-stake jobs, then exploit reduced auditing
    2. **No Stake Floor**: Exploit when minimum stake isn't enforced
    3. **Sybil Attack**: Create multiple identities to spread risk
    4. **Collusion**: Provider-client coordination to avoid auditing
    5. **Griefing**: File frivolous disputes to delay honest providers
    6. **Censorship**: Block dispute transactions to reduce enforcement

    ### Protocol Design Recommendations

    From Section 7 of the paper:
    1. **Stake floors indexed by job class**
    2. **Permissionless challenging** for watcher markets
    3. **Randomized audits** for exogenous detection baseline
    4. **Reducing verification cost** through trusted fallback providers
    5. **Timeout sizing** by job class
    6. **Anti-griefing** through challenge bonds

    ### Agent Types

    **Providers:**
    - *Honest*: Always executes correctly
    - *Rational*: Expected utility maximizer
    - *Adversarial*: Strategic attacker
    - *Reputation Farmer*: Builds reputation then exploits

    **Clients:**
    - *Always Audit*: Verifies every job
    - *Never Audit*: Trusts all providers
    - *Mixed Strategy*: Follows equilibrium audit probability
    - *Reputation Weighted*: Adjusts auditing based on provider reputation

    ### References

    - Hellas Protocol Whitepaper
    - Inspection Games in Economics (Avenhaus & Canty)
    - Mechanism Design for Blockchains (Roughgarden)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with Streamlit | Hellas ABM Simulator v1.0</p>
    <p>CryptoEconLab © 2026</p>
</div>
""", unsafe_allow_html=True)
