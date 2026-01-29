#!/usr/bin/env python3
"""
Run comprehensive experiments for the LaTeX report.
Outputs data in a format suitable for LaTeX tables and figures.
"""

import numpy as np
import json
from pathlib import Path

from simulation.config import SimulationConfig, ProtocolParameters
from simulation.core.engine import SimulationEngine
from simulation.analysis.metrics import (
    compute_theoretical_equilibrium,
    parameter_sensitivity_analysis,
    compute_stake_thresholds,
)
from simulation.attacks.scenarios import (
    ReputationFarmingAttack,
    NoStakeFloorAttack,
    SybilAttack,
    CollusionAttack,
    GriefingAttack,
    CensorshipAttack,
)


def run_baseline_convergence(n_periods=1000, n_runs=10):
    """Test convergence of simulated values to theoretical equilibrium."""
    print("=" * 60)
    print("EXPERIMENT 1: Baseline Convergence Analysis")
    print("=" * 60)

    protocol = ProtocolParameters()
    config = SimulationConfig(
        n_providers=50,
        n_clients=100,
        n_periods=n_periods,
        jobs_per_period=20,
    )

    # Theoretical values
    eq = compute_theoretical_equilibrium(protocol, P_set=50, S_P=100, L=50)

    results = {
        "theoretical": {
            "v_star": eq.v_star,
            "q_star": eq.q_star,
            "theta": eq.theta,
            "Delta": eq.Delta,
            "S_P_min": eq.S_P_min,
        },
        "simulated": [],
    }

    for seed in range(n_runs):
        print(f"  Run {seed + 1}/{n_runs}...")
        config.seed = seed
        engine = SimulationEngine(config)
        result = engine.run(show_progress=False)

        results["simulated"].append({
            "seed": seed,
            "fraud_rate": result.fraud_rate,
            "detection_rate": result.detection_rate,
            "total_jobs": result.total_jobs,
            "total_frauds": result.total_frauds,
            "welfare": result.social_welfare,
            "fraud_rate_history": result.fraud_rate_history[::10],  # Sample every 10
        })

    # Compute statistics
    fraud_rates = [r["fraud_rate"] for r in results["simulated"]]
    results["statistics"] = {
        "fraud_rate_mean": np.mean(fraud_rates),
        "fraud_rate_std": np.std(fraud_rates),
        "fraud_rate_min": np.min(fraud_rates),
        "fraud_rate_max": np.max(fraud_rates),
        "deviation_from_theory": abs(np.mean(fraud_rates) - eq.q_star),
    }

    print(f"\n  Theoretical q* = {eq.q_star:.4f}")
    print(f"  Simulated mean = {results['statistics']['fraud_rate_mean']:.4f} ± {results['statistics']['fraud_rate_std']:.4f}")
    print(f"  Deviation = {results['statistics']['deviation_from_theory']:.4f}")

    return results


def run_parameter_sensitivity():
    """Analyze sensitivity to key parameters."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Parameter Sensitivity Analysis")
    print("=" * 60)

    protocol = ProtocolParameters()
    results = {}

    # Parameters to analyze
    params = {
        "S_P_min": np.linspace(10, 300, 15).tolist(),
        "p_w": np.linspace(0.5, 1.0, 11).tolist(),
        "C_safe": np.linspace(2, 30, 15).tolist(),
        "beta": np.linspace(0.1, 1.0, 10).tolist(),
        "L_base": np.linspace(10, 150, 15).tolist(),
    }

    for param_name, values in params.items():
        print(f"\n  Analyzing {param_name}...")
        sensitivity = parameter_sensitivity_analysis(
            protocol, param_name, values,
            P_set=50, S_P=100, L=50
        )
        results[param_name] = {
            "values": values,
            "q_star": sensitivity["q_star"],
            "v_star": sensitivity["v_star"],
            "Delta": sensitivity["Delta"],
            "S_P_min": sensitivity["S_P_min"],
        }

    return results


def run_attack_analysis(n_periods=500):
    """Comprehensive attack vector analysis."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Attack Vector Analysis")
    print("=" * 60)

    config = SimulationConfig(
        n_providers=50,
        n_clients=100,
        n_periods=n_periods,
        seed=42,
    )

    results = {}

    # Baseline
    print("\n  Running baseline...")
    engine = SimulationEngine(config)
    baseline = engine.run(show_progress=False)
    results["baseline"] = {
        "fraud_rate": baseline.fraud_rate,
        "detection_rate": baseline.detection_rate,
        "welfare": baseline.social_welfare,
        "client_losses": baseline.total_client_losses,
    }

    # Attack scenarios
    attacks = [
        ("reputation_farming_enforced", ReputationFarmingAttack(config, min_stake_enforced=True)),
        ("reputation_farming_no_enforce", ReputationFarmingAttack(config, min_stake_enforced=False)),
        ("no_stake_floor", NoStakeFloorAttack(config, min_stake_override=1.0)),
        ("sybil", SybilAttack(config, n_sybils_per_attacker=10)),
        ("collusion", CollusionAttack(config, n_colluding_pairs=10)),
        ("griefing", GriefingAttack(config, n_griefers=5)),
        ("censorship_30", CensorshipAttack(config, censorship_rate=0.3)),
        ("censorship_50", CensorshipAttack(config, censorship_rate=0.5)),
    ]

    for name, attack in attacks:
        print(f"  Running {name}...")
        result = attack.run(n_periods=n_periods, show_progress=False)
        results[name] = {
            "fraud_rate": result.attack_result.fraud_rate,
            "fraud_rate_increase": result.fraud_rate_increase,
            "detection_rate": result.attack_result.detection_rate,
            "detection_rate_change": result.detection_rate_change,
            "welfare": result.attack_result.social_welfare,
            "welfare_loss": result.social_welfare_loss,
            "attacker_profit": result.attacker_profit,
            "victim_losses": result.victim_losses,
        }

    return results


def run_reputation_farming_deep_analysis(n_periods=500):
    """Deep dive into reputation farming mechanics."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Reputation Farming Deep Analysis")
    print("=" * 60)

    config = SimulationConfig(n_periods=n_periods, seed=42)

    # Vary farming duration
    farming_periods = [10, 25, 50, 75, 100, 150, 200]
    results = {"farming_duration": []}

    for periods in farming_periods:
        print(f"  Farming period = {periods}...")
        attack = ReputationFarmingAttack(
            config,
            farming_periods=periods,
            min_stake_enforced=False,
        )
        result = attack.run(n_periods=n_periods, show_progress=False)

        # Estimate ROI
        farming_cost = config.protocol.c_H * periods
        exploit_profit = result.attacker_profit

        results["farming_duration"].append({
            "periods": periods,
            "fraud_rate_increase": result.fraud_rate_increase,
            "attacker_profit": exploit_profit,
            "farming_cost": farming_cost,
            "roi": exploit_profit / farming_cost if farming_cost > 0 else 0,
        })

    # Find optimal
    rois = [r["roi"] for r in results["farming_duration"]]
    optimal_idx = np.argmax(rois)
    results["optimal_farming_period"] = farming_periods[optimal_idx]
    results["max_roi"] = rois[optimal_idx]

    print(f"\n  Optimal farming period: {results['optimal_farming_period']}")
    print(f"  Maximum ROI: {results['max_roi']:.2f}x")

    return results


def run_stake_threshold_analysis():
    """Analyze minimum viable stake across payment levels."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 5: Stake Threshold Analysis")
    print("=" * 60)

    protocol = ProtocolParameters()
    P_set_values = np.linspace(10, 200, 20).tolist()

    results = compute_stake_thresholds(protocol, P_set_values)

    # Additional analysis at different enforcement probabilities
    p_w_values = [0.7, 0.85, 0.95, 1.0]
    results["by_enforcement"] = {}

    for p_w in p_w_values:
        protocol_mod = ProtocolParameters(p_w=p_w)
        thresholds = compute_stake_thresholds(protocol_mod, P_set_values)
        results["by_enforcement"][str(p_w)] = thresholds["S_P_min"]

    return results


def main():
    """Run all experiments and save results."""
    print("\n" + "=" * 60)
    print("HELLAS ABM - COMPREHENSIVE EXPERIMENTAL ANALYSIS")
    print("=" * 60)

    all_results = {}

    # Run experiments
    all_results["convergence"] = run_baseline_convergence(n_periods=500, n_runs=5)
    all_results["sensitivity"] = run_parameter_sensitivity()
    all_results["attacks"] = run_attack_analysis(n_periods=300)
    all_results["reputation_farming"] = run_reputation_farming_deep_analysis(n_periods=300)
    all_results["stake_thresholds"] = run_stake_threshold_analysis()

    # Save results
    output_dir = Path("simulation/results")
    output_dir.mkdir(exist_ok=True)

    # Convert numpy arrays to lists for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(v) for v in obj]
        return obj

    serializable_results = convert_to_serializable(all_results)

    with open(output_dir / "experiment_results.json", "w") as f:
        json.dump(serializable_results, f, indent=2)

    print("\n" + "=" * 60)
    print("EXPERIMENTS COMPLETE")
    print(f"Results saved to {output_dir / 'experiment_results.json'}")
    print("=" * 60)

    # Print summary for LaTeX
    print("\n\nLATEX TABLE DATA SUMMARY:")
    print("-" * 60)

    # Convergence
    conv = all_results["convergence"]
    print(f"\nConvergence (Table 1):")
    print(f"  q* theoretical: {conv['theoretical']['q_star']:.4f}")
    print(f"  q* simulated:   {conv['statistics']['fraud_rate_mean']:.4f} ± {conv['statistics']['fraud_rate_std']:.4f}")

    # Attacks
    print(f"\nAttack Results (Table 2):")
    for name, data in all_results["attacks"].items():
        if name != "baseline":
            print(f"  {name}: Δq={data['fraud_rate_increase']:+.4f}, welfare_loss=${data['welfare_loss']:.0f}")

    return all_results


if __name__ == "__main__":
    results = main()
