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
  Lock, 
  Globe2, 
  ExternalLink, 
  Zap 
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
  
  // Apify config fields
  const [apifyToken, setApifyToken] = useState('');
  const [savingApify, setSavingApify] = useState(false);

  // Meta API config fields
  const [metaToken, setMetaToken] = useState('');
  const [metaAccountId, setMetaAccountId] = useState('');
  const [savingMeta, setSavingMeta] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sources, healthData] = await Promise.all([
        fetchDataSources(),
        fetchDataSourceHealth()
      ]);
      setDataSources(sources);
      setHealth(healthData);

      // Pre-fill Apify token if present
      const apifySource = sources.find(s => s.provider_type === 'apify_provider');
      if (apifySource?.config_json) {
        try {
          const cfg = JSON.parse(apifySource.config_json);
          if (cfg.api_token) setApifyToken(cfg.api_token);
        } catch (e) {}
      }

      // Pre-fill Meta token if present
      const metaSource = sources.find(s => s.provider_type === 'official_graph_api');
      if (metaSource?.config_json) {
        try {
          const cfg = JSON.parse(metaSource.config_json);
          if (cfg.access_token) setMetaToken(cfg.access_token);
          if (cfg.account_id) setMetaAccountId(cfg.account_id);
        } catch (e) {}
      }
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

  const handleSaveApify = async (apifySourceId) => {
    try {
      setSavingApify(true);
      await updateDataSourceConfig(apifySourceId, {
        api_token: apifyToken
      });
      alert('Apify API token saved successfully! You can now activate and sync real Instagram reels.');
      await loadData();
    } catch (err) {
      alert('Failed to save Apify settings: ' + err.message);
    } finally {
      setSavingApify(false);
    }
  };

  const handleSaveMeta = async (metaSourceId) => {
    try {
      setSavingMeta(true);
      await updateDataSourceConfig(metaSourceId, {
        access_token: metaToken,
        account_id: metaAccountId
      });
      alert('Meta Graph API settings saved successfully!');
      await loadData();
    } catch (err) {
      alert('Failed to save settings: ' + err.message);
    } finally {
      setSavingMeta(false);
    }
  };

  const handleTriggerSync = async (sourceId) => {
    try {
      setSyncing(true);
      setSyncSuccessMsg('');
      await triggerSync(sourceId);
      setSyncSuccessMsg('Live reels ingested & scored into Neon PostgreSQL successfully!');
      await loadData();
      if (onSyncComplete) onSyncComplete();
    } catch (err) {
      alert('Sync error: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const activeSource = dataSources.find(ds => ds.is_active);
  const apifySource = dataSources.find(ds => ds.provider_type === 'apify_provider');
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
              <p className="text-xs text-slate-400">Live Real Instagram Ingestion (Zero Unauthorized Browser Scraping)</p>
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
                <p className="text-xs text-slate-300 pt-2 border-t border-slate-800">
                  {health.message}
                </p>
              )}
            </div>
          )}

          {/* Section: Option B - Apify Real Instagram Feed (Cheapest & Recommended) */}
          {apifySource && (
            <div className="p-5 rounded-2xl bg-gradient-to-b from-purple-950/30 to-indigo-950/20 border-2 border-purple-500/40 shadow-lg space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-300 flex items-center justify-center font-bold">
                    <Zap className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-white text-sm">Apify Instagram Cloud Feed</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        FREE $5/mo Credit
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">Pulls real public reels across Tech, AI, and Blockchain</span>
                  </div>
                </div>

                <a
                  href="https://console.apify.com/account/integrations"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-purple-300 hover:text-purple-200 font-semibold underline self-start sm:self-auto"
                >
                  <span>Get Free API Token</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <div className="pt-2 space-y-2">
                <label className="block text-xs font-medium text-slate-300">
                  Apify Personal API Token (<code className="text-purple-300">apify_api_...</code>)
                </label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    placeholder="apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={apifyToken}
                    onChange={(e) => setApifyToken(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500 font-mono"
                  />
                  <button
                    onClick={() => handleSaveApify(apifySource.id)}
                    disabled={savingApify || !apifyToken}
                    className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white transition disabled:opacity-50 shrink-0"
                  >
                    {savingApify ? 'Saving...' : 'Save Token'}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-purple-800/30 text-xs">
                <span className="text-slate-400 text-[11px]">
                  No Facebook account or Meta App Review required.
                </span>
                {apifySource.is_active ? (
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                    <Check className="w-3.5 h-3.5" /> Currently Active Ingestion Source
                  </span>
                ) : (
                  <button
                    onClick={() => handleActivate(apifySource.id)}
                    className="px-3 py-1.5 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border border-purple-400/30 text-xs font-semibold transition"
                  >
                    Activate Apify Feed
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Available Providers List */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-purple-400" />
              <span>All Available Adapters</span>
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
                          Type: <code className="text-slate-300">{ds.provider_type}</code> • Status: <span className="text-slate-300">{ds.status_message}</span>
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
                            <span>{syncing ? 'Ingesting Real Reels...' : 'Sync Real Reels'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {syncSuccessMsg && (
            <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-xs text-emerald-300 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{syncSuccessMsg}</span>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>Real-time Ingestion into Neon PostgreSQL</span>
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
