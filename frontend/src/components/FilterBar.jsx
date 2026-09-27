import React from 'react';
import { 
  Clock, 
  Rocket, 
  Trophy, 
  LayoutGrid, 
  Search, 
  ArrowUpDown, 
  SlidersHorizontal 
} from 'lucide-react';

const FILTER_TABS = [
  { id: 'last_24h', label: 'Last 24 Hours', icon: Clock, badge: 'Fresh' },
  { id: 'fastest_growing', label: 'Fastest Growing', icon: Rocket, badge: 'Surge' },
  { id: 'top_100', label: 'Top 100 Leaderboard', icon: Trophy, badge: 'Ranked' },
  { id: 'all', label: 'All Reels', icon: LayoutGrid },
];

const SORT_OPTIONS = [
  { value: 'trending', label: 'Popularity Score' },
  { value: 'velocity', label: 'Growth Velocity' },
  { value: 'views', label: 'Total Views' },
  { value: 'likes', label: 'Likes' },
  { value: 'comments', label: 'Comments' },
  { value: 'engagement', label: 'Engagement Rate' },
  { value: 'newest', label: 'Newest First' },
];

const REGION_TABS = [
  { id: 'all', label: 'All Regions', flag: '🌏', code: 'IN • PK • BD • NP' },
  { id: 'India', label: 'India', flag: '🇮🇳' },
  { id: 'Pakistan', label: 'Pakistan', flag: '🇵🇰' },
  { id: 'Bangladesh', label: 'Bangladesh', flag: '🇧🇩' },
  { id: 'Nepal', label: 'Nepal', flag: '🇳🇵' },
];

export default function FilterBar({
  activeFilter,
  onChangeFilter,
  selectedCountry,
  onChangeCountry,
  sortBy,
  onChangeSort,
  searchTerm,
  onChangeSearch,
  totalItems
}) {
  return (
    <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-3 sm:p-4 mb-6 backdrop-blur-md shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        
        {/* Navigation Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {FILTER_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeFilter === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => onChangeFilter(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-800 text-purple-400 border border-purple-500/20'
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Search & Sort Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
          
          {/* Search Input */}
          <div className="relative min-w-[220px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search captions or creators..."
              value={searchTerm}
              onChange={(e) => onChangeSearch(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-800/90 rounded-xl pl-9 pr-3 py-1.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500/70 transition"
            />
            {searchTerm && (
              <button
                onClick={() => onChangeSearch('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
              >
                ×
              </button>
            )}
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-800/90 rounded-xl px-3 py-1.5">
            <ArrowUpDown className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="text-xs text-slate-400 hidden sm:inline">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => onChangeSort(e.target.value)}
              className="bg-transparent text-xs sm:text-sm text-slate-200 font-medium focus:outline-none cursor-pointer pr-1"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-slate-900 text-slate-200">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

        </div>

      </div>

      {/* South Asian Country Selector Row */}
      <div className="flex items-center gap-1.5 pt-3 mt-3 border-t border-slate-800/60 overflow-x-auto pb-0.5">
        <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1 shrink-0">
          <span>Region:</span>
        </span>
        {REGION_TABS.map((r) => {
          const isSelected = (selectedCountry || 'all') === r.id;
          return (
            <button
              key={r.id}
              onClick={() => onChangeCountry && onChangeCountry(r.id)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-semibold transition shrink-0 ${
                isSelected
                  ? 'bg-purple-600/30 text-purple-200 border border-purple-500/50 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <span>{r.flag}</span>
              <span>{r.label}</span>
              {r.code && (
                <span className="text-[10px] text-slate-500 font-normal hidden sm:inline">
                  ({r.code})
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Filter Status Line */}
      <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2 flex-wrap">
          <span>Showing <strong className="text-slate-200">{totalItems}</strong> reels</span>
          {selectedCountry && selectedCountry !== 'all' && (
            <span className="text-purple-400 font-medium">
              • Region: {selectedCountry}
            </span>
          )}
          {activeFilter === 'last_24h' && (
            <span className="text-blue-400 font-medium">• Filtered strictly to posts within the last 24 hours</span>
          )}
          {activeFilter === 'fastest_growing' && (
            <span className="text-rose-400 font-medium">• Ranked by hourly growth velocity and momentum</span>
          )}
          {activeFilter === 'top_100' && (
            <span className="text-amber-400 font-medium">• Top 100 popularity leaderboard</span>
          )}
        </div>
      </div>
    </div>
  );
}
