import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { SimulationResult } from '../../lib/simulation';

interface SimulationChartProps {
  result: SimulationResult;
  metric: 'fraudRate' | 'welfare' | 'reputation';
}

export function SimulationChart({ result, metric }: SimulationChartProps) {
  const data = result.periods.map((period, i) => ({
    period,
    fraudRate: result.fraudRates[i] * 100,
    detectionRate: result.detectionRates[i] * 100,
    reputation: result.reputationHistory[i],
    welfare: result.cumulativeWelfare[i],
    providerProfit: result.providerProfits[i],
    clientLoss: -result.clientLosses[i],
  }));

  const configs = {
    fraudRate: {
      keys: ['fraudRate', 'detectionRate'],
      colors: ['#ef4444', '#22c55e'],
      labels: ['Fraud Rate (%)', 'Detection Rate (%)'],
      yFormat: (v: number) => `${v.toFixed(0)}%`,
    },
    welfare: {
      keys: ['providerProfit', 'clientLoss', 'welfare'],
      colors: ['#0ea5e9', '#f59e0b', '#8b5cf6'],
      labels: ['Provider Profit', 'Client Cost', 'Net Welfare'],
      yFormat: (v: number) => `$${v.toFixed(0)}`,
    },
    reputation: {
      keys: ['reputation'],
      colors: ['#8b5cf6'],
      labels: ['Avg Reputation'],
      yFormat: (v: number) => v.toFixed(0),
    },
  };

  const config = configs[metric];

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            {config.keys.map((key, i) => (
              <linearGradient key={key} id={`color${key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={config.colors[i]} stopOpacity={0.3} />
                <stop offset="95%" stopColor={config.colors[i]} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
          <XAxis
            dataKey="period"
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => `${v}`}
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickFormatter={config.yFormat}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(51, 65, 85, 0.5)',
              borderRadius: '12px',
              padding: '12px',
            }}
            labelFormatter={(v) => `Period ${v}`}
          />
          <Legend
            wrapperStyle={{ paddingTop: '10px' }}
            formatter={(value) => {
              const idx = config.keys.indexOf(value);
              return <span className="text-sm text-slate-300">{config.labels[idx]}</span>;
            }}
          />
          {config.keys.map((key, i) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={config.colors[i]}
              fill={`url(#color${key})`}
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
