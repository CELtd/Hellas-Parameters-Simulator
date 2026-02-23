/**
 * Hellas Fraud Game Simulation Engine
 *
 * Implements the economic model from:
 * "Fraud Game Analysis for Hellas Protocol" (CryptoEconLab, 2026)
 */

export interface ProtocolParams {
  S_P: number;      // Provider stake
  P_set: number;    // Settlement payment
  c_H: number;      // Honest execution cost
  c_F: number;      // Cheating cost
  C_safe: number;   // Safe fallback cost
  c_proof: number;  // Proof generation cost
  c_tx: number;     // Transaction cost
  beta: number;     // Slash reward fraction
  lambda: number;   // Payment routing fraction
  p_w: number;      // Enforcement probability
  B_C: number;      // Challenge bond
  L: number;        // Client loss from incorrect result
  v_min: number;    // Minimum audit probability (random audit floor)
}

export interface EquilibriumValues {
  v_star: number;           // Equilibrium audit probability
  q_star: number;           // Equilibrium cheating probability
  theta: number;            // Provider IC threshold
  Delta: number;            // Net dispute surplus
  S_P_min: number;          // Minimum viable stake
  mu_star: number;          // Belief threshold
  isEnforcementViable: boolean;
  isICsatisfied: boolean;
  expectedProviderUtility: number;
  expectedClientUtility: number;
}

export interface SimulationResult {
  periods: number[];
  fraudRates: number[];
  detectionRates: number[];
  auditRates: number[];        // Adaptive audit probability over time
  reputationHistory: number[];
  providerProfits: number[];
  clientLosses: number[];
  cumulativeWelfare: number[];
  totalJobs: number;
  totalFrauds: number;
  totalDetected: number;
  finalFraudRate: number;
  finalDetectionRate: number;
  socialWelfare: number;
}

export const DEFAULT_PARAMS: ProtocolParams = {
  S_P: 100,
  P_set: 50,
  c_H: 5.0,
  c_F: 0.5,
  C_safe: 8.0,
  c_proof: 2.0,
  c_tx: 1.0,
  beta: 0.5,
  lambda: 1.0,
  p_w: 0.95,
  B_C: 5.0,
  L: 50,
  v_min: 0.02,  // 2% minimum random audit probability
};

/**
 * Compute the net dispute surplus Δ
 * Δ = p_w(β·S_P + λ·P_set) - (c_proof + c_tx) - (1-p_w)·B_C
 */
export function computeDelta(params: ProtocolParams): number {
  const { p_w, beta, S_P, lambda, P_set, c_proof, c_tx, B_C } = params;
  return p_w * (beta * S_P + lambda * P_set) - (c_proof + c_tx) - (1 - p_w) * B_C;
}

/**
 * Compute provider incentive threshold θ
 * θ = (c_H - c_F) / (P_set + S_P)
 */
export function computeTheta(params: ProtocolParams): number {
  const { c_H, c_F, P_set, S_P } = params;
  return (c_H - c_F) / (P_set + S_P);
}

/**
 * Compute minimum viable stake S_P^min
 * S_P^min = max{0, (C_disp + (1-p_w)B_C - p_w·λ·P_set) / (p_w·β)}
 */
export function computeMinViableStake(params: ProtocolParams): number {
  const { C_safe, c_proof, c_tx, p_w, B_C, lambda, P_set, beta } = params;
  const C_disp = C_safe + c_proof + c_tx;
  const numerator = C_disp + (1 - p_w) * B_C - p_w * lambda * P_set;
  const denominator = p_w * beta;
  return Math.max(0, numerator / denominator);
}

/**
 * Compute equilibrium audit probability v*
 * v* = (c_H - c_F) / (P_set + S_P)
 */
export function computeVStar(params: ProtocolParams): number {
  return computeTheta(params);
}

/**
 * Compute equilibrium cheating probability q*
 * q* = C_safe / (L + Δ)
 */
export function computeQStar(params: ProtocolParams): number {
  const Delta = computeDelta(params);
  const { C_safe, L } = params;

  if (L + Delta <= 0) return 1.0;
  return Math.min(1.0, C_safe / (L + Delta));
}

/**
 * Compute all equilibrium values
 */
export function computeEquilibrium(params: ProtocolParams): EquilibriumValues {
  const v_star = computeVStar(params);
  const q_star = computeQStar(params);
  const theta = computeTheta(params);
  const Delta = computeDelta(params);
  const S_P_min = computeMinViableStake(params);
  const mu_star = q_star; // Same formula at equilibrium

  const isEnforcementViable = params.S_P >= S_P_min;
  const isICsatisfied = v_star >= theta;

  // Expected utilities at equilibrium
  const expectedProviderUtility = params.P_set - params.c_H;
  const expectedClientUtility =
    -params.P_set
    - v_star * params.C_safe
    - (1 - v_star) * q_star * params.L
    + v_star * q_star * Delta;

  return {
    v_star,
    q_star,
    theta,
    Delta,
    S_P_min,
    mu_star,
    isEnforcementViable,
    isICsatisfied,
    expectedProviderUtility,
    expectedClientUtility,
  };
}

/**
 * Simple random number generator with seed
 */
class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  next(): number {
    this.seed = (this.seed * 1103515245 + 12345) & 0x7fffffff;
    return this.seed / 0x7fffffff;
  }
}

/**
 * Run a simplified simulation with adaptive client auditing
 */
export function runSimulation(
  params: ProtocolParams,
  nPeriods: number = 100,
  nJobsPerPeriod: number = 20,
  honestFraction: number = 0.6,
  seed: number = 42
): SimulationResult {
  const rng = new SeededRandom(seed);
  const eq = computeEquilibrium(params);

  const periods: number[] = [];
  const fraudRates: number[] = [];
  const detectionRates: number[] = [];
  const auditRates: number[] = [];
  const reputationHistory: number[] = [];
  const providerProfits: number[] = [];
  const clientLosses: number[] = [];
  const cumulativeWelfare: number[] = [];

  let totalJobs = 0;
  let totalFrauds = 0;
  let totalDetected = 0;
  let avgReputation = 50;
  let cumProviderProfit = 0;
  let cumClientLoss = 0;

  // Adaptive auditing state: track recent fraud observations
  const recentWindowSize = 5; // periods to consider for fraud estimation
  const recentFraudRates: number[] = [];
  let adaptiveAuditProb = eq.v_star; // Start at equilibrium

  for (let t = 0; t < nPeriods; t++) {
    let periodFrauds = 0;
    let periodDetected = 0;
    let periodProviderProfit = 0;
    let periodClientLoss = 0;
    let periodAudits = 0;

    for (let j = 0; j < nJobsPerPeriod; j++) {
      totalJobs++;

      // Determine if provider is honest type
      const isHonestType = rng.next() < honestFraction;

      // Provider decision: now considers the adaptive audit probability
      let cheats = false;
      if (!isHonestType) {
        // Rational provider estimates audit probability based on:
        // 1. Current adaptive audit rate (public knowledge from recent behavior)
        // 2. Reputation adjustment (providers may think high rep = less scrutiny)
        const reputationFactor = Math.exp(-0.01 * (avgReputation - 50)); // Reduced from 0.02
        const estimatedAuditProb = adaptiveAuditProb * reputationFactor;

        const U_honest = params.P_set - params.c_H;
        const U_cheat = params.P_set - params.c_F - estimatedAuditProb * (params.P_set + params.S_P);

        // Provider plays mixed strategy when utilities are close
        const utilityDiff = U_cheat - U_honest;
        if (utilityDiff > 1) {
          // Clear advantage to cheat
          cheats = rng.next() > 0.2; // 80% cheat
        } else if (utilityDiff > -1) {
          // Utilities close: play mixed strategy near q*
          cheats = rng.next() < eq.q_star;
        }
        // else: U_honest clearly better, don't cheat
      }

      if (cheats) {
        totalFrauds++;
        periodFrauds++;

        // Client audit decision: adaptive with floor
        // Audit probability = max(v_min, adaptive rate)
        const effectiveAuditProb = Math.max(params.v_min, adaptiveAuditProb);
        const audits = rng.next() < effectiveAuditProb;

        if (audits) {
          totalDetected++;
          periodDetected++;
          periodAudits++;

          // Dispute outcome
          if (rng.next() < params.p_w) {
            // Successful dispute
            const reward = params.beta * params.S_P + params.lambda * params.P_set;
            periodProviderProfit -= params.S_P;
            periodClientLoss -= (reward - params.C_safe - params.c_proof - params.c_tx);
            avgReputation = Math.max(0, avgReputation - 5);
          } else {
            periodClientLoss += params.C_safe + params.B_C;
          }
        } else {
          // Undetected fraud
          periodProviderProfit += params.P_set - params.c_F;
          periodClientLoss += params.L;
        }
      } else {
        // Honest execution
        periodProviderProfit += params.P_set - params.c_H;
        avgReputation = Math.min(100, avgReputation + 0.1);
      }
    }

    // Update adaptive audit probability based on observed fraud
    const periodFraudRate = periodFrauds / nJobsPerPeriod;
    recentFraudRates.push(periodFraudRate);
    if (recentFraudRates.length > recentWindowSize) {
      recentFraudRates.shift();
    }

    // Clients adapt: if fraud is high, audit more; if low, audit less
    // But always respect the floor v_min and cap at reasonable maximum
    const observedFraudRate = recentFraudRates.reduce((a, b) => a + b, 0) / recentFraudRates.length;
    const Delta = computeDelta(params);

    // Adaptive rule: v_adaptive = C_safe / (L + Delta) when q = observedFraudRate
    // At equilibrium: q* = C_safe / (L + Delta), so if q > q*, clients should audit more
    // Scale audit probability proportionally to observed fraud vs equilibrium
    const fraudRatio = eq.q_star > 0 ? observedFraudRate / eq.q_star : 1;
    const targetAuditProb = eq.v_star * Math.sqrt(fraudRatio); // Dampened response

    // Smooth adjustment toward target (don't jump instantly)
    const learningRate = 0.3;
    adaptiveAuditProb = adaptiveAuditProb + learningRate * (targetAuditProb - adaptiveAuditProb);

    // Enforce floor and ceiling
    adaptiveAuditProb = Math.max(params.v_min, Math.min(1.0, adaptiveAuditProb));

    cumProviderProfit += periodProviderProfit;
    cumClientLoss += periodClientLoss;

    periods.push(t);
    fraudRates.push(periodFraudRate);
    // Detection rate: only count periods with fraud; use previous value for no-fraud periods
    detectionRates.push(periodFrauds > 0 ? periodDetected / periodFrauds : (t > 0 ? detectionRates[t-1] : eq.v_star));
    auditRates.push(adaptiveAuditProb);
    reputationHistory.push(avgReputation);
    providerProfits.push(cumProviderProfit);
    clientLosses.push(cumClientLoss);
    cumulativeWelfare.push(cumProviderProfit - cumClientLoss);
  }

  return {
    periods,
    fraudRates,
    detectionRates,
    auditRates,
    reputationHistory,
    providerProfits,
    clientLosses,
    cumulativeWelfare,
    totalJobs,
    totalFrauds,
    totalDetected,
    finalFraudRate: totalFrauds / totalJobs,
    finalDetectionRate: totalFrauds > 0 ? totalDetected / totalFrauds : eq.v_star,
    socialWelfare: cumProviderProfit - cumClientLoss,
  };
}

/**
 * Parameter sensitivity analysis
 */
export function sensitivityAnalysis(
  baseParams: ProtocolParams,
  paramName: keyof ProtocolParams,
  values: number[]
): { values: number[]; q_star: number[]; v_star: number[]; Delta: number[]; S_P_min: number[] } {
  const results = {
    values,
    q_star: [] as number[],
    v_star: [] as number[],
    Delta: [] as number[],
    S_P_min: [] as number[],
  };

  for (const value of values) {
    const params = { ...baseParams, [paramName]: value };
    const eq = computeEquilibrium(params);

    results.q_star.push(eq.q_star);
    results.v_star.push(eq.v_star);
    results.Delta.push(eq.Delta);
    results.S_P_min.push(eq.S_P_min);
  }

  return results;
}

/**
 * Attack scenario types
 */
export type AttackType =
  | 'reputation_farming'
  | 'no_stake_floor'
  | 'sybil'
  | 'collusion'
  | 'censorship';

export interface AttackResult {
  name: string;
  description: string;
  baselineFraudRate: number;
  attackFraudRate: number;
  fraudRateChange: number;
  welfareLoss: number;
  attackerProfit: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

/**
 * Simulate attack scenarios
 */
export function simulateAttack(
  params: ProtocolParams,
  attackType: AttackType,
  nPeriods: number = 100
): AttackResult {
  const baselineResult = runSimulation(params, nPeriods, 20, 0.6, 42);

  let attackParams = { ...params };
  let attackHonestFraction = 0.6;
  let name = '';
  let description = '';

  switch (attackType) {
    case 'reputation_farming':
      name = 'Reputation Farming';
      description = 'Attacker builds reputation with honest behavior, then exploits reduced auditing';
      attackHonestFraction = 0.4; // More adversarial
      break;
    case 'no_stake_floor':
      name = 'No Stake Floor';
      description = 'Minimal stake when floor not enforced, reducing slashing penalty';
      attackParams.S_P = 5; // Very low stake
      break;
    case 'sybil':
      name = 'Sybil Attack';
      description = 'Multiple identities spread risk and dilute reputation penalties';
      attackHonestFraction = 0.3;
      break;
    case 'collusion':
      name = 'Collusion';
      description = 'Provider-client coordination to avoid auditing';
      attackHonestFraction = 0.4;
      attackParams.C_safe = params.C_safe * 2; // Effective higher verification cost
      break;
    case 'censorship':
      name = 'Censorship Attack';
      description = 'Blocking dispute transactions reduces enforcement probability';
      attackParams.p_w = params.p_w * 0.7;
      break;
  }

  const attackResult = runSimulation(attackParams, nPeriods, 20, attackHonestFraction, 43);

  const fraudRateChange = attackResult.finalFraudRate - baselineResult.finalFraudRate;
  const welfareLoss = baselineResult.socialWelfare - attackResult.socialWelfare;

  let severity: 'low' | 'medium' | 'high' | 'critical' = 'low';
  if (welfareLoss > 5000) severity = 'critical';
  else if (welfareLoss > 2000) severity = 'high';
  else if (welfareLoss > 500) severity = 'medium';

  return {
    name,
    description,
    baselineFraudRate: baselineResult.finalFraudRate,
    attackFraudRate: attackResult.finalFraudRate,
    fraudRateChange,
    welfareLoss,
    attackerProfit: welfareLoss * 0.4, // Approximate
    severity,
  };
}
