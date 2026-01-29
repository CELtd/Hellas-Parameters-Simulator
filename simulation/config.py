"""
Hellas Fraud Game ABM - Configuration Module

This module defines all configurable parameters for the simulation,
directly mapping to the theoretical model in the paper.

Reference: "Fraud Game Analysis for Hellas Protocol" (CryptoEconLab, 2026)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import numpy as np


class AgentStrategy(Enum):
    """Provider strategic behavior types."""
    HONEST = "honest"           # Always honest
    RATIONAL = "rational"       # Expected utility maximizer
    ADVERSARIAL = "adversarial" # Strategic attacker
    MIXED = "mixed"             # Follows mixed equilibrium
    REPUTATION_FARMER = "reputation_farmer"  # Builds reputation then exploits


class ClientBehavior(Enum):
    """Client auditing behavior types."""
    ALWAYS_AUDIT = "always_audit"
    NEVER_AUDIT = "never_audit"
    BELIEF_THRESHOLD = "belief_threshold"
    MIXED_EQUILIBRIUM = "mixed_equilibrium"
    REPUTATION_WEIGHTED = "reputation_weighted"


@dataclass
class ProtocolParameters:
    """
    Core protocol parameters from Table 1 of the paper.

    These parameters define the economic structure of the fraud game.
    """
    # Stake and payments
    S_P_min: float = 100.0          # Minimum provider stake floor
    S_P_max: float = 10000.0        # Maximum provider stake
    P_set_base: float = 10.0        # Base settlement payment

    # Cost structure
    c_H: float = 5.0                # Provider cost of honest execution
    c_F: float = 0.5                # Provider cost of cheating (typically << c_H)
    C_safe: float = 8.0             # Cost of safe fallback computation
    c_proof: float = 2.0            # Cost of fraud proof generation
    c_tx: float = 1.0               # On-chain transaction cost

    # Reward routing (Proposition 2)
    beta: float = 0.5               # Fraction of slashed stake to challenger
    lambda_: float = 1.0            # Fraction of P_set routed to challenger

    # Enforcement
    B_C: float = 5.0                # Challenge bond
    p_w: float = 0.95               # Enforcement reliability probability

    # Client parameters
    L_base: float = 50.0            # Base client loss from incorrect result
    L_variance: float = 20.0        # Variance in job-specific loss

    # Capital costs
    r: float = 0.05                 # Opportunity cost rate (annual)
    tau: float = 0.01               # Capital lock duration (fraction of year)

    # Timing
    T_challenge: int = 100          # Challenge window (time steps)

    def compute_C_disp(self) -> float:
        """Total dispute cost: C_disp = C_safe + c_proof + c_tx"""
        return self.C_safe + self.c_proof + self.c_tx

    def compute_S_P_min_viable(self, P_set: float) -> float:
        """
        Minimum viable stake from Proposition 2:
        S_P^min = max{0, (C_disp + (1-p_w)B_C - p_w*lambda*P_set) / (p_w*beta)}
        """
        C_disp = self.compute_C_disp()
        numerator = C_disp + (1 - self.p_w) * self.B_C - self.p_w * self.lambda_ * P_set
        denominator = self.p_w * self.beta
        return max(0.0, numerator / denominator)

    def compute_theta(self, P_set: float, S_P: float) -> float:
        """
        Provider incentive threshold (Proposition 1):
        theta = (c_H - c_F) / (P_set + S_P)
        """
        return (self.c_H - self.c_F) / (P_set + S_P)

    def compute_Delta(self, S_P: float, P_set: float) -> float:
        """
        Net expected dispute surplus (conditional on fraud):
        Delta = p_w(beta*S_P + lambda*P_set) - (c_proof + c_tx) - (1-p_w)*B_C
        """
        return (
            self.p_w * (self.beta * S_P + self.lambda_ * P_set)
            - (self.c_proof + self.c_tx)
            - (1 - self.p_w) * self.B_C
        )

    def compute_v_star(self, P_set: float, S_P: float) -> float:
        """
        Mixed equilibrium audit probability (Proposition 3):
        v* = (c_H - c_F) / (P_set + S_P)
        """
        return self.compute_theta(P_set, S_P)

    def compute_q_star(self, S_P: float, P_set: float, L: float) -> float:
        """
        Mixed equilibrium cheating probability (Proposition 4):
        q* = C_safe / (L + Delta)
        """
        Delta = self.compute_Delta(S_P, P_set)
        if L + Delta <= 0:
            return 1.0  # Cheating is always optimal
        return min(1.0, self.C_safe / (L + Delta))

    def compute_mu_star(self, S_P: float, P_set: float, L: float) -> float:
        """
        Belief threshold for auditing (Proposition 5):
        mu* = C_safe / (L + Delta)
        """
        return self.compute_q_star(S_P, P_set, L)


@dataclass
class ReputationParameters:
    """
    Parameters for the reputation system extension.

    Models on-chain observable state that shifts priors.
    """
    # Reputation mechanics
    reputation_decay: float = 0.99        # Per-period reputation decay
    reputation_gain_honest: float = 1.0   # Reputation gain per honest job
    reputation_loss_fraud: float = 50.0   # Reputation loss per detected fraud

    # Reputation effects on behavior
    prior_sensitivity: float = 0.1        # How much reputation shifts prior mu_0
    min_reputation_threshold: float = 10.0  # Minimum reputation to participate

    # Attack vulnerability parameters
    self_buy_discount: float = 0.9        # Cost factor for self-buying
    min_stake_enforcement: bool = True    # Whether minimum stake is enforced
    reputation_weight_in_matching: float = 0.5  # Weight in client matching


@dataclass
class AttackParameters:
    """Parameters for adversarial scenarios."""

    # Reputation farming attack
    farming_warmup_periods: int = 50      # Periods to build reputation
    farming_exploit_threshold: float = 0.8  # Reputation level to start exploiting

    # Sybil attack
    sybil_creation_cost: float = 10.0     # Cost to create new identity
    sybil_stake_per_identity: float = 50.0  # Stake per sybil identity

    # Collusion
    collusion_split: float = 0.5          # How colluding parties split gains
    collusion_detection_prob: float = 0.1 # Probability of detecting collusion

    # Griefing
    griefing_budget: float = 1000.0       # Budget for griefing attacks

    # Eclipse/Censorship
    censorship_probability: float = 0.0   # Probability of censoring disputes


@dataclass
class SimulationConfig:
    """Master configuration for the simulation."""

    # Simulation parameters
    n_providers: int = 50
    n_clients: int = 100
    n_challengers: int = 10
    n_periods: int = 1000
    seed: int = 42

    # Market parameters
    jobs_per_period: int = 20
    job_value_distribution: str = "lognormal"  # or "uniform", "exponential"
    job_value_mean: float = 50.0
    job_value_std: float = 25.0

    # Agent type distributions (fractions)
    provider_honest_frac: float = 0.6
    provider_rational_frac: float = 0.3
    provider_adversarial_frac: float = 0.1

    client_always_audit_frac: float = 0.1
    client_never_audit_frac: float = 0.2
    client_mixed_frac: float = 0.7

    # Component configs
    protocol: ProtocolParameters = field(default_factory=ProtocolParameters)
    reputation: ReputationParameters = field(default_factory=ReputationParameters)
    attack: AttackParameters = field(default_factory=AttackParameters)

    def __post_init__(self):
        """Validate configuration."""
        assert abs(self.provider_honest_frac + self.provider_rational_frac +
                   self.provider_adversarial_frac - 1.0) < 1e-6
        assert abs(self.client_always_audit_frac + self.client_never_audit_frac +
                   self.client_mixed_frac - 1.0) < 1e-6


# Pre-configured scenarios
BASELINE_CONFIG = SimulationConfig()

WEAK_ENFORCEMENT_CONFIG = SimulationConfig(
    protocol=ProtocolParameters(p_w=0.7, beta=0.3)
)

HIGH_VERIFICATION_COST_CONFIG = SimulationConfig(
    protocol=ProtocolParameters(C_safe=25.0, c_proof=5.0)
)

NO_STAKE_FLOOR_CONFIG = SimulationConfig(
    protocol=ProtocolParameters(S_P_min=0.0),
    reputation=ReputationParameters(min_stake_enforcement=False)
)

ADVERSARIAL_HEAVY_CONFIG = SimulationConfig(
    provider_honest_frac=0.3,
    provider_rational_frac=0.3,
    provider_adversarial_frac=0.4
)
