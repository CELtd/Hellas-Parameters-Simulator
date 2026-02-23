"""
Metrics and Theoretical Analysis for Hellas ABM

Computes theoretical equilibrium values and welfare metrics
to compare with simulation results.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np

from ..config import ProtocolParameters, SimulationConfig


@dataclass
class TheoreticalEquilibrium:
    """Theoretical equilibrium values from the paper."""
    v_star: float  # Equilibrium audit probability
    q_star: float  # Equilibrium cheating probability
    theta: float   # Provider incentive threshold
    Delta: float   # Net dispute surplus
    S_P_min: float # Minimum viable stake
    mu_star: float # Belief threshold for auditing

    is_enforcement_viable: bool
    is_ic_satisfied: bool

    # Expected outcomes
    expected_fraud_rate: float
    expected_detection_rate: float
    expected_provider_utility: float
    expected_client_utility: float


def compute_theoretical_equilibrium(
    protocol: ProtocolParameters,
    P_set: float,
    S_P: float,
    L: float,
) -> TheoreticalEquilibrium:
    """
    Compute theoretical equilibrium values from the paper.

    From Theorem 2 (Mixed Equilibrium):
    - v* = (c_H - c_F) / (P_set + S_P)
    - q* = C_safe / (L + Delta)

    where Delta = p_w(beta*S_P + lambda*P_set) - (c_proof + c_tx) - (1-p_w)*B_C
    """
    # Core equilibrium values
    v_star = protocol.compute_v_star(P_set, S_P)
    q_star = protocol.compute_q_star(S_P, P_set, L)
    theta = protocol.compute_theta(P_set, S_P)
    Delta = protocol.compute_Delta(S_P, P_set)
    S_P_min = protocol.compute_S_P_min_viable(P_set)
    mu_star = protocol.compute_mu_star(S_P, P_set, L)

    # Viability conditions
    is_enforcement_viable = S_P >= S_P_min
    is_ic_satisfied = v_star >= theta  # Always true at equilibrium

    # Expected outcomes at equilibrium
    expected_fraud_rate = q_star if L + Delta > 0 else 1.0
    expected_detection_rate = v_star if q_star > 0 else 1.0

    # Expected provider utility at equilibrium (indifference)
    # U_P(H) = P_set - c_H
    expected_provider_utility = P_set - protocol.c_H

    # Expected client utility
    # If provider cheats with prob q and client audits with prob v:
    # E[U_C] = -P_set - v*C_safe - (1-v)*q*L + v*q*Delta
    expected_client_utility = (
        -P_set
        - v_star * protocol.C_safe
        - (1 - v_star) * q_star * L
        + v_star * q_star * Delta
    )

    return TheoreticalEquilibrium(
        v_star=v_star,
        q_star=q_star,
        theta=theta,
        Delta=Delta,
        S_P_min=S_P_min,
        mu_star=mu_star,
        is_enforcement_viable=is_enforcement_viable,
        is_ic_satisfied=is_ic_satisfied,
        expected_fraud_rate=expected_fraud_rate,
        expected_detection_rate=expected_detection_rate,
        expected_provider_utility=expected_provider_utility,
        expected_client_utility=expected_client_utility,
    )


def compute_welfare_metrics(
    provider_profits: Dict[str, float],
    client_losses: Dict[str, float],
    challenger_profits: Dict[str, float],
    total_frauds: int,
    total_jobs: int,
) -> Dict[str, float]:
    """
    Compute welfare metrics for the simulation.

    Social welfare = sum of all agent utilities
    """
    provider_welfare = sum(provider_profits.values())
    client_welfare = -sum(client_losses.values())
    challenger_welfare = sum(challenger_profits.values())

    total_welfare = provider_welfare + client_welfare + challenger_welfare

    # Gini coefficient for provider profits
    profits = list(provider_profits.values())
    gini = _compute_gini(profits)

    return {
        "total_welfare": total_welfare,
        "provider_welfare": provider_welfare,
        "client_welfare": client_welfare,
        "challenger_welfare": challenger_welfare,
        "mean_provider_profit": np.mean(profits) if profits else 0,
        "std_provider_profit": np.std(profits) if profits else 0,
        "gini_coefficient": gini,
        "fraud_rate": total_frauds / total_jobs if total_jobs > 0 else 0,
        "avg_client_loss": np.mean(list(client_losses.values())) if client_losses else 0,
    }


def _compute_gini(values: List[float]) -> float:
    """Compute Gini coefficient of inequality."""
    if not values or len(values) < 2:
        return 0.0

    values = np.array(sorted(values))
    n = len(values)
    index = np.arange(1, n + 1)

    return (2 * np.sum(index * values)) / (n * np.sum(values)) - (n + 1) / n


def parameter_sensitivity_analysis(
    base_protocol: ProtocolParameters,
    parameter_name: str,
    parameter_values: List[float],
    P_set: float = 50.0,
    S_P: float = 100.0,
    L: float = 50.0,
) -> Dict[str, List[float]]:
    """
    Analyze sensitivity of equilibrium to a single parameter.

    Returns dict mapping metric names to lists of values.
    """
    results = {
        "parameter_values": parameter_values,
        "v_star": [],
        "q_star": [],
        "theta": [],
        "Delta": [],
        "S_P_min": [],
        "expected_fraud_rate": [],
        "expected_provider_utility": [],
        "expected_client_utility": [],
    }

    for value in parameter_values:
        # Create modified protocol
        protocol = ProtocolParameters(
            **{k: v for k, v in base_protocol.__dict__.items()}
        )
        setattr(protocol, parameter_name, value)

        # Compute equilibrium
        eq = compute_theoretical_equilibrium(protocol, P_set, S_P, L)

        results["v_star"].append(eq.v_star)
        results["q_star"].append(eq.q_star)
        results["theta"].append(eq.theta)
        results["Delta"].append(eq.Delta)
        results["S_P_min"].append(eq.S_P_min)
        results["expected_fraud_rate"].append(eq.expected_fraud_rate)
        results["expected_provider_utility"].append(eq.expected_provider_utility)
        results["expected_client_utility"].append(eq.expected_client_utility)

    return results


def compute_stake_thresholds(
    protocol: ProtocolParameters,
    P_set_values: List[float],
    L: float = 50.0,
) -> Dict[str, List[float]]:
    """
    Compute minimum viable stake for different payment levels.

    From Proposition 2:
    S_P^min = max{0, (C_disp + (1-p_w)B_C - p_w*lambda*P_set) / (p_w*beta)}
    """
    results = {
        "P_set": P_set_values,
        "S_P_min": [],
        "q_star_at_min": [],
        "v_star_at_min": [],
    }

    for P_set in P_set_values:
        S_P_min = protocol.compute_S_P_min_viable(P_set)
        results["S_P_min"].append(S_P_min)

        # Equilibrium at minimum stake
        if S_P_min > 0:
            eq = compute_theoretical_equilibrium(protocol, P_set, S_P_min, L)
            results["q_star_at_min"].append(eq.q_star)
            results["v_star_at_min"].append(eq.v_star)
        else:
            results["q_star_at_min"].append(0)
            results["v_star_at_min"].append(0)

    return results


def compute_incentive_compatibility_region(
    protocol: ProtocolParameters,
    P_set_range: Tuple[float, float] = (10, 200),
    S_P_range: Tuple[float, float] = (10, 500),
    resolution: int = 50,
) -> Dict[str, np.ndarray]:
    """
    Compute the incentive compatibility region in (P_set, S_P) space.

    IC requires: p_d >= theta = (c_H - c_F) / (P_set + S_P)

    Also computes the minimum viable stake curve.
    """
    P_set_vals = np.linspace(P_set_range[0], P_set_range[1], resolution)
    S_P_vals = np.linspace(S_P_range[0], S_P_range[1], resolution)

    P_grid, S_grid = np.meshgrid(P_set_vals, S_P_vals)

    # Compute theta at each point
    theta_grid = (protocol.c_H - protocol.c_F) / (P_grid + S_grid)

    # Compute S_P_min curve
    S_P_min_curve = np.array([
        protocol.compute_S_P_min_viable(P)
        for P in P_set_vals
    ])

    # IC region: where stake >= S_P_min
    ic_region = S_grid >= np.tile(S_P_min_curve, (resolution, 1))

    return {
        "P_set": P_set_vals,
        "S_P": S_P_vals,
        "theta": theta_grid,
        "S_P_min_curve": S_P_min_curve,
        "ic_region": ic_region,
    }


def analyze_attack_profitability(
    protocol: ProtocolParameters,
    P_set: float,
    S_P: float,
    L: float,
    attack_type: str,
) -> Dict[str, float]:
    """
    Analyze the profitability of different attacks.

    Returns expected profit/loss from the attack.
    """
    eq = compute_theoretical_equilibrium(protocol, P_set, S_P, L)

    if attack_type == "reputation_farming":
        # Profit from reduced auditing after building reputation
        # Assume reputation reduces audit rate by 50%
        reduced_v = eq.v_star * 0.5
        cheat_profit = P_set - protocol.c_F - reduced_v * (P_set + S_P)
        honest_profit = P_set - protocol.c_H

        return {
            "cheat_profit": cheat_profit,
            "honest_profit": honest_profit,
            "attack_advantage": cheat_profit - honest_profit,
            "farming_cost": protocol.c_H * 20,  # Cost of 20 honest jobs
            "net_attack_profit": cheat_profit - honest_profit - protocol.c_H * 20 / 5,
        }

    elif attack_type == "no_stake_floor":
        # Profit from using minimal stake
        min_stake = 1.0
        # Check if disputing is still viable
        S_P_min = protocol.compute_S_P_min_viable(P_set)

        if min_stake < S_P_min:
            # Disputing not viable, can cheat freely
            cheat_profit = P_set - protocol.c_F
        else:
            cheat_profit = P_set - protocol.c_F - eq.v_star * (P_set + min_stake)

        return {
            "cheat_profit": cheat_profit,
            "honest_profit": P_set - protocol.c_H,
            "attack_advantage": cheat_profit - (P_set - protocol.c_H),
            "S_P_min_viable": S_P_min,
            "disputing_viable": min_stake >= S_P_min,
        }

    elif attack_type == "censorship":
        # Profit from reduced enforcement
        reduced_p_w = protocol.p_w * 0.7  # 30% censorship
        reduced_Delta = (
            reduced_p_w * (protocol.beta * S_P + protocol.lambda_ * P_set)
            - (protocol.c_proof + protocol.c_tx)
            - (1 - reduced_p_w) * protocol.B_C
        )

        # New equilibrium with reduced enforcement
        new_q_star = protocol.C_safe / (L + reduced_Delta) if L + reduced_Delta > 0 else 1.0

        return {
            "original_q_star": eq.q_star,
            "new_q_star": new_q_star,
            "fraud_rate_increase": new_q_star - eq.q_star,
            "original_Delta": eq.Delta,
            "new_Delta": reduced_Delta,
        }

    else:
        return {"error": f"Unknown attack type: {attack_type}"}
