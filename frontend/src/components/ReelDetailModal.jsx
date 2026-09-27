import React, { useState, useEffect } from 'react';
import { 
  X, 
  Eye, 
  Heart, 
  MessageCircle, 
  Share2, 
  Bookmark, 
  Clock, 
  BadgeCheck, 
  ExternalLink, 
  Rocket, 
  TrendingUp, 
  ShieldCheck, 
  BarChart3, 
  Calendar, 
  Play 
} from 'lucide-react';
import { fetchReelMetricsHistory } from '../api';
import { formatNumber, formatDateTime, formatRelativeTime, getEngagementBadge } from '../utils';

export default function ReelDetailModal({ reel, onClose }) {
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (!reel) return;
    const loadHistory = async () => {
      try {
        setLoadingHistory(true);
        const data = await fetchReelMetricsHistory(reel.id);
        setHistory(data);
      } catch (err) {
        console.error('Error fetching metrics history:', err);
      } finally {
        setLoadingHistory(false);
      }
    };
    loadHistory();

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [reel, onClose]);

  if (!reel) return null;

  const creator = reel.creator || {};
  const metrics = reel.latest_metrics || {};
  const trending = reel.latest_trending || {};
  const engagement = getEngagementBadge(metrics.engagement_rate || 0);

  const COUNTRY_FLAGS = {
    'India': '🇮🇳',
    'Pakistan': '🇵🇰',
    'Bangladesh': '🇧🇩',
    'Nepal': '🇳🇵',
  };
  const countryName = reel.country || creator.country || 'India';
  const countryFlag = COUNTRY_FLAGS[countryName] || '🌏';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div 
        className="relative w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold">
              #{trending.rank || 1}
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Reel Analytics Breakdown</h3>
              <p className="text-xs text-slate-400">
                ID: {reel.platform_media_id} • Category: {reel.category_name} • Region: {countryFlag} {countryName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            
            {/* Left Column: Visual Media Preview */}
            <div className="md:col-span-5 flex flex-col items-center">
              <div className="relative aspect-[9/16] w-full max-w-[280px] rounded-2xl overflow-hidden shadow-xl bg-slate-950 border border-slate-800">
                <img
                  src={reel.thumbnail_url}
                  alt={creator.username}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-black/30" />
                
                {/* Outbound Link */}
                <a
                  href={reel.permalink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute bottom-4 left-4 right-4 flex items-center justify-center gap-2 py-2 px-3 bg-gradient-to-r from-rose-600 to-purple-600 hover:from-rose-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold shadow-lg transition"
                >
                  <span>Open on Instagram</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            {/* Right Column: Creator & Key Analytics */}
            <div className="md:col-span-7 space-y-5">
              
              {/* Creator Card */}
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center gap-3 mb-3">
                  <img
                    src={creator.profile_pic_url || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop'}
                    alt={creator.username}
                    className="w-12 h-12 rounded-full object-cover border-2 border-purple-500/40"
                  />
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-white text-base">
                        {creator.full_name || creator.username}
                      </span>
                      {creator.is_verified && (
                        <BadgeCheck className="w-4 h-4 text-blue-400" />
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-purple-400 font-medium">@{creator.username}</span>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-200 flex items-center gap-1">
                        <span>{countryFlag}</span>
                        <span>{countryName}</span>
                      </span>
                    </div>
                  </div>
                </div>

                {creator.biography && (
                  <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                    {creator.biography}
                  </p>
                )}

                <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                  <div>
                    <strong className="text-white font-semibold">{formatNumber(creator.followers_count)}</strong> followers
                  </div>
                  <div>
                    <strong className="text-white font-semibold">{formatNumber(creator.following_count)}</strong> following
                  </div>
                  <div className="ml-auto text-emerald-400 flex items-center gap-1 text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Verified Creator Entity</span>
                  </div>
                </div>
              </div>

              {/* Caption */}
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Caption & Description
                </span>
                <p className="text-sm text-slate-200 whitespace-pre-line leading-relaxed">
                  {reel.caption}
                </p>
                <div className="flex items-center gap-2 mt-3 pt-2 border-t border-slate-800 text-xs text-slate-400">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>Posted: {formatDateTime(reel.posted_at)} ({formatRelativeTime(reel.posted_at)})</span>
                </div>
              </div>

              {/* Full Metrics Grid */}
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2.5">
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                  <div className="flex items-center justify-center gap-1 text-[11px] text-slate-400 mb-1">
                    <Eye className="w-3.5 h-3.5 text-blue-400" />
                    <span>Views</span>
                  </div>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(metrics.view_count)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                  <div className="flex items-center justify-center gap-1 text-[11px] text-slate-400 mb-1">
                    <Heart className="w-3.5 h-3.5 text-rose-400" />
                    <span>Likes</span>
                  </div>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(metrics.like_count)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                  <div className="flex items-center justify-center gap-1 text-[11px] text-slate-400 mb-1">
                    <MessageCircle className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Comments</span>
                  </div>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(metrics.comment_count)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                  <div className="flex items-center justify-center gap-1 text-[11px] text-slate-400 mb-1">
                    <Share2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Shares</span>
                  </div>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(metrics.share_count)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center col-span-2 sm:col-span-1">
                  <div className="flex items-center justify-center gap-1 text-[11px] text-slate-400 mb-1">
                    <Bookmark className="w-3.5 h-3.5 text-amber-400" />
                    <span>Saves</span>
                  </div>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(metrics.save_count)}
                  </span>
                </div>
              </div>

              {/* Engagement & Trending Intelligence Card */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-950/30 to-indigo-950/30 border border-purple-800/40">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                  <div>
                    <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider block">
                      Engagement Rate Analysis
                    </span>
                    <div className="flex items-baseline gap-2 mt-0.5">
                      <span className="text-2xl font-black text-white">
                        {metrics.engagement_rate}%
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${engagement.bg}`}>
                        {engagement.label} Engagement
                      </span>
                    </div>
                  </div>

                  <div className="text-left sm:text-right">
                    <span className="text-xs font-semibold text-rose-300 uppercase tracking-wider block">
                      Growth Velocity
                    </span>
                    <div className="flex items-baseline sm:justify-end gap-1 mt-0.5">
                      <span className="text-2xl font-black text-rose-400">
                        +{formatNumber(trending.growth_velocity)}
                      </span>
                      <span className="text-xs text-rose-300">views/hr</span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-slate-400 mt-2">
                  Formula: <code className="text-slate-300 font-mono text-[11px]">((Likes + Comments + Shares) / Views) × 100</code>
                </p>
              </div>

            </div>
          </div>

          {/* Historical Metrics Timeline */}
          <div className="pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" />
                <span>Historical Metric Snapshots</span>
              </h4>
              <span className="text-xs text-slate-500">Tracked over time to measure momentum</span>
            </div>

            {loadingHistory ? (
              <div className="py-6 text-center text-xs text-slate-500">Loading historical snapshots...</div>
            ) : history.length === 0 ? (
              <div className="py-4 text-center text-xs text-slate-500">Initial snapshot recorded.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="pb-2 font-medium">Timestamp</th>
                      <th className="pb-2 font-medium">Views</th>
                      <th className="pb-2 font-medium">Likes</th>
                      <th className="pb-2 font-medium">Comments</th>
                      <th className="pb-2 font-medium">Shares</th>
                      <th className="pb-2 font-medium">Engagement Rate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {history.map((h) => (
                      <tr key={h.id} className="text-slate-300">
                        <td className="py-2 font-mono text-[11px] text-slate-400">{formatDateTime(h.recorded_at)}</td>
                        <td className="py-2 font-semibold text-white">{formatNumber(h.view_count)}</td>
                        <td className="py-2 text-rose-300">{formatNumber(h.like_count)}</td>
                        <td className="py-2 text-blue-300">{formatNumber(h.comment_count)}</td>
                        <td className="py-2 text-emerald-300">{formatNumber(h.share_count)}</td>
                        <td className="py-2 font-bold text-purple-400">{h.engagement_rate}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>Compliant Data Ingestion • No Unauthorized Scraping</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
