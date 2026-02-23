import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts';
import { sensitivityAnalysis, ProtocolParams } from '../../lib/simulation';
import { useMemo } from 'react';

interface EquilibriumChartProps {
  params: ProtocolParams;
  parameter: 'S_P' | 'p_w' | 'C_safe' | 'beta' | 'L';
}

const parameterConfig: Record<string, { min: number; max: number; label: string; unit: string }> = {
  S_P: { min: 10, max: 300, label: 'Provider Stake', unit: '$' },
  p_w: { min: 0.5, max: 1, label: 'Enforcement Probability', unit: '' },
  C_safe: { min: 1, max: 30, label: 'Verification Cost', unit: '$' },
  beta: { min: 0.1, max: 1, label: 'Slash Reward (β)', unit: '' },
  L: { min: 10, max: 150, label: 'Client Loss', unit: '$' },
};

export function EquilibriumChart({ params, parameter }: EquilibriumChartProps) {
  const config = parameterConfig[parameter];

  const data = useMemo(() => {
    const steps = 30;
    const values = Array.from(
      { length: steps },
      (_, i) => config.min + (i / (steps - 1)) * (config.max - config.min)
    );

    const results = sensitivityAnalysis(params, parameter, values);

    return values.map((val, i) => ({
      param: val,
      q_star: results.q_star[i] * 100,
      v_star: results.v_star[i] * 100,
      Delta: results.Delta[i],
    }));
  }, [params, parameter, config]);

  const currentValue = params[parameter];

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorQStar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorVStar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
          <XAxis
            dataKey="param"
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => `${config.unit}${v.toFixed(parameter === 'p_w' ? 2 : 0)}`}
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => `${v.toFixed(1)}%`}
            domain={[0, 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(51, 65, 85, 0.5)',
              borderRadius: '12px',
              padding: '12px',
            }}
            labelFormatter={(v) => `${config.label}: ${config.unit}${Number(v).toFixed(2)}`}
          />
          <Area
            type="monotone"
            dataKey="q_star"
            stroke="#ef4444"
            fill="url(#colorQStar)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="v_star"
            stroke="#22c55e"
            fill="url(#colorVStar)"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="q_star"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
            name="q_star"
          />
          <Line
            type="monotone"
            dataKey="v_star"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
            name="v_star"
          />
          <ReferenceLine
            x={currentValue}
            stroke="#8b5cf6"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: 'Current',
              position: 'top',
              fill: '#8b5cf6',
              fontSize: 12,
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
