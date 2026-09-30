import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Users, Plus, Trash2, RefreshCw, Bell, BellDot, Eye, Zap, TrendingUp,
  Clock, AlertTriangle, Shield, Search, X, ChevronDown, Star, Radio,
  Flame, BarChart3, UserPlus, Filter, Target, Activity, Sparkles,
  ExternalLink, Play, Heart, MessageCircle, Share2, Bookmark,
  ArrowUpRight, Crown, ChevronRight
} from 'lucide-react';
import {
  fetchCompetitors, addCompetitor, removeCompetitor, scrapeAllCompetitors,
  fetchCompetitorReels, fetchSpikeAlerts, fetchCompetitorStats,
  fetchCompetitorSuggestions, scrapeSingleCompetitor
} from '../api';

const TIMEFRAME_OPTIONS = [
  { value: 'all', label: 'All Time' },
  { value: '24h', label: 'Past 24 Hours' },
  { value: '2d', label: 'Past 2 Days' },
  { value: '7d', label: 'Past 1 Week' },
];

const VIEW_THRESHOLD_OPTIONS = [
  { value: 0,       label: 'All Views' },
  { value: 100000,  label: '100K+ Views' },
  { value: 500000,  label: '500K+ Views' },
  { value: 1000000, label: '1M+ Views' },
  { value: 2000000, label: '2M+ Views' },
];

const SORT_OPTIONS = [
  { value: 'views',           label: 'Most Views' },
  { value: 'growth_velocity', label: 'Fastest Growing' },
  { value: 'recent',          label: 'Most Recent' },
  { value: 'engagement',      label: 'Highest Engagement' },
];

function formatNumber(n) {
  if (!n && n !== 0) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toLocaleString();
}

function formatVelocity(v) {
  if (!v) return '—';
  if (v >= 1_000_000) return `+${(v / 1_000_000).toFixed(1)}M/hr`;
  if (v >= 1_000) return `+${(v / 1_000).toFixed(0)}K/hr`;
  return `+${Math.round(v)}/hr`;
}

function getSurgeColor(level) {
  if (!level) return '';
  if (level.includes('Extreme')) return 'text-red-400';
  if (level.includes('Viral')) return 'text-orange-400';
  return 'text-yellow-400';
}

function getSurgeBg(level) {
  if (!level) return 'bg-slate-800/40';
  if (level.includes('Extreme')) return 'bg-red-500/10 border-red-500/30';
  if (level.includes('Viral')) return 'bg-orange-500/10 border-orange-500/30';
  return 'bg-yellow-500/10 border-yellow-500/30';
}

// ─── Sub-Components ───────────────────────────────────────────────────────────

function CompetitorCard({ comp, onRemove, onScrape, isScraping }) {
  return (
    <div className="group relative bg-gradient-to-br from-slate-900/90 to-slate-800/60 border border-slate-700/50 rounded-2xl p-4 hover:border-purple-500/40 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10">
      {/* Active pulse */}
      {comp.active_spikes_count > 0 && (
        <span className="absolute top-3 right-3 flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
        </span>
      )}

      <div className="flex items-start gap-3 mb-3">
        <div className="relative shrink-0">
          <img
            src={comp.avatar_url || `https://api.dicebear.com/7.x/identicon/svg?seed=${comp.username}`}
            alt={comp.username}
            className="w-11 h-11 rounded-full object-cover border-2 border-slate-700 group-hover:border-purple-500/50 transition"
            onError={e => { e.target.src = `https://api.dicebear.com/7.x/identicon/svg?seed=${comp.username}`; }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="font-bold text-white text-sm truncate">@{comp.username}</p>
          </div>
          <p className="text-xs text-slate-400 truncate">{comp.name || comp.username}</p>
          <p className="text-xs text-slate-500">{formatNumber(comp.followers_count)} followers</p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-slate-800/60 rounded-xl p-2.5">
          <p className="text-[10px] text-slate-500 mb-0.5 flex items-center gap-1"><Eye className="w-3 h-3" /> Avg Views</p>
          <p className="text-sm font-bold text-white">{formatNumber(comp.avg_views)}</p>
        </div>
        <div className="bg-slate-800/60 rounded-xl p-2.5">
          <p className="text-[10px] text-slate-500 mb-0.5 flex items-center gap-1"><Zap className="w-3 h-3" /> Max Views</p>
          <p className="text-sm font-bold text-white">{formatNumber(comp.max_views)}</p>
        </div>
        <div className="bg-slate-800/60 rounded-xl p-2.5">
          <p className="text-[10px] text-slate-500 mb-0.5 flex items-center gap-1"><BarChart3 className="w-3 h-3" /> Reels</p>
          <p className="text-sm font-bold text-white">{comp.total_reels}</p>
        </div>
        <div className={`rounded-xl p-2.5 ${comp.active_spikes_count > 0 ? 'bg-red-500/10 border border-red-500/30' : 'bg-slate-800/60'}`}>
          <p className={`text-[10px] mb-0.5 flex items-center gap-1 ${comp.active_spikes_count > 0 ? 'text-red-400' : 'text-slate-500'}`}>
            <Flame className="w-3 h-3" /> Active Spikes
          </p>
          <p className={`text-sm font-bold ${comp.active_spikes_count > 0 ? 'text-red-400' : 'text-white'}`}>
            {comp.active_spikes_count}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onScrape(comp.id)}
          disabled={isScraping}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-300 text-xs font-semibold transition"
        >
          <RefreshCw className={`w-3 h-3 ${isScraping ? 'animate-spin' : ''}`} />
          Sync
        </button>
        <button
          onClick={() => onRemove(comp.id)}
          className="p-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 transition"
          title="Remove competitor"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

function AddCompetitorModal({ onClose, onAdd, suggestions }) {
  const [username, setUsername] = useState('');
  const [category, setCategory] = useState('Tech');
  const [threshold, setThreshold] = useState(500000);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) return;
    try {
      setLoading(true);
      setError('');
      await onAdd({ username: username.trim(), category, custom_view_threshold: threshold });
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gradient-to-br from-[#0d1117] to-[#0b1628] border border-slate-700/60 rounded-3xl p-6 w-full max-w-lg shadow-2xl shadow-purple-900/20" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-purple-400" />
              Add Competitor
            </h2>
            <p className="text-xs text-slate-400 mt-1">Track a creator's real-time reel performance</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Instagram Username</label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">@</span>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="e.g. techburner"
                className="w-full pl-8 pr-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Category</label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full px-3 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-purple-500 transition"
              >
                {['Tech', 'AI', 'Blockchain', 'Other', 'Niche'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">View Alert Threshold</label>
              <select
                value={threshold}
                onChange={e => setThreshold(Number(e.target.value))}
                className="w-full px-3 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-purple-500 transition"
              >
                {VIEW_THRESHOLD_OPTIONS.filter(o => o.value > 0).map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              {error}
            </div>
          )}

          {/* Quick suggestions */}
          {suggestions.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Quick Add — Popular creators:</p>
              <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                {suggestions.slice(0, 8).map(s => (
                  <button
                    key={s.username}
                    type="button"
                    onClick={() => setUsername(s.username)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition border ${username === s.username ? 'bg-purple-600/30 border-purple-500/50 text-purple-300' : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white hover:border-slate-600'}`}
                  >
                    @{s.username}
                  </button>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username.trim()}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {loading ? 'Adding...' : 'Add Competitor & Start Tracking'}
          </button>
        </form>
      </div>
    </div>
  );
}

function SpikeAlertCard({ alert }) {
  const surgeColor = getSurgeColor(alert.surge_level);
  const surgeBg = getSurgeBg(alert.surge_level);

  return (
    <div className={`relative border rounded-2xl p-4 transition-all duration-300 overflow-hidden ${surgeBg}`}>
      {/* Animated background pulse */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-red-500/5 via-orange-500/5 to-yellow-500/5 animate-pulse pointer-events-none" />

      <div className="relative flex gap-3">
        {/* Thumbnail */}
        <div className="shrink-0 w-16 h-20 rounded-xl overflow-hidden border border-slate-700/50">
          <img
            src={alert.thumbnail_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&h=300&fit=crop'}
            alt="Reel thumbnail"
            className="w-full h-full object-cover"
            onError={e => { e.target.src = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&h=300&fit=crop'; }}
          />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${surge_level_badge(alert.surge_level)}`}>
              {alert.surge_level}
            </span>
            <span className="text-[10px] text-slate-500">{alert.hours_ago}h ago</span>
          </div>

          {/* Creator */}
          <div className="flex items-center gap-1.5 mb-1.5">
            <img
              src={alert.creator_avatar || `https://api.dicebear.com/7.x/identicon/svg?seed=${alert.creator_username}`}
              alt=""
              className="w-4 h-4 rounded-full"
              onError={e => { e.target.src = `https://api.dicebear.com/7.x/identicon/svg?seed=${alert.creator_username}`; }}
            />
            <span className="text-xs text-slate-300 font-semibold">@{alert.creator_username}</span>
          </div>

          <p className="text-xs text-slate-400 line-clamp-2 mb-2">{alert.caption || 'Trending reel without caption'}</p>

          <div className="grid grid-cols-2 gap-x-3 gap-y-1">
            <div className="flex items-center gap-1">
              <Eye className="w-3 h-3 text-slate-500" />
              <span className="text-xs text-white font-semibold">{formatNumber(alert.current_views)}</span>
            </div>
            <div className={`flex items-center gap-1 ${surgeColor}`}>
              <TrendingUp className="w-3 h-3" />
              <span className="text-xs font-bold">{formatVelocity(alert.current_growth_velocity)}</span>
            </div>
          </div>

          <div className="mt-2 text-[11px] text-slate-400 font-medium">{alert.milestone_text}</div>

          <a
            href={alert.permalink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 mt-2 text-[11px] text-purple-400 hover:text-purple-300 transition"
          >
            View on Instagram <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );
}

function surge_level_badge(level) {
  if (!level) return 'text-slate-400 border-slate-600 bg-slate-800/50';
  if (level.includes('Extreme')) return 'text-red-400 border-red-500/40 bg-red-500/10';
  if (level.includes('Viral')) return 'text-orange-400 border-orange-500/40 bg-orange-500/10';
  return 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10';
}

function CompetitorReelCard({ reel, onViewDetail }) {
  return (
    <div
      onClick={() => onViewDetail && onViewDetail(reel)}
      className={`group cursor-pointer relative rounded-2xl overflow-hidden border transition-all duration-300 hover:scale-[1.02] hover:shadow-xl ${reel.is_spike ? 'border-orange-500/40 hover:border-orange-400/60 shadow-orange-500/10' : 'border-slate-700/50 hover:border-purple-500/40 shadow-purple-500/5'}`}
    >
      {/* Spike badge */}
      {reel.is_spike && (
        <div className={`absolute top-2 left-2 z-10 px-2 py-0.5 rounded-full text-[10px] font-bold border ${surge_level_badge(reel.surge_level)}`}>
          {reel.surge_level || '⚡ Spike'}
        </div>
      )}

      {/* Thumbnail */}
      <div className="relative aspect-[9/16] bg-slate-800 overflow-hidden">
        <img
          src={reel.thumbnail_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=711&fit=crop'}
          alt="reel"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={e => { e.target.src = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=711&fit=crop'; }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />

        {/* Milestone badge */}
        {reel.milestone_badge && (
          <div className="absolute top-2 right-2 text-[10px] font-bold bg-black/60 backdrop-blur-sm px-2 py-0.5 rounded-full text-yellow-300 border border-yellow-500/30">
            {reel.milestone_badge}
          </div>
        )}

        {/* Bottom info */}
        <div className="absolute bottom-0 left-0 right-0 p-3">
          {/* Creator */}
          <div className="flex items-center gap-1.5 mb-1.5">
            <img
              src={reel.creator_avatar || `https://api.dicebear.com/7.x/identicon/svg?seed=${reel.creator_username}`}
              alt=""
              className="w-5 h-5 rounded-full border border-white/30"
              onError={e => { e.target.src = `https://api.dicebear.com/7.x/identicon/svg?seed=${reel.creator_username}`; }}
            />
            <span className="text-xs text-white font-semibold">@{reel.creator_username}</span>
            <span className="text-[10px] text-slate-400 ml-auto">{reel.time_ago}</span>
          </div>

          <p className="text-[11px] text-slate-300 line-clamp-2 mb-2">{reel.caption || 'Trending reel'}</p>

          {/* Metrics row */}
          <div className="flex items-center gap-3 text-[11px]">
            <span className="flex items-center gap-0.5 text-white font-bold">
              <Eye className="w-3 h-3 text-blue-400" />
              {formatNumber(reel.current_views)}
            </span>
            <span className="flex items-center gap-0.5 text-rose-400">
              <Heart className="w-3 h-3" />
              {formatNumber(reel.current_likes)}
            </span>
            {reel.is_spike && (
              <span className={`flex items-center gap-0.5 font-bold ml-auto ${getSurgeColor(reel.surge_level)}`}>
                <TrendingUp className="w-3 h-3" />
                {formatVelocity(reel.current_growth_velocity)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main CompetitorTracker Component ─────────────────────────────────────────

export default function CompetitorTracker() {
  const [tab, setTab] = useState('reels'); // 'reels' | 'alerts' | 'manage'
  const [competitors, setCompetitors] = useState([]);
  const [reels, setReels] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  const [timeframe, setTimeframe] = useState('all');
  const [minViews, setMinViews] = useState(0);
  const [selectedCompetitor, setSelectedCompetitor] = useState('all');
  const [sortBy, setSortBy] = useState('views');

  const [loading, setLoading] = useState(true);
  const [reelsLoading, setReelsLoading] = useState(false);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [scrapingId, setScrapingId] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [toast, setToast] = useState('');

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3500);
  };

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const [comps, suggs, statsData] = await Promise.all([
          fetchCompetitors(),
          fetchCompetitorSuggestions(),
          fetchCompetitorStats().catch(() => null),
        ]);
        setCompetitors(comps);
        setSuggestions(suggs);
        if (statsData) setStats(statsData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // Load reels when filters change
  const loadReels = useCallback(async () => {
    try {
      setReelsLoading(true);
      const data = await fetchCompetitorReels({
        timeframe,
        minViews,
        competitor: selectedCompetitor !== 'all' ? selectedCompetitor : null,
        sortBy,
        limit: 50,
      });
      setReels(data);
    } catch (err) {
      console.error(err);
    } finally {
      setReelsLoading(false);
    }
  }, [timeframe, minViews, selectedCompetitor, sortBy]);

  useEffect(() => {
    if (tab === 'reels') loadReels();
  }, [tab, loadReels]);

  // Load spike alerts
  const loadAlerts = useCallback(async () => {
    try {
      setAlertsLoading(true);
      const data = await fetchSpikeAlerts();
      setAlerts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === 'alerts') loadAlerts();
  }, [tab, loadAlerts]);

  const handleAddCompetitor = async (payload) => {
    const newComp = await addCompetitor(payload);
    const refreshed = await fetchCompetitors();
    setCompetitors(refreshed);
    const statsData = await fetchCompetitorStats().catch(() => null);
    if (statsData) setStats(statsData);
    showToast(`✅ @${payload.username} added to competitor tracking!`);
    if (tab === 'reels') await loadReels();
  };

  const handleRemoveCompetitor = async (id) => {
    await removeCompetitor(id);
    const refreshed = await fetchCompetitors();
    setCompetitors(refreshed);
    showToast('Competitor removed successfully.');
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    try {
      const result = await scrapeAllCompetitors();
      const [comps, statsData] = await Promise.all([fetchCompetitors(), fetchCompetitorStats().catch(() => null)]);
      setCompetitors(comps);
      if (statsData) setStats(statsData);
      if (tab === 'reels') await loadReels();
      if (tab === 'alerts') await loadAlerts();
      showToast(`🔥 Synced real-time reels for ${result.competitors_count} competitors!`);
    } catch (err) {
      showToast('⚠️ Sync error: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleScrapeSingle = async (id) => {
    setScrapingId(id);
    try {
      const result = await scrapeSingleCompetitor(id);
      const comps = await fetchCompetitors();
      setCompetitors(comps);
      if (tab === 'reels') await loadReels();
      showToast(`✅ Synced @${result.username}: ${result.reels_ingested} new reels ingested!`);
    } catch (err) {
      showToast('⚠️ Sync error: ' + err.message);
    } finally {
      setScrapingId(null);
    }
  };

  const alertsCount = alerts.length;

  return (
    <div className="min-h-full">
      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-2 text-sm font-semibold border border-purple-400/30 animate-bounce">
          <Sparkles className="w-4 h-4" />
          <span>{toast}</span>
        </div>
      )}

      {/* Add Competitor Modal */}
      {showAddModal && (
        <AddCompetitorModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddCompetitor}
          suggestions={suggestions}
        />
      )}

      {/* ─── Stats Header Bar ─────────────────────────────────── */}
      <div className="bg-gradient-to-r from-slate-900/90 to-slate-800/50 border-b border-slate-800/80 px-4 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-400" />
                Competitor Tracker
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-1">
                  <Radio className="w-3 h-3" /> Live
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">Monitor real-time reel performance of your tracked competitors</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSyncAll}
                disabled={syncing}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-300 text-sm font-semibold transition disabled:opacity-60"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync All'}
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-sm font-semibold transition shadow-lg shadow-purple-600/25"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Creator
              </button>
            </div>
          </div>

          {/* Stats overview */}
          {stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Tracked Creators', value: stats.total_competitors, icon: Users, color: 'text-purple-400' },
                { label: 'Reels Tracked', value: formatNumber(stats.total_reels_tracked), icon: BarChart3, color: 'text-blue-400' },
                { label: 'Avg Views / Reel', value: formatNumber(stats.avg_views_overall), icon: Eye, color: 'text-emerald-400' },
                { label: 'Active Spikes 🔥', value: stats.active_spikes_count, icon: Flame, color: 'text-red-400' },
              ].map(({ label, value, icon: Icon, color }) => (
                <div key={label} className="bg-slate-900/60 border border-slate-800/60 rounded-2xl px-4 py-3 flex items-center gap-3">
                  <Icon className={`w-5 h-5 ${color} shrink-0`} />
                  <div>
                    <p className="text-[11px] text-slate-500">{label}</p>
                    <p className="text-lg font-bold text-white leading-tight">{value ?? '—'}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─── Tab Navigation ───────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 pt-4">
        <div className="flex items-center bg-slate-900/60 p-1.5 rounded-2xl border border-slate-800 w-fit mb-6">
          {[
            { id: 'reels', label: 'Content Feed', icon: Play },
            { id: 'alerts', label: `Spike Alerts${alertsCount > 0 ? ` (${alertsCount})` : ''}`, icon: BellDot },
            { id: 'manage', label: `Manage (${competitors.length})`, icon: Users },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 whitespace-nowrap ${tab === id ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/30' : 'text-slate-400 hover:text-slate-200'}`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* ─── CONTENT FEED TAB ─────────────────────────────── */}
        {tab === 'reels' && (
          <div>
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3 mb-6 p-4 bg-slate-900/40 border border-slate-800/60 rounded-2xl">
              <div className="flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-xs text-slate-500 font-medium">Filters:</span>
              </div>

              {/* Timeframe */}
              <div className="flex items-center gap-1 bg-slate-800/80 rounded-xl p-1">
                {TIMEFRAME_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setTimeframe(opt.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${timeframe === opt.value ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* View Threshold */}
              <select
                value={minViews}
                onChange={e => setMinViews(Number(e.target.value))}
                className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-purple-500 transition"
              >
                {VIEW_THRESHOLD_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>

              {/* Creator Filter */}
              <select
                value={selectedCompetitor}
                onChange={e => setSelectedCompetitor(e.target.value)}
                className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-purple-500 transition"
              >
                <option value="all">All Creators</option>
                {competitors.map(c => (
                  <option key={c.id} value={c.username}>@{c.username}</option>
                ))}
              </select>

              {/* Sort */}
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
                className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-purple-500 transition"
              >
                {SORT_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>

              <button
                onClick={loadReels}
                className="px-3 py-2 rounded-xl bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs font-semibold hover:bg-indigo-600/40 transition"
              >
                Apply Filters
              </button>
            </div>

            {/* Reels Grid */}
            {reelsLoading ? (
              <div className="flex items-center justify-center py-24">
                <div className="flex flex-col items-center gap-3">
                  <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
                  <p className="text-slate-400 text-sm">Loading competitor reels...</p>
                </div>
              </div>
            ) : reels.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-800/60 flex items-center justify-center mb-4">
                  <Target className="w-8 h-8 text-slate-600" />
                </div>
                <p className="text-slate-400 font-semibold mb-1">No reels found</p>
                <p className="text-slate-500 text-sm max-w-sm">Add competitors and sync real-time data to see their content feed here.</p>
                <button onClick={() => setShowAddModal(true)} className="mt-4 px-4 py-2 rounded-xl bg-purple-600/20 border border-purple-500/30 text-purple-300 text-sm font-semibold transition hover:bg-purple-600/30">
                  + Add Your First Competitor
                </button>
              </div>
            ) : (
              <>
                <p className="text-xs text-slate-500 mb-3">{reels.length} reels from tracked competitors</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 pb-8">
                  {reels.map(reel => (
                    <CompetitorReelCard key={reel.id} reel={reel} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* ─── SPIKE ALERTS TAB ─────────────────────────────── */}
        {tab === 'alerts' && (
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <BellDot className="w-4 h-4 text-red-400 animate-pulse" />
                  Real-Time Spike Alerts
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">Reels from tracked competitors experiencing rapid surges in views</p>
              </div>
              <button
                onClick={loadAlerts}
                disabled={alertsLoading}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 text-xs font-medium hover:border-purple-500/50 transition"
              >
                <RefreshCw className={`w-3 h-3 ${alertsLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>

            {alertsLoading ? (
              <div className="flex items-center justify-center py-24">
                <div className="flex flex-col items-center gap-3">
                  <RefreshCw className="w-8 h-8 text-orange-400 animate-spin" />
                  <p className="text-slate-400 text-sm">Scanning for real-time spikes...</p>
                </div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-800/60 flex items-center justify-center mb-4">
                  <Bell className="w-8 h-8 text-slate-600" />
                </div>
                <p className="text-slate-400 font-semibold mb-1">No active spikes detected</p>
                <p className="text-slate-500 text-sm max-w-sm">Spike alerts appear here when a tracked competitor's reel crosses 500K+ views or gains 25K+ views per hour.</p>
                <button onClick={handleSyncAll} className="mt-4 px-4 py-2 rounded-xl bg-orange-600/20 border border-orange-500/30 text-orange-300 text-sm font-semibold transition hover:bg-orange-600/30">
                  Sync Now to Scan for Spikes
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-8">
                {alerts.map((alert, i) => (
                  <SpikeAlertCard key={`${alert.reel_id}-${i}`} alert={alert} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── MANAGE COMPETITORS TAB ───────────────────────── */}
        {tab === 'manage' && (
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Users className="w-4 h-4 text-purple-400" />
                  Tracked Creators
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">Add or remove creators to monitor their real-time performance</p>
              </div>
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold transition hover:from-purple-500 hover:to-indigo-500"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Creator
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-24">
                <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
              </div>
            ) : competitors.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600/20 to-indigo-600/20 border border-purple-500/30 flex items-center justify-center mb-4">
                  <UserPlus className="w-8 h-8 text-purple-400" />
                </div>
                <p className="text-slate-300 font-semibold mb-1">No competitors added yet</p>
                <p className="text-slate-500 text-sm max-w-sm">Start tracking your competitors' real-time reel performance by adding their Instagram usernames.</p>
                <button onClick={() => setShowAddModal(true)} className="mt-4 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold transition hover:from-purple-500 hover:to-indigo-500">
                  + Add Your First Competitor
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-8">
                {competitors.map(comp => (
                  <CompetitorCard
                    key={comp.id}
                    comp={comp}
                    onRemove={handleRemoveCompetitor}
                    onScrape={handleScrapeSingle}
                    isScraping={scrapingId === comp.id}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
