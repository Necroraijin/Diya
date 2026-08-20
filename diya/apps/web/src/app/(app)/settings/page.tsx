'use client';

import { useState } from 'react';
import {
  Settings,
  Globe,
  Bell,
  Shield,
  Database,
  Cloud,
  Key,
  Monitor,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SettingToggle {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('general');
  const [settings, setSettings] = useState<Record<string, SettingToggle[]>>({
    general: [
      { id: 'auto-detect', label: 'Auto Conflict Detection', description: 'Automatically run conflict detection when new planned works are ingested', enabled: true },
      { id: 'auto-notice', label: 'Auto Notice Generation', description: 'Automatically generate citizen notices when conflicts are resolved', enabled: true },
      { id: 'dark-mode', label: 'Dark Mode', description: 'Application theme (dark mode is always on for DIYA)', enabled: true },
    ],
    notifications: [
      { id: 'conflict-alerts', label: 'Conflict Alerts', description: 'Push notifications for new critical conflicts', enabled: true },
      { id: 'resolution-alerts', label: 'Resolution Alerts', description: 'Notify when a conflict is resolved', enabled: true },
      { id: 'agent-errors', label: 'Agent Error Alerts', description: 'Notify when an agent encounters an error or is blocked', enabled: true },
      { id: 'daily-digest', label: 'Daily Digest', description: 'Email summary of daily conflict activity', enabled: false },
    ],
    security: [
      { id: 'model-armor', label: 'Model Armor', description: 'Screen citizen input for prompt injection before reaching agents', enabled: true },
      { id: 'identity-enforcement', label: 'Agent Identity Enforcement', description: 'Enforce per-department read scoping via Agent Identity', enabled: true },
      { id: 'audit-log', label: 'Audit Logging', description: 'Log all agent actions and identity verifications', enabled: true },
      { id: 'max-turns', label: 'Max Turn Caps', description: 'Limit coordinator agent negotiation loops to prevent runaway execution', enabled: true },
    ],
  });

  const sections = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security & Governance', icon: Shield },
  ];

  const toggleSetting = (section: string, settingId: string) => {
    setSettings((prev) => ({
      ...prev,
      [section]: prev[section].map((s) =>
        s.id === settingId ? { ...s, enabled: !s.enabled } : s
      ),
    }));
  };

  return (
    <div className="page-container">
      <div className="mb-5 sm:mb-6">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">System configuration and governance controls</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
        {/* Section nav */}
        <div className="lg:w-56 flex-shrink-0">
          <div className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  'flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm whitespace-nowrap transition-colors duration-150',
                  activeSection === section.id
                    ? 'bg-white/10 text-white font-medium'
                    : 'text-diya-text-muted hover:text-diya-text hover:bg-diya-card'
                )}
              >
                <section.icon className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
                {section.label}
              </button>
            ))}
          </div>
        </div>

        {/* Settings content */}
        <div className="flex-1 max-w-2xl">
          <div className="space-y-1">
            {settings[activeSection]?.map((setting) => (
              <div
                key={setting.id}
                className="card hover:border-diya-border-light transition-colors duration-150"
              >
                <div className="card-body flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium">{setting.label}</h3>
                    <p className="text-xs text-diya-text-muted mt-0.5">{setting.description}</p>
                  </div>
                  <button
                    onClick={() => toggleSetting(activeSection, setting.id)}
                    className={cn(
                      'relative w-10 h-5 rounded-full transition-colors duration-200 flex-shrink-0',
                      setting.enabled ? 'bg-white/30' : 'bg-diya-border'
                    )}
                  >
                    <div
                      className={cn(
                        'absolute top-0.5 w-4 h-4 rounded-full transition-all duration-200',
                        setting.enabled ? 'left-5.5 bg-white' : 'left-0.5 bg-diya-text-muted'
                      )}
                      style={{ left: setting.enabled ? '22px' : '2px' }}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* GCP Connection Info */}
          {activeSection === 'general' && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-3">Infrastructure</h3>
              <div className="card">
                <div className="card-body space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Cloud className="w-4 h-4 text-diya-text-muted" />
                      <span className="text-xs">GCP Project</span>
                    </div>
                    <span className="text-xs font-mono text-diya-text-secondary">diya-demo</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-diya-text-muted" />
                      <span className="text-xs">Region</span>
                    </div>
                    <span className="text-xs font-mono text-diya-text-secondary">us-central1</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4 text-diya-text-muted" />
                      <span className="text-xs">Firestore</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="status-dot status-dot-online" />
                      <span className="text-xs text-diya-text-secondary">Connected</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-diya-text-muted" />
                      <span className="text-xs">Agent Runtime</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="status-dot status-dot-online" />
                      <span className="text-xs text-diya-text-secondary">6 agents active</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Key className="w-4 h-4 text-diya-text-muted" />
                      <span className="text-xs">LLM</span>
                    </div>
                    <span className="text-xs font-mono text-diya-text-secondary">gemini-3.5-flash</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Security governance info */}
          {activeSection === 'security' && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-3">Governance Stack</h3>
              <div className="card">
                <div className="card-body">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { name: 'Agent Registry', status: 'active' },
                      { name: 'Agent Runtime', status: 'active' },
                      { name: 'Agent Identity', status: 'active' },
                      { name: 'Agent Gateway', status: 'active' },
                      { name: 'Model Armor', status: 'active' },
                      { name: 'Memory Bank', status: 'active' },
                      { name: 'Observability', status: 'active' },
                    ].map((item) => (
                      <div key={item.name} className="flex items-center gap-2 px-3 py-2 bg-diya-surface rounded-md">
                        <div className="status-dot status-dot-online" />
                        <span className="text-xs">{item.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
