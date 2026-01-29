"""
Reputation System for Hellas ABM

Models on-chain observable state that shifts priors and affects market behavior.
Critical for analyzing reputation farming attacks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class ReputationRecord:
    """Individual provider's reputation record."""
    provider_id: str
    score: float = 50.0  # Starting reputation
    total_jobs: int = 0
    honest_jobs: int = 0
    detected_frauds: int = 0
    stake_weighted_volume: float = 0.0
    time_in_system: int = 0

    # History for analysis
    score_history: List[float] = field(default_factory=list)

    @property
    def fraud_rate(self) -> float:
        """Observable fraud rate."""
        if self.total_jobs == 0:
            return 0.0
        return self.detected_frauds / self.total_jobs


class ReputationSystem:
    """
    On-chain reputation system.

    Properties that make reputation meaningful (from Section 7):
    1. Derived from hard-to-forge history
    2. Stake-weighted service volume
    3. Time in system
    4. Dispute outcomes

    Vulnerabilities:
    1. Reputation farming if minimum stake not enforced
    2. Self-buying to inflate volume
    3. Sybil attacks to create multiple identities
    """

    def __init__(
        self,
        decay_rate: float = 0.99,
        gain_honest: float = 1.0,
        loss_fraud: float = 50.0,
        stake_weight: float = 0.01,  # How much stake affects reputation gain
        time_weight: float = 0.001,  # How much time in system matters
        min_stake_for_reputation: float = 10.0,  # Minimum stake to gain reputation
    ):
        self.decay_rate = decay_rate
        self.gain_honest = gain_honest
        self.loss_fraud = loss_fraud
        self.stake_weight = stake_weight
        self.time_weight = time_weight
        self.min_stake_for_reputation = min_stake_for_reputation

        self.records: Dict[str, ReputationRecord] = {}

    def register_provider(self, provider_id: str) -> None:
        """Register a new provider in the reputation system."""
        if provider_id not in self.records:
            self.records[provider_id] = ReputationRecord(provider_id=provider_id)

    def get_reputation(self, provider_id: str) -> float:
        """Get provider's current reputation score."""
        if provider_id not in self.records:
            return 50.0  # Default for unknown providers
        return self.records[provider_id].score

    def record_job_outcome(
        self,
        provider_id: str,
        honest: bool,
        stake_used: float,
        job_value: float,
    ) -> Tuple[float, float]:
        """
        Record job outcome and update reputation.

        Returns (old_score, new_score)
        """
        if provider_id not in self.records:
            self.register_provider(provider_id)

        record = self.records[provider_id]
        old_score = record.score

        record.total_jobs += 1

        if honest:
            record.honest_jobs += 1

            # Reputation gain depends on stake (anti-farming measure)
            if stake_used >= self.min_stake_for_reputation:
                stake_bonus = self.stake_weight * stake_used
                gain = self.gain_honest + stake_bonus
                record.score = min(100.0, record.score + gain)
            else:
                # Reduced reputation gain for low-stake jobs
                record.score = min(100.0, record.score + self.gain_honest * 0.1)
        else:
            record.detected_frauds += 1
            record.score = max(0.0, record.score - self.loss_fraud)

        # Update stake-weighted volume
        record.stake_weighted_volume += stake_used * job_value

        record.score_history.append(record.score)

        return old_score, record.score

    def apply_time_decay(self) -> None:
        """Apply per-period reputation decay and time bonus."""
        for record in self.records.values():
            # Time decay
            record.score *= self.decay_rate

            # Time in system bonus (capped)
            record.time_in_system += 1
            time_bonus = self.time_weight * min(record.time_in_system, 1000)
            record.score = min(100.0, record.score + time_bonus)

    def compute_prior_from_reputation(
        self,
        provider_id: str,
        base_prior: float = 0.1,
        sensitivity: float = 0.02,
    ) -> float:
        """
        Compute prior belief of cheating from reputation.

        mu_0 = base_prior * exp(-sensitivity * (reputation - 50))

        Higher reputation -> lower prior belief of cheating.
        This is the source of reputation farming vulnerability.
        """
        reputation = self.get_reputation(provider_id)
        return base_prior * np.exp(-sensitivity * (reputation - 50))

    def get_top_providers(self, n: int = 10) -> List[Tuple[str, float]]:
        """Get top n providers by reputation."""
        sorted_records = sorted(
            self.records.items(),
            key=lambda x: x[1].score,
            reverse=True
        )
        return [(r[0], r[1].score) for r in sorted_records[:n]]

    def detect_reputation_farming(
        self,
        provider_id: str,
        stake_threshold: float = 20.0,
        job_count_threshold: int = 10,
    ) -> bool:
        """
        Heuristic detection of reputation farming.

        Flags providers with:
        1. High job count
        2. Low average stake per job
        3. High reputation score
        """
        if provider_id not in self.records:
            return False

        record = self.records[provider_id]

        if record.total_jobs < job_count_threshold:
            return False

        avg_stake = record.stake_weighted_volume / (record.total_jobs * 50)  # Approximate

        # Suspicious if high reputation with low stake history
        is_suspicious = (
            record.score > 70 and
            avg_stake < stake_threshold and
            record.total_jobs > job_count_threshold
        )

        return is_suspicious

    def get_statistics(self) -> Dict:
        """Get system-wide reputation statistics."""
        if not self.records:
            return {}

        scores = [r.score for r in self.records.values()]
        fraud_rates = [r.fraud_rate for r in self.records.values()]

        return {
            "n_providers": len(self.records),
            "mean_reputation": np.mean(scores),
            "std_reputation": np.std(scores),
            "median_reputation": np.median(scores),
            "mean_fraud_rate": np.mean(fraud_rates),
            "total_jobs": sum(r.total_jobs for r in self.records.values()),
            "total_frauds": sum(r.detected_frauds for r in self.records.values()),
        }


class SelfBuyingDetector:
    """
    Detector for self-buying attacks.

    Self-buying: Provider creates fake jobs to themselves to build reputation
    without real economic activity.
    """

    def __init__(
        self,
        min_unique_clients: int = 3,
        max_self_ratio: float = 0.5,
    ):
        self.min_unique_clients = min_unique_clients
        self.max_self_ratio = max_self_ratio

        # Track client-provider relationships
        self.provider_clients: Dict[str, Dict[str, int]] = {}  # provider -> {client -> count}

    def record_job(self, provider_id: str, client_id: str) -> None:
        """Record a job between provider and client."""
        if provider_id not in self.provider_clients:
            self.provider_clients[provider_id] = {}

        if client_id not in self.provider_clients[provider_id]:
            self.provider_clients[provider_id][client_id] = 0

        self.provider_clients[provider_id][client_id] += 1

    def detect_self_buying(self, provider_id: str) -> Tuple[bool, Dict]:
        """
        Detect potential self-buying.

        Returns (is_suspicious, details)
        """
        if provider_id not in self.provider_clients:
            return False, {}

        clients = self.provider_clients[provider_id]
        total_jobs = sum(clients.values())
        n_unique_clients = len(clients)

        if total_jobs == 0:
            return False, {}

        # Check for concentration (one client dominating)
        max_client_jobs = max(clients.values())
        concentration_ratio = max_client_jobs / total_jobs

        # Check for same-entity pattern (provider_id similar to client_id)
        suspicious_clients = [
            c for c in clients
            if self._ids_similar(provider_id, c)
        ]
        self_buy_ratio = sum(clients[c] for c in suspicious_clients) / total_jobs

        is_suspicious = (
            n_unique_clients < self.min_unique_clients or
            concentration_ratio > self.max_self_ratio or
            self_buy_ratio > self.max_self_ratio
        )

        return is_suspicious, {
            "n_unique_clients": n_unique_clients,
            "total_jobs": total_jobs,
            "concentration_ratio": concentration_ratio,
            "self_buy_ratio": self_buy_ratio,
        }

    def _ids_similar(self, id1: str, id2: str) -> bool:
        """Check if two IDs might be from same entity."""
        # Simple heuristic: check prefix similarity
        min_len = min(len(id1), len(id2), 4)
        return id1[:min_len] == id2[:min_len]
