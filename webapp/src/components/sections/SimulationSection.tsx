import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Play, RotateCcw, Activity, Users, Coins, Trophy } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { StatCard } from '../ui/StatCard';
import { SimulationChart } from '../charts/SimulationChart';
import { ProtocolParams, runSimulation, SimulationResult, computeEquilibrium } from '../../lib/simulation';
import { formatPercent, formatCurrency, formatNumber } from '../../lib/utils';

interface SimulationSectionProps {
  params: ProtocolParams;
}

export function SimulationSection({ params }: SimulationSectionProps) {
  const [nPeriods, setNPeriods] = useState(200);
  const [honestFraction, setHonestFraction] = useState(0.6);
  const [isRunning, setIsRunning] = useState(false);
  const [seed, setSeed] = useState(42);
  const [result, setResult] = useState<SimulationResult | null>(null);

  const equilibrium = useMemo(() => computeEquilibrium(params), [params]);

  const runSim = () => {
    setIsRunning(true);
    // Small delay for animation
    setTimeout(() => {
      const simResult = runSimulation(params, nPeriods, 20, honestFraction, seed);
      setResult(simResult);
      setIsRunning(false);
    }, 100);
  };

  const resetSim = () => {
    setResult(null);
    setSeed(Math.floor(Math.random() * 10000));
  };

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Run Simulation</h2>
          <p className="mt-1 text-slate-400">
            Agent-based model with heterogeneous populations
          </p>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Periods */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-200">
                Simulation Periods
              </label>
              <input
                type="range"
                min={50}
                max={500}
                step={50}
                value={nPeriods}
                onChange={(e) => setNPeriods(Number(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>50</span>
                <span className="font-mono text-primary-400">{nPeriods} periods</span>
                <span>500</span>
              </div>
            </div>

            {/* Honest Fraction */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-200">
                Honest Provider Fraction
              </label>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={honestFraction * 100}
                onChange={(e) => setHonestFraction(Number(e.target.value) / 100)}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>0%</span>
                <span className="font-mono text-emerald-400">{formatPercent(honestFraction)}</span>
                <span>100%</span>
              </div>
            </div>

            {/* Run Button */}
            <div className="flex items-end gap-3">
              <button
                onClick={runSim}
                disabled={isRunning}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-primary-500 px-6 py-3 font-medium text-white transition-all hover:bg-primary-600 disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    Run Simulation
                  </>
                )}
              </button>
              <button
                onClick={resetSim}
                className="rounded-xl border border-slate-700 bg-slate-800 p-3 text-slate-400 transition-all hover:border-slate-600 hover:text-slate-200"
              >
                <RotateCcw className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Theoretical Reference */}
          <div className="rounded-xl bg-slate-800/50 p-4">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Activity className="h-4 w-4" />
              <span>Theoretical equilibrium: </span>
              <span className="font-mono text-red-400">q* = {formatPercent(equilibrium.q_star)}</span>
              <span className="text-slate-600">|</span>
              <span className="font-mono text-emerald-400">v* = {formatPercent(equilibrium.v_star)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total Jobs"
              value={result.totalJobs.toLocaleString()}
              icon={<Activity className="h-5 w-5" />}
              color="primary"
              delay={0}
            />
            <StatCard
              label="Fraud Rate"
              value={formatPercent(result.finalFraudRate)}
              subValue={`theory: ${formatPercent(equilibrium.q_star)}`}
              icon={<Users className="h-5 w-5" />}
              color={result.finalFraudRate > equilibrium.q_star * 1.5 ? 'danger' : 'success'}
              trend={result.finalFraudRate < equilibrium.q_star ? 'down' : 'up'}
              trendValue={`${((result.finalFraudRate - equilibrium.q_star) / equilibrium.q_star * 100).toFixed(0)}% vs theory`}
              delay={1}
            />
            <StatCard
              label="Detection Rate"
              value={formatPercent(result.finalDetectionRate)}
              icon={<Trophy className="h-5 w-5" />}
              color={result.finalDetectionRate > 0.5 ? 'success' : 'warning'}
              delay={2}
            />
            <StatCard
              label="Social Welfare"
              value={formatCurrency(result.socialWelfare)}
              icon={<Coins className="h-5 w-5" />}
              color={result.socialWelfare > 0 ? 'success' : 'danger'}
              delay={3}
            />
          </div>

          {/* Charts */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card hover>
              <CardHeader
                title="Fraud & Detection Over Time"
                subtitle="Per-period rates"
              />
              <CardContent>
                <SimulationChart result={result} metric="fraudRate" />
              </CardContent>
            </Card>

            <Card hover>
              <CardHeader
                title="Welfare Accumulation"
                subtitle="Cumulative profits and losses"
              />
              <CardContent>
                <SimulationChart result={result} metric="welfare" />
              </CardContent>
            </Card>
          </div>

          {/* Summary */}
          <Card>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <SummaryItem
                  label="Frauds Detected"
                  value={`${result.totalDetected} / ${result.totalFrauds}`}
                  subValue={`${formatPercent(result.totalDetected / Math.max(1, result.totalFrauds))} detection`}
                />
                <SummaryItem
                  label="Avg Reputation"
                  value={formatNumber(result.reputationHistory[result.reputationHistory.length - 1], 1)}
                  subValue="final period"
                />
                <SummaryItem
                  label="Provider Profit"
                  value={formatCurrency(result.providerProfits[result.providerProfits.length - 1])}
                  subValue="cumulative"
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {!result && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-900/30 py-16">
          <Play className="h-12 w-12 text-slate-600" />
          <p className="mt-4 text-lg text-slate-500">Run a simulation to see results</p>
          <p className="mt-1 text-sm text-slate-600">
            Configure parameters and click "Run Simulation"
          </p>
        </div>
      )}
    </section>
  );
}

function SummaryItem({ label, value, subValue }: { label: string; value: string; subValue: string }) {
  return (
    <div className="text-center">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-bold text-slate-100">{value}</div>
      <div className="text-xs text-slate-500">{subValue}</div>
    </div>
  );
}
