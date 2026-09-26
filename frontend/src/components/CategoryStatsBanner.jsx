import React from 'react';
import { 
  Film, 
  Clock, 
  Activity, 
  TrendingUp, 
  Eye, 
  Heart, 
  Rocket, 
  Sparkles, 
  CheckCircle2 
} from 'lucide-react';
import { formatNumber } from '../utils';

export default function CategoryStatsBanner({ category, stats }) {
  if (!stats) return null;

  return (
    <div className="mb-8">
      {/* Category Intro */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: category.color || '#8B5CF6' }} 
            />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {category.name} Reels Radar
            </h1>
          </div>
          <p className="text-slate-400 text-sm max-w-2xl">
            {category.description}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800/80 w-fit">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Real-time Popularity & Velocity Decay Algorithm</span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: Total Reels */}
        <div className="relative overflow-hidden bg-slate-900/60 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 hover:border-slate-700/80 transition group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Total Ingested Reels
            </span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Film className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">
              {stats.total_reels}
            </span>
            <span className="text-xs text-slate-400">tracked</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Ranked & indexed with historical metric snapshots
          </p>
        </div>

        {/* Card 2: Last 24 Hours */}
        <div className="relative overflow-hidden bg-slate-900/60 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 hover:border-slate-700/80 transition group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Last 24 Hours Volume
            </span>
            <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-blue-400">
              {stats.reels_last_24h}
            </span>
            <span className="text-xs text-slate-400">new posts</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {stats.total_reels > 0 
              ? `${Math.round((stats.reels_last_24h / stats.total_reels) * 100)}% of content posted today` 
              : 'Fresh feeds monitored'}
          </p>
        </div>

        {/* Card 3: Avg Engagement Rate */}
        <div className="relative overflow-hidden bg-slate-900/60 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 hover:border-slate-700/80 transition group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Avg Engagement Rate
            </span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400">
              {stats.avg_engagement_rate}%
            </span>
            <span className="text-xs text-emerald-500 font-medium">Interactions/Views</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Total Views: <span className="text-slate-300 font-semibold">{formatNumber(stats.total_views)}</span>
          </p>
        </div>

        {/* Card 4: Fastest Growing Velocity */}
        <div className="relative overflow-hidden bg-slate-900/60 backdrop-blur-md border border-rose-500/20 rounded-2xl p-5 hover:border-rose-500/40 transition group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl group-hover:bg-rose-500/20 transition" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-rose-300">
              Peak Growth Velocity
            </span>
            <div className="w-8 h-8 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center">
              <Rocket className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-rose-400">
              +{formatNumber(stats.fastest_growing?.latest_trending?.growth_velocity || 0)}
            </span>
            <span className="text-xs text-rose-300/80 font-medium">views/hr</span>
          </div>
          <p className="text-xs text-slate-400 mt-2 truncate">
            Leader: <span className="text-white font-medium">@{stats.fastest_growing?.creator?.username || 'trending'}</span>
          </p>
        </div>

      </div>
    </div>
  );
}
