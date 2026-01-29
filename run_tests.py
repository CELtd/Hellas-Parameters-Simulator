#!/usr/bin/env python3
"""
Quick test script to verify the Hellas ABM simulator works correctly.

Run with: python run_tests.py
"""

import sys
import os
import numpy as np


def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")

    from simulation.config import SimulationConfig, ProtocolParameters
    from simulation.core.engine import SimulationEngine
    from simulation.core.reputation import ReputationSystem
    from simulation.agents.provider import HonestProvider, RationalProvider, AdversarialProvider
    from simulation.agents.client import MixedStrategyClient, BeliefThresholdClient
    from simulation.analysis.metrics import compute_theoretical_equilibrium
    from simulation.attacks.scenarios import ReputationFarmingAttack, NoStakeFloorAttack

    print("  All imports successful")
    return True


def test_theoretical_equilibrium():
    """Test theoretical equilibrium computation."""
    print("\nTesting theoretical equilibrium...")

    from simulation.config import ProtocolParameters
    from simulation.analysis.metrics import compute_theoretical_equilibrium

    protocol = ProtocolParameters()
    eq = compute_theoretical_equilibrium(protocol, P_set=50, S_P=100, L=50)

    # Verify key relationships
    assert 0 < eq.v_star < 1, f"v* should be in (0,1), got {eq.v_star}"
    assert 0 < eq.q_star < 1, f"q* should be in (0,1), got {eq.q_star}"

    print(f"  v* = {eq.v_star:.6f}")
    print(f"  q* = {eq.q_star:.6f}")
    print(f"  Delta = {eq.Delta:.2f}")
    print(f"  S_P^min = {eq.S_P_min:.2f}")
    print("  Theoretical equilibrium computed correctly")
    return True


def test_simulation():
    """Test running a short simulation."""
    print("\nTesting simulation engine...")

    from simulation.config import SimulationConfig, ProtocolParameters
    from simulation.core.engine import SimulationEngine

    config = SimulationConfig(
        n_providers=10,
        n_clients=20,
        n_challengers=2,
        n_periods=50,
        jobs_per_period=5,
        seed=42,
    )

    engine = SimulationEngine(config)
    result = engine.run(show_progress=False)

    assert result.total_jobs > 0, "Should have some jobs"
    assert 0 <= result.fraud_rate <= 1, "Fraud rate should be valid"
    assert len(result.fraud_rate_history) == config.n_periods

    print(f"  Total jobs: {result.total_jobs}")
    print(f"  Fraud rate: {result.fraud_rate:.4f}")
    print(f"  Detection rate: {result.detection_rate:.4f}")
    print("  Simulation completed successfully")
    return True


def test_attack_scenario():
    """Test attack scenario analysis."""
    print("\nTesting attack scenarios...")

    from simulation.config import SimulationConfig
    from simulation.attacks.scenarios import NoStakeFloorAttack

    config = SimulationConfig(
        n_periods=30,
        n_providers=10,
        n_clients=20,
    )

    attack = NoStakeFloorAttack(config, min_stake_override=1.0)
    result = attack.run(n_periods=30, show_progress=False)

    assert result.baseline_result is not None
    assert result.attack_result is not None

    print(f"  Baseline fraud rate: {result.baseline_result.fraud_rate:.4f}")
    print(f"  Attack fraud rate: {result.attack_result.fraud_rate:.4f}")
    print(f"  Fraud rate increase: {result.fraud_rate_increase:+.4f}")
    print("  Attack scenario analysis working")
    return True


def test_reputation_system():
    """Test reputation system mechanics."""
    print("\nTesting reputation system...")

    from simulation.core.reputation import ReputationSystem

    rep_system = ReputationSystem()
    provider_id = "test_provider"

    # Register and update
    rep_system.register_provider(provider_id)
    initial_rep = rep_system.get_reputation(provider_id)

    # Record honest jobs
    for _ in range(5):
        rep_system.record_job_outcome(provider_id, honest=True, stake_used=100, job_value=50)

    after_honest = rep_system.get_reputation(provider_id)
    assert after_honest > initial_rep, "Reputation should increase after honest jobs"

    # Record fraud
    rep_system.record_job_outcome(provider_id, honest=False, stake_used=100, job_value=50)
    after_fraud = rep_system.get_reputation(provider_id)
    assert after_fraud < after_honest, "Reputation should decrease after detected fraud"

    print(f"  Initial reputation: {initial_rep:.2f}")
    print(f"  After 5 honest jobs: {after_honest:.2f}")
    print(f"  After 1 fraud: {after_fraud:.2f}")
    print("  Reputation system working correctly")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("HELLAS ABM SIMULATOR - TEST SUITE")
    print("=" * 60)

    tests = [
        test_imports,
        test_theoretical_equilibrium,
        test_simulation,
        test_attack_scenario,
        test_reputation_system,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\nAll tests passed! The simulator is ready to use.")
        print("\nNext steps:")
        print("  1. Run 'streamlit run simulation/app.py' for the interactive dashboard")
        print("  2. Open simulation/notebooks/hellas_abm_experiments.ipynb for examples")
        print("  3. See simulation/README.md for full documentation")
    else:
        print("\nSome tests failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
