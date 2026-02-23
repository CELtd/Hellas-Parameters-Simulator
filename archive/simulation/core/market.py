"""
Market Module for Hellas ABM

Models the matching between clients and providers,
job generation, and market dynamics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from ..agents.base import Job
from ..config import ProtocolParameters


@dataclass
class MarketState:
    """Tracks market-level statistics."""
    period: int = 0
    total_jobs_created: int = 0
    total_jobs_completed: int = 0
    total_frauds: int = 0
    total_frauds_detected: int = 0
    total_disputes: int = 0
    total_successful_disputes: int = 0
    total_stake_slashed: float = 0.0
    total_payments: float = 0.0
    total_client_losses: float = 0.0

    # Per-period tracking
    jobs_per_period: List[int] = field(default_factory=list)
    frauds_per_period: List[int] = field(default_factory=list)
    detection_rate_per_period: List[float] = field(default_factory=list)
    avg_stake_per_period: List[float] = field(default_factory=list)

    @property
    def fraud_rate(self) -> float:
        if self.total_jobs_completed == 0:
            return 0.0
        return self.total_frauds / self.total_jobs_completed

    @property
    def detection_rate(self) -> float:
        if self.total_frauds == 0:
            return 0.0
        return self.total_frauds_detected / self.total_frauds


class Market:
    """
    Market mechanism for matching clients with providers.

    Supports various matching strategies:
    - Random matching
    - Reputation-weighted matching
    - Stake-weighted matching
    """

    def __init__(
        self,
        protocol: ProtocolParameters,
        matching_strategy: str = "reputation_weighted",
        reputation_weight: float = 0.5,
        stake_weight: float = 0.3,
    ):
        self.protocol = protocol
        self.matching_strategy = matching_strategy
        self.reputation_weight = reputation_weight
        self.stake_weight = stake_weight
        self.state = MarketState()

        self._rng = np.random.default_rng()

    def set_rng(self, rng: np.random.Generator):
        self._rng = rng

    def generate_jobs(
        self,
        n_jobs: int,
        client_ids: List[str],
        value_distribution: str = "lognormal",
        value_mean: float = 50.0,
        value_std: float = 25.0,
    ) -> List[Job]:
        """
        Generate jobs for a period.

        Job values follow specified distribution.
        Client losses L are correlated with job value.
        """
        jobs = []

        for _ in range(n_jobs):
            # Select random client
            client_id = self._rng.choice(client_ids)

            # Generate job value
            if value_distribution == "lognormal":
                # Log-normal for realistic job value distribution
                mu = np.log(value_mean) - 0.5 * np.log(1 + (value_std / value_mean) ** 2)
                sigma = np.sqrt(np.log(1 + (value_std / value_mean) ** 2))
                value = self._rng.lognormal(mu, sigma)
            elif value_distribution == "uniform":
                value = self._rng.uniform(value_mean - value_std, value_mean + value_std)
            else:  # exponential
                value = self._rng.exponential(value_mean)

            value = max(1.0, value)  # Minimum value

            # Client loss correlates with job value
            # Higher-value jobs have higher stakes
            L = self.protocol.L_base + self._rng.normal(0, self.protocol.L_variance)
            L = max(value * 0.5, L)  # At least 50% of job value

            job = Job.create(client_id, value, L, self._rng)
            jobs.append(job)

            self.state.total_jobs_created += 1

        return jobs

    def match_provider(
        self,
        job: Job,
        available_providers: List[Tuple[str, float, float]],  # (id, reputation, stake_capacity)
    ) -> Optional[str]:
        """
        Match a job to a provider.

        Returns provider_id or None if no match.
        """
        if not available_providers:
            return None

        if self.matching_strategy == "random":
            return self._rng.choice([p[0] for p in available_providers])

        elif self.matching_strategy == "reputation_weighted":
            # Weight by reputation
            reputations = np.array([p[1] for p in available_providers])
            # Softmax-like weighting
            weights = np.exp(reputations / 20)  # Temperature = 20
            weights /= weights.sum()

            idx = self._rng.choice(len(available_providers), p=weights)
            return available_providers[idx][0]

        elif self.matching_strategy == "stake_weighted":
            # Weight by stake capacity
            stakes = np.array([p[2] for p in available_providers])
            weights = stakes / stakes.sum() if stakes.sum() > 0 else None

            if weights is None:
                return self._rng.choice([p[0] for p in available_providers])

            idx = self._rng.choice(len(available_providers), p=weights)
            return available_providers[idx][0]

        else:  # mixed
            reputations = np.array([p[1] for p in available_providers])
            stakes = np.array([p[2] for p in available_providers])

            # Combine weights
            rep_weights = np.exp(reputations / 20)
            stake_weights = stakes + 1  # Add 1 to avoid zero weights

            combined = (
                self.reputation_weight * rep_weights / rep_weights.sum() +
                self.stake_weight * stake_weights / stake_weights.sum()
            )
            combined /= combined.sum()

            idx = self._rng.choice(len(available_providers), p=combined)
            return available_providers[idx][0]

    def compute_market_equilibrium(
        self,
        n_providers: int,
        n_clients: int,
        avg_job_value: float,
        avg_stake: float,
    ) -> Dict:
        """
        Compute theoretical market equilibrium values.

        From Theorem 2:
        - v* = (c_H - c_F) / (P_set + S_P)
        - q* = C_safe / (L + Delta)
        """
        P_set = avg_job_value
        S_P = avg_stake
        L = self.protocol.L_base

        v_star = self.protocol.compute_v_star(P_set, S_P)
        q_star = self.protocol.compute_q_star(S_P, P_set, L)
        theta = self.protocol.compute_theta(P_set, S_P)
        Delta = self.protocol.compute_Delta(S_P, P_set)
        S_P_min = self.protocol.compute_S_P_min_viable(P_set)

        return {
            "v_star": v_star,
            "q_star": q_star,
            "theta": theta,
            "Delta": Delta,
            "S_P_min_viable": S_P_min,
            "is_enforcement_viable": S_P >= S_P_min,
            "is_ic_satisfied": v_star >= theta,
        }

    def record_period(
        self,
        jobs_completed: int,
        frauds: int,
        frauds_detected: int,
        avg_stake: float,
    ) -> None:
        """Record period statistics."""
        self.state.period += 1
        self.state.total_jobs_completed += jobs_completed
        self.state.total_frauds += frauds
        self.state.total_frauds_detected += frauds_detected

        self.state.jobs_per_period.append(jobs_completed)
        self.state.frauds_per_period.append(frauds)

        detection_rate = frauds_detected / frauds if frauds > 0 else 1.0
        self.state.detection_rate_per_period.append(detection_rate)
        self.state.avg_stake_per_period.append(avg_stake)

    def get_statistics(self) -> Dict:
        """Get comprehensive market statistics."""
        return {
            "total_periods": self.state.period,
            "total_jobs": self.state.total_jobs_completed,
            "total_frauds": self.state.total_frauds,
            "fraud_rate": self.state.fraud_rate,
            "detection_rate": self.state.detection_rate,
            "total_stake_slashed": self.state.total_stake_slashed,
            "total_client_losses": self.state.total_client_losses,
            "avg_jobs_per_period": (
                np.mean(self.state.jobs_per_period)
                if self.state.jobs_per_period else 0
            ),
            "avg_detection_rate": (
                np.mean(self.state.detection_rate_per_period)
                if self.state.detection_rate_per_period else 0
            ),
        }


class JobQueue:
    """
    Queue for managing pending jobs across periods.

    Handles challenge windows and finalization timing.
    """

    def __init__(self, challenge_window: int = 100):
        self.challenge_window = challenge_window
        self.pending_jobs: Dict[str, Tuple[Job, int, float]] = {}  # job_id -> (job, deadline, stake)
        self.finalized_jobs: List[Job] = []

    def add_job(self, job: Job, current_time: int, stake: float) -> None:
        """Add a job to the queue."""
        deadline = current_time + self.challenge_window
        self.pending_jobs[job.job_id] = (job, deadline, stake)

    def get_challengeable_jobs(self, current_time: int) -> List[Tuple[Job, float]]:
        """Get jobs that are still within challenge window."""
        return [
            (job, stake)
            for job_id, (job, deadline, stake) in self.pending_jobs.items()
            if current_time < deadline
        ]

    def finalize_expired(self, current_time: int) -> List[Tuple[Job, float]]:
        """
        Finalize jobs whose challenge window has expired.

        Returns list of finalized jobs with their stakes.
        """
        to_finalize = []
        to_remove = []

        for job_id, (job, deadline, stake) in self.pending_jobs.items():
            if current_time >= deadline:
                to_finalize.append((job, stake))
                to_remove.append(job_id)
                self.finalized_jobs.append(job)

        for job_id in to_remove:
            del self.pending_jobs[job_id]

        return to_finalize
