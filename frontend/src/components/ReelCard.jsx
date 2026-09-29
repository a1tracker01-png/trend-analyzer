import React from 'react';
import { 
  Eye, 
  Heart, 
  MessageCircle, 
  Share2, 
  Bookmark, 
  Clock, 
  BadgeCheck, 
  ExternalLink, 
  Rocket, 
  Play, 
  TrendingUp 
} from 'lucide-react';
import { formatNumber, formatRelativeTime, formatDateTime, getEngagementBadge } from '../utils';

export default function ReelCard({ reel, rank, onSelect }) {
  const creator = reel.creator || {};
  const metrics = reel.latest_metrics || {};
  const trending = reel.latest_trending || {};
  const engagement = getEngagementBadge(metrics.engagement_rate || 0);

  // Rank badge styling
  const isPodium = rank <= 3;
  const podiumStyles = {
    1: 'bg-gradient-to-r from-amber-400 to-yellow-500 text-slate-950 font-black shadow-amber-500/30',
    2: 'bg-gradient-to-r from-slate-200 to-slate-400 text-slate-950 font-black shadow-slate-400/30',
    3: 'bg-gradient-to-r from-amber-600 to-amber-700 text-white font-black shadow-amber-700/30',
  };

  const COUNTRY_FLAGS = {
    'India': '🇮🇳',
    'Bangladesh': '🇧🇩',
    'Nepal': '🇳🇵',
  };
  const rawCountry = reel.country || creator.country || 'India';
  const countryName = rawCountry === 'Pakistan' ? 'India' : rawCountry;
  const countryFlag = COUNTRY_FLAGS[countryName] || '🌏';

  return (
    <div 
      onClick={() => onSelect(reel)}
      className="group relative cursor-pointer bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800/80 hover:border-purple-500/50 rounded-2xl overflow-hidden transition-all duration-300 shadow-md hover:shadow-purple-500/10 hover:-translate-y-1 flex flex-col justify-between"
    >
      {/* 9:16 Media Container Preview */}
      <div className="relative aspect-[9/14] w-full overflow-hidden bg-slate-950">
        <img
          src={reel.thumbnail_url}
          alt={creator.username}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />

        {/* Gradient Shadow Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-slate-950/40" />

        {/* Top Badges: Rank & Velocity */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          {/* Rank & Country Badge */}
          <div className="flex items-center gap-1.5">
            <div className={`px-2.5 py-0.5 rounded-full text-xs shadow-md ${
              isPodium ? podiumStyles[rank] : 'bg-slate-900/90 text-slate-200 border border-slate-700 font-bold'
            }`}>
              #{rank}
            </div>
            <div className="px-2 py-0.5 rounded-full bg-slate-900/90 text-slate-200 border border-slate-700/80 text-[11px] font-bold shadow-md flex items-center gap-1 backdrop-blur-sm">
              <span>{countryFlag}</span>
              <span className="text-[10px] text-slate-300 hidden sm:inline">{countryName}</span>
            </div>
          </div>

          {/* Growth Velocity Surge Pill */}
          {trending.growth_velocity > 0 && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-600/90 text-white text-[11px] font-bold shadow-md backdrop-blur-sm">
              <Rocket className="w-3 h-3" />
              <span>+{formatNumber(trending.growth_velocity)}/h</span>
            </div>
          )}
        </div>

        {/* Play Icon on Hover */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="w-12 h-12 rounded-full bg-purple-600/90 text-white flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform">
            <Play className="w-5 h-5 fill-current ml-0.5" />
          </div>
        </div>

        {/* Posting Time & Duration Overlay */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[11px] text-slate-300 pointer-events-none">
          <div 
            className="flex items-center gap-1 bg-slate-900/80 px-2 py-0.5 rounded-md backdrop-blur-sm border border-slate-800"
            title={`Posted on ${formatDateTime(reel.posted_at)}`}
          >
            <Clock className="w-3 h-3 text-slate-400" />
            <span>{formatRelativeTime(reel.posted_at)}</span>
          </div>

          {reel.duration > 0 && (
            <span className="bg-black/60 px-1.5 py-0.5 rounded backdrop-blur-sm font-semibold">
              {Math.round(reel.duration)}s
            </span>
          )}
        </div>

      </div>

      {/* Card Content & Details */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        
        <div>
          {/* Creator Information */}
          <div className="flex items-center justify-between gap-2 mb-2.5">
            <div className="flex items-center gap-2 min-w-0">
              <img
                src={creator.profile_pic_url || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop'}
                alt={creator.username}
                className="w-7 h-7 rounded-full object-cover border border-purple-500/30 shrink-0"
              />
              <div className="min-w-0">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-bold text-white truncate hover:underline">
                    @{creator.username}
                  </span>
                  {creator.is_verified && (
                    <BadgeCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  )}
                  <span className="text-[11px] shrink-0" title={`Region: ${countryName}`}>
                    {countryFlag}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 block truncate">
                  {formatNumber(creator.followers_count)} followers • {countryName}
                </span>
              </div>
            </div>

            {/* External Reel Link */}
            <a
              href={reel.permalink}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-slate-500 hover:text-purple-400 p-1 rounded-lg hover:bg-slate-800 transition shrink-0"
              title="View on Instagram"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Caption Snippet */}
          <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-3">
            {reel.caption}
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="pt-3 border-t border-slate-800/80">
          <div className="grid grid-cols-4 gap-1 text-center mb-3">
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-1 text-[11px] text-slate-400">
                <Eye className="w-3 h-3 text-slate-400" />
              </div>
              <span className="text-xs font-bold text-white">
                {formatNumber(metrics.view_count)}
              </span>
            </div>

            <div className="flex flex-col items-center">
              <div className="flex items-center gap-1 text-[11px] text-slate-400">
                <Heart className="w-3 h-3 text-rose-400" />
              </div>
              <span className="text-xs font-bold text-white">
                {formatNumber(metrics.like_count)}
              </span>
            </div>

            <div className="flex flex-col items-center">
              <div className="flex items-center gap-1 text-[11px] text-slate-400">
                <MessageCircle className="w-3 h-3 text-blue-400" />
              </div>
              <span className="text-xs font-bold text-white">
                {formatNumber(metrics.comment_count)}
              </span>
            </div>

            <div className="flex flex-col items-center">
              <div className="flex items-center gap-1 text-[11px] text-slate-400">
                <Share2 className="w-3 h-3 text-emerald-400" />
              </div>
              <span className="text-xs font-bold text-white">
                {formatNumber(metrics.share_count)}
              </span>
            </div>
          </div>

          {/* Footer Badge: Engagement Rate & Popularity Score */}
          <div className="flex items-center justify-between text-xs pt-1">
            <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${engagement.bg}`}>
              {metrics.engagement_rate}% Eng.
            </span>

            <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-purple-400" />
              Score: <strong className="text-slate-200">{formatNumber(trending.score)}</strong>
            </span>
          </div>

        </div>

      </div>

    </div>
  );
}
