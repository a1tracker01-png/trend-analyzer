import React, { useState, useEffect } from 'react';
import { 
  X, 
  ShieldCheck, 
  Database, 
  RefreshCw, 
  Check, 
  Key, 
  Server, 
  Activity, 
  AlertCircle, 
  Sliders, 
  Lock 
} from 'lucide-react';
import { 
  fetchDataSources, 
  fetchDataSourceHealth, 
  activateDataSource, 
  updateDataSourceConfig, 
  triggerSync 
} from '../api';
import { formatDateTime } from '../utils';

export default function DataSourceModal({ isOpen, onClose, onSyncComplete }) {
  const [dataSources, setDataSources] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState('');
  
  // Meta API config fields
  const [metaToken, setMetaToken] = useState('');
  const [metaAccountId, setMetaAccountId] = useState('');
  const [savingConfig, setSavingConfig] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sources, healthData] = await Promise.all([
        fetchDataSources(),
        fetchDataSourceHealth()
      ]);
      setDataSources(sources);
      setHealth(healthData);
    } catch (err) {
      console.error('Error loading data sources:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleActivate = async (id) => {
    try {
      await activateDataSource(id);
      await loadData();
    } catch (err) {
      alert('Failed to switch data source: ' + err.message);
    }
  };

  const handleSaveMetaConfig = async (metaSourceId) => {
    try {
      setSavingConfig(true);
      await updateDataSourceConfig(metaSourceId, {
        access_token: metaToken,
        account_id: metaAccountId
      });
      alert('Meta Graph API settings saved successfully!');
      await loadData();
    } catch (err) {
      alert('Failed to save settings: ' + err.message);
    } finally {
      setSavingConfig(false);
    }
  };

  const handleTriggerSync = async (sourceId) => {
    try {
      setSyncing(true);
      setSyncSuccessMsg('');
      const res = await triggerSync(sourceId);
      setSyncSuccessMsg('Ingestion & ranking completed successfully!');
      await loadData();
      if (onSyncComplete) onSyncComplete();
    } catch (err) {
      alert('Sync error: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const activeSource = dataSources.find(ds => ds.is_active);
  const metaSource = dataSources.find(ds => ds.provider_type === 'official_graph_api');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div 
        className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Pluggable Data Source Engine</h3>
              <p className="text-xs text-slate-400">Compliance-First Architecture (Zero Illegal Web Scraping)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-6 space-y-6">
          
          {/* Policy Compliance Notice */}
          <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 space-y-1">
              <span className="font-bold text-emerald-300 block text-sm">
                100% Terms of Service Compliant
              </span>
              <p>
                This application does <strong>not</strong> scrape Instagram HTML or bypass authentication/rate limits.
                Data is ingested strictly via either official Meta Graph API endpoints or verified permitted sandbox feeds.
              </p>
            </div>
          </div>

          {/* Active Data Source Health & Quota */}
          {health && (
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Active Provider Status
                </span>
                <span className={`flex items-center gap-1.5 text-xs font-bold px-2 py-0.5 rounded-full ${
                  health.healthy ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${health.healthy ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                  {health.status.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 text-xs">
                <div>
                  <span className="text-slate-500 block">Current Provider</span>
                  <span className="text-white font-semibold">{health.provider_name}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Rate Limit Remaining</span>
                  <span className="text-emerald-400 font-bold">{health.rate_limit?.remaining} / {health.rate_limit?.limit} calls</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Last Synced</span>
                  <span className="text-slate-300">{activeSource?.last_synced_at ? formatDateTime(activeSource.last_synced_at) : 'Just now'}</span>
                </div>
              </div>

              {health.message && (
                <p className="text-xs text-slate-400 pt-2 border-t border-slate-800">
                  {health.message}
                </p>
              )}
            </div>
          )}

          {/* Available Providers List */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-purple-400" />
              <span>Available Ingestion Adapters</span>
            </h4>

            <div className="space-y-3">
              {dataSources.map((ds) => {
                const isActive = ds.is_active;

                return (
                  <div
                    key={ds.id}
                    className={`p-4 rounded-2xl border transition-all ${
                      isActive
                        ? 'bg-purple-950/20 border-purple-500/50 shadow-md shadow-purple-950/30'
                        : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white">{ds.name}</span>
                          {isActive && (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500 text-white">
                              ACTIVE
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                          Type: <code className="text-slate-300">{ds.provider_type}</code> • Auth: <code className="text-slate-300">{ds.auth_type}</code>
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {!isActive ? (
                          <button
                            onClick={() => handleActivate(ds.id)}
                            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-purple-600 text-xs font-semibold text-white transition"
                          >
                            Set Active
                          </button>
                        ) : (
                          <button
                            onClick={() => handleTriggerSync(ds.id)}
                            disabled={syncing}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white shadow transition disabled:opacity-50"
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                            <span>{syncing ? 'Ingesting...' : 'Sync Now'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Meta Instagram Graph API Configuration */}
          {metaSource && (
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <Lock className="w-4 h-4 text-purple-400" />
                <span>Meta Instagram Graph API Credentials (Optional)</span>
              </div>
              <p className="text-xs text-slate-400">
                To connect a live Instagram Business or Creator account, input your Graph API User/Page Token and Account ID.
              </p>

              <div className="space-y-3 pt-1">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Meta Graph Access Token
                  </label>
                  <input
                    type="password"
                    placeholder="EAAB..."
                    value={metaToken}
                    onChange={(e) => setMetaToken(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Instagram Business/Creator Account ID
                  </label>
                  <input
                    type="text"
                    placeholder="17841400..."
                    value={metaAccountId}
                    onChange={(e) => setMetaAccountId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500 font-mono"
                  />
                </div>

                <button
                  onClick={() => handleSaveMetaConfig(metaSource.id)}
                  disabled={savingConfig}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition disabled:opacity-50"
                >
                  {savingConfig ? 'Saving...' : 'Save Meta Configuration'}
                </button>
              </div>
            </div>
          )}

          {syncSuccessMsg && (
            <div className="p-3 rounded-xl bg-purple-500/20 border border-purple-500/40 text-xs text-purple-300 flex items-center gap-2">
              <Check className="w-4 h-4 text-purple-400 shrink-0" />
              <span>{syncSuccessMsg}</span>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>Active Rate Limit: Safe Quota Enforcement</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium transition"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
}
