"""
Visualization Module for Hellas ABM

Uses Plotly for interactive visualizations.
"""

from typing import Dict, List, Optional, Any
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..config import ProtocolParameters
from ..core.engine import SimulationResult
from ..attacks.scenarios import AttackResult
from .metrics import (
    compute_theoretical_equilibrium,
    parameter_sensitivity_analysis,
    compute_incentive_compatibility_region,
)


# Color scheme
COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "warning": "#9467bd",
    "info": "#17becf",
    "honest": "#2ca02c",
    "fraud": "#d62728",
    "theoretical": "#ff7f0e",
    "simulated": "#1f77b4",
}


def plot_simulation_results(
    result: SimulationResult,
    title: str = "Hellas ABM Simulation Results",
) -> go.Figure:
    """
    Create comprehensive visualization of simulation results.
    """
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Fraud Rate Over Time",
            "Detection Rate Over Time",
            "Average Stake Over Time",
            "Average Reputation Over Time",
            "Provider Profit Distribution",
            "Fraud vs Detection Rates",
        ),
        vertical_spacing=0.1,
        horizontal_spacing=0.1,
    )

    periods = list(range(len(result.fraud_rate_history)))

    # Fraud rate
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=result.fraud_rate_history,
            mode="lines",
            name="Fraud Rate",
            line=dict(color=COLORS["danger"]),
        ),
        row=1, col=1,
    )

    # Add theoretical equilibrium line
    protocol = result.config.protocol
    eq = compute_theoretical_equilibrium(
        protocol,
        result.config.job_value_mean,
        np.mean(result.avg_stake_history) if result.avg_stake_history else 100,
        protocol.L_base,
    )
    fig.add_hline(
        y=eq.q_star,
        line_dash="dash",
        line_color=COLORS["theoretical"],
        annotation_text=f"q* = {eq.q_star:.3f}",
        row=1, col=1,
    )

    # Detection rate
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=result.detection_rate_history,
            mode="lines",
            name="Detection Rate",
            line=dict(color=COLORS["success"]),
        ),
        row=1, col=2,
    )

    # Average stake
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=result.avg_stake_history,
            mode="lines",
            name="Avg Stake",
            line=dict(color=COLORS["primary"]),
        ),
        row=2, col=1,
    )

    # Minimum viable stake line
    S_P_min = protocol.compute_S_P_min_viable(result.config.job_value_mean)
    fig.add_hline(
        y=S_P_min,
        line_dash="dash",
        line_color=COLORS["warning"],
        annotation_text=f"S_P^min = {S_P_min:.1f}",
        row=2, col=1,
    )

    # Reputation
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=result.avg_reputation_history,
            mode="lines",
            name="Avg Reputation",
            line=dict(color=COLORS["info"]),
        ),
        row=2, col=2,
    )

    # Provider profit distribution
    profits = list(result.provider_profits.values())
    fig.add_trace(
        go.Histogram(
            x=profits,
            nbinsx=30,
            name="Provider Profits",
            marker_color=COLORS["primary"],
        ),
        row=3, col=1,
    )

    # Fraud vs Detection scatter
    fig.add_trace(
        go.Scatter(
            x=result.fraud_rate_history,
            y=result.detection_rate_history,
            mode="markers",
            marker=dict(
                size=5,
                color=periods,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Period"),
            ),
            name="Fraud vs Detection",
        ),
        row=3, col=2,
    )

    fig.update_layout(
        title=title,
        height=900,
        showlegend=True,
        template="plotly_white",
    )

    return fig


def plot_attack_comparison(
    attack_results: Dict[str, AttackResult],
    title: str = "Attack Scenario Comparison",
) -> go.Figure:
    """
    Compare multiple attack scenarios.
    """
    attack_names = list(attack_results.keys())

    metrics = {
        "Fraud Rate Increase": [r.fraud_rate_increase for r in attack_results.values()],
        "Detection Rate Change": [r.detection_rate_change for r in attack_results.values()],
        "Attacker Profit": [r.attacker_profit for r in attack_results.values()],
        "Victim Losses": [r.victim_losses for r in attack_results.values()],
        "Welfare Loss": [r.social_welfare_loss for r in attack_results.values()],
    }

    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=list(metrics.keys()) + ["Attack Success Ratio"],
        vertical_spacing=0.15,
        horizontal_spacing=0.1,
    )

    positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]

    for (metric_name, values), (row, col) in zip(metrics.items(), positions):
        colors = [
            COLORS["danger"] if v > 0 else COLORS["success"]
            for v in values
        ]
        fig.add_trace(
            go.Bar(
                x=attack_names,
                y=values,
                name=metric_name,
                marker_color=colors,
                showlegend=False,
            ),
            row=row, col=col,
        )

    # Attack success ratio
    success_ratios = [
        r.attack_result.attack_metrics.get("attack_success_ratio", 0)
        for r in attack_results.values()
    ]
    fig.add_trace(
        go.Bar(
            x=attack_names,
            y=success_ratios,
            name="Success Ratio",
            marker_color=COLORS["warning"],
            showlegend=False,
        ),
        row=2, col=3,
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", row=2, col=3)

    fig.update_layout(
        title=title,
        height=600,
        template="plotly_white",
    )

    return fig


def plot_equilibrium_analysis(
    protocol: ProtocolParameters,
    P_set_range: tuple = (10, 200),
    S_P_range: tuple = (10, 500),
    L: float = 50.0,
    title: str = "Equilibrium Analysis",
) -> go.Figure:
    """
    Visualize the incentive compatibility region and equilibrium values.
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "IC Region (S_P vs P_set)",
            "Equilibrium q* (Cheating Rate)",
            "Equilibrium v* (Audit Rate)",
            "Minimum Viable Stake",
        ),
        specs=[
            [{"type": "heatmap"}, {"type": "heatmap"}],
            [{"type": "heatmap"}, {"type": "xy"}],
        ],
    )

    # Compute IC region
    ic_data = compute_incentive_compatibility_region(
        protocol, P_set_range, S_P_range, resolution=50
    )

    # IC region heatmap
    fig.add_trace(
        go.Heatmap(
            x=ic_data["P_set"],
            y=ic_data["S_P"],
            z=ic_data["ic_region"].astype(float),
            colorscale=[[0, COLORS["danger"]], [1, COLORS["success"]]],
            showscale=False,
            name="IC Region",
        ),
        row=1, col=1,
    )

    # Add S_P_min curve
    fig.add_trace(
        go.Scatter(
            x=ic_data["P_set"],
            y=ic_data["S_P_min_curve"],
            mode="lines",
            name="S_P^min",
            line=dict(color="white", width=2, dash="dash"),
        ),
        row=1, col=1,
    )

    # q* heatmap
    q_star_grid = np.zeros((50, 50))
    for i, S_P in enumerate(ic_data["S_P"]):
        for j, P_set in enumerate(ic_data["P_set"]):
            eq = compute_theoretical_equilibrium(protocol, P_set, S_P, L)
            q_star_grid[i, j] = eq.q_star

    fig.add_trace(
        go.Heatmap(
            x=ic_data["P_set"],
            y=ic_data["S_P"],
            z=q_star_grid,
            colorscale="Reds",
            name="q*",
            colorbar=dict(title="q*", x=0.45),
        ),
        row=1, col=2,
    )

    # v* heatmap
    v_star_grid = np.zeros((50, 50))
    for i, S_P in enumerate(ic_data["S_P"]):
        for j, P_set in enumerate(ic_data["P_set"]):
            eq = compute_theoretical_equilibrium(protocol, P_set, S_P, L)
            v_star_grid[i, j] = eq.v_star

    fig.add_trace(
        go.Heatmap(
            x=ic_data["P_set"],
            y=ic_data["S_P"],
            z=v_star_grid,
            colorscale="Blues",
            name="v*",
            colorbar=dict(title="v*", x=1.0),
        ),
        row=2, col=1,
    )

    # S_P_min curve
    fig.add_trace(
        go.Scatter(
            x=ic_data["P_set"],
            y=ic_data["S_P_min_curve"],
            mode="lines+markers",
            name="S_P^min(P_set)",
            line=dict(color=COLORS["primary"], width=2),
        ),
        row=2, col=2,
    )

    fig.update_xaxes(title_text="P_set", row=1, col=1)
    fig.update_yaxes(title_text="S_P", row=1, col=1)
    fig.update_xaxes(title_text="P_set", row=1, col=2)
    fig.update_yaxes(title_text="S_P", row=1, col=2)
    fig.update_xaxes(title_text="P_set", row=2, col=1)
    fig.update_yaxes(title_text="S_P", row=2, col=1)
    fig.update_xaxes(title_text="P_set", row=2, col=2)
    fig.update_yaxes(title_text="S_P^min", row=2, col=2)

    fig.update_layout(
        title=title,
        height=800,
        template="plotly_white",
    )

    return fig


def plot_parameter_sensitivity(
    protocol: ProtocolParameters,
    parameter_name: str,
    parameter_values: List[float],
    P_set: float = 50.0,
    S_P: float = 100.0,
    L: float = 50.0,
    title: str = None,
) -> go.Figure:
    """
    Visualize sensitivity of equilibrium to a single parameter.
    """
    results = parameter_sensitivity_analysis(
        protocol, parameter_name, parameter_values, P_set, S_P, L
    )

    if title is None:
        title = f"Sensitivity to {parameter_name}"

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Cheating Rate q*",
            "Audit Rate v*",
            "Dispute Surplus Δ",
            "Expected Utilities",
        ),
    )

    # q*
    fig.add_trace(
        go.Scatter(
            x=parameter_values,
            y=results["q_star"],
            mode="lines+markers",
            name="q*",
            line=dict(color=COLORS["danger"]),
        ),
        row=1, col=1,
    )

    # v*
    fig.add_trace(
        go.Scatter(
            x=parameter_values,
            y=results["v_star"],
            mode="lines+markers",
            name="v*",
            line=dict(color=COLORS["success"]),
        ),
        row=1, col=2,
    )

    # Delta
    fig.add_trace(
        go.Scatter(
            x=parameter_values,
            y=results["Delta"],
            mode="lines+markers",
            name="Δ",
            line=dict(color=COLORS["primary"]),
        ),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

    # Expected utilities
    fig.add_trace(
        go.Scatter(
            x=parameter_values,
            y=results["expected_provider_utility"],
            mode="lines+markers",
            name="E[U_P]",
            line=dict(color=COLORS["primary"]),
        ),
        row=2, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=parameter_values,
            y=results["expected_client_utility"],
            mode="lines+markers",
            name="E[U_C]",
            line=dict(color=COLORS["secondary"]),
        ),
        row=2, col=2,
    )

    fig.update_xaxes(title_text=parameter_name)
    fig.update_layout(
        title=title,
        height=600,
        template="plotly_white",
        showlegend=True,
    )

    return fig


def plot_reputation_farming_analysis(
    result: SimulationResult,
    attack_metrics: Dict,
    title: str = "Reputation Farming Attack Analysis",
) -> go.Figure:
    """
    Specialized visualization for reputation farming attack.
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Reputation vs Fraud Detection",
            "Farming Phase Behavior",
            "Attack Profitability Over Time",
            "Victim Distribution",
        ),
    )

    periods = list(range(len(result.fraud_rate_history)))

    # Reputation vs Detection
    fig.add_trace(
        go.Scatter(
            x=result.avg_reputation_history,
            y=result.detection_rate_history,
            mode="markers",
            marker=dict(
                size=5,
                color=periods,
                colorscale="Viridis",
            ),
            name="Rep vs Detection",
        ),
        row=1, col=1,
    )

    # Add trend line showing inverse relationship
    if result.avg_reputation_history:
        z = np.polyfit(result.avg_reputation_history, result.detection_rate_history, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(result.avg_reputation_history), max(result.avg_reputation_history), 100)
        fig.add_trace(
            go.Scatter(
                x=x_trend,
                y=p(x_trend),
                mode="lines",
                name="Trend",
                line=dict(color="red", dash="dash"),
            ),
            row=1, col=1,
        )

    # Farming phase (first N periods)
    farming_periods = 50
    fig.add_trace(
        go.Scatter(
            x=periods[:farming_periods],
            y=result.fraud_rate_history[:farming_periods],
            mode="lines",
            name="Fraud Rate (Farming)",
            line=dict(color=COLORS["success"]),
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=periods[farming_periods:],
            y=result.fraud_rate_history[farming_periods:],
            mode="lines",
            name="Fraud Rate (Exploit)",
            line=dict(color=COLORS["danger"]),
        ),
        row=1, col=2,
    )

    # Cumulative adversarial profit
    adversarial_profit = attack_metrics.get("adversarial_total_profit", 0)
    honest_profit = attack_metrics.get("honest_mean_profit", 0) * len([
        p for p in result.provider_profits if "H" in p
    ])

    fig.add_trace(
        go.Bar(
            x=["Adversarial", "Honest (total)"],
            y=[adversarial_profit, honest_profit],
            marker_color=[COLORS["danger"], COLORS["success"]],
            name="Profits",
        ),
        row=2, col=1,
    )

    # Victim losses distribution
    client_losses = list(result.client_losses.values())
    fig.add_trace(
        go.Histogram(
            x=client_losses,
            nbinsx=30,
            name="Client Losses",
            marker_color=COLORS["warning"],
        ),
        row=2, col=2,
    )

    fig.update_layout(
        title=title,
        height=700,
        template="plotly_white",
    )

    return fig


def create_dashboard_figures(
    result: SimulationResult,
    attack_results: Optional[Dict[str, AttackResult]] = None,
) -> Dict[str, go.Figure]:
    """
    Create all figures for a Streamlit dashboard.
    """
    figures = {}

    # Main simulation results
    figures["simulation_overview"] = plot_simulation_results(result)

    # Equilibrium analysis
    figures["equilibrium"] = plot_equilibrium_analysis(result.config.protocol)

    # Parameter sensitivities
    protocol = result.config.protocol

    figures["sensitivity_stake"] = plot_parameter_sensitivity(
        protocol, "S_P_min",
        np.linspace(10, 200, 20).tolist(),
        title="Sensitivity to Minimum Stake"
    )

    figures["sensitivity_enforcement"] = plot_parameter_sensitivity(
        protocol, "p_w",
        np.linspace(0.5, 1.0, 20).tolist(),
        title="Sensitivity to Enforcement Probability"
    )

    figures["sensitivity_verification_cost"] = plot_parameter_sensitivity(
        protocol, "C_safe",
        np.linspace(1, 30, 20).tolist(),
        title="Sensitivity to Verification Cost"
    )

    # Attack comparison if available
    if attack_results:
        figures["attack_comparison"] = plot_attack_comparison(attack_results)

    return figures
