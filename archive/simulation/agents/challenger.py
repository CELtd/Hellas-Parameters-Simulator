"""
Challenger Agents for Hellas ABM

Challengers are entities that can initiate disputes when fraud is detected.
In the baseline model, the client is the challenger.
In protocol variants, challenging can be permissionless (watchers).
"""

from typing import Optional, List, Tuple
import numpy as np
from .base import Agent, Job, Channel
from ..config import ProtocolParameters


class Challenger(Agent):
    """
    Base challenger class.

    Challengers incur dispute costs and receive rewards if enforcement succeeds.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 1000.0,
        is_permissionless: bool = False,
    ):
        super().__init__(agent_id, initial_balance)
        self.is_permissionless = is_permissionless

        # Challenger-specific tracking
        self.disputes_submitted: int = 0
        self.disputes_won: int = 0
        self.disputes_lost: int = 0
        self.total_rewards: float = 0.0
        self.total_costs: float = 0.0
        self.bonds_forfeited: float = 0.0

    def get_agent_type(self) -> str:
        perm = "Permissionless" if self.is_permissionless else "Client"
        return f"Challenger[{perm}]"

    def compute_dispute_expected_value(
        self,
        protocol: ProtocolParameters,
        S_P: float,
        P_set: float,
    ) -> float:
        """
        Expected value of initiating a dispute (Proposition 2):
        E[U_C(dispute)] = p_w * R - C_disp - (1-p_w) * B_C

        where R = beta * S_P + lambda * P_set
        """
        R = protocol.beta * S_P + protocol.lambda_ * P_set
        C_disp = protocol.compute_C_disp()

        return (
            protocol.p_w * R
            - C_disp
            - (1 - protocol.p_w) * protocol.B_C
        )

    def decide_dispute(
        self,
        job: Job,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        """
        Decide whether to initiate a dispute.

        Dispute if expected value is positive (Proposition 2):
        p_w * R - C_disp - (1-p_w) * B_C > 0
        """
        expected_value = self.compute_dispute_expected_value(
            protocol, provider_stake, job.value
        )

        # Also check if we have enough balance for costs
        C_disp = protocol.compute_C_disp()
        can_afford = self.balance >= (C_disp + protocol.B_C)

        return expected_value > 0 and can_afford

    def execute_dispute(
        self,
        job: Job,
        provider_stake: float,
        protocol: ProtocolParameters,
        rng: np.random.Generator,
    ) -> Tuple[bool, float, float]:
        """
        Execute a dispute.

        Returns:
            (success, reward_if_success, cost)
        """
        C_disp = protocol.compute_C_disp()

        # Pay dispute costs
        self.debit(C_disp, "dispute_costs")
        self.total_costs += C_disp

        # Lock challenge bond
        self.debit(protocol.B_C, "challenge_bond")

        self.disputes_submitted += 1

        # Enforcement succeeds with probability p_w
        success = rng.random() < protocol.p_w

        if success:
            # Receive reward
            R = protocol.beta * provider_stake + protocol.lambda_ * job.value
            self.credit(R, "dispute_reward")
            self.total_rewards += R

            # Bond returned
            self.credit(protocol.B_C, "bond_return")

            self.disputes_won += 1
            return True, R, C_disp
        else:
            # Bond forfeited
            self.bonds_forfeited += protocol.B_C
            self.disputes_lost += 1
            return False, 0, C_disp + protocol.B_C


class PermissionlessChallenger(Challenger):
    """
    Permissionless watcher that monitors for fraud opportunities.

    These challengers create a market for auditing, raising effective
    detection probability without increasing client burden.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 2000.0,
        monitoring_cost_per_job: float = 0.5,  # Cost to monitor a job
        selectivity: float = 0.5,  # Fraction of jobs to monitor
    ):
        super().__init__(agent_id, initial_balance, is_permissionless=True)
        self.monitoring_cost_per_job = monitoring_cost_per_job
        self.selectivity = selectivity
        self.jobs_monitored: int = 0

    def decide_to_monitor(
        self,
        job: Job,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> bool:
        """
        Decide whether to monitor a job for potential fraud.

        Monitors if expected value of monitoring is positive.
        """
        # Expected value = P(fraud) * E[dispute profit] - monitoring cost
        # Assume base fraud rate (can be estimated from market data)
        estimated_fraud_rate = protocol.compute_q_star(
            provider_stake, job.value, job.loss_if_incorrect
        )

        expected_dispute_value = self.compute_dispute_expected_value(
            protocol, provider_stake, job.value
        )

        expected_monitoring_value = (
            estimated_fraud_rate * expected_dispute_value
            - self.monitoring_cost_per_job
        )

        # Also apply selectivity (resource constraint)
        if self._rng.random() > self.selectivity:
            return False

        return expected_monitoring_value > 0

    def monitor_and_dispute(
        self,
        job: Job,
        is_fraudulent: bool,
        provider_stake: float,
        protocol: ProtocolParameters,
    ) -> Optional[Tuple[bool, float]]:
        """
        Monitor a job and dispute if fraud is found.

        Returns:
            None if no fraud found or didn't monitor
            (success, net_profit) if dispute initiated
        """
        # Pay monitoring cost
        self.debit(self.monitoring_cost_per_job, "monitoring")
        self.total_costs += self.monitoring_cost_per_job
        self.jobs_monitored += 1

        if not is_fraudulent:
            return None  # No fraud to dispute

        # Fraud found - decide whether to dispute
        if not self.decide_dispute(job, provider_stake, protocol):
            return None  # Not profitable to dispute

        # Execute dispute
        success, reward, cost = self.execute_dispute(
            job, provider_stake, protocol, self._rng
        )

        net_profit = reward - cost - self.monitoring_cost_per_job
        return success, net_profit


class GriefingChallenger(Challenger):
    """
    Malicious challenger that files frivolous disputes to grief honest providers.

    Attack vector: Delay settlement and impose costs on honest providers.
    This is mitigated by the challenge bond B_C.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 5000.0,
        griefing_budget: float = 1000.0,
    ):
        super().__init__(agent_id, initial_balance, is_permissionless=True)
        self.griefing_budget = griefing_budget
        self.griefing_spent: float = 0.0

    def attempt_grief(
        self,
        job: Job,
        is_actually_fraudulent: bool,
        protocol: ProtocolParameters,
    ) -> Tuple[bool, float]:
        """
        Attempt to file a frivolous dispute.

        If the job is actually honest, the dispute will fail and
        the griefer loses the challenge bond.

        Returns:
            (dispute_filed, cost_incurred)
        """
        if self.griefing_spent >= self.griefing_budget:
            return False, 0

        # Cost of griefing attempt
        C_disp = protocol.compute_C_disp()
        total_cost = C_disp + protocol.B_C

        if self.balance < total_cost:
            return False, 0

        # File dispute
        self.debit(total_cost, "griefing_attempt")
        self.griefing_spent += total_cost
        self.disputes_submitted += 1

        if is_actually_fraudulent:
            # Accidentally caught real fraud
            if self._rng.random() < protocol.p_w:
                # Bond returned, get reward
                self.credit(protocol.B_C, "bond_return")
                self.disputes_won += 1
                return True, C_disp
            else:
                self.disputes_lost += 1
                return True, total_cost
        else:
            # Frivolous dispute - will fail, lose bond
            self.bonds_forfeited += protocol.B_C
            self.disputes_lost += 1
            return True, total_cost
