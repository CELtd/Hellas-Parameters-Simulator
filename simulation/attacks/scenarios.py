"""
Attack Scenarios for Hellas ABM

Implements various adversarial strategies and their analysis:
1. Reputation Farming: Build reputation then exploit trust
2. Sybil Attack: Create multiple identities to spread risk
3. Collusion: Provider-client coordination to avoid auditing
4. Griefing: File frivolous disputes to delay honest providers
5. No Stake Floor: Exploit when minimum stake isn't enforced
6. Censorship: Block dispute transactions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from copy import deepcopy

from ..config import SimulationConfig, ProtocolParameters, ReputationParameters
from ..core.engine import SimulationEngine, SimulationResult


@dataclass
class AttackResult:
    """Results from an attack scenario."""
    attack_name: str
    baseline_result: SimulationResult
    attack_result: SimulationResult

    # Comparative metrics
    fraud_rate_increase: float = 0.0
    detection_rate_change: float = 0.0
    attacker_profit: float = 0.0
    victim_losses: float = 0.0
    social_welfare_loss: float = 0.0

    # Attack-specific metrics
    attack_specific: Dict[str, Any] = field(default_factory=dict)


class BaseAttack:
    """Base class for attack scenarios."""

    name: str = "BaseAttack"

    def __init__(self, base_config: SimulationConfig):
        self.base_config = base_config

    def create_attack_config(self) -> SimulationConfig:
        """Create configuration for the attack scenario."""
        raise NotImplementedError

    def run(self, n_periods: int = 500, show_progress: bool = True) -> AttackResult:
        """
        Run the attack scenario and compare to baseline.
        """
        # Run baseline
        baseline_config = deepcopy(self.base_config)
        baseline_config.n_periods = n_periods
        baseline_engine = SimulationEngine(baseline_config)
        baseline_result = baseline_engine.run(show_progress=show_progress)

        # Run attack scenario
        attack_config = self.create_attack_config()
        attack_config.n_periods = n_periods
        attack_engine = SimulationEngine(attack_config)
        attack_result = attack_engine.run(show_progress=show_progress)

        # Compute comparative metrics
        result = AttackResult(
            attack_name=self.name,
            baseline_result=baseline_result,
            attack_result=attack_result,
        )

        self._compute_comparative_metrics(result)

        return result

    def _compute_comparative_metrics(self, result: AttackResult) -> None:
        """Compute comparative metrics between baseline and attack."""
        baseline = result.baseline_result
        attack = result.attack_result

        result.fraud_rate_increase = attack.fraud_rate - baseline.fraud_rate
        result.detection_rate_change = attack.detection_rate - baseline.detection_rate
        result.social_welfare_loss = baseline.social_welfare - attack.social_welfare

        # Attacker profit (adversarial providers)
        result.attacker_profit = attack.attack_metrics.get("adversarial_total_profit", 0)

        # Victim losses (honest participants)
        result.victim_losses = attack.total_client_losses - baseline.total_client_losses


class ReputationFarmingAttack(BaseAttack):
    """
    Reputation Farming Attack

    Attack vector:
    1. Provider uses low-stake jobs to build high reputation
    2. Clients with reputation-weighted auditing reduce their audit rate
    3. Provider exploits reduced auditing to commit profitable fraud

    Vulnerability condition:
    - Reputation is not stake-weighted
    - Minimum stake floor is not enforced
    - Clients reduce auditing for high-reputation providers
    """

    name = "ReputationFarming"

    def __init__(
        self,
        base_config: SimulationConfig,
        n_farmers: int = 5,
        farming_periods: int = 50,
        min_stake_enforced: bool = False,
    ):
        super().__init__(base_config)
        self.n_farmers = n_farmers
        self.farming_periods = farming_periods
        self.min_stake_enforced = min_stake_enforced

    def create_attack_config(self) -> SimulationConfig:
        """Create config with reputation farmers and vulnerable reputation system."""
        config = deepcopy(self.base_config)

        # Reduce minimum stake if not enforced
        if not self.min_stake_enforced:
            config.protocol.S_P_min = 1.0  # Very low minimum

        # Adjust reputation system to be exploitable
        config.reputation.min_stake_enforcement = self.min_stake_enforced

        # Increase adversarial fraction
        total_adv = min(0.5, self.n_farmers / config.n_providers + 0.1)
        config.provider_adversarial_frac = total_adv
        config.provider_honest_frac = 0.3
        config.provider_rational_frac = 1.0 - total_adv - 0.3

        # Increase reputation-weighted clients (vulnerable to farming)
        config.client_always_audit_frac = 0.05
        config.client_never_audit_frac = 0.15
        config.client_mixed_frac = 0.8  # Many use reputation-weighted

        return config


class SybilAttack(BaseAttack):
    """
    Sybil Attack

    Attack vector:
    1. Attacker creates multiple identities
    2. Spreads stake across identities to reduce per-identity risk
    3. Cheats with some identities while maintaining others' reputation

    Vulnerability condition:
    - Identity creation is cheap
    - No linkage between identities
    - Per-identity stake can be low
    """

    name = "SybilAttack"

    def __init__(
        self,
        base_config: SimulationConfig,
        n_sybils_per_attacker: int = 10,
        n_attackers: int = 3,
        identity_cost: float = 10.0,
    ):
        super().__init__(base_config)
        self.n_sybils_per_attacker = n_sybils_per_attacker
        self.n_attackers = n_attackers
        self.identity_cost = identity_cost

    def create_attack_config(self) -> SimulationConfig:
        """Create config with sybil attackers."""
        config = deepcopy(self.base_config)

        # Add sybil identities as separate providers
        # In practice, these would be controlled by same entity
        n_sybil_total = self.n_sybils_per_attacker * self.n_attackers
        config.n_providers += n_sybil_total

        # Adjust fractions
        total_providers = config.n_providers
        config.provider_adversarial_frac = (
            n_sybil_total + int(self.base_config.n_providers * 0.1)
        ) / total_providers
        config.provider_honest_frac = int(self.base_config.n_providers * 0.6) / total_providers
        config.provider_rational_frac = 1.0 - config.provider_adversarial_frac - config.provider_honest_frac

        return config


class CollusionAttack(BaseAttack):
    """
    Collusion Attack

    Attack vector:
    1. Provider and client form a collusion ring
    2. Client never audits colluding provider
    3. Provider cheats and splits savings with client

    Savings for collusion:
    - Client saves C_safe (no auditing)
    - Provider saves c_H - c_F (cheating cost)
    - Both share the "value" of unperformed computation

    Vulnerability condition:
    - No external auditing (permissionless challengers)
    - No randomized protocol audits
    """

    name = "CollusionAttack"

    def __init__(
        self,
        base_config: SimulationConfig,
        n_colluding_pairs: int = 10,
        collusion_split: float = 0.5,
    ):
        super().__init__(base_config)
        self.n_colluding_pairs = n_colluding_pairs
        self.collusion_split = collusion_split

    def create_attack_config(self) -> SimulationConfig:
        """Create config with colluding provider-client pairs."""
        config = deepcopy(self.base_config)

        # Increase never-audit clients (some are colluding)
        config.client_never_audit_frac = (
            self.base_config.client_never_audit_frac +
            self.n_colluding_pairs / config.n_clients
        )
        config.client_mixed_frac = 1.0 - config.client_always_audit_frac - config.client_never_audit_frac

        # Increase adversarial providers
        config.provider_adversarial_frac = (
            self.base_config.provider_adversarial_frac +
            self.n_colluding_pairs / config.n_providers
        )
        config.provider_honest_frac = 1.0 - config.provider_adversarial_frac - config.provider_rational_frac

        # Disable permissionless challengers
        config.n_challengers = 0

        return config


class GriefingAttack(BaseAttack):
    """
    Griefing Attack

    Attack vector:
    1. Attacker files many frivolous disputes
    2. Delays settlement for honest providers
    3. Imposes on-chain costs and reputational uncertainty

    Mitigation:
    - Challenge bond B_C that is forfeited on failed dispute
    - Reputation cost for failed disputes

    Analysis: How much griefing is economically sustainable?
    """

    name = "GriefingAttack"

    def __init__(
        self,
        base_config: SimulationConfig,
        n_griefers: int = 5,
        griefing_budget_per_griefer: float = 500.0,
    ):
        super().__init__(base_config)
        self.n_griefers = n_griefers
        self.griefing_budget = griefing_budget_per_griefer

    def create_attack_config(self) -> SimulationConfig:
        """Create config with griefing challengers."""
        config = deepcopy(self.base_config)

        # Add griefers as challengers
        config.n_challengers += self.n_griefers

        # Reduce challenge bond (makes griefing cheaper)
        config.protocol.B_C = max(1.0, config.protocol.B_C * 0.5)

        return config


class NoStakeFloorAttack(BaseAttack):
    """
    No Stake Floor Attack

    Attack vector:
    1. Protocol doesn't enforce minimum stake
    2. Provider uses minimal stake
    3. Even if caught, slashing amount is small
    4. Cheating becomes profitable because penalty is low

    From Proposition 2:
    If S_P < S_P^min, disputing is not profitable for challenger,
    so no disputes are filed even when fraud is detected.
    """

    name = "NoStakeFloorAttack"

    def __init__(
        self,
        base_config: SimulationConfig,
        min_stake_override: float = 1.0,
    ):
        super().__init__(base_config)
        self.min_stake_override = min_stake_override

    def create_attack_config(self) -> SimulationConfig:
        """Create config with no stake floor."""
        config = deepcopy(self.base_config)

        # Remove stake floor
        config.protocol.S_P_min = self.min_stake_override

        # Increase adversarial providers who will exploit this
        config.provider_adversarial_frac = 0.3
        config.provider_rational_frac = 0.4
        config.provider_honest_frac = 0.3

        return config


class CensorshipAttack(BaseAttack):
    """
    Censorship Attack

    Attack vector:
    1. Attacker controls block production or has MEV capability
    2. Censors dispute transactions before challenge deadline
    3. Provider can cheat knowing disputes won't be included

    This reduces effective p_w (enforcement probability).
    """

    name = "CensorshipAttack"

    def __init__(
        self,
        base_config: SimulationConfig,
        censorship_rate: float = 0.3,  # 30% of disputes censored
    ):
        super().__init__(base_config)
        self.censorship_rate = censorship_rate

    def create_attack_config(self) -> SimulationConfig:
        """Create config with reduced enforcement probability."""
        config = deepcopy(self.base_config)

        # Reduce p_w to simulate censorship
        config.protocol.p_w = self.base_config.protocol.p_w * (1 - self.censorship_rate)

        return config


def run_attack_scenario(
    attack_class: type,
    base_config: SimulationConfig = None,
    n_periods: int = 500,
    **attack_kwargs,
) -> AttackResult:
    """
    Convenience function to run an attack scenario.

    Args:
        attack_class: The attack class to run
        base_config: Base configuration (uses default if None)
        n_periods: Number of simulation periods
        **attack_kwargs: Arguments passed to attack constructor

    Returns:
        AttackResult with comparative analysis
    """
    if base_config is None:
        base_config = SimulationConfig()

    attack = attack_class(base_config, **attack_kwargs)
    return attack.run(n_periods=n_periods)


def run_all_attacks(
    base_config: SimulationConfig = None,
    n_periods: int = 300,
    show_progress: bool = True,
) -> Dict[str, AttackResult]:
    """
    Run all attack scenarios and return results.
    """
    if base_config is None:
        base_config = SimulationConfig()

    attacks = {
        "reputation_farming": ReputationFarmingAttack(base_config),
        "sybil": SybilAttack(base_config),
        "collusion": CollusionAttack(base_config),
        "griefing": GriefingAttack(base_config),
        "no_stake_floor": NoStakeFloorAttack(base_config),
        "censorship": CensorshipAttack(base_config),
    }

    results = {}
    for name, attack in attacks.items():
        print(f"\nRunning {name} attack scenario...")
        results[name] = attack.run(n_periods=n_periods, show_progress=show_progress)

    return results
