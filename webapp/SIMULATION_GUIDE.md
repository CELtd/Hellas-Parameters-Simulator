# Hellas Fraud Game Simulator - User Guide

This guide walks you through the interactive webapp for exploring the economics of off-chain computation verification.

---

## Quick Start

```bash
cd webapp
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Interface Overview

The webapp has three main areas:

```
┌─────────────────────────────────────────────────────────┐
│  HEADER - Quick stats: Stake, Payment, Enforcement      │
├─────────────────┬───────────────────────────────────────┤
│  LEFT SIDEBAR   │  MAIN CONTENT                         │
│  - Parameters   │  [Equilibrium] [Simulation] [Attacks] │
│  - Reset        │                                       │
│  - Resources    │  (tab content here)                   │
└─────────────────┴───────────────────────────────────────┘
```

---

## Sidebar Parameters

Adjust these to explore different protocol configurations:

### Economic Parameters
| Parameter | Symbol | Default | Description |
|-----------|--------|---------|-------------|
| Provider Stake | S_P | $100 | Collateral locked by providers |
| Settlement Payment | P_set | $50 | Fee paid for completed jobs |
| Client Loss | L | $50 | Damage from incorrect results |

### Costs
| Parameter | Symbol | Default | Description |
|-----------|--------|---------|-------------|
| Honest Cost | c_H | $5 | Cost to execute honestly |
| Cheating Cost | c_F | $0.50 | Cost to cheat |
| Safe Fallback | C_safe | $8 | Client's self-execution cost |
| Proof Cost | c_proof | $2 | Generating fraud proofs |
| Transaction Cost | c_tx | $1 | On-chain transaction fees |
| Challenge Bond | B_C | $5 | Bond posted by challengers |

### Protocol Design
| Parameter | Symbol | Default | Description |
|-----------|--------|---------|-------------|
| Slash Reward (β) | β | 0.5 | Fraction of stake given to challenger |
| Payment Routing (λ) | λ | 1.0 | Payment fraction routed through protocol |
| Enforcement Prob (p_w) | p_w | 0.95 | Probability disputes resolve correctly |

---

## Tab 1: Equilibrium Analysis

This tab shows the **mixed-strategy Nash equilibrium** of the fraud game.

### Key Metrics

| Metric | Meaning | What to Watch |
|--------|---------|---------------|
| **v*** (Audit Rate) | Probability clients verify results | Higher = more security overhead |
| **q*** (Cheat Rate) | Probability rational providers cheat | Lower = safer protocol |
| **Δ** (Dispute Surplus) | Expected profit from challenging fraud | Must be > 0 for enforcement |
| **S_P^min** | Minimum viable stake | Stake must exceed this |

### Status Indicators

- **Enforcement Viable** (green): S_P ≥ S_P^min - disputes are profitable
- **Incentive Compatible** (green): v* ≥ θ - honest execution is rational

### Sensitivity Charts

Select a parameter to see how equilibrium values respond:
- **S_P sweep**: How stake affects cheating rate
- **p_w sweep**: How enforcement reliability affects behavior
- **C_safe sweep**: How fallback costs affect client auditing
- **β sweep**: How slash rewards affect challenger incentives
- **L sweep**: How client losses affect verification rates

---

## Tab 2: Simulation

Run agent-based Monte Carlo simulations to see dynamics over time.

### Controls

| Setting | Range | Description |
|---------|-------|-------------|
| Periods | 50-500 | Number of simulation rounds |
| Honest Fraction | 0-100% | Percentage of always-honest providers |

### Running a Simulation

1. Adjust parameters in the sidebar
2. Set simulation periods and honest fraction
3. Click **Run Simulation**
4. View results in three chart modes:
   - **Fraud Rate**: Cheating and detection over time
   - **Welfare**: Provider profits, client costs, net welfare
   - **Reputation**: Average provider reputation trajectory

### Summary Metrics

After simulation completes:
- **Total Jobs**: Number of jobs processed
- **Fraud Rate**: Percentage of fraudulent executions
- **Detection Rate**: Percentage of fraud caught
- **Social Welfare**: Net economic value created

---

## Tab 3: Attack Analysis

Explore protocol vulnerabilities and their impact.

### Attack Types

| Attack | Mechanism | Severity |
|--------|-----------|----------|
| **Reputation Farming** | Build trust with small jobs, then defraud big ones | Medium |
| **No Stake Floor** | Exploit zero minimum stake requirement | High |
| **Sybil Attacks** | Create multiple identities to dilute penalties | High |
| **Collusion** | Provider-challenger coordination | Critical |
| **Censorship** | Block dispute transactions | Medium |

### Reading the Results

- **Welfare Loss Chart**: Horizontal bars showing damage from each attack
- **Attack Cards**: Individual analysis with fraud rate changes
- **Severity Badges**: Color-coded risk levels

---

## Workflow Examples

### Example 1: Finding Minimum Viable Stake

1. Go to **Equilibrium** tab
2. Note the current S_P^min value
3. Use the S_P slider to reduce stake below S_P^min
4. Watch the "Enforcement Viable" indicator turn red
5. This shows the threshold where disputes become unprofitable

### Example 2: Testing High-Stakes Environment

1. Set S_P = $500 (high stake)
2. Set P_set = $100 (higher payment)
3. Observe how q* (cheating rate) drops significantly
4. Run a **Simulation** to confirm low fraud rates

### Example 3: Stress Testing Enforcement

1. Set p_w = 0.70 (lower enforcement reliability)
2. Watch Δ (dispute surplus) decrease
3. If Δ < 0, challengers won't dispute fraud
4. Test mitigations: increase β or S_P

### Example 4: Evaluating Attack Resilience

1. Go to **Attacks** tab
2. Note welfare losses for each attack type
3. Adjust parameters to reduce critical vulnerabilities
4. Re-check attack outcomes

---

## Key Equations

### Equilibrium Cheating Rate
```
q* = C_safe / (L + Δ)
```
Clients audit until indifferent between verifying and trusting.

### Equilibrium Audit Rate
```
v* = (c_H - c_F) / (P_set + S_P)
```
Providers cheat until indifferent between honesty and fraud.

### Dispute Surplus
```
Δ = p_w(βS_P + λP_set) - (c_proof + c_tx) - (1-p_w)B_C
```
Must be positive for challengers to participate.

### Minimum Viable Stake
```
S_P^min = max{0, (C_disp + (1-p_w)B_C - p_w·λ·P_set) / (p_w·β)}
```
Protocol requires S_P ≥ S_P^min for enforcement.

---

## Tips

- **Reset Parameters**: Click the reset button to return to defaults
- **Real-time Updates**: All tabs update immediately when you change parameters
- **Compare Scenarios**: Note values, change parameters, compare new values
- **Use Sensitivity Charts**: Understand which parameters matter most

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Charts not updating | Check browser console for errors |
| Simulation stuck | Reduce period count, refresh page |
| Negative welfare | Normal for some attack scenarios |
| v* > 1 displayed | Indicates equilibrium breakdown |

---

## Next Steps

- Read the [academic paper](../main.tex) for theoretical foundations
- Explore the [Python simulation](../simulation/) for deeper analysis
- Check [simulation_report.tex](../simulation_report.tex) for experiment results
