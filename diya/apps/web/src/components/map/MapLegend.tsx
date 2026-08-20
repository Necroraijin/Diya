'use client';

import { motion } from 'framer-motion';

const legendItems = [
  { color: 'rgba(255, 255, 255, 0.25)', label: 'Road Network', type: 'line' },
  { color: 'rgba(255, 255, 255, 0.15)', label: 'Building Footprint', type: 'rect' },
  { color: 'rgba(239, 68, 68, 0.6)', label: 'Conflict Zone', type: 'line' },
  { color: 'rgba(239, 68, 68, 0.8)', label: 'Conflicted Work', type: 'dot' },
  { color: 'rgba(255, 255, 255, 0.6)', label: 'Planned Work', type: 'dot' },
];

export default function MapLegend() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="absolute bottom-4 left-4 glass rounded-lg p-3"
    >
      <span className="text-[10px] text-diya-text-muted uppercase tracking-wider mb-2 block">
        Legend
      </span>
      <div className="space-y-1.5">
        {legendItems.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            {item.type === 'line' && (
              <div className="w-4 h-0.5 rounded" style={{ backgroundColor: item.color }} />
            )}
            {item.type === 'rect' && (
              <div
                className="w-3 h-3 border rounded-sm"
                style={{ borderColor: item.color, backgroundColor: item.color.replace('0.15', '0.05') }}
              />
            )}
            {item.type === 'dot' && (
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
            )}
            <span className="text-[10px] text-diya-text-secondary">{item.label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
