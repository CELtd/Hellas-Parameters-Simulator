import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'none' | 'primary' | 'success' | 'danger' | 'accent';
}

export function Card({ children, className, hover = false, glow = 'none' }: CardProps) {
  const glowStyles = {
    none: '',
    primary: 'hover:shadow-primary-500/20 hover:border-primary-500/30',
    success: 'hover:shadow-emerald-500/20 hover:border-emerald-500/30',
    danger: 'hover:shadow-red-500/20 hover:border-red-500/30',
    accent: 'hover:shadow-violet-500/20 hover:border-violet-500/30',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm',
        hover && 'transition-all duration-300 hover:border-slate-700',
        glow !== 'none' && `hover:shadow-lg ${glowStyles[glow]}`,
        className
      )}
    >
      {children}
    </motion.div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export function CardHeader({ title, subtitle, icon, action }: CardHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
      <div className="flex items-center gap-3">
        {icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-500/10 text-primary-400">
            {icon}
          </div>
        )}
        <div>
          <h3 className="font-semibold text-slate-100">{title}</h3>
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

export function CardContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('p-6', className)}>{children}</div>;
}
