import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Scale,
  Eye,
  AlertTriangle,
  TrendingUp,
  Shield,
  HelpCircle,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { StatCard } from '../ui/StatCard';
import { Tooltip } from '../ui/Tooltip';
import { EquilibriumChart } from '../charts/EquilibriumChart';
import { ProtocolParams, computeEquilibrium, EquilibriumValues } from '../../lib/simulation';
import { formatPercent, formatCurrency } from '../../lib/utils';

interface EquilibriumSectionProps {
  params: ProtocolParams;
}

export function EquilibriumSection({ params }: EquilibriumSectionProps) {
  const equilibrium = useMemo(() => computeEquilibrium(params), [params]);

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Equilibrium Analysis</h2>
          <p className="mt-1 text-slate-400">
            Mixed strategy Nash equilibrium predictions
          </p>
        </div>
        <Tooltip content="Based on Theorem 2 from the Hellas Protocol paper">
          <button className="rounded-lg bg-slate-800 p-2 text-slate-400 hover:text-slate-200 transition-colors">
            <HelpCircle className="h-5 w-5" />
          </button>
        </Tooltip>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Cheating Rate (q*)"
          value={formatPercent(equilibrium.q_star)}
          subValue="equilibrium"
          icon={<AlertTriangle className="h-5 w-5" />}
          color={equilibrium.q_star > 0.1 ? 'danger' : equilibrium.q_star > 0.05 ? 'warning' : 'success'}
          delay={0}
        />
        <StatCard
          label="Audit Rate (v*)"
          value={formatPercent(equilibrium.v_star)}
          subValue="equilibrium"
          icon={<Eye className="h-5 w-5" />}
          color="primary"
          delay={1}
        />
        <StatCard
          label="Dispute Surplus (Δ)"
          value={formatCurrency(equilibrium.Delta)}
          subValue={equilibrium.Delta > 0 ? 'profitable' : 'unprofitable'}
          icon={<TrendingUp className="h-5 w-5" />}
          color={equilibrium.Delta > 0 ? 'success' : 'danger'}
          delay={2}
        />
        <StatCard
          label="Min Viable Stake"
          value={formatCurrency(equilibrium.S_P_min)}
          subValue={equilibrium.isEnforcementViable ? 'enforced' : 'at risk'}
          icon={<Shield className="h-5 w-5" />}
          color={equilibrium.isEnforcementViable ? 'success' : 'danger'}
          delay={3}
        />
      </div>

      {/* Equations */}
      <Card hover>
        <CardHeader
          title="Equilibrium Equations"
          subtitle="From Theorem 2 (Mixed Strategy Equilibrium)"
          icon={<Scale className="h-5 w-5" />}
        />
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <EquationDisplay
              label="Audit Probability"
              equation="v* = (c_H - c_F) / (P_set + S_P)"
              result={formatPercent(equilibrium.v_star)}
              color="emerald"
            />
            <EquationDisplay
              label="Cheating Probability"
              equation="q* = C_safe / (L + Δ)"
              result={formatPercent(equilibrium.q_star)}
              color="red"
            />
            <EquationDisplay
              label="Dispute Surplus"
              equation="Δ = p_w(βS_P + λP_set) - C_disp - (1-p_w)B_C"
              result={formatCurrency(equilibrium.Delta)}
              color="primary"
            />
            <EquationDisplay
              label="Min Stake"
              equation="S_P^min = max{0, (C_disp + (1-p_w)B_C - p_w·λ·P_set) / (p_w·β)}"
              result={formatCurrency(equilibrium.S_P_min)}
              color="violet"
            />
          </div>
        </CardContent>
      </Card>

      {/* Sensitivity Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card hover>
          <CardHeader
            title="Stake Sensitivity"
            subtitle="Effect of provider stake on equilibrium"
          />
          <CardContent>
            <EquilibriumChart params={params} parameter="S_P" />
            <div className="mt-4 rounded-lg bg-slate-800/50 p-3 text-sm text-slate-400">
              <strong className="text-slate-200">Insight:</strong> Higher stake
              reduces both cheating (q*) and required auditing (v*) by increasing
              the penalty for detected fraud.
            </div>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader
            title="Verification Cost Sensitivity"
            subtitle="Effect of C_safe on equilibrium"
          />
          <CardContent>
            <EquilibriumChart params={params} parameter="C_safe" />
            <div className="mt-4 rounded-lg bg-slate-800/50 p-3 text-sm text-slate-400">
              <strong className="text-slate-200">Insight:</strong> Reducing C_safe
              is the most effective lever—cheating rate is directly proportional
              to verification cost.
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status Indicators */}
      <div className="grid gap-4 md:grid-cols-2">
        <StatusCard
          title="Enforcement Viability"
          description={`Current stake (${formatCurrency(params.S_P)}) ${equilibrium.isEnforcementViable ? '≥' : '<'} minimum (${formatCurrency(equilibrium.S_P_min)})`}
          isHealthy={equilibrium.isEnforcementViable}
          healthyText="Disputes are profitable for challengers"
          unhealthyText="Disputes are NOT profitable—impunity region"
        />
        <StatusCard
          title="Incentive Compatibility"
          description={`Audit rate v* (${formatPercent(equilibrium.v_star)}) ${equilibrium.isICsatisfied ? '≥' : '<'} threshold θ (${formatPercent(equilibrium.theta)})`}
          isHealthy={equilibrium.isICsatisfied}
          healthyText="Provider prefers honest execution"
          unhealthyText="Cheating may be preferred"
        />
      </div>
    </section>
  );
}

interface EquationDisplayProps {
  label: string;
  equation: string;
  result: string;
  color: 'emerald' | 'red' | 'primary' | 'violet';
}

function EquationDisplay({ label, equation, result, color }: EquationDisplayProps) {
  const colorStyles = {
    emerald: 'text-emerald-400 border-emerald-500/20',
    red: 'text-red-400 border-red-500/20',
    primary: 'text-primary-400 border-primary-500/20',
    violet: 'text-violet-400 border-violet-500/20',
  };

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
      <div className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div className="font-mono text-sm text-slate-300">{equation}</div>
      <div className={`mt-2 text-2xl font-bold ${colorStyles[color].split(' ')[0]}`}>
        = {result}
      </div>
    </div>
  );
}

interface StatusCardProps {
  title: string;
  description: string;
  isHealthy: boolean;
  healthyText: string;
  unhealthyText: string;
}

function StatusCard({ title, description, isHealthy, healthyText, unhealthyText }: StatusCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`rounded-2xl border p-5 ${
        isHealthy
          ? 'border-emerald-500/30 bg-emerald-500/10'
          : 'border-red-500/30 bg-red-500/10'
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`rounded-full p-2 ${
            isHealthy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
          }`}
        >
          {isHealthy ? <Shield className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
        </div>
        <div>
          <h4 className={`font-semibold ${isHealthy ? 'text-emerald-400' : 'text-red-400'}`}>
            {title}: {isHealthy ? '✓ Satisfied' : '✗ Not Satisfied'}
          </h4>
          <p className="mt-1 text-sm text-slate-400">{description}</p>
          <p className={`mt-2 text-sm ${isHealthy ? 'text-emerald-300' : 'text-red-300'}`}>
            {isHealthy ? healthyText : unhealthyText}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
