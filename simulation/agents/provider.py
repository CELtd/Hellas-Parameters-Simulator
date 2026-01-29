"""
Provider Agents for Hellas ABM

Implements different provider strategies:
- Honest: Always executes correctly
- Rational: Expected utility maximizer following equilibrium
- Adversarial: Strategic attacker exploiting weaknesses
- Reputation Farmer: Builds reputation then exploits
"""

from typing import Optional, Tuple
import numpy as np
from .base import Agent, Job
from ..config import ProtocolParameters, ReputationParameters, AgentStrategy


class Provider(Agent):
    """
    Base provider class.

    Providers post stake, execute computations, and receive payment
    if no successful fraud proof is submitted.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 1000.0,
        stake_amount: float = 100.0,
        strategy: AgentStrategy = AgentStrategy.HONEST,
    ):
        super().__init__(agent_id, initial_balance)
        self.strategy = strategy
        self.default_stake = stake_amount

        # Provider-specific tracking
        self.total_cheats: int = 0
        self.total_honest: int = 0
        self.times_slashed: int = 0
        self.total_slashed_amount: float = 0.0

    def get_agent_type(self) -> str:
        return f"Provider[{self.strategy.value}]"

    def decide_stake(self, protocol: ProtocolParameters, job_value: float) -> float:
        """
        Decide how much stake to post for a job.

        Default: Use protocol minimum or default stake, whichever is higher.
        """
        min_viable = protocol.compute_S_P_min_viable(job_value)
        return max(protocol.S_P_min, min_viable, self.default_stake)

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """
        Decide whether to execute honestly.

        Returns True for honest execution, False for cheating.
        This is the core strategic decision.
        """
        raise NotImplementedError("Subclasses must implement decide_execution")

    def compute_expected_utility_cheat(
        self,
        protocol: ProtocolParameters,
        P_set: float,
        S_P: float,
        p_d: float,
    ) -> float:
        """
        Expected utility from cheating (Proposition 1):
        E[U_P(C)] = (1-p_d)(P_set - c_F) + p_d(-S_P - c_F)
                  = P_set - c_F - p_d(P_set + S_P)
        """
        return P_set - protocol.c_F - p_d * (P_set + S_P)

    def compute_utility_honest(
        self,
        protocol: ProtocolParameters,
        P_set: float,
    ) -> float:
        """
        Utility from honest execution:
        U_P(H) = P_set - c_H
        """
        return P_set - protocol.c_H


class HonestProvider(Provider):
    """Provider that always executes honestly."""

    def __init__(self, agent_id: Optional[str] = None, initial_balance: float = 1000.0):
        super().__init__(agent_id, initial_balance, strategy=AgentStrategy.HONEST)

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """Always honest."""
        return True


class RationalProvider(Provider):
    """
    Provider that maximizes expected utility.

    Follows the mixed equilibrium strategy when conditions apply,
    otherwise chooses the dominant action.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 1000.0,
        stake_amount: float = 100.0,
    ):
        super().__init__(agent_id, initial_balance, stake_amount, AgentStrategy.RATIONAL)

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """
        Rational decision based on expected utility comparison.

        Honest if: U_P(H) >= E[U_P(C)]
        i.e., P_set - c_H >= P_set - c_F - p_d(P_set + S_P)
        i.e., p_d >= (c_H - c_F) / (P_set + S_P) = theta
        """
        P_set = job.value
        theta = protocol.compute_theta(P_set, stake)

        # If audit probability meets threshold, be honest
        if estimated_audit_prob >= theta:
            return True

        # Otherwise, compare expected utilities
        U_honest = self.compute_utility_honest(protocol, P_set)
        U_cheat = self.compute_expected_utility_cheat(
            protocol, P_set, stake, estimated_audit_prob
        )

        # Add small noise for mixed strategy behavior
        noise = self._rng.normal(0, 0.1)
        return U_honest + noise >= U_cheat


class AdversarialProvider(Provider):
    """
    Strategic attacker that exploits protocol weaknesses.

    Behaviors:
    1. Cheats when audit probability is below threshold
    2. Exploits low-stake situations
    3. Can engage in reputation farming
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 2000.0,
        stake_amount: float = 50.0,  # Adversaries may under-stake
        exploit_threshold: float = 0.3,  # Cheat if audit prob below this
    ):
        super().__init__(agent_id, initial_balance, stake_amount, AgentStrategy.ADVERSARIAL)
        self.exploit_threshold = exploit_threshold
        self.in_farming_phase = True
        self.farming_jobs_completed = 0
        self.farming_target = 20  # Jobs to complete before exploiting

    def decide_stake(self, protocol: ProtocolParameters, job_value: float) -> float:
        """
        Adversaries may try to under-stake if minimum isn't enforced.
        """
        if protocol.S_P_min > 0:
            # Must meet minimum
            return protocol.S_P_min
        else:
            # Try to minimize stake
            return self.default_stake

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """
        Adversarial decision logic:
        1. In farming phase: be honest to build reputation
        2. After farming: exploit when profitable
        """
        # Reputation farming phase
        if self.in_farming_phase:
            self.farming_jobs_completed += 1
            if self.farming_jobs_completed >= self.farming_target:
                self.in_farming_phase = False
            return True

        # Exploitation phase: cheat if expected value is positive
        P_set = job.value
        U_honest = self.compute_utility_honest(protocol, P_set)
        U_cheat = self.compute_expected_utility_cheat(
            protocol, P_set, stake, estimated_audit_prob
        )

        # More aggressive: cheat if audit probability is low
        if estimated_audit_prob < self.exploit_threshold:
            return False  # Cheat

        return U_cheat < U_honest


class ReputationFarmerProvider(Provider):
    """
    Provider that strategically builds reputation then exploits it.

    Attack vector: If reputation reduces audit probability (clients trust
    high-reputation providers), then farming reputation enables later fraud.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 3000.0,
        reputation_target: float = 80.0,
        exploit_jobs: int = 5,  # Number of high-value jobs to exploit
    ):
        super().__init__(
            agent_id, initial_balance,
            strategy=AgentStrategy.REPUTATION_FARMER
        )
        self.reputation_target = reputation_target
        self.exploit_jobs_remaining = exploit_jobs
        self.total_exploited_value = 0.0

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """
        Strategy:
        1. Build reputation until target reached
        2. Then exploit high-value jobs with low audit probability
        """
        # Still building reputation
        if self.reputation < self.reputation_target:
            return True

        # Check if this is a good exploitation opportunity
        if self.exploit_jobs_remaining > 0:
            P_set = job.value

            # Only exploit if:
            # 1. Job value is high enough
            # 2. Audit probability is low (reputation effect)
            expected_gain = P_set - protocol.c_F - estimated_audit_prob * (P_set + stake)

            if expected_gain > protocol.c_H and estimated_audit_prob < 0.3:
                self.exploit_jobs_remaining -= 1
                self.total_exploited_value += P_set
                return False  # Cheat

        return True


class SybilProvider(Provider):
    """
    Sybil attacker that creates multiple identities.

    Attack vector: Create many low-stake identities to:
    1. Spread risk across identities
    2. Exploit minimum stake thresholds
    3. Build multiple reputations
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 5000.0,
        n_identities: int = 10,
        stake_per_identity: float = 50.0,
    ):
        super().__init__(agent_id, initial_balance, strategy=AgentStrategy.ADVERSARIAL)
        self.n_identities = n_identities
        self.stake_per_identity = stake_per_identity
        self.identity_reputations = {i: 50.0 for i in range(n_identities)}
        self.identity_balances = {i: initial_balance / n_identities for i in range(n_identities)}
        self.current_identity = 0

    def select_identity(self) -> int:
        """Select which identity to use for next job."""
        # Use identity with highest reputation
        return max(self.identity_reputations, key=self.identity_reputations.get)

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """
        Sybil strategy: Cheat with low-reputation identities,
        preserve high-reputation ones.
        """
        identity = self.select_identity()

        # If identity has low reputation, use it to cheat
        if self.identity_reputations[identity] < 30:
            return False

        # Otherwise, build reputation
        return True


class ColludingProvider(Provider):
    """
    Provider that colludes with clients.

    Attack vector: Provider and client split the savings from:
    1. Never auditing (client saves C_safe)
    2. Never disputing (provider keeps P_set even if cheating)
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 1000.0,
        colluding_clients: set = None,
        collusion_split: float = 0.5,
    ):
        super().__init__(agent_id, initial_balance, strategy=AgentStrategy.ADVERSARIAL)
        self.colluding_clients = colluding_clients or set()
        self.collusion_split = collusion_split

    def is_colluding_with(self, client_id: str) -> bool:
        return client_id in self.colluding_clients

    def decide_execution(
        self,
        job: Job,
        protocol: ProtocolParameters,
        stake: float,
        estimated_audit_prob: float,
    ) -> bool:
        """
        If colluding with client, always cheat (client won't audit).
        Otherwise, behave rationally.
        """
        if self.is_colluding_with(job.client_id):
            return False  # Cheat - client won't dispute

        # Non-colluding: rational behavior
        P_set = job.value
        theta = protocol.compute_theta(P_set, stake)
        return estimated_audit_prob >= theta
