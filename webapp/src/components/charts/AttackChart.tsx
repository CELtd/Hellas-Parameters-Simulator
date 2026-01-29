import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { AttackResult } from '../../lib/simulation';

interface AttackChartProps {
  attacks: AttackResult[];
}

export function AttackChart({ attacks }: AttackChartProps) {
  const data = attacks.map((attack) => ({
    name: attack.name,
    fraudChange: attack.fraudRateChange * 100,
    welfareLoss: attack.welfareLoss,
    severity: attack.severity,
  }));

  const severityColors: Record<string, string> = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
  };

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 100, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" horizontal={true} vertical={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => `$${v}`}
            domain={[0, 'auto']}
          />
          <YAxis
            dataKey="name"
            type="category"
            stroke="#64748b"
            fontSize={12}
            width={90}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(51, 65, 85, 0.5)',
              borderRadius: '12px',
              padding: '12px',
            }}
            formatter={(value, name) => {
              const numValue = Number(value) || 0;
              return [
                name === 'welfareLoss' ? `$${numValue.toFixed(0)}` : `${numValue.toFixed(2)}%`,
                name === 'welfareLoss' ? 'Welfare Loss' : 'Fraud Rate Change',
              ];
            }}
          />
          <Bar dataKey="welfareLoss" radius={[0, 8, 8, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={severityColors[entry.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface SeverityBadgeProps {
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const styles: Record<string, string> = {
    low: 'bg-emerald-500/20 text-emerald-400',
    medium: 'bg-amber-500/20 text-amber-400',
    high: 'bg-orange-500/20 text-orange-400',
    critical: 'bg-red-500/20 text-red-400',
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[severity]}`}>
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
}
