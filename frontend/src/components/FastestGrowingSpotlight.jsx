import React from 'react';
import { 
  Rocket, 
  Flame, 
  Clock, 
  Eye, 
  Heart, 
  MessageCircle, 
  Share2, 
  BadgeCheck, 
  ExternalLink, 
  TrendingUp, 
  Play 
} from 'lucide-react';
import { formatNumber, formatRelativeTime, getEngagementBadge } from '../utils';

export default function FastestGrowingSpotlight({ reels, onSelectReel }) {
  if (!reels || reels.length === 0) return null;

  // Take top 3 fastest growing
  const topFastest = reels.slice(0, 3);

  return (
    <div className="mb-10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center">
            <Rocket className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Fastest Growing Reels
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                Surging Velocity 🔥
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Content gaining views and engagement at the highest rate per hour
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {topFastest.map((reel, index) => {
          const metrics = reel.latest_metrics || {};
          const trending = reel.latest_trending || {};
          const creator = reel.creator || {};
          const engagement = getEngagementBadge(metrics.engagement_rate || 0);

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
              key={reel.id}
              onClick={() => onSelectReel(reel)}
              className="group relative cursor-pointer overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800/90 hover:border-rose-500/50 transition-all duration-300 shadow-lg hover:shadow-rose-500/10 hover:-translate-y-1 flex flex-col"
            >
              {/* Top Image Preview Banner */}
              <div className="relative aspect-[16/10] overflow-hidden bg-slate-950">
                <img
                  src={reel.thumbnail_url}
                  alt={creator.username}
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/30 to-transparent" />
                
                {/* Velocity Surge Badge */}
                <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-600/90 text-white text-xs font-bold shadow-md shadow-rose-950/50 backdrop-blur-sm">
                  <Rocket className="w-3.5 h-3.5" />
                  <span>+{formatNumber(trending.growth_velocity)} / hr</span>
                </div>

                {/* Rank Badge */}
                <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-slate-900/80 border border-white/20 text-white text-xs font-extrabold flex items-center justify-center backdrop-blur-sm">
                  #{index + 1}
                </div>

                {/* Play Button Overlay */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="w-12 h-12 rounded-full bg-rose-600/90 text-white flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform">
                    <Play className="w-5 h-5 fill-current ml-0.5" />
                  </div>
                </div>

                {/* Posting Time Pill */}
                <div className="absolute bottom-3 left-3 flex items-center gap-1 text-[11px] font-medium text-slate-300 bg-slate-900/80 px-2 py-0.5 rounded-md backdrop-blur-sm border border-slate-800">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <span>{formatRelativeTime(reel.posted_at)}</span>
                </div>

                {/* Duration */}
                {reel.duration > 0 && (
                  <div className="absolute bottom-3 right-3 text-[11px] font-semibold text-slate-200 bg-black/60 px-1.5 py-0.5 rounded backdrop-blur-sm">
                    {Math.round(reel.duration)}s
                  </div>
                )}
              </div>

              {/* Card Body */}
              <div className="p-4 flex-1 flex flex-col justify-between">
                <div>
                  {/* Creator Info */}
                  <div className="flex items-center gap-2.5 mb-2">
                    <img
                      src={creator.profile_pic_url || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop'}
                      alt={creator.username}
                      className="w-8 h-8 rounded-full object-cover border border-purple-500/40"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="text-sm font-semibold text-white truncate">
                          @{creator.username}
                        </span>
                        {creator.is_verified && (
                          <BadgeCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                        )}
                        <span className="text-xs shrink-0" title={`Region: ${countryName}`}>
                          {countryFlag}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {formatNumber(creator.followers_count)} followers • {countryName}
                      </span>
                    </div>
                  </div>

                  {/* Caption preview */}
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-3">
                    {reel.caption}
                  </p>
                </div>

                {/* Metrics Footer */}
                <div className="pt-3 border-t border-slate-800/80">
                  <div className="grid grid-cols-4 gap-1 text-center mb-2.5 text-slate-300">
                    <div className="flex flex-col items-center">
                      <div className="flex items-center gap-1 text-[11px] text-slate-400">
                        <Eye className="w-3 h-3" />
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

                  <div className="flex items-center justify-between text-xs">
                    <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${engagement.bg}`}>
                      {metrics.engagement_rate}% Eng.
                    </span>
                    <span className="text-purple-400 font-semibold group-hover:translate-x-0.5 transition-transform flex items-center gap-1 text-[11px]">
                      Analyze Details →
                    </span>
                  </div>
                </div>

              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}
