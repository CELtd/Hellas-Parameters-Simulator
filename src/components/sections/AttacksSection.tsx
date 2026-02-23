import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Swords, AlertOctagon, Users, Lock, Ban, Radio, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { AttackChart, SeverityBadge } from '../charts/AttackChart';
import { ProtocolParams, simulateAttack, AttackResult, AttackType } from '../../lib/simulation';
import { formatPercent, formatCurrency, formatChange } from '../../lib/utils';

interface AttacksSectionProps {
  params: ProtocolParams;
}

const attackTypes: { type: AttackType; icon: typeof Swords; color: string }[] = [
  { type: 'reputation_farming', icon: Users, color: 'text-violet-400' },
  { type: 'no_stake_floor', icon: AlertOctagon, color: 'text-red-400' },
  { type: 'sybil', icon: Users, color: 'text-orange-400' },
  { type: 'collusion', icon: Lock, color: 'text-amber-400' },
  { type: 'censorship', icon: Radio, color: 'text-rose-400' },
];

export function AttacksSection({ params }: AttacksSectionProps) {
  const attacks = useMemo(() => {
    return attackTypes.map(({ type }) => simulateAttack(params, type, 100));
  }, [params]);

  // Sort by welfare loss
  const sortedAttacks = [...attacks].sort((a, b) => b.welfareLoss - a.welfareLoss);

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Attack Analysis</h2>
          <p className="mt-1 text-slate-400">
            Adversarial scenarios and their impact
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2">
          <Swords className="h-5 w-5 text-red-400" />
          <span className="text-sm text-slate-300">
            {attacks.filter((a) => a.severity === 'critical' || a.severity === 'high').length} high-risk attacks
          </span>
        </div>
      </div>

      {/* Overview Chart */}
      <Card hover>
        <CardHeader
          title="Welfare Loss by Attack"
          subtitle="Comparative impact analysis"
          icon={<AlertOctagon className="h-5 w-5" />}
        />
        <CardContent>
          <AttackChart attacks={sortedAttacks} />
          <div className="mt-4 flex flex-wrap gap-3">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <div className="h-3 w-3 rounded-full bg-emerald-500" /> Low
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <div className="h-3 w-3 rounded-full bg-amber-500" /> Medium
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <div className="h-3 w-3 rounded-full bg-orange-500" /> High
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <div className="h-3 w-3 rounded-full bg-red-500" /> Critical
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Attack Cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sortedAttacks.map((attack, i) => (
          <AttackCard key={attack.name} attack={attack} index={i} />
        ))}
      </div>

      {/* Key Vulnerabilities */}
      <Card>
        <CardHeader
          title="Key Vulnerabilities & Mitigations"
          subtitle="Protocol design recommendations"
          icon={<Lock className="h-5 w-5" />}
        />
        <CardContent>
          <div className="space-y-4">
            <VulnerabilityItem
              title="No Stake Floor"
              description="Without minimum stake, slashing penalties become insignificant"
              mitigation="Enforce S_P ≥ S_P^min computed from Proposition 2"
              severity="critical"
            />
            <VulnerabilityItem
              title="Reputation Farming"
              description="Low-stake honest jobs build trust for later exploitation"
              mitigation="Stake-weight reputation gains: ρ_gain = g_H × min(1, S_P/S_P_target)"
              severity="high"
            />
            <VulnerabilityItem
              title="Censorship"
              description="Blocking disputes reduces enforcement probability p_w"
              mitigation="Use censorship-resistant dispute mechanisms and fallback paths"
              severity="medium"
            />
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

interface AttackCardProps {
  attack: AttackResult;
  index: number;
}

function AttackCard({ attack, index }: AttackCardProps) {
  const severityColors = {
    low: 'border-emerald-500/30 hover:border-emerald-500/50',
    medium: 'border-amber-500/30 hover:border-amber-500/50',
    high: 'border-orange-500/30 hover:border-orange-500/50',
    critical: 'border-red-500/30 hover:border-red-500/50',
  };

  const bgColors = {
    low: 'from-emerald-500/5',
    medium: 'from-amber-500/5',
    high: 'from-orange-500/5',
    critical: 'from-red-500/5',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`rounded-2xl border bg-gradient-to-br ${bgColors[attack.severity]} to-slate-900/50 p-5 transition-all ${severityColors[attack.severity]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-slate-100">{attack.name}</h3>
          <p className="mt-1 text-sm text-slate-400 line-clamp-2">{attack.description}</p>
        </div>
        <SeverityBadge severity={attack.severity} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <MetricItem
          label="Fraud Change"
          value={formatChange(attack.fraudRateChange)}
          isNegative={attack.fraudRateChange > 0}
        />
        <MetricItem
          label="Welfare Loss"
          value={formatCurrency(attack.welfareLoss)}
          isNegative={attack.welfareLoss > 0}
        />
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-slate-700/50 pt-4">
        <div className="text-sm text-slate-500">
          Baseline: {formatPercent(attack.baselineFraudRate)}
        </div>
        <div className="text-sm">
          <span className="text-slate-400">Attack: </span>
          <span className="font-medium text-slate-200">{formatPercent(attack.attackFraudRate)}</span>
        </div>
      </div>
    </motion.div>
  );
}

function MetricItem({ label, value, isNegative }: { label: string; value: string; isNegative: boolean }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 font-mono text-lg font-semibold ${isNegative ? 'text-red-400' : 'text-emerald-400'}`}>
        {value}
      </div>
    </div>
  );
}

interface VulnerabilityItemProps {
  title: string;
  description: string;
  mitigation: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

function VulnerabilityItem({ title, description, mitigation, severity }: VulnerabilityItemProps) {
  const colors = {
    low: 'border-emerald-500/30 bg-emerald-500/5',
    medium: 'border-amber-500/30 bg-amber-500/5',
    high: 'border-orange-500/30 bg-orange-500/5',
    critical: 'border-red-500/30 bg-red-500/5',
  };

  return (
    <div className={`rounded-xl border p-4 ${colors[severity]}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-slate-200">{title}</h4>
            <SeverityBadge severity={severity} />
          </div>
          <p className="mt-1 text-sm text-slate-400">{description}</p>
        </div>
      </div>
      <div className="mt-3 flex items-start gap-2 rounded-lg bg-slate-800/50 p-3">
        <ChevronRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-400" />
        <p className="text-sm text-emerald-300">{mitigation}</p>
      </div>
    </div>
  );
}
