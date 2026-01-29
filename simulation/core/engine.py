"""
Simulation Engine for Hellas ABM

The main simulation loop that orchestrates all agents and market interactions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from tqdm import tqdm

from ..config import SimulationConfig, ProtocolParameters
from ..agents.base import Agent, Job
from ..agents.provider import (
    Provider, HonestProvider, RationalProvider, AdversarialProvider,
    ReputationFarmerProvider, SybilProvider, ColludingProvider
)
from ..agents.client import (
    Client, AlwaysAuditClient, NeverAuditClient, MixedStrategyClient,
    BeliefThresholdClient, ReputationWeightedClient, ColludingClient
)
from ..agents.challenger import (
    Challenger, PermissionlessChallenger, GriefingChallenger
)
from .market import Market, JobQueue
from .reputation import ReputationSystem, SelfBuyingDetector


@dataclass
class SimulationResult:
    """Results from a simulation run."""
    config: SimulationConfig
    n_periods: int
    seed: int

    # Aggregate metrics
    total_jobs: int = 0
    total_frauds: int = 0
    total_frauds_detected: int = 0
    total_disputes: int = 0
    total_successful_disputes: int = 0
    total_stake_slashed: float = 0.0
    total_client_losses: float = 0.0

    # Time series
    fraud_rate_history: List[float] = field(default_factory=list)
    detection_rate_history: List[float] = field(default_factory=list)
    avg_reputation_history: List[float] = field(default_factory=list)
    avg_stake_history: List[float] = field(default_factory=list)
    welfare_history: List[float] = field(default_factory=list)

    # Agent-level results
    provider_profits: Dict[str, float] = field(default_factory=dict)
    client_losses: Dict[str, float] = field(default_factory=dict)
    challenger_profits: Dict[str, float] = field(default_factory=dict)

    # Attack analysis
    attack_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def fraud_rate(self) -> float:
        return self.total_frauds / self.total_jobs if self.total_jobs > 0 else 0

    @property
    def detection_rate(self) -> float:
        return self.total_frauds_detected / self.total_frauds if self.total_frauds > 0 else 1.0

    @property
    def social_welfare(self) -> float:
        """Total welfare = sum of all agent utilities."""
        provider_welfare = sum(self.provider_profits.values())
        client_welfare = -sum(self.client_losses.values())  # Losses are negative
        challenger_welfare = sum(self.challenger_profits.values())
        return provider_welfare + client_welfare + challenger_welfare


class SimulationEngine:
    """
    Main simulation engine for the Hellas fraud game ABM.

    Orchestrates:
    1. Agent creation and initialization
    2. Job generation and matching
    3. Execution decisions (honest vs cheat)
    4. Audit decisions
    5. Dispute resolution
    6. Reputation updates
    7. Settlement and finalization
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.protocol = config.protocol
        self.rng = np.random.default_rng(config.seed)

        # Initialize components
        self.market = Market(self.protocol)
        self.market.set_rng(self.rng)

        self.reputation_system = ReputationSystem(
            decay_rate=config.reputation.reputation_decay,
            gain_honest=config.reputation.reputation_gain_honest,
            loss_fraud=config.reputation.reputation_loss_fraud,
        )

        self.self_buy_detector = SelfBuyingDetector()
        self.job_queue = JobQueue(self.protocol.T_challenge)

        # Agents
        self.providers: List[Provider] = []
        self.clients: List[Client] = []
        self.challengers: List[Challenger] = []

        # State
        self.current_time = 0
        self.period_stats: List[Dict] = []

    def initialize_agents(self) -> None:
        """Create all agents based on configuration."""
        self._create_providers()
        self._create_clients()
        self._create_challengers()

        # Register providers in reputation system
        for provider in self.providers:
            self.reputation_system.register_provider(provider.agent_id)

    def _create_providers(self) -> None:
        """Create provider agents based on distribution."""
        n = self.config.n_providers

        n_honest = int(n * self.config.provider_honest_frac)
        n_rational = int(n * self.config.provider_rational_frac)
        n_adversarial = n - n_honest - n_rational

        for i in range(n_honest):
            p = HonestProvider(agent_id=f"P_H_{i}")
            p.set_rng(self.rng)
            self.providers.append(p)

        for i in range(n_rational):
            p = RationalProvider(agent_id=f"P_R_{i}")
            p.set_rng(self.rng)
            self.providers.append(p)

        for i in range(n_adversarial):
            # Mix of adversarial types
            if i % 3 == 0:
                p = AdversarialProvider(agent_id=f"P_A_{i}")
            elif i % 3 == 1:
                p = ReputationFarmerProvider(agent_id=f"P_RF_{i}")
            else:
                p = AdversarialProvider(agent_id=f"P_A_{i}")
            p.set_rng(self.rng)
            self.providers.append(p)

    def _create_clients(self) -> None:
        """Create client agents based on distribution."""
        n = self.config.n_clients

        n_always = int(n * self.config.client_always_audit_frac)
        n_never = int(n * self.config.client_never_audit_frac)
        n_mixed = n - n_always - n_never

        for i in range(n_always):
            c = AlwaysAuditClient(agent_id=f"C_AA_{i}")
            c.set_rng(self.rng)
            self.clients.append(c)

        for i in range(n_never):
            c = NeverAuditClient(agent_id=f"C_NA_{i}")
            c.set_rng(self.rng)
            self.clients.append(c)

        for i in range(n_mixed):
            # Mix of mixed-strategy types
            if i % 2 == 0:
                c = MixedStrategyClient(agent_id=f"C_MS_{i}")
            else:
                c = ReputationWeightedClient(agent_id=f"C_RW_{i}")
            c.set_rng(self.rng)
            self.clients.append(c)

    def _create_challengers(self) -> None:
        """Create challenger agents."""
        for i in range(self.config.n_challengers):
            c = PermissionlessChallenger(agent_id=f"CH_{i}")
            c.set_rng(self.rng)
            self.challengers.append(c)

    def run(self, show_progress: bool = True) -> SimulationResult:
        """
        Run the full simulation.

        Returns SimulationResult with all metrics.
        """
        self.initialize_agents()

        result = SimulationResult(
            config=self.config,
            n_periods=self.config.n_periods,
            seed=self.config.seed,
        )

        iterator = range(self.config.n_periods)
        if show_progress:
            iterator = tqdm(iterator, desc="Simulating")

        for period in iterator:
            period_result = self._run_period()
            self._record_period_result(period_result, result)
            self.current_time += 1

        # Finalize results
        self._finalize_results(result)

        return result

    def _run_period(self) -> Dict:
        """Run a single simulation period."""
        # Generate jobs
        client_ids = [c.agent_id for c in self.clients]
        jobs = self.market.generate_jobs(
            n_jobs=self.config.jobs_per_period,
            client_ids=client_ids,
            value_distribution=self.config.job_value_distribution,
            value_mean=self.config.job_value_mean,
            value_std=self.config.job_value_std,
        )

        period_stats = {
            "jobs": len(jobs),
            "frauds": 0,
            "frauds_detected": 0,
            "disputes": 0,
            "successful_disputes": 0,
            "stake_slashed": 0.0,
            "client_losses": 0.0,
            "stakes_used": [],
        }

        # Process each job
        for job in jobs:
            result = self._process_job(job)
            self._aggregate_job_result(result, period_stats)

        # Apply reputation decay
        self.reputation_system.apply_time_decay()

        # Record agent states
        for agent in self.providers + self.clients + self.challengers:
            agent.record_period()

        return period_stats

    def _process_job(self, job: Job) -> Dict:
        """
        Process a single job through the full lifecycle.

        Returns dict with job outcome.
        """
        # 1. Match to provider
        available_providers = [
            (p.agent_id, self.reputation_system.get_reputation(p.agent_id), p.balance)
            for p in self.providers
            if p.state.is_active and p.balance > self.protocol.S_P_min
        ]

        if not available_providers:
            return {"matched": False}

        provider_id = self.market.match_provider(job, available_providers)
        provider = next(p for p in self.providers if p.agent_id == provider_id)

        job.provider_id = provider_id

        # 2. Provider decides stake
        stake = provider.decide_stake(self.protocol, job.value)
        stake = min(stake, provider.balance)

        if stake < self.protocol.S_P_min:
            return {"matched": False}

        provider.lock_stake(stake)

        # 3. Provider decides execution (honest or cheat)
        # Estimate audit probability based on client type and reputation
        reputation = self.reputation_system.get_reputation(provider_id)
        estimated_audit_prob = self._estimate_audit_probability(
            job, provider_id, reputation, stake
        )

        is_honest = provider.decide_execution(
            job, self.protocol, stake, estimated_audit_prob
        )

        job.is_honest = is_honest

        # 4. Client decides whether to audit
        client = next(c for c in self.clients if c.agent_id == job.client_id)
        will_audit = client.decide_audit(
            job, provider_id, reputation, stake, self.protocol
        )

        job.is_audited = will_audit

        # 5. Audit outcome
        fraud_detected = False
        if will_audit:
            client.jobs_audited += 1
            client.audit_costs += self.protocol.C_safe
            client.debit(self.protocol.C_safe, "audit_cost")

            if not is_honest:
                fraud_detected = True
                job.fraud_detected = True

        # 6. Dispute resolution
        dispute_initiated = False
        dispute_successful = False
        slashed_amount = 0.0

        if fraud_detected:
            # Client can dispute
            if client.balance >= self.protocol.B_C + self.protocol.c_proof + self.protocol.c_tx:
                # Check if disputing is profitable
                expected_value = (
                    self.protocol.p_w * (self.protocol.beta * stake + self.protocol.lambda_ * job.value)
                    - (self.protocol.c_proof + self.protocol.c_tx)
                    - (1 - self.protocol.p_w) * self.protocol.B_C
                )

                if expected_value > 0:
                    dispute_initiated = True
                    job.dispute_initiated = True

                    # Pay dispute costs
                    client.debit(self.protocol.c_proof + self.protocol.c_tx, "dispute_costs")
                    client.debit(self.protocol.B_C, "challenge_bond")

                    # Enforcement outcome
                    if self.rng.random() < self.protocol.p_w:
                        dispute_successful = True
                        job.dispute_successful = True

                        # Slash provider
                        slashed_amount = provider.slash_stake(stake)
                        provider.times_slashed += 1
                        provider.total_slashed_amount += slashed_amount

                        # Reward client
                        reward = self.protocol.beta * slashed_amount + self.protocol.lambda_ * job.value
                        client.credit(reward, "dispute_reward")
                        client.dispute_rewards += reward

                        # Return bond
                        client.credit(self.protocol.B_C, "bond_return")
                    else:
                        # Dispute failed - lose bond
                        client.state.disputes_lost += 1

        # 7. Settlement
        if is_honest or not dispute_successful:
            # Provider gets paid (if not slashed)
            if not dispute_successful:
                provider.credit(job.value, "job_payment")
                provider.total_honest += 1 if is_honest else 0

            # Unlock remaining stake
            remaining_stake = stake - slashed_amount
            if remaining_stake > 0:
                provider.unlock_stake(remaining_stake)

        # 8. Client loss from undetected fraud
        client_loss = 0.0
        if not is_honest and not fraud_detected:
            client_loss = job.loss_if_incorrect
            client.losses_from_fraud += client_loss
            client.debit(client_loss, "fraud_loss")

        # 9. Update reputation
        if fraud_detected and dispute_successful:
            self.reputation_system.record_job_outcome(
                provider_id, honest=False, stake_used=stake, job_value=job.value
            )
            provider.total_cheats += 1
        else:
            self.reputation_system.record_job_outcome(
                provider_id, honest=True, stake_used=stake, job_value=job.value
            )

        # 10. Track self-buying patterns
        self.self_buy_detector.record_job(provider_id, job.client_id)

        return {
            "matched": True,
            "is_honest": is_honest,
            "is_audited": will_audit,
            "fraud_detected": fraud_detected,
            "dispute_initiated": dispute_initiated,
            "dispute_successful": dispute_successful,
            "stake": stake,
            "slashed": slashed_amount,
            "client_loss": client_loss,
        }

    def _estimate_audit_probability(
        self,
        job: Job,
        provider_id: str,
        reputation: float,
        stake: float,
    ) -> float:
        """
        Estimate the probability that this job will be audited.

        Used by providers to make strategic decisions.
        """
        # Base: equilibrium audit probability
        v_star = self.protocol.compute_v_star(job.value, stake)

        # Adjust based on reputation (higher rep -> lower audit probability)
        rep_factor = np.exp(-0.02 * (reputation - 50))

        # Consider client mix
        # Assume provider knows approximate client distribution
        frac_always = self.config.client_always_audit_frac
        frac_never = self.config.client_never_audit_frac
        frac_mixed = 1 - frac_always - frac_never

        expected_audit = (
            frac_always * 1.0 +
            frac_never * 0.0 +
            frac_mixed * min(v_star * rep_factor, 1.0)
        )

        return expected_audit

    def _aggregate_job_result(self, result: Dict, period_stats: Dict) -> None:
        """Aggregate job result into period statistics."""
        if not result.get("matched"):
            return

        if not result["is_honest"]:
            period_stats["frauds"] += 1

        if result["fraud_detected"]:
            period_stats["frauds_detected"] += 1

        if result["dispute_initiated"]:
            period_stats["disputes"] += 1

        if result["dispute_successful"]:
            period_stats["successful_disputes"] += 1
            period_stats["stake_slashed"] += result["slashed"]

        period_stats["client_losses"] += result["client_loss"]
        period_stats["stakes_used"].append(result["stake"])

    def _record_period_result(self, period_stats: Dict, result: SimulationResult) -> None:
        """Record period results into simulation result."""
        result.total_jobs += period_stats["jobs"]
        result.total_frauds += period_stats["frauds"]
        result.total_frauds_detected += period_stats["frauds_detected"]
        result.total_disputes += period_stats["disputes"]
        result.total_successful_disputes += period_stats["successful_disputes"]
        result.total_stake_slashed += period_stats["stake_slashed"]
        result.total_client_losses += period_stats["client_losses"]

        # Time series
        fraud_rate = period_stats["frauds"] / period_stats["jobs"] if period_stats["jobs"] > 0 else 0
        detection_rate = (
            period_stats["frauds_detected"] / period_stats["frauds"]
            if period_stats["frauds"] > 0 else 1.0
        )
        avg_stake = np.mean(period_stats["stakes_used"]) if period_stats["stakes_used"] else 0

        result.fraud_rate_history.append(fraud_rate)
        result.detection_rate_history.append(detection_rate)
        result.avg_stake_history.append(avg_stake)

        # Reputation
        rep_stats = self.reputation_system.get_statistics()
        result.avg_reputation_history.append(rep_stats.get("mean_reputation", 50))

        self.period_stats.append(period_stats)

    def _finalize_results(self, result: SimulationResult) -> None:
        """Finalize simulation results."""
        # Provider profits
        for provider in self.providers:
            result.provider_profits[provider.agent_id] = provider.state.total_profit

        # Client losses
        for client in self.clients:
            result.client_losses[client.agent_id] = (
                client.losses_from_fraud + client.audit_costs - client.dispute_rewards
            )

        # Challenger profits
        for challenger in self.challengers:
            result.challenger_profits[challenger.agent_id] = (
                challenger.total_rewards - challenger.total_costs
            )

        # Attack metrics
        result.attack_metrics = self._compute_attack_metrics()

    def _compute_attack_metrics(self) -> Dict:
        """Compute metrics related to attack success."""
        metrics = {}

        # Reputation farming detection
        farming_suspects = []
        for provider in self.providers:
            if isinstance(provider, (ReputationFarmerProvider, AdversarialProvider)):
                is_suspect = self.reputation_system.detect_reputation_farming(
                    provider.agent_id
                )
                if is_suspect:
                    farming_suspects.append(provider.agent_id)

        metrics["reputation_farming_suspects"] = farming_suspects
        metrics["n_farming_suspects"] = len(farming_suspects)

        # Self-buying detection
        self_buy_suspects = []
        for provider in self.providers:
            is_suspect, details = self.self_buy_detector.detect_self_buying(
                provider.agent_id
            )
            if is_suspect:
                self_buy_suspects.append((provider.agent_id, details))

        metrics["self_buy_suspects"] = self_buy_suspects

        # Adversarial success
        adversarial_profits = []
        for provider in self.providers:
            if isinstance(provider, (AdversarialProvider, ReputationFarmerProvider)):
                adversarial_profits.append(provider.state.total_profit)

        metrics["adversarial_total_profit"] = sum(adversarial_profits)
        metrics["adversarial_mean_profit"] = (
            np.mean(adversarial_profits) if adversarial_profits else 0
        )

        # Honest provider comparison
        honest_profits = []
        for provider in self.providers:
            if isinstance(provider, HonestProvider):
                honest_profits.append(provider.state.total_profit)

        metrics["honest_mean_profit"] = np.mean(honest_profits) if honest_profits else 0

        # Attack success ratio
        if metrics["honest_mean_profit"] > 0:
            metrics["attack_success_ratio"] = (
                metrics["adversarial_mean_profit"] / metrics["honest_mean_profit"]
            )
        else:
            metrics["attack_success_ratio"] = 0

        return metrics
