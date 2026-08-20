'use client';

import { motion } from 'framer-motion';
import {
  Building2,
  Route,
  AlertTriangle,
  Wrench,
  Layers,
  Upload,
  MapPin,
} from 'lucide-react';
import { cities } from '@/lib/mock-data';
import { cn } from '@/lib/utils';

interface MapControlsProps {
  selectedCity: string;
  onCityChange: (city: string) => void;
  activeLayers: Record<string, boolean>;
  onToggleLayer: (layer: any) => void;
}

const layerConfig = [
  { id: 'buildings', label: 'Buildings', icon: Building2 },
  { id: 'roads', label: 'Roads', icon: Route },
  { id: 'conflicts', label: 'Conflicts', icon: AlertTriangle },
  { id: 'works', label: 'Works', icon: Wrench },
];

export default function MapControls({
  selectedCity,
  onCityChange,
  activeLayers,
  onToggleLayer,
}: MapControlsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className="absolute top-4 left-4 space-y-2"
    >
      {/* City selector */}
      <div className="glass rounded-lg p-2">
        <div className="flex items-center gap-1.5 mb-2 px-1">
          <MapPin className="w-3 h-3 text-diya-text-muted" />
          <span className="text-[10px] text-diya-text-muted uppercase tracking-wider">City</span>
        </div>
        <div className="space-y-0.5">
          {cities.map((city) => (
            <button
              key={city.id}
              onClick={() => onCityChange(city.id)}
              className={cn(
                'w-full text-left px-3 py-1.5 rounded-md text-xs transition-all duration-200',
                selectedCity === city.id
                  ? 'bg-white/10 text-white font-medium'
                  : 'text-diya-text-muted hover:text-diya-text hover:bg-white/5'
              )}
            >
              {city.name}
            </button>
          ))}
          <button className="w-full text-left px-3 py-1.5 rounded-md text-xs text-diya-text-muted hover:text-diya-text hover:bg-white/5 transition-all duration-200 flex items-center gap-2 border-t border-diya-border mt-1 pt-2">
            <Upload className="w-3 h-3" />
            Upload Map
          </button>
        </div>
      </div>

      {/* Layer toggles */}
      <div className="glass rounded-lg p-2">
        <div className="flex items-center gap-1.5 mb-2 px-1">
          <Layers className="w-3 h-3 text-diya-text-muted" />
          <span className="text-[10px] text-diya-text-muted uppercase tracking-wider">Layers</span>
        </div>
        <div className="space-y-0.5">
          {layerConfig.map((layer) => (
            <button
              key={layer.id}
              onClick={() => onToggleLayer(layer.id)}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-1.5 rounded-md text-xs transition-all duration-200',
                activeLayers[layer.id]
                  ? 'text-white bg-white/5'
                  : 'text-diya-text-muted hover:text-diya-text'
              )}
            >
              <layer.icon className="w-3 h-3" />
              <span>{layer.label}</span>
              <div
                className={cn(
                  'ml-auto w-6 h-3 rounded-full transition-colors duration-200 relative',
                  activeLayers[layer.id] ? 'bg-white/30' : 'bg-diya-border'
                )}
              >
                <div
                  className={cn(
                    'absolute top-0.5 w-2 h-2 rounded-full transition-all duration-200',
                    activeLayers[layer.id] ? 'left-3.5 bg-white' : 'left-0.5 bg-diya-text-muted'
                  )}
                />
              </div>
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
