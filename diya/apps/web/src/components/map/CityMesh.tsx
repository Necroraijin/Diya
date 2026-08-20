'use client';

import { useState, useMemo, useCallback } from 'react';
import {
  mumbaiBuildings,
  mumbaiRoads,
  delhiBuildings,
  delhiRoads,
  conflictZones,
  plannedWorks,
  cities,
} from '@/lib/mock-data';
import MapControls from './MapControls';
import MapLegend from './MapLegend';
import ConflictPanel from './ConflictPanel';

interface CityMeshProps {
  selectedCity: string;
  onCityChange: (city: string) => void;
}

export default function CityMesh({ selectedCity, onCityChange }: CityMeshProps) {
  const [activeLayers, setActiveLayers] = useState({
    buildings: true,
    roads: true,
    conflicts: true,
    works: true,
    zones: true,
  });
  const [selectedConflict, setSelectedConflict] = useState<string | null>(null);
  const [hoveredElement, setHoveredElement] = useState<string | null>(null);

  const city = cities.find((c) => c.id === selectedCity) || cities[0];
  const buildings = selectedCity === 'delhi' ? delhiBuildings : mumbaiBuildings;
  const roads = selectedCity === 'delhi' ? delhiRoads : mumbaiRoads;
  const cityWorks = plannedWorks.filter((w) => w.city === selectedCity);

  const viewBox = useMemo(() => {
    const allLngs = buildings.flatMap((b) => b.coordinates.map((c) => c[0]));
    const allLats = buildings.flatMap((b) => b.coordinates.map((c) => c[1]));
    const roadLngs = roads.flatMap((r) => r.path.map((p) => p[0]));
    const roadLats = roads.flatMap((r) => r.path.map((p) => p[1]));
    const lngs = [...allLngs, ...roadLngs];
    const lats = [...allLats, ...roadLats];
    const minLng = Math.min(...lngs) - 0.002;
    const maxLng = Math.max(...lngs) + 0.002;
    const minLat = Math.min(...lats) - 0.002;
    const maxLat = Math.max(...lats) + 0.002;
    return { minLng, maxLng, minLat, maxLat };
  }, [buildings, roads]);

  const project = useCallback(
    (lng: number, lat: number): [number, number] => {
      const x = ((lng - viewBox.minLng) / (viewBox.maxLng - viewBox.minLng)) * 1000;
      const y = (1 - (lat - viewBox.minLat) / (viewBox.maxLat - viewBox.minLat)) * 700;
      return [x, y];
    },
    [viewBox]
  );

  const toggleLayer = (layer: keyof typeof activeLayers) => {
    setActiveLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  return (
    <div className="relative w-full h-full bg-diya-bg overflow-hidden">
      {/* Grid background */}
      <div className="absolute inset-0 grid-pattern opacity-50" />

      {/* SVG Map - preserveAspectRatio ensures proper scaling */}
      <svg
        viewBox="0 0 1000 700"
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 w-full h-full"
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glowStrong">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="conflictGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(239, 68, 68, 0.3)" />
            <stop offset="70%" stopColor="rgba(239, 68, 68, 0.1)" />
            <stop offset="100%" stopColor="rgba(239, 68, 68, 0)" />
          </radialGradient>
        </defs>

        {/* Roads */}
        {activeLayers.roads &&
          roads.map((road) => {
            const pathPoints = road.path.map(([lng, lat]) => project(lng, lat));
            const d = pathPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
            const isConflict = road.wayId === 'way-48213001' || road.wayId === 'way-92001001';
            return (
              <g key={road.wayId}>
                <path
                  d={d}
                  fill="none"
                  stroke={isConflict && activeLayers.conflicts ? 'rgba(239, 68, 68, 0.12)' : 'rgba(255, 255, 255, 0.04)'}
                  strokeWidth={road.width * 4}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d={d}
                  fill="none"
                  stroke={isConflict && activeLayers.conflicts ? 'rgba(239, 68, 68, 0.6)' : 'rgba(255, 255, 255, 0.25)'}
                  strokeWidth={road.width}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter={isConflict ? 'url(#glow)' : undefined}
                  onMouseEnter={() => setHoveredElement(road.wayId)}
                  onMouseLeave={() => setHoveredElement(null)}
                  style={{ cursor: 'pointer' }}
                />
                {hoveredElement === road.wayId && (
                  <text
                    x={pathPoints[Math.floor(pathPoints.length / 2)][0]}
                    y={pathPoints[Math.floor(pathPoints.length / 2)][1] - 12}
                    fill="white"
                    fontSize="11"
                    textAnchor="middle"
                    style={{ pointerEvents: 'none' }}
                    fontFamily="Inter, sans-serif"
                  >
                    {road.name}
                  </text>
                )}
              </g>
            );
          })}

        {/* Buildings (wireframe 3D) */}
        {activeLayers.buildings &&
          buildings.map((building) => {
            const basePoints = building.coordinates.map(([lng, lat]) => project(lng, lat));
            const heightOffset = building.height * 0.35;
            const topPoints = basePoints.map(([x, y]) => [x, y - heightOffset]);
            const topPath = topPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ') + 'Z';
            const isHovered = hoveredElement === building.wayId;

            return (
              <g
                key={building.wayId}
                onMouseEnter={() => setHoveredElement(building.wayId)}
                onMouseLeave={() => setHoveredElement(null)}
                style={{ cursor: 'pointer' }}
              >
                {basePoints.map((bp, i) => {
                  const next = basePoints[(i + 1) % basePoints.length];
                  const tp = topPoints[i];
                  const tnext = topPoints[(i + 1) % topPoints.length];
                  const facePath = `M${bp[0]},${bp[1]} L${next[0]},${next[1]} L${tnext[0]},${tnext[1]} L${tp[0]},${tp[1]} Z`;
                  return (
                    <path
                      key={i}
                      d={facePath}
                      fill={isHovered ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.02)'}
                      stroke={isHovered ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)'}
                      strokeWidth={0.5}
                    />
                  );
                })}
                <path
                  d={topPath}
                  fill={isHovered ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.03)'}
                  stroke={isHovered ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.15)'}
                  strokeWidth={0.5}
                />
              </g>
            );
          })}

        {/* Conflict zones */}
        {activeLayers.conflicts &&
          conflictZones.map((zone) => {
            const [cx, cy] = project(zone.center[0], zone.center[1]);
            const r = zone.radius * 0.15;
            return (
              <g key={zone.conflictId}>
                <circle cx={cx} cy={cy} r={r} fill="url(#conflictGradient)" opacity={0.8}>
                  <animate attributeName="opacity" values="0.5;0.9;0.5" dur="3s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx} cy={cy} r={r * 0.4} fill="none" stroke="rgba(239, 68, 68, 0.5)" strokeWidth={1} filter="url(#glow)">
                  <animate attributeName="r" values={`${r * 0.35};${r * 0.45};${r * 0.35}`} dur="2s" repeatCount="indefinite" />
                </circle>
                <circle
                  cx={cx} cy={cy} r={5}
                  fill="#ef4444"
                  filter="url(#glowStrong)"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedConflict(zone.conflictId)}
                />
                <text x={cx} y={cy - r - 10} fill="#ef4444" fontSize="10" textAnchor="middle" fontFamily="Inter, sans-serif" fontWeight="500">
                  CONFLICT ZONE
                </text>
              </g>
            );
          })}

        {/* Planned work markers */}
        {activeLayers.works &&
          cityWorks.map((work) => {
            const [cx, cy] = project(work.location.lng, work.location.lat);
            const isConflicted = work.status === 'conflicted';
            return (
              <circle
                key={work.id}
                cx={cx} cy={cy} r={3.5}
                fill={isConflicted ? 'rgba(239, 68, 68, 0.8)' : 'rgba(255, 255, 255, 0.6)'}
                stroke={isConflicted ? '#ef4444' : 'rgba(255,255,255,0.3)'}
                strokeWidth={0.5}
                style={{ cursor: 'pointer' }}
                filter={isConflicted ? 'url(#glow)' : undefined}
              />
            );
          })}
      </svg>

      {/* Controls overlay */}
      <MapControls
        selectedCity={selectedCity}
        onCityChange={onCityChange}
        activeLayers={activeLayers}
        onToggleLayer={toggleLayer}
      />

      <MapLegend />

      {/* City label */}
      <div className="absolute top-3 sm:top-4 left-1/2 -translate-x-1/2 px-3 sm:px-4 py-1.5 sm:py-2 glass rounded-lg animate-fade-in">
        <span className="text-[10px] sm:text-xs font-medium tracking-widest uppercase">{city.name}</span>
        <span className="text-[10px] sm:text-xs text-diya-text-muted ml-2">
          {cityWorks.length} planned works
        </span>
      </div>

      {/* Selected conflict panel */}
      {selectedConflict && (
        <ConflictPanel
          conflictId={selectedConflict}
          onClose={() => setSelectedConflict(null)}
        />
      )}
    </div>
  );
}
