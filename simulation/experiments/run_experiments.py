"""
Experiment Runner for Hellas ABM

This module provides functions to run comprehensive experiments
and generate publication-quality analysis.

Usage:
    python -m simulation.experiments.run_experiments

Or in Python:
    from simulation.experiments import run_full_analysis
    results = run_full_analysis()
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
import warnings

from ..config import (
    SimulationConfig, ProtocolParameters, ReputationParameters,
    BASELINE_CONFIG, WEAK_ENFORCEMENT_CONFIG, NO_STAKE_FLOOR_CONFIG,
)
from ..core.engine import SimulationEngine, SimulationResult
from ..attacks.scenarios import (
    ReputationFarmingAttack, SybilAttack, CollusionAttack,
    GriefingAttack, NoStakeFloorAttack, CensorshipAttack,
    run_all_attacks, AttackResult,
)
from ..analysis.metrics import (
    compute_theoretical_equilibrium, compute_welfare_metrics,
    parameter_sensitivity_analysis, compute_stake_thresholds,
    analyze_attack_profitability,
)
from ..analysis.visualization import (
    plot_simulation_results, plot_attack_comparison,
    plot_equilibrium_analysis, plot_parameter_sensitivity,
)


@dataclass
class ExperimentResult:
    """Container for experiment results."""
    name: str
    timestamp: str
    config: Dict
    metrics: Dict
    time_series: Dict
    attack_results: Optional[Dict] = None
    sensitivity_results: Optional[Dict] = None


def run_baseline_experiment(
    n_periods: int = 1000,
    n_runs: int = 5,
    seed_base: int = 42,
    verbose: bool = True,
) -> ExperimentResult:
    """
    Run baseline experiment with multiple random seeds.

    Returns aggregated statistics across runs.
    """
    if verbose:
        print(f"Running baseline experiment ({n_runs} runs, {n_periods} periods each)...")

    results = []
    for i in range(n_runs):
        config = SimulationConfig(n_periods=n_periods, seed=seed_base + i)
        engine = SimulationEngine(config)
        result = engine.run(show_progress=verbose)
        results.append(result)

    # Aggregate metrics
    metrics = {
        "fraud_rate": {
            "mean": np.mean([r.fraud_rate for r in results]),
            "std": np.std([r.fraud_rate for r in results]),
            "min": np.min([r.fraud_rate for r in results]),
            "max": np.max([r.fraud_rate for r in results]),
        },
        "detection_rate": {
            "mean": np.mean([r.detection_rate for r in results]),
            "std": np.std([r.detection_rate for r in results]),
        },
        "total_stake_slashed": {
            "mean": np.mean([r.total_stake_slashed for r in results]),
            "std": np.std([r.total_stake_slashed for r in results]),
        },
        "social_welfare": {
            "mean": np.mean([r.social_welfare for r in results]),
            "std": np.std([r.social_welfare for r in results]),
        },
    }

    # Time series (averaged)
    time_series = {
        "fraud_rate_history": np.mean(
            [r.fraud_rate_history for r in results], axis=0
        ).tolist(),
        "detection_rate_history": np.mean(
            [r.detection_rate_history for r in results], axis=0
        ).tolist(),
    }

    # Compare to theoretical equilibrium
    protocol = BASELINE_CONFIG.protocol
    eq = compute_theoretical_equilibrium(
        protocol,
        BASELINE_CONFIG.job_value_mean,
        protocol.S_P_min,
        protocol.L_base,
    )

    metrics["theoretical_comparison"] = {
        "q_star_theoretical": eq.q_star,
        "q_star_simulated": metrics["fraud_rate"]["mean"],
        "v_star_theoretical": eq.v_star,
        "deviation": abs(eq.q_star - metrics["fraud_rate"]["mean"]),
    }

    if verbose:
        print(f"\nBaseline Results:")
        print(f"  Fraud Rate: {metrics['fraud_rate']['mean']:.4f} ± {metrics['fraud_rate']['std']:.4f}")
        print(f"  Theoretical q*: {eq.q_star:.4f}")
        print(f"  Detection Rate: {metrics['detection_rate']['mean']:.4f}")

    return ExperimentResult(
        name="baseline",
        timestamp=datetime.now().isoformat(),
        config=BASELINE_CONFIG.__dict__,
        metrics=metrics,
        time_series=time_series,
    )


def run_parameter_sweep(
    parameter_name: str,
    parameter_values: List[float],
    n_periods: int = 500,
    n_runs: int = 3,
    verbose: bool = True,
) -> ExperimentResult:
    """
    Sweep a single parameter and measure outcomes.
    """
    if verbose:
        print(f"Running parameter sweep: {parameter_name}")
        print(f"  Values: {parameter_values[:3]}...{parameter_values[-3:]}")

    results = []

    for value in parameter_values:
        # Create modified config
        protocol_dict = {k: v for k, v in BASELINE_CONFIG.protocol.__dict__.items()}
        protocol_dict[parameter_name] = value
        protocol = ProtocolParameters(**protocol_dict)

        config = SimulationConfig(
            n_periods=n_periods,
            protocol=protocol,
        )

        # Run multiple seeds
        run_results = []
        for seed in range(n_runs):
            config.seed = seed
            engine = SimulationEngine(config)
            result = engine.run(show_progress=False)
            run_results.append(result)

        # Aggregate
        results.append({
            "parameter_value": value,
            "fraud_rate_mean": np.mean([r.fraud_rate for r in run_results]),
            "fraud_rate_std": np.std([r.fraud_rate for r in run_results]),
            "detection_rate_mean": np.mean([r.detection_rate for r in run_results]),
            "welfare_mean": np.mean([r.social_welfare for r in run_results]),
        })

        if verbose:
            print(f"  {parameter_name}={value:.2f}: fraud_rate={results[-1]['fraud_rate_mean']:.4f}")

    return ExperimentResult(
        name=f"sweep_{parameter_name}",
        timestamp=datetime.now().isoformat(),
        config={"parameter_name": parameter_name, "values": parameter_values},
        metrics={},
        time_series={},
        sensitivity_results={"sweep_data": results},
    )


def run_attack_comparison(
    n_periods: int = 500,
    verbose: bool = True,
) -> ExperimentResult:
    """
    Run all attack scenarios and compare to baseline.
    """
    if verbose:
        print("Running attack comparison analysis...")

    # Run all attacks
    attack_results = run_all_attacks(
        BASELINE_CONFIG,
        n_periods=n_periods,
        show_progress=verbose,
    )

    # Extract key metrics
    metrics = {}
    for name, result in attack_results.items():
        metrics[name] = {
            "fraud_rate_increase": result.fraud_rate_increase,
            "detection_rate_change": result.detection_rate_change,
            "attacker_profit": result.attacker_profit,
            "victim_losses": result.victim_losses,
            "welfare_loss": result.social_welfare_loss,
            "attack_success_ratio": result.attack_result.attack_metrics.get(
                "attack_success_ratio", 0
            ),
        }

    # Rank attacks by severity
    ranked = sorted(
        metrics.items(),
        key=lambda x: x[1]["welfare_loss"],
        reverse=True,
    )

    if verbose:
        print("\nAttack Severity Ranking (by welfare loss):")
        for i, (name, m) in enumerate(ranked, 1):
            print(f"  {i}. {name}: welfare_loss=${m['welfare_loss']:.2f}, fraud_rate_Δ={m['fraud_rate_increase']:+.2%}")

    return ExperimentResult(
        name="attack_comparison",
        timestamp=datetime.now().isoformat(),
        config=BASELINE_CONFIG.__dict__,
        metrics=metrics,
        time_series={},
        attack_results={name: str(r) for name, r in attack_results.items()},
    )


def run_reputation_farming_deep_dive(
    farming_periods_list: List[int] = [20, 50, 100, 200],
    n_periods: int = 500,
    verbose: bool = True,
) -> ExperimentResult:
    """
    Deep dive into reputation farming attack mechanics.
    """
    if verbose:
        print("Running reputation farming deep dive...")

    results = []

    for farming_periods in farming_periods_list:
        attack = ReputationFarmingAttack(
            BASELINE_CONFIG,
            farming_periods=farming_periods,
            min_stake_enforced=False,
        )
        result = attack.run(n_periods=n_periods, show_progress=False)

        results.append({
            "farming_periods": farming_periods,
            "baseline_fraud_rate": result.baseline_result.fraud_rate,
            "attack_fraud_rate": result.attack_result.fraud_rate,
            "fraud_rate_increase": result.fraud_rate_increase,
            "attacker_profit": result.attacker_profit,
            "roi": result.attacker_profit / (BASELINE_CONFIG.protocol.c_H * farming_periods)
            if farming_periods > 0 else 0,
        })

        if verbose:
            print(f"  Farming {farming_periods} periods: Δfraud={result.fraud_rate_increase:+.2%}, "
                  f"ROI={results[-1]['roi']:.2f}x")

    # Find optimal farming duration
    optimal_idx = np.argmax([r["roi"] for r in results])
    optimal_farming = farming_periods_list[optimal_idx]

    metrics = {
        "results": results,
        "optimal_farming_periods": optimal_farming,
        "max_roi": results[optimal_idx]["roi"],
    }

    return ExperimentResult(
        name="reputation_farming_deep_dive",
        timestamp=datetime.now().isoformat(),
        config={},
        metrics=metrics,
        time_series={},
    )


def run_stake_threshold_analysis(
    P_set_values: List[float] = None,
    verbose: bool = True,
) -> ExperimentResult:
    """
    Analyze minimum viable stake thresholds across payment levels.
    """
    if P_set_values is None:
        P_set_values = np.linspace(10, 200, 20).tolist()

    if verbose:
        print("Running stake threshold analysis...")

    protocol = BASELINE_CONFIG.protocol
    results = compute_stake_thresholds(protocol, P_set_values)

    # Find break-even points
    break_even_idx = np.argmin(np.abs(np.array(results["S_P_min"]) - np.array(P_set_values)))

    metrics = {
        "threshold_data": {
            "P_set": results["P_set"],
            "S_P_min": results["S_P_min"],
            "q_star_at_min": results["q_star_at_min"],
        },
        "break_even_P_set": P_set_values[break_even_idx],
        "stake_to_payment_ratio": [
            s / p if p > 0 else 0
            for s, p in zip(results["S_P_min"], P_set_values)
        ],
    }

    if verbose:
        print(f"  Break-even P_set: {metrics['break_even_P_set']:.2f}")
        print(f"  At P_set=50: S_P^min = {protocol.compute_S_P_min_viable(50):.2f}")

    return ExperimentResult(
        name="stake_threshold_analysis",
        timestamp=datetime.now().isoformat(),
        config={"protocol": protocol.__dict__},
        metrics=metrics,
        time_series={},
    )


def run_full_analysis(
    output_dir: str = None,
    n_periods: int = 500,
    verbose: bool = True,
) -> Dict[str, ExperimentResult]:
    """
    Run comprehensive analysis including all experiments.

    This is the main entry point for generating publication-quality results.
    """
    if verbose:
        print("=" * 60)
        print("HELLAS FRAUD GAME ABM - FULL ANALYSIS")
        print("=" * 60)

    results = {}

    # 1. Baseline experiment
    results["baseline"] = run_baseline_experiment(
        n_periods=n_periods, n_runs=5, verbose=verbose
    )

    # 2. Parameter sweeps
    key_parameters = {
        "S_P_min": np.linspace(10, 300, 15).tolist(),
        "p_w": np.linspace(0.5, 1.0, 11).tolist(),
        "C_safe": np.linspace(1, 30, 15).tolist(),
        "beta": np.linspace(0.1, 1.0, 10).tolist(),
    }

    for param_name, values in key_parameters.items():
        results[f"sweep_{param_name}"] = run_parameter_sweep(
            param_name, values, n_periods=n_periods // 2, verbose=verbose
        )

    # 3. Attack comparison
    results["attacks"] = run_attack_comparison(n_periods=n_periods, verbose=verbose)

    # 4. Reputation farming deep dive
    results["reputation_farming"] = run_reputation_farming_deep_dive(
        n_periods=n_periods, verbose=verbose
    )

    # 5. Stake threshold analysis
    results["stake_thresholds"] = run_stake_threshold_analysis(verbose=verbose)

    # Save results if output directory specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save JSON summary
        summary = {
            name: {
                "name": r.name,
                "timestamp": r.timestamp,
                "metrics": r.metrics,
            }
            for name, r in results.items()
        }

        with open(output_path / "results_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)

        if verbose:
            print(f"\nResults saved to {output_path}")

    if verbose:
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)

        # Print key findings
        print("\nKEY FINDINGS:")
        print("-" * 40)

        # Baseline
        baseline = results["baseline"].metrics
        print(f"1. Baseline fraud rate: {baseline['fraud_rate']['mean']:.4f} ± {baseline['fraud_rate']['std']:.4f}")
        print(f"   Theoretical q*: {baseline['theoretical_comparison']['q_star_theoretical']:.4f}")

        # Attacks
        if "attacks" in results:
            attacks = results["attacks"].metrics
            worst_attack = max(attacks.items(), key=lambda x: x[1]["welfare_loss"])
            print(f"2. Most damaging attack: {worst_attack[0]}")
            print(f"   Welfare loss: ${worst_attack[1]['welfare_loss']:.2f}")

        # Reputation farming
        if "reputation_farming" in results:
            rf = results["reputation_farming"].metrics
            print(f"3. Optimal reputation farming: {rf['optimal_farming_periods']} periods")
            print(f"   Maximum ROI: {rf['max_roi']:.2f}x")

    return results


def generate_publication_figures(
    results: Dict[str, ExperimentResult],
    output_dir: str = "figures",
    format: str = "pdf",
):
    """
    Generate publication-quality figures from experiment results.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # This would generate figures using matplotlib/plotly
    # For now, just create the visualization objects
    warnings.warn("Figure generation not yet fully implemented")


if __name__ == "__main__":
    # Run full analysis when executed as script
    results = run_full_analysis(output_dir="results", n_periods=500, verbose=True)
