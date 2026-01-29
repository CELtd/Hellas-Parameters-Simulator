"""
Hellas Fraud Game ABM Simulator

A comprehensive Agent-Based Model for analyzing incentive compatibility
in off-chain computation protocols.

Based on: "Fraud Game Analysis for Hellas Protocol" (CryptoEconLab, 2026)

Example usage:
    from simulation import SimulationConfig, SimulationEngine
    from simulation.attacks import ReputationFarmingAttack

    # Run baseline simulation
    config = SimulationConfig(n_periods=500)
    engine = SimulationEngine(config)
    result = engine.run()

    # Run attack analysis
    attack = ReputationFarmingAttack(config)
    attack_result = attack.run()
"""

from .config import (
    SimulationConfig,
    ProtocolParameters,
    ReputationParameters,
    AttackParameters,
    AgentStrategy,
    ClientBehavior,
    BASELINE_CONFIG,
    WEAK_ENFORCEMENT_CONFIG,
    HIGH_VERIFICATION_COST_CONFIG,
    NO_STAKE_FLOOR_CONFIG,
    ADVERSARIAL_HEAVY_CONFIG,
)

from .core.engine import SimulationEngine, SimulationResult
from .core.market import Market, MarketState
from .core.reputation import ReputationSystem

from .agents import (
    Provider, HonestProvider, RationalProvider, AdversarialProvider,
    Client, MixedStrategyClient, BeliefThresholdClient,
    Challenger, PermissionlessChallenger,
)

from .attacks import (
    ReputationFarmingAttack,
    SybilAttack,
    CollusionAttack,
    GriefingAttack,
    NoStakeFloorAttack,
    CensorshipAttack,
    run_attack_scenario,
)

from .analysis import (
    plot_simulation_results,
    plot_attack_comparison,
    plot_equilibrium_analysis,
    plot_parameter_sensitivity,
    compute_theoretical_equilibrium,
    compute_welfare_metrics,
)

__version__ = "1.0.0"
__author__ = "CryptoEconLab"

__all__ = [
    # Config
    "SimulationConfig",
    "ProtocolParameters",
    "ReputationParameters",
    "AttackParameters",
    "AgentStrategy",
    "ClientBehavior",
    "BASELINE_CONFIG",
    "WEAK_ENFORCEMENT_CONFIG",
    "HIGH_VERIFICATION_COST_CONFIG",
    "NO_STAKE_FLOOR_CONFIG",
    "ADVERSARIAL_HEAVY_CONFIG",
    # Core
    "SimulationEngine",
    "SimulationResult",
    "Market",
    "MarketState",
    "ReputationSystem",
    # Agents
    "Provider",
    "HonestProvider",
    "RationalProvider",
    "AdversarialProvider",
    "Client",
    "MixedStrategyClient",
    "BeliefThresholdClient",
    "Challenger",
    "PermissionlessChallenger",
    # Attacks
    "ReputationFarmingAttack",
    "SybilAttack",
    "CollusionAttack",
    "GriefingAttack",
    "NoStakeFloorAttack",
    "CensorshipAttack",
    "run_attack_scenario",
    # Analysis
    "plot_simulation_results",
    "plot_attack_comparison",
    "plot_equilibrium_analysis",
    "plot_parameter_sensitivity",
    "compute_theoretical_equilibrium",
    "compute_welfare_metrics",
]
