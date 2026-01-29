"""
Client Agents for Hellas ABM

Implements different client auditing strategies:
- Always Audit: Verifies every job
- Never Audit: Trusts all providers
- Belief Threshold: Audits based on posterior belief (Proposition 5)
- Mixed Strategy: Follows equilibrium audit probability (Proposition 3)
- Reputation Weighted: Adjusts audit probability based on provider reputation
"""

from typing import Optional, Dict, Tuple
import numpy as np
from .base import Agent, Job
from ..config import ProtocolParameters, ReputationParameters, ClientBehavior


class Client(Agent):
    """
    Base client class.

    Clients request computation, escrow payment, and decide whether to audit.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 500.0,
        behavior: ClientBehavior = ClientBehavior.MIXED_EQUILIBRIUM,
    ):
        super().__init__(agent_id, initial_balance)
        self.behavior = behavior

        # Client-specific tracking
        self.jobs_requested: int = 0
        self.jobs_audited: int = 0
        self.fraud_detected: int = 0
        self.losses_from_fraud: float = 0.0
        self.audit_costs: float = 0.0
        self.dispute_rewards: float = 0.0

        # Belief tracking
        self.provider_beliefs: Dict[str, float] = {}  # provider_id -> prior belief of cheating

    def get_agent_type(self) -> str:
        return f"Client[{self.behavior.value}]"

    def get_prior_belief(self, provider_id: str, provider_reputation: float) -> float:
        """
        Get prior belief that provider will cheat.

        mu_0 can be:
        - Fixed (e.g., 0.1)
        - Reputation-adjusted: mu_0 = f(reputation) with f'(rho) < 0
        """
        base_prior = 0.1  # Default 10% prior belief of cheating

        # Reputation adjustment: higher reputation -> lower prior
        # mu_0 = base_prior * exp(-alpha * (reputation - 50) / 50)
        alpha = 0.5
        reputation_factor = np.exp(-alpha * (provider_reputation - 50) / 50)

        return min(0.99, base_prior * reputation_factor)

    def update_belief(self, provider_id: str, cheated: bool) -> None:
        """
        Bayesian update of belief about provider after observing outcome.
        """
        if provider_id not in self.provider_beliefs:
            self.provider_beliefs[provider_id] = 0.1

        prior = self.provider_beliefs[provider_id]

        if cheated:
            # If fraud detected, increase belief
            self.provider_beliefs[provider_id] = min(0.99, prior + 0.3)
        else:
            # If honest, decrease belief slightly
            self.provider_beliefs[provider_id] = max(0.01, prior * 0.9)

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        """
        Decide whether to audit a job.

        Returns True if client decides to audit, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement decide_audit")

    def compute_audit_net_gain(
        self,
        mu: float,
        L: float,
        protocol: ProtocolParameters,
        S_P: float,
        P_set: float,
    ) -> float:
        """
        Net expected gain from auditing vs accepting (Proposition 5):
        G(mu) = -C_safe + mu(L + Delta)

        where Delta = p_w(beta*S_P + lambda*P_set) - (c_proof + c_tx) - (1-p_w)*B_C
        """
        Delta = protocol.compute_Delta(S_P, P_set)
        return -protocol.C_safe + mu * (L + Delta)


class AlwaysAuditClient(Client):
    """Client that always audits every job."""

    def __init__(self, agent_id: Optional[str] = None, initial_balance: float = 500.0):
        super().__init__(agent_id, initial_balance, ClientBehavior.ALWAYS_AUDIT)

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        return True


class NeverAuditClient(Client):
    """Client that never audits (fully trusts providers)."""

    def __init__(self, agent_id: Optional[str] = None, initial_balance: float = 500.0):
        super().__init__(agent_id, initial_balance, ClientBehavior.NEVER_AUDIT)

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        return False


class BeliefThresholdClient(Client):
    """
    Client that audits based on belief threshold (Proposition 5).

    Audits if mu > mu* = C_safe / (L + Delta)
    """

    def __init__(self, agent_id: Optional[str] = None, initial_balance: float = 500.0):
        super().__init__(agent_id, initial_balance, ClientBehavior.BELIEF_THRESHOLD)

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        # Get prior belief
        mu = self.get_prior_belief(provider_id, provider_reputation)

        # Compute threshold
        mu_star = protocol.compute_mu_star(provider_stake, job.value, job.loss_if_incorrect)

        return mu > mu_star


class MixedStrategyClient(Client):
    """
    Client that follows mixed equilibrium strategy (Theorem 2).

    Audits with probability v* = (c_H - c_F) / (P_set + S_P)
    """

    def __init__(self, agent_id: Optional[str] = None, initial_balance: float = 500.0):
        super().__init__(agent_id, initial_balance, ClientBehavior.MIXED_EQUILIBRIUM)

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        # Compute equilibrium audit probability
        v_star = protocol.compute_v_star(job.value, provider_stake)

        # Randomize
        return self._rng.random() < v_star


class ReputationWeightedClient(Client):
    """
    Client that adjusts audit probability based on provider reputation.

    This models the realistic scenario where clients audit less frequently
    for trusted providers, which creates the reputation farming vulnerability.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 500.0,
        base_audit_prob: float = 0.3,
        reputation_sensitivity: float = 0.02,
    ):
        super().__init__(agent_id, initial_balance, ClientBehavior.REPUTATION_WEIGHTED)
        self.base_audit_prob = base_audit_prob
        self.reputation_sensitivity = reputation_sensitivity

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        """
        Audit probability decreases with reputation:
        v = base_prob * exp(-sensitivity * (reputation - 50))

        This creates the vulnerability: high-reputation providers
        are audited less, enabling exploitation.
        """
        # Reputation-adjusted audit probability
        reputation_factor = np.exp(
            -self.reputation_sensitivity * (provider_reputation - 50)
        )
        audit_prob = self.base_audit_prob * reputation_factor

        # Also consider the equilibrium audit probability
        v_star = protocol.compute_v_star(job.value, provider_stake)

        # Use minimum of reputation-adjusted and equilibrium
        effective_prob = min(audit_prob, v_star)

        return self._rng.random() < effective_prob


class ColludingClient(Client):
    """
    Client that colludes with specific providers.

    Never audits colluding providers, shares savings from avoided verification.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 500.0,
        colluding_providers: set = None,
    ):
        super().__init__(agent_id, initial_balance, ClientBehavior.NEVER_AUDIT)
        self.colluding_providers = colluding_providers or set()

    def is_colluding_with(self, provider_id: str) -> bool:
        return provider_id in self.colluding_providers

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        # Never audit colluding providers
        if self.is_colluding_with(provider_id):
            return False

        # Otherwise, use mixed strategy
        v_star = protocol.compute_v_star(job.value, provider_stake)
        return self._rng.random() < v_star


class NaiveClient(Client):
    """
    Client that doesn't understand game theory - audits with fixed probability.

    Represents unsophisticated market participants.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 500.0,
        fixed_audit_prob: float = 0.1,
    ):
        super().__init__(agent_id, initial_balance, ClientBehavior.MIXED_EQUILIBRIUM)
        self.fixed_audit_prob = fixed_audit_prob

    def decide_audit(
        self,
        job: Job,
        provider_id: str,
        provider_reputation: float,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        return self._rng.random() < self.fixed_audit_prob
