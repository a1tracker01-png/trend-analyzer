import React, { useState, useEffect } from 'react';
import { 
  X, 
  Database, 
  RefreshCw, 
  Check, 
  Trash2, 
  ExternalLink, 
  Zap, 
  AlertCircle,
  ShieldCheck
} from 'lucide-react';
import { 
  fetchDataSources, 
  fetchDataSourceHealth, 
  activateDataSource, 
  updateDataSourceConfig, 
  triggerSync,
  purgeMockData
} from '../api';

export default function DataSourceModal({ isOpen, onClose, onSyncComplete }) {
  const [dataSources, setDataSources] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState('');
  const [apifyToken, setApifyToken] = useState('');
  const [savingApify, setSavingApify] = useState(false);
  const [purging, setPurging] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sources, healthData] = await Promise.all([
        fetchDataSources(),
        fetchDataSourceHealth()
      ]);
      setDataSources(sources);
      setHealth(healthData);

      const apifySource = sources.find(s => s.provider_type === 'apify_provider');
      if (apifySource?.config_json) {
        try {
          const cfg = JSON.parse(apifySource.config_json);
          if (cfg.api_token) setApifyToken(cfg.api_token);
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

  const handleSaveApify = async (apifySourceId) => {
    try {
      setSavingApify(true);
      await updateDataSourceConfig(apifySourceId, {
        api_token: apifyToken.trim(),
        is_active: true
      });
      await activateDataSource(apifySourceId);
      alert('Apify API Token saved and set as active provider!');
      await loadData();
    } catch (err) {
      alert('Failed to save Apify token: ' + err.message);
    } finally {
      setSavingApify(false);
    }
  };

  const handleTriggerSync = async (sourceId) => {
    if (!apifyToken.trim()) {
      alert('Please enter your Apify API Token first.');
      return;
    }

    try {
      setSyncing(true);
      setSyncSuccessMsg('');

      // Auto-save the token and activate Apify first
      await updateDataSourceConfig(sourceId, {
        api_token: apifyToken.trim(),
        is_active: true
      });
      await activateDataSource(sourceId);

      // Trigger sync with token passed
      const res = await triggerSync(sourceId, null, apifyToken.trim());
      
      const count = res.reels_count ?? (res.details?.reels_count ?? 0);
      setSyncSuccessMsg(res.message || `Successfully ingested real reels! Fake seed data purged.`);

      await loadData();
      if (onSyncComplete) onSyncComplete();
    } catch (err) {
      alert('Sync Notice: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handlePurgeMockData = async () => {
    if (!window.confirm('Delete all fake / seed reels from the database? Only 100% real Instagram reels will remain.')) {
      return;
    }
    try {
      setPurging(true);
      const res = await purgeMockData();
      alert(`Deleted ${res.purged_count} fake seed reels from your database!`);
      await loadData();
      if (onSyncComplete) onSyncComplete();
    } catch (err) {
      alert('Purge error: ' + err.message);
    } finally {
      setPurging(false);
    }
  };

  const apifySource = dataSources.find(ds => ds.provider_type === 'apify_provider');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div 
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <Zap className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Real Instagram Data Integration</h3>
              <p className="text-xs text-slate-400">Live cloud ingestion with your free Apify API Token</p>
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
          
          {/* Apify Real Data Card */}
          {apifySource && (
            <div className="p-5 rounded-2xl bg-gradient-to-b from-purple-950/40 to-slate-950 border-2 border-purple-500/50 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-white text-base">Apify Cloud Ingestion</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    FREE $5/mo Credit Included
                  </span>
                </div>

                <a
                  href="https://console.apify.com/account/integrations"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-purple-300 hover:text-purple-200 font-semibold underline"
                >
                  <span>Get Apify Token</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <p className="text-xs text-slate-300">
                Paste your Apify Personal API token below. Tap <strong>Sync Real Reels Now</strong> to immediately fetch real reels from your Apify account into your Neon database and purge all fake seed data!
              </p>

              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300">
                  Apify Personal API Token:
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
                    disabled={savingApify || !apifyToken.trim()}
                    className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition disabled:opacity-50 shrink-0"
                  >
                    {savingApify ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>

              {/* Status and Action Buttons */}
              <div className="pt-3 border-t border-purple-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="text-xs">
                  <span className="text-slate-400 block text-[11px]">Sync Status:</span>
                  <span className="font-semibold text-purple-300 text-xs">
                    {apifySource.status_message || 'Ready to sync'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTriggerSync(apifySource.id)}
                    disabled={syncing || !apifyToken.trim()}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-extrabold text-white shadow-lg shadow-purple-600/30 transition disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                    <span>{syncing ? 'Ingesting Real Reels...' : 'Sync Real Reels Now'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Purge Fake Seed Data Card */}
          <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="font-bold text-rose-300 text-sm block">Delete All Fake / Seed Data</span>
              <p className="text-xs text-slate-400">
                Purge all synthetic sample reels from the database so only 100% real Instagram data is shown.
              </p>
            </div>
            <button
              onClick={handlePurgeMockData}
              disabled={purging}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/40 text-xs font-semibold transition disabled:opacity-50 shrink-0 self-start sm:self-auto"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{purging ? 'Purging...' : 'Purge Fake Data'}</span>
            </button>
          </div>

          {syncSuccessMsg && (
            <div className="p-3.5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-xs text-emerald-300 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="font-semibold">{syncSuccessMsg}</span>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Neon PostgreSQL Cloud Database</span>
          </div>
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
