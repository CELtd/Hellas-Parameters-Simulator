import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Play,
  Swords,
  Settings,
  ChevronDown,
  Github,
  BookOpen,
  Zap,
  Shield,
  TrendingUp,
  HelpCircle,
} from 'lucide-react';
import { Card, CardContent } from './components/ui/Card';
import { Slider } from './components/ui/Slider';
import { Tooltip } from './components/ui/Tooltip';
import { EquilibriumSection } from './components/sections/EquilibriumSection';
import { SimulationSection } from './components/sections/SimulationSection';
import { AttacksSection } from './components/sections/AttacksSection';
import { DEFAULT_PARAMS, ProtocolParams } from './lib/simulation';
import { formatCurrency, formatPercent } from './lib/utils';

type Tab = 'equilibrium' | 'simulation' | 'attacks';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('equilibrium');
  const [params, setParams] = useState<ProtocolParams>(DEFAULT_PARAMS);
  const [showParams, setShowParams] = useState(true);

  const updateParam = (key: keyof ProtocolParams, value: number) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const tabs: { id: Tab; label: string; icon: typeof Scale }[] = [
    { id: 'equilibrium', label: 'Equilibrium', icon: Scale },
    { id: 'simulation', label: 'Simulation', icon: Play },
    { id: 'attacks', label: 'Attacks', icon: Swords },
  ];

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Header */}
      <header className="relative overflow-hidden border-b border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-500/10 via-transparent to-transparent" />
        <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-primary-500/10 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 h-96 w-96 rounded-full bg-violet-500/10 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-primary-500/10 px-4 py-1.5 text-sm text-primary-400 ring-1 ring-primary-500/20">
              <Zap className="h-4 w-4" />
              Interactive Economic Simulator
            </div>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-100 sm:text-5xl lg:text-6xl">
              <span className="gradient-text">Hellas</span> Fraud Game
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-400">
              Analyze incentive compatibility for off-chain computation.
              Explore equilibrium dynamics, run simulations, and understand attack vectors.
            </p>

            {/* Quick Stats */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-6">
              <QuickStat icon={<Shield className="h-5 w-5" />} label="Stake" value={formatCurrency(params.S_P)} />
              <QuickStat icon={<TrendingUp className="h-5 w-5" />} label="Payment" value={formatCurrency(params.P_set)} />
              <QuickStat icon={<Scale className="h-5 w-5" />} label="Enforcement" value={formatPercent(params.p_w)} />
            </div>
          </motion.div>
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-8 lg:flex-row">
          {/* Sidebar - Parameters */}
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:w-80 lg:flex-shrink-0"
          >
            <div className="sticky top-8 space-y-4">
              {/* Parameters Card */}
              <Card>
                <button
                  onClick={() => setShowParams(!showParams)}
                  className="flex w-full items-center justify-between border-b border-slate-800 px-5 py-4 text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-primary-500/10 p-2 text-primary-400">
                      <Settings className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-100">Parameters</h3>
                      <p className="text-xs text-slate-500">Protocol configuration</p>
                    </div>
                  </div>
                  <ChevronDown
                    className={`h-5 w-5 text-slate-400 transition-transform ${showParams ? 'rotate-180' : ''}`}
                  />
                </button>

                <AnimatePresence>
                  {showParams && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <CardContent className="space-y-6">
                        <ParamGroup title="Economic Parameters">
                          <Slider
                            label="Provider Stake (S_P)"
                            value={params.S_P}
                            onChange={(v) => updateParam('S_P', v)}
                            min={10}
                            max={500}
                            step={10}
                            unit="$"
                            description="Collateral locked by provider"
                          />
                          <Slider
                            label="Payment (P_set)"
                            value={params.P_set}
                            onChange={(v) => updateParam('P_set', v)}
                            min={5}
                            max={200}
                            step={5}
                            unit="$"
                            description="Settlement payment to provider"
                          />
                          <Slider
                            label="Client Loss (L)"
                            value={params.L}
                            onChange={(v) => updateParam('L', v)}
                            min={10}
                            max={200}
                            step={5}
                            unit="$"
                            description="Loss from incorrect result"
                          />
                        </ParamGroup>

                        <ParamGroup title="Costs">
                          <Slider
                            label="Honest Cost (c_H)"
                            value={params.c_H}
                            onChange={(v) => updateParam('c_H', v)}
                            min={1}
                            max={20}
                            step={0.5}
                            unit="$"
                            description="Cost of honest execution"
                          />
                          <Slider
                            label="Cheat Cost (c_F)"
                            value={params.c_F}
                            onChange={(v) => updateParam('c_F', v)}
                            min={0}
                            max={5}
                            step={0.1}
                            unit="$"
                            description="Cost of cheating"
                          />
                          <Slider
                            label="Verification (C_safe)"
                            value={params.C_safe}
                            onChange={(v) => updateParam('C_safe', v)}
                            min={1}
                            max={50}
                            step={1}
                            unit="$"
                            description="Safe fallback cost"
                          />
                        </ParamGroup>

                        <ParamGroup title="Protocol Design">
                          <Slider
                            label="Enforcement (p_w)"
                            value={params.p_w}
                            onChange={(v) => updateParam('p_w', v)}
                            min={0.5}
                            max={1}
                            step={0.01}
                            formatValue={(v) => `${(v * 100).toFixed(0)}%`}
                            description="Dispute success probability"
                          />
                          <Slider
                            label="Slash Reward (β)"
                            value={params.beta}
                            onChange={(v) => updateParam('beta', v)}
                            min={0.1}
                            max={1}
                            step={0.05}
                            formatValue={(v) => `${(v * 100).toFixed(0)}%`}
                            description="Fraction to challenger"
                          />
                          <Slider
                            label="Payment Route (λ)"
                            value={params.lambda}
                            onChange={(v) => updateParam('lambda', v)}
                            min={0}
                            max={1}
                            step={0.1}
                            formatValue={(v) => `${(v * 100).toFixed(0)}%`}
                            description="Payment routed on success"
                          />
                        </ParamGroup>

                        <button
                          onClick={() => setParams(DEFAULT_PARAMS)}
                          className="w-full rounded-xl border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
                        >
                          Reset to Defaults
                        </button>
                      </CardContent>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>

              {/* Resources */}
              <Card className="p-4">
                <div className="space-y-3">
                  <a
                    href="#"
                    className="flex items-center gap-3 rounded-lg p-2 text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
                  >
                    <BookOpen className="h-4 w-4" />
                    Read the Paper
                  </a>
                  <a
                    href="#"
                    className="flex items-center gap-3 rounded-lg p-2 text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
                  >
                    <Github className="h-4 w-4" />
                    View Source Code
                  </a>
                  <a
                    href="#"
                    className="flex items-center gap-3 rounded-lg p-2 text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
                  >
                    <HelpCircle className="h-4 w-4" />
                    Documentation
                  </a>
                </div>
              </Card>
            </div>
          </motion.aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            {/* Tabs */}
            <div className="mb-8 flex gap-2 rounded-xl bg-slate-900/50 p-1.5">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-slate-800 text-slate-100 shadow-lg'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 rounded-lg bg-gradient-to-r from-primary-500/10 to-violet-500/10 ring-1 ring-primary-500/20"
                      transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                {activeTab === 'equilibrium' && <EquilibriumSection params={params} />}
                {activeTab === 'simulation' && <SimulationSection params={params} />}
                {activeTab === 'attacks' && <AttacksSection params={params} />}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-800 bg-slate-900/50">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="text-sm text-slate-500">
              Based on "Fraud Game Analysis for Hellas Protocol" (CryptoEconLab, 2026)
            </div>
            <div className="flex items-center gap-4 text-sm text-slate-500">
              <span>Built with React + Recharts</span>
              <span className="text-slate-700">|</span>
              <a href="#" className="text-primary-400 hover:text-primary-300">
                View Simulation Report
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function QuickStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 rounded-full bg-slate-800/50 px-4 py-2 ring-1 ring-slate-700/50">
      <span className="text-primary-400">{icon}</span>
      <span className="text-sm text-slate-400">{label}:</span>
      <span className="font-mono font-medium text-slate-200">{value}</span>
    </div>
  );
}

function ParamGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</h4>
      <div className="space-y-5">{children}</div>
    </div>
  );
}

export default App;
