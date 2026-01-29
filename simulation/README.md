# Hellas Fraud Game ABM Simulator

A comprehensive Agent-Based Model (ABM) for analyzing incentive compatibility in off-chain computation protocols, implementing the economic model from *"Fraud Game Analysis for Hellas Protocol"* (CryptoEconLab, 2026).

## Overview

This simulator models the strategic interactions between:
- **Providers**: Execute computations, post stake that can be slashed
- **Clients**: Request computation, decide whether to audit results
- **Challengers**: Monitor for fraud and submit dispute proofs

The simulation validates theoretical equilibrium predictions and analyzes adversarial attack vectors.

## Installation

```bash
cd simulation
pip install -r requirements.txt
```

## Quick Start

### 1. Run a Basic Simulation

```python
from simulation import SimulationConfig, SimulationEngine

# Create configuration
config = SimulationConfig(
    n_providers=50,
    n_clients=100,
    n_periods=500,
    seed=42,
)

# Run simulation
engine = SimulationEngine(config)
result = engine.run()

print(f"Fraud Rate: {result.fraud_rate:.4f}")
print(f"Detection Rate: {result.detection_rate:.4f}")
print(f"Social Welfare: ${result.social_welfare:.2f}")
```

### 2. Launch Interactive Dashboard

```bash
streamlit run app.py
```

### 3. Run Attack Analysis

```python
from simulation import SimulationConfig
from simulation.attacks import ReputationFarmingAttack, run_all_attacks

# Analyze reputation farming attack
config = SimulationConfig()
attack = ReputationFarmingAttack(config, min_stake_enforced=False)
result = attack.run(n_periods=500)

print(f"Fraud Rate Increase: {result.fraud_rate_increase:+.2%}")
print(f"Attacker Profit: ${result.attacker_profit:.2f}")
print(f"Welfare Loss: ${result.social_welfare_loss:.2f}")

# Run all attack scenarios
all_attacks = run_all_attacks(config, n_periods=500)
```

## Theoretical Model

### Key Equations

**Mixed Strategy Nash Equilibrium (Theorem 2):**

```
v* = (c_H - c_F) / (P_set + S_P)     # Equilibrium audit probability
q* = C_safe / (L + Δ)                 # Equilibrium cheating probability
```

**Net Dispute Surplus:**
```
Δ = p_w(β·S_P + λ·P_set) - (c_proof + c_tx) - (1-p_w)·B_C
```

**Minimum Viable Stake (Proposition 2):**
```
S_P^min = max{0, (C_disp + (1-p_w)B_C - p_w·λ·P_set) / (p_w·β)}
```

### Parameters

| Symbol | Description | Default |
|--------|-------------|---------|
| S_P | Provider stake | 100 |
| P_set | Settlement payment | 50 |
| c_H | Honest execution cost | 5 |
| c_F | Cheating cost | 0.5 |
| C_safe | Safe fallback cost | 8 |
| β | Slash reward fraction | 0.5 |
| λ | Payment routing fraction | 1.0 |
| p_w | Enforcement probability | 0.95 |
| B_C | Challenge bond | 5 |
| L | Client loss from fraud | 50 |

## Attack Vectors

### 1. Reputation Farming

**Mechanism:**
1. Provider completes many low-stake honest jobs
2. Builds high reputation score
3. Clients reduce auditing for trusted providers
4. Provider exploits reduced auditing to commit fraud

**Vulnerability Condition:**
- Reputation not stake-weighted
- Minimum stake floor not enforced
- Clients use reputation-weighted auditing

### 2. No Stake Floor Attack

**Mechanism:**
- Without minimum stake enforcement, providers use minimal stake
- Slashing penalty becomes economically insignificant
- From Proposition 2: if S_P < S_P^min, disputing is not profitable

### 3. Sybil Attack

**Mechanism:**
- Create multiple low-stake identities
- Spread risk across identities
- Cheat with some while maintaining others' reputation

### 4. Collusion Attack

**Mechanism:**
- Provider-client coordination
- Client never audits colluding provider
- Split savings from avoided verification

### 5. Censorship Attack

**Mechanism:**
- Block dispute transactions before challenge deadline
- Reduces effective enforcement probability p_w
- Makes cheating more profitable

### 6. Griefing Attack

**Mechanism:**
- File frivolous disputes to delay honest providers
- Impose costs and reputational uncertainty
- Mitigated by challenge bond B_C

## Project Structure

```
simulation/
├── __init__.py              # Package exports
├── config.py                # Configuration classes
├── app.py                   # Streamlit dashboard
├── requirements.txt         # Dependencies
├── README.md                # This file
│
├── agents/                  # Agent implementations
│   ├── base.py              # Base Agent, Job, Channel
│   ├── provider.py          # Provider strategies
│   ├── client.py            # Client auditing behaviors
│   └── challenger.py        # Dispute challengers
│
├── core/                    # Core simulation
│   ├── engine.py            # Main simulation loop
│   ├── market.py            # Job matching, market dynamics
│   └── reputation.py        # Reputation system
│
├── attacks/                 # Attack scenarios
│   └── scenarios.py         # All attack implementations
│
├── analysis/                # Analysis tools
│   ├── metrics.py           # Theoretical computations
│   └── visualization.py     # Plotly visualizations
│
└── experiments/             # Experiment runners
    └── run_experiments.py   # Comprehensive analysis
```

## Agent Types

### Providers

| Type | Behavior |
|------|----------|
| Honest | Always executes correctly |
| Rational | Maximizes expected utility |
| Adversarial | Strategic exploitation |
| ReputationFarmer | Builds trust then exploits |
| Sybil | Multiple identity attack |
| Colluding | Coordinates with clients |

### Clients

| Type | Behavior |
|------|----------|
| AlwaysAudit | Verifies every job |
| NeverAudit | Trusts all providers |
| MixedStrategy | Follows equilibrium v* |
| BeliefThreshold | Audits if μ > μ* |
| ReputationWeighted | Less auditing for trusted providers |
| Colluding | Never audits colluding provider |

## Running Experiments

### Full Analysis Pipeline

```python
from simulation.experiments import run_full_analysis

# Run comprehensive analysis
results = run_full_analysis(
    output_dir="results",
    n_periods=500,
    verbose=True
)

# Access individual results
baseline = results["baseline"]
attacks = results["attacks"]
stake_analysis = results["stake_thresholds"]
```

### Parameter Sensitivity

```python
from simulation.experiments import run_parameter_sweep

# Sweep minimum stake
results = run_parameter_sweep(
    parameter_name="S_P_min",
    parameter_values=[10, 50, 100, 200, 500],
    n_periods=500,
)
```

## Visualization

### Using Plotly

```python
from simulation.analysis import (
    plot_simulation_results,
    plot_attack_comparison,
    plot_equilibrium_analysis,
    plot_parameter_sensitivity,
)

# Plot simulation results
fig = plot_simulation_results(result)
fig.show()

# Plot equilibrium analysis
fig = plot_equilibrium_analysis(protocol)
fig.show()
```

## Key Findings

1. **Equilibrium Validation**: Simulated fraud rates converge to theoretical q* predictions

2. **Stake Floor Critical**: Without minimum stake enforcement, fraud rates increase significantly

3. **Reputation Farming Profitable**: Optimal farming period exists that maximizes attack ROI

4. **Enforcement Reliability**: Lower p_w dramatically increases equilibrium cheating

5. **Verification Cost Impact**: Reducing C_safe is the most effective lever for improving outcomes

## Protocol Design Recommendations

Based on Section 7 of the paper:

1. **Stake floors indexed by job class**
2. **Permissionless challenging** for watcher markets
3. **Randomized audits** for exogenous detection baseline
4. **Reducing verification cost** through trusted fallback providers
5. **Timeout sizing** by job class
6. **Anti-griefing** through challenge bonds

## Citation

```bibtex
@article{hellas2026,
  title={Fraud Game Analysis for Hellas Protocol: Incentives, Detection, and Protocol Design},
  author={CryptoEconLab},
  year={2026},
  month={January}
}
```

## License

MIT License - CryptoEconLab 2026
