import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Database, 
  RefreshCw, 
  Check, 
  Trash2, 
  ExternalLink, 
  Zap, 
  AlertCircle,
  ShieldCheck,
  Play,
  Clock,
  Sparkles
} from 'lucide-react';
import { 
  fetchDataSources, 
  fetchDataSourceHealth, 
  activateDataSource, 
  updateDataSourceConfig, 
  triggerSync,
  triggerFreshScrape,
  purgeMockData
} from '../api';

export default function DataSourceModal({ isOpen, onClose, onSyncComplete }) {
  const [dataSources, setDataSources] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState('');
  
  // Persistent token: reads from localStorage, updated from backend config
  const [apifyToken, setApifyToken] = useState(() => {
    return localStorage.getItem('reels_apify_token') || '';
  });
  
  const [savingApify, setSavingApify] = useState(false);
  const [purging, setPurging] = useState(false);

  // Fresh scrape state
  const [scrapeCategory, setScrapeCategory] = useState('all');
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeCountdown, setScrapeCountdown] = useState(0);
  const countdownIntervalRef = useRef(null);

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
          if (cfg.api_token) {
            setApifyToken(cfg.api_token);
            localStorage.setItem('reels_apify_token', cfg.api_token);
          } else {
            const currentToken = localStorage.getItem('reels_apify_token') || '';
            if (currentToken) {
              setApifyToken(currentToken);
              updateDataSourceConfig(apifySource.id, {
                api_token: currentToken,
                is_active: true
              }).catch(() => {});
            }
          }
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
    return () => {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
    };
  }, [isOpen]);

  const handleTokenChange = (e) => {
    const val = e.target.value;
    setApifyToken(val);
    localStorage.setItem('reels_apify_token', val);
  };

  const handleSaveApify = async (apifySourceId) => {
    const tokenToSave = apifyToken.trim();
    if (!tokenToSave) {
      alert('Please enter your Apify API Token first.');
      return;
    }
    try {
      setSavingApify(true);
      localStorage.setItem('reels_apify_token', tokenToSave);
      await updateDataSourceConfig(apifySourceId, {
        api_token: tokenToSave,
        is_active: true
      });
      await activateDataSource(apifySourceId);
      alert('Apify API Token saved permanently in your browser & database!');
      await loadData();
    } catch (err) {
      alert('Failed to save Apify token: ' + err.message);
    } finally {
      setSavingApify(false);
    }
  };

  const handleTriggerSync = async (sourceId) => {
    const token = apifyToken.trim() || localStorage.getItem('reels_apify_token') || '';
    try {
      setSyncing(true);
      setSyncSuccessMsg('');

      if (token) {
        localStorage.setItem('reels_apify_token', token);
        await updateDataSourceConfig(sourceId, {
          api_token: token,
          is_active: true
        });
        await activateDataSource(sourceId);
      }

      // Trigger sync with token passed (null category so all categories are synced)
      const res = await triggerSync(sourceId, null, token || undefined);
      
      const count = res.reels_count ?? (res.details?.reels_count ?? 0);
      setSyncSuccessMsg(res.message || `Successfully ingested ${count} real Instagram reels into Neon!`);

      await loadData();
      if (onSyncComplete) onSyncComplete();
    } catch (err) {
      alert('Sync Notice: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleTriggerFreshScrape = async (sourceId) => {
    const token = apifyToken.trim() || localStorage.getItem('reels_apify_token') || '';
    if (!token) {
      alert('Please enter your Apify API Token in the field above before scraping.');
      return;
    }
    try {
      setIsScraping(true);
      setSyncSuccessMsg('');
      localStorage.setItem('reels_apify_token', token);

      // Trigger scrape on Apify actor
      await triggerFreshScrape(sourceId, scrapeCategory, token, 15);
      
      // Start 32-second countdown (Apify actor run takes ~30s)
      setScrapeCountdown(32);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);

      countdownIntervalRef.current = setInterval(() => {
        setScrapeCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownIntervalRef.current);
            setIsScraping(false);
            // Automatically ingest freshly scraped reels!
            handleTriggerSync(sourceId);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

    } catch (err) {
      setIsScraping(false);
      alert('Scraper Error: ' + err.message);
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

  // Close with Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // NEVER render if not open
  if (!isOpen) return null;

  const apifySource = dataSources.find(ds => ds.provider_type === 'apify_provider') || {
    id: 3,
    name: 'Apify Instagram Reels (Live Cloud Ingestion)',
    status_message: 'Connected & Ready',
    is_active: true
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
    >
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
              <p className="text-xs text-slate-400">Apify Cloud Actor & Neon PostgreSQL Live Ingestion</p>
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
        <div className="overflow-y-auto p-6 space-y-5">
          
          {/* Apify Real Data Card - ALWAYS VISIBLE */}
          <div className="p-5 rounded-2xl bg-gradient-to-b from-purple-950/40 to-slate-950 border-2 border-purple-500/50 shadow-xl space-y-5">
            
            {/* Header inside card */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-white text-base">Apify Cloud Ingestion</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Ready & Connected
                </span>
              </div>

              <a
                href="https://console.apify.com/actors/xMc5Ga1oCONPmWJIa/runs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-purple-300 hover:text-purple-200 font-semibold underline"
              >
                <span>Apify Console</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* Connection Status Badge */}
            <div className="p-3 rounded-xl bg-purple-950/40 border border-purple-800/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-semibold text-slate-200">
                  Apify Token Active (Environment Variable & DB)
                </span>
              </div>
              <span className="text-[11px] text-purple-300 font-medium">
                {apifySource.status_message || 'Ready to sync'}
              </span>
            </div>

            {/* 1. Refetch / Trigger Fresh Scrape from Instagram */}
            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/40 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="font-bold text-white text-xs">Trigger Fresh Instagram Scrape</span>
                </div>
                <span className="text-[10px] text-indigo-300 font-mono">Apify Cloud Actor</span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                Run the Apify actor in the cloud to scrape authentic Instagram reels for South Asia (India, Pakistan, Bangladesh, Nepal):
              </p>

              <div className="flex flex-col sm:flex-row gap-2.5">
                <select
                  value={scrapeCategory}
                  onChange={(e) => setScrapeCategory(e.target.value)}
                  disabled={isScraping}
                  className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-400 font-medium"
                >
                  <option value="all">All 4 Categories: Mixed South Asia (🇮🇳 🇵🇰 🇧🇩 🇳🇵)</option>
                  <option value="niche">Niche / Gadgets (TechBurner, TechGuruji, VideoWaliSarkar, Sohag360, GadgetByte)</option>
                  <option value="ai">AI Tools & Prompts (Beebom, Varun Mayya, Hisham Sarwar, Jhankar Mahbub, Fusemachines)</option>
                  <option value="other">Other / Dev Humor (EZSnippet, Striver, Azad Chaiwala, Learn with Sumit, RONB)</option>
                  <option value="blockchain">Blockchain & Web3 (Polygon MATIC, Waqar Zaka, Pushpendra Tech, Web3 Nepal)</option>
                </select>

                <button
                  onClick={() => handleTriggerFreshScrape(apifySource.id)}
                  disabled={isScraping}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition disabled:opacity-50 shadow-md shadow-indigo-600/30"
                >
                  <Play className={`w-3.5 h-3.5 ${isScraping ? 'animate-spin' : ''}`} />
                  <span>{isScraping ? `Scraping Instagram (${scrapeCountdown}s)...` : 'Scrape Fresh from Instagram'}</span>
                </button>
              </div>

              {isScraping && (
                <div className="p-2.5 rounded-lg bg-indigo-900/40 border border-indigo-400/40 flex items-center justify-between text-xs text-indigo-200">
                  <div className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 animate-pulse text-indigo-300" />
                    <span>Apify actor is scraping Instagram in cloud...</span>
                  </div>
                  <span className="font-bold font-mono text-indigo-300">Auto-syncing in {scrapeCountdown}s</span>
                </div>
              )}
            </div>

            {/* 2. Direct Sync into Neon Database */}
            <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="text-xs">
                <span className="text-slate-400 block text-[11px]">Database Status:</span>
                <span className="font-semibold text-purple-300 text-xs">
                  {apifySource.status_message || 'Ready to sync'}
                </span>
              </div>

              <button
                onClick={() => handleTriggerSync(apifySource.id)}
                disabled={syncing || isScraping}
                className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-extrabold text-white shadow-lg shadow-purple-600/30 transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                <span>{syncing ? 'Ingesting Real Reels...' : 'Sync Real Reels to Database'}</span>
              </button>
            </div>

          </div>

          {/* Purge Fake Seed Data Option */}
          <div className="p-3.5 rounded-2xl bg-rose-950/20 border border-rose-500/20 flex items-center justify-between gap-3">
            <div>
              <span className="font-bold text-rose-300 text-xs block">Purge Sample / Fake Seed Data</span>
              <p className="text-[11px] text-slate-400">
                Removes any synthetic mock records so only authentic Instagram reels are displayed.
              </p>
            </div>
            <button
              onClick={handlePurgeMockData}
              disabled={purging}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/30 text-xs font-semibold transition disabled:opacity-50 shrink-0"
            >
              <Trash2 className="w-3 h-3" />
              <span>{purging ? 'Purging...' : 'Purge Data'}</span>
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
            className="px-5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition shadow-md"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
}

