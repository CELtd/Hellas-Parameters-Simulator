# Hellas Fraud Game Interactive Simulator

An interactive web application for exploring the economic dynamics of the Hellas Protocol's fraud game mechanism. This tool allows researchers and protocol designers to analyze equilibrium behavior, run simulations, and understand attack vectors in off-chain computation verification systems.

## Overview

The Hellas Protocol uses a fraud game mechanism to ensure honest computation in off-chain settings. Providers post stake that can be slashed if they submit incorrect results, while clients can challenge disputed outcomes. This simulator helps visualize and understand the game-theoretic equilibria that emerge from different parameter choices.

### Key Concepts

- **Mixed Strategy Equilibrium**: Providers cheat with probability `v*`, clients verify with probability `q*`
- **Minimum Viable Stake**: The stake threshold below which honest behavior cannot be incentivized
- **Dispute Surplus (Δ)**: The expected gain from challenging fraudulent results

## Features

### Equilibrium Analysis
- Interactive sensitivity analysis for all protocol parameters
- Real-time computation of equilibrium values (v*, q*, Δ, θ)
- Visual exploration of how parameter changes affect system behavior

### Monte Carlo Simulation
- Configurable multi-round simulations with heterogeneous agent populations
- Track fraud rates and welfare loss over time
- Analyze steady-state behavior under different conditions

### Attack Vector Analysis
- **Reputation Farming**: Exploiting low-stake periods to build false reputation
- **No Stake Floor**: Consequences of allowing arbitrarily low stakes
- **Sybil Attacks**: Multiple identities to circumvent slashing
- **Collusion**: Provider-challenger coordination
- **Griefing**: Malicious challenges against honest providers
- **Censorship**: Blocking legitimate disputes

## Installation

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup

```bash
# Navigate to the webapp directory
cd webapp

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The production build will be output to the `dist/` directory.

## Usage

### Parameter Controls

The sidebar contains all configurable protocol parameters:

| Parameter | Symbol | Description | Default |
|-----------|--------|-------------|---------|
| Provider Stake | S_P | Collateral locked by provider | $100 |
| Payment | P_set | Settlement payment to provider | $50 |
| Client Loss | L | Loss from incorrect result | $75 |
| Honest Cost | c_H | Cost of honest execution | $5 |
| Cheat Cost | c_F | Cost of cheating | $0.5 |
| Verification Cost | C_safe | Safe fallback cost | $10 |
| Enforcement | p_w | Dispute success probability | 95% |
| Slash Reward | β | Fraction of slash to challenger | 50% |
| Payment Route | λ | Payment routed on success | 100% |

### Tabs

1. **Equilibrium**: Explore how equilibrium values change with parameter variations
2. **Simulation**: Run Monte Carlo simulations with configurable agent populations
3. **Attacks**: Analyze the impact of various attack scenarios

## Mathematical Foundation

### Provider's Fraud Probability

```
v* = (c_H - c_F) / (P_set + S_P)
```

The probability a rational provider cheats depends on the cost savings from cheating relative to potential losses.

### Client's Verification Probability

```
q* = C_safe / (L + Δ)
```

Clients verify based on the cost of safe fallback relative to potential loss plus dispute surplus.

### Dispute Surplus

```
Δ = p_w(βS_P + λP_set) - (c_proof + c_tx) - (1-p_w)B_C
```

The expected gain from challenging a fraudulent result.

### Minimum Viable Stake

```
S_P^min = ((c_H - c_F)(L + Δ)) / (C_safe(1 - θ)) - P_set
```

The minimum stake required to achieve a target maximum fraud rate θ.

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS v4** - Styling
- **Recharts** - Data visualization
- **Framer Motion** - Animations
- **Lucide React** - Icons

## Project Structure

```
webapp/
├── src/
│   ├── components/
│   │   ├── charts/          # Visualization components
│   │   │   ├── AttackChart.tsx
│   │   │   ├── EquilibriumChart.tsx
│   │   │   └── SimulationChart.tsx
│   │   ├── sections/        # Main content sections
│   │   │   ├── AttacksSection.tsx
│   │   │   ├── EquilibriumSection.tsx
│   │   │   └── SimulationSection.tsx
│   │   └── ui/              # Reusable UI components
│   │       ├── Card.tsx
│   │       ├── Slider.tsx
│   │       ├── StatCard.tsx
│   │       └── Tooltip.tsx
│   ├── lib/
│   │   ├── simulation.ts    # Core simulation logic
│   │   └── utils.ts         # Utility functions
│   ├── App.tsx              # Main application
│   ├── index.css            # Global styles
│   └── main.tsx             # Entry point
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Related Resources

- [Hellas Protocol Paper](../main.tex) - Full academic paper on fraud game analysis
- [Python Simulation](../simulation/) - Advanced ABM simulator with Streamlit dashboard
- [Simulation Report](../simulation_report.tex) - Detailed experimental results

## Development

### Type Checking

```bash
npx tsc --noEmit
```

### Building

```bash
npm run build
```

## License

This project is part of the Hellas Protocol research conducted by CryptoEconLab.

## Citation

If you use this simulator in your research, please cite:

```bibtex
@article{hellas2026,
  title={Fraud Game Analysis for Hellas Protocol},
  author={CryptoEconLab},
  year={2026},
  note={Interactive simulator available at https://github.com/cryptoeconlab/hellas}
}
```
