import React from 'react';
import { 
  Sparkles, 
  Cpu, 
  Globe, 
  Blocks, 
  Layers, 
  Database, 
  RefreshCw, 
  ShieldCheck, 
  Flame, 
  Laptop 
} from 'lucide-react';

const CATEGORY_ICONS = {
  niche: Laptop,
  ai: Cpu,
  other: Globe,
  blockchain: Blocks,
};

export default function Header({
  categories,
  selectedCategory,
  onSelectCategory,
  activeDataSource,
  onOpenDataSources,
  onSyncCurrent,
  isSyncing,
}) {
  return (
    <header className="sticky top-0 z-40 bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 py-2">
          
          {/* Brand Logo & Name */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-rose-500 to-purple-600 p-[2px] shadow-lg shadow-rose-500/20 shrink-0">
              <div className="w-full h-full bg-[#0B0F19] rounded-[10px] flex items-center justify-center">
                <Flame className="w-5 h-5 text-rose-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-rose-400 via-purple-300 to-indigo-300 bg-clip-text text-transparent">
                  ReelsPulse
                </span>
                <span className="text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1">
                  <span>South Asia</span>
                  <span>🇮🇳 🇧🇩 🇳🇵</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden lg:block">
                India • Bangladesh • Nepal Velocity Engine
              </p>
            </div>
          </div>

          {/* Center Category Switcher */}
          <div className="flex items-center bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800/90 shadow-inner overflow-x-auto max-w-[60vw] md:max-w-none">
            {categories.map((cat) => {
              const Icon = CATEGORY_ICONS[cat.slug] || Layers;
              const isSelected = selectedCategory?.slug === cat.slug;
              
              return (
                <button
                  key={cat.id}
                  onClick={() => onSelectCategory(cat)}
                  className={`relative flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                    isSelected
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/30 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                  <span>{cat.name}</span>
                  <span
                    className={`ml-1 text-[11px] px-1.5 py-0.2 rounded-md ${
                      isSelected
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {cat.total_reels}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Right Action Tools: Data Source & Sync */}
          <div className="flex items-center gap-2.5">
            {/* Compliance Badge & Source Selector */}
            <button
              onClick={onOpenDataSources}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white transition group"
              title="Manage compliant data source and API settings"
            >
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <span className="hidden xl:inline font-medium">
                {activeDataSource ? activeDataSource.name.split(' ')[0] : 'Data Source'}
              </span>
              <Database className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400 transition" />
            </button>

            {/* Sync Button */}
            <button
              onClick={onSyncCurrent}
              disabled={isSyncing}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-300 hover:text-white text-xs font-semibold transition ${
                isSyncing ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-purple-400' : ''}`} />
              <span className="hidden sm:inline">{isSyncing ? 'Syncing...' : 'Sync Feed'}</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
