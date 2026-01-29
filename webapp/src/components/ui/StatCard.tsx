import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'default' | 'primary' | 'success' | 'danger' | 'warning';
  tooltip?: string;
  delay?: number;
}

export function StatCard({
  label,
  value,
  subValue,
  icon,
  trend,
  trendValue,
  color = 'default',
  delay = 0,
}: StatCardProps) {
  const colorStyles = {
    default: 'from-slate-800/80 to-slate-900/80 border-slate-700/50',
    primary: 'from-primary-900/30 to-slate-900/80 border-primary-500/20',
    success: 'from-emerald-900/30 to-slate-900/80 border-emerald-500/20',
    danger: 'from-red-900/30 to-slate-900/80 border-red-500/20',
    warning: 'from-amber-900/30 to-slate-900/80 border-amber-500/20',
  };

  const valueColors = {
    default: 'text-slate-100',
    primary: 'text-primary-400',
    success: 'text-emerald-400',
    danger: 'text-red-400',
    warning: 'text-amber-400',
  };

  const iconColors = {
    default: 'bg-slate-700/50 text-slate-300',
    primary: 'bg-primary-500/20 text-primary-400',
    success: 'bg-emerald-500/20 text-emerald-400',
    danger: 'bg-red-500/20 text-red-400',
    warning: 'bg-amber-500/20 text-amber-400',
  };

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, delay: delay * 0.1 }}
      className={cn(
        'relative overflow-hidden rounded-2xl border bg-gradient-to-br p-5',
        colorStyles[color]
      )}
    >
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/5 blur-2xl" />

      <div className="relative">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-400">{label}</p>
            <div className="mt-2 flex items-baseline gap-2">
              <span className={cn('text-3xl font-bold tracking-tight', valueColors[color])}>
                {value}
              </span>
              {subValue && (
                <span className="text-sm text-slate-500">{subValue}</span>
              )}
            </div>
            {trend && trendValue && (
              <div className={cn('mt-2 flex items-center gap-1 text-sm', trendColor)}>
                <TrendIcon className="h-4 w-4" />
                <span>{trendValue}</span>
              </div>
            )}
          </div>
          {icon && (
            <div className={cn('rounded-xl p-3', iconColors[color])}>
              {icon}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
