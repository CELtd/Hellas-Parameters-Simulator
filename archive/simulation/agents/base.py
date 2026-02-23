"""
Base Agent Class for Hellas ABM

Defines the common interface and state tracking for all agent types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
from uuid import uuid4


@dataclass
class AgentState:
    """Tracks agent's economic state over time."""
    balance: float = 0.0
    locked_stake: float = 0.0
    total_profit: float = 0.0
    total_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    disputes_initiated: int = 0
    disputes_won: int = 0
    disputes_lost: int = 0
    reputation_score: float = 50.0  # Starting reputation
    is_active: bool = True

    # History tracking
    balance_history: List[float] = field(default_factory=list)
    reputation_history: List[float] = field(default_factory=list)


class Agent(ABC):
    """
    Abstract base class for all agents in the Hellas fraud game.

    Each agent maintains internal state and implements decision methods
    specific to their role (provider, client, challenger).
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 1000.0,
        risk_aversion: float = 0.0,  # 0 = risk neutral (baseline assumption)
    ):
        self.agent_id = agent_id or str(uuid4())[:8]
        self.state = AgentState(balance=initial_balance)
        self.risk_aversion = risk_aversion
        self._rng = np.random.default_rng()

    def set_rng(self, rng: np.random.Generator):
        """Set the random number generator for reproducibility."""
        self._rng = rng

    @property
    def balance(self) -> float:
        return self.state.balance

    @property
    def reputation(self) -> float:
        return self.state.reputation_score

    def credit(self, amount: float, reason: str = "") -> None:
        """Add funds to agent's balance."""
        self.state.balance += amount
        self.state.total_profit += amount

    def debit(self, amount: float, reason: str = "") -> bool:
        """
        Remove funds from agent's balance.
        Returns False if insufficient funds.
        """
        if self.state.balance >= amount:
            self.state.balance -= amount
            return True
        return False

    def lock_stake(self, amount: float) -> bool:
        """Lock stake for a channel."""
        if self.debit(amount, "stake_lock"):
            self.state.locked_stake += amount
            return True
        return False

    def unlock_stake(self, amount: float) -> None:
        """Return stake after channel settlement."""
        self.state.locked_stake -= amount
        self.credit(amount, "stake_unlock")

    def slash_stake(self, amount: float) -> float:
        """
        Slash locked stake. Returns amount actually slashed.
        """
        slashed = min(amount, self.state.locked_stake)
        self.state.locked_stake -= slashed
        return slashed

    def update_reputation(self, delta: float) -> None:
        """Update reputation score."""
        self.state.reputation_score = max(0.0, self.state.reputation_score + delta)

    def record_period(self) -> None:
        """Record state at end of period for history tracking."""
        self.state.balance_history.append(self.state.balance)
        self.state.reputation_history.append(self.state.reputation_score)

    @abstractmethod
    def get_agent_type(self) -> str:
        """Return the type of agent."""
        pass

    def __repr__(self) -> str:
        return f"{self.get_agent_type()}(id={self.agent_id}, balance={self.balance:.2f}, rep={self.reputation:.2f})"


@dataclass
class Job:
    """Represents a computation job in the channel."""
    job_id: str
    client_id: str
    value: float              # P_set - payment amount
    loss_if_incorrect: float  # L - client loss from incorrect result
    complexity: float = 1.0   # Multiplier for costs

    # Execution state
    provider_id: Optional[str] = None
    is_executed: bool = False
    is_honest: bool = True
    is_audited: bool = False
    fraud_detected: bool = False
    dispute_initiated: bool = False
    dispute_successful: bool = False

    @classmethod
    def create(cls, client_id: str, value: float, L: float, rng: np.random.Generator) -> "Job":
        """Factory method to create a new job."""
        return cls(
            job_id=str(uuid4())[:8],
            client_id=client_id,
            value=value,
            loss_if_incorrect=L,
        )


@dataclass
class Channel:
    """
    Represents a state channel between client and provider.

    Timeline: Open -> Execution -> Challenge Window -> Finalization
    """
    channel_id: str
    client_id: str
    provider_id: str
    provider_stake: float
    payment_escrow: float
    challenge_bond: float

    # State
    is_open: bool = True
    is_disputed: bool = False
    is_finalized: bool = False
    time_opened: int = 0
    challenge_deadline: int = 0

    # Jobs in this channel
    jobs: List[Job] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        client_id: str,
        provider_id: str,
        stake: float,
        payment: float,
        bond: float,
        current_time: int,
        challenge_window: int,
    ) -> "Channel":
        return cls(
            channel_id=str(uuid4())[:8],
            client_id=client_id,
            provider_id=provider_id,
            provider_stake=stake,
            payment_escrow=payment,
            challenge_bond=bond,
            time_opened=current_time,
            challenge_deadline=current_time + challenge_window,
        )
