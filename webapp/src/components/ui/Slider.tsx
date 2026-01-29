import * as SliderPrimitive from '@radix-ui/react-slider';
import { cn } from '../../lib/utils';

interface SliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  description?: string;
  formatValue?: (value: number) => string;
}

export function Slider({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit = '',
  description,
  formatValue,
}: SliderProps) {
  const displayValue = formatValue ? formatValue(value) : `${value}${unit}`;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <label className="text-sm font-medium text-slate-200">{label}</label>
          {description && (
            <p className="text-xs text-slate-500">{description}</p>
          )}
        </div>
        <span className="rounded-lg bg-slate-800 px-3 py-1 font-mono text-sm text-primary-400">
          {displayValue}
        </span>
      </div>
      <SliderPrimitive.Root
        className="relative flex h-5 w-full touch-none select-none items-center"
        value={[value]}
        onValueChange={([v]) => onChange(v)}
        min={min}
        max={max}
        step={step}
      >
        <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-slate-700">
          <SliderPrimitive.Range className="absolute h-full bg-gradient-to-r from-primary-500 to-primary-400" />
        </SliderPrimitive.Track>
        <SliderPrimitive.Thumb
          className={cn(
            'block h-5 w-5 rounded-full bg-white shadow-lg shadow-primary-500/30',
            'ring-offset-slate-900 transition-transform hover:scale-110',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            'cursor-grab active:cursor-grabbing'
          )}
        />
      </SliderPrimitive.Root>
      <div className="flex justify-between text-xs text-slate-500">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}
