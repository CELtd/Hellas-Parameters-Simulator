# Hellas Protocol: Fraud Game Analysis

A comprehensive research project analyzing the game-theoretic foundations of fraud prevention in off-chain computation verification systems. This repository contains the academic paper, an advanced agent-based simulation framework, and an interactive web application for exploring protocol dynamics.

## Project Components

### 1. Academic Paper (`main.tex`)

The foundational research paper presenting the formal game-theoretic analysis of the Hellas Protocol's fraud game mechanism.

**Key Contributions:**
- Mixed strategy Nash equilibrium characterization
- Minimum viable stake derivation
- Incentive compatibility conditions
- Attack vector taxonomy

**Build the paper:**
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### 2. Python Simulation Framework (`simulation/`)

An advanced agent-based modeling (ABM) framework for simulating protocol dynamics with heterogeneous agent populations.

**Features:**
- Multiple agent types: Honest, Rational, Adversarial, Reputation Farmer
- Monte Carlo simulation engine
- Attack scenario analysis
- Streamlit interactive dashboard
- Comprehensive metrics and visualization

**Quick Start:**
```bash
cd simulation
pip install -e .
streamlit run app.py
```

See [`simulation/README.md`](simulation/README.md) for detailed documentation.

### 3. React Web Application (`webapp/`)

A beautiful, interactive web application for exploring equilibrium dynamics and running simulations.

**Features:**
- Real-time equilibrium analysis with sensitivity charts
- Monte Carlo simulation with configurable parameters
- Attack vector impact visualization
- Modern UI with Tailwind CSS and Framer Motion

**Quick Start:**
```bash
cd webapp
npm install
npm run dev
```

See [`webapp/README.md`](webapp/README.md) for detailed documentation.

### 4. Simulation Report (`simulation_report.tex`)

A detailed academic report documenting the simulation methodology, experiments, and findings.

**Build the report:**
```bash
pdflatex simulation_report.tex
```

## Theoretical Foundation

### The Fraud Game

The Hellas Protocol uses a verification game where:
- **Providers** execute computations and post stake as collateral
- **Clients** can verify results or accept them on trust
- **Challengers** can dispute incorrect results for rewards

### Key Equations

**Provider's Fraud Probability:**
```
v* = (c_H - c_F) / (P_set + S_P)
```

**Client's Verification Probability:**
```
q* = C_safe / (L + Δ)
```

**Dispute Surplus:**
```
Δ = p_w(βS_P + λP_set) - (c_proof + c_tx) - (1-p_w)B_C
```

**Minimum Viable Stake:**
```
S_P^min = ((c_H - c_F)(L + Δ)) / (C_safe(1 - θ)) - P_set
```

### Parameters

| Symbol | Description |
|--------|-------------|
| S_P | Provider stake (collateral) |
| P_set | Settlement payment to provider |
| L | Client loss from incorrect result |
| c_H | Cost of honest execution |
| c_F | Cost of cheating |
| C_safe | Cost of safe fallback verification |
| p_w | Probability dispute succeeds |
| β | Fraction of slashed stake to challenger |
| λ | Payment routing parameter |
| θ | Target maximum fraud rate |

## Attack Vectors Analyzed

1. **Reputation Farming** - Building false reputation through low-stake honest transactions
2. **No Stake Floor** - Exploiting absence of minimum stake requirements
3. **Sybil Attacks** - Using multiple identities to circumvent slashing
4. **Collusion** - Provider-challenger coordination to extract value
5. **Griefing** - Malicious challenges against honest providers
6. **Censorship** - Blocking legitimate dispute transactions

## Repository Structure

```
helas/
├── main.tex                    # Academic paper
├── simulation_report.tex       # Simulation report
├── simulation/                 # Python ABM framework
│   ├── config.py              # Protocol parameters
│   ├── agents/                # Agent implementations
│   ├── core/                  # Simulation engine
│   ├── attacks/               # Attack scenarios
│   ├── analysis/              # Metrics and visualization
│   ├── app.py                 # Streamlit dashboard
│   └── README.md
├── webapp/                     # React web application
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── lib/               # Simulation logic
│   │   └── App.tsx
│   └── README.md
└── README.md                   # This file
```

## Getting Started

### For Researchers

1. Read the paper (`main.tex`) for theoretical foundations
2. Run experiments with the Python simulation framework
3. Explore parameter spaces with the interactive webapp

### For Protocol Designers

1. Use the webapp to understand equilibrium dynamics
2. Analyze attack scenarios to identify vulnerabilities
3. Tune parameters to achieve desired security properties

### For Developers

1. Study the simulation architecture in `simulation/`
2. Extend agent types for new behavioral models
3. Add new attack scenarios to stress-test designs

## Requirements

**Paper:**
- LaTeX distribution (TeX Live, MiKTeX)

**Python Simulation:**
- Python 3.9+
- Dependencies: numpy, pandas, matplotlib, plotly, streamlit

**React Webapp:**
- Node.js 18+
- npm or yarn

## Citation

```bibtex
@article{hellas2026,
  title={Fraud Game Analysis for Hellas Protocol},
  author={CryptoEconLab},
  journal={Working Paper},
  year={2026}
}
```

## License

Research conducted by CryptoEconLab. See individual components for specific licensing.

## Acknowledgments

This research is part of the broader effort to establish rigorous economic foundations for decentralized verification systems.
