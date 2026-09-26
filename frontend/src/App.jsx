import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import CategoryStatsBanner from './components/CategoryStatsBanner';
import FastestGrowingSpotlight from './components/FastestGrowingSpotlight';
import FilterBar from './components/FilterBar';
import ReelCard from './components/ReelCard';
import ReelDetailModal from './components/ReelDetailModal';
import DataSourceModal from './components/DataSourceModal';
import { 
  fetchCategories, 
  fetchCategoryStats, 
  fetchReels, 
  fetchDataSources, 
  triggerSync 
} from './api';
import { 
  AlertCircle, 
  Loader2, 
  Sparkles, 
  Clock, 
  Rocket, 
  Trophy 
} from 'lucide-react';

export default function App() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [categoryStats, setCategoryStats] = useState(null);
  
  const [reels, setReels] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [fastestGrowingReels, setFastestGrowingReels] = useState([]);
  
  const [filterMode, setFilterMode] = useState('last_24h'); // Default to last 24 hours
  const [sortBy, setSortBy] = useState('trending');
  const [searchTerm, setSearchTerm] = useState('');
  
  const [selectedReel, setSelectedReel] = useState(null);
  const [isDataSourcesOpen, setIsDataSourcesOpen] = useState(false);
  const [activeDataSource, setActiveDataSource] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [loadingReels, setLoadingReels] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  // Initial load: Categories and Data Sources
  useEffect(() => {
    const initApp = async () => {
      try {
        setLoading(true);
        const [cats, sources] = await Promise.all([
          fetchCategories(),
          fetchDataSources()
        ]);
        setCategories(cats);
        if (cats.length > 0) {
          // Select Niche or AI initially
          setSelectedCategory(cats[0]);
        }
        const active = sources.find(s => s.is_active);
        setActiveDataSource(active || sources[0]);
      } catch (err) {
        console.error('Initialization error:', err);
      } finally {
        setLoading(false);
      }
    };
    initApp();
  }, []);

  // Fetch Category Stats & Spotlight Fastest Growing
  useEffect(() => {
    if (!selectedCategory) return;

    const loadCategoryData = async () => {
      try {
        const statsData = await fetchCategoryStats(selectedCategory.slug);
        setCategoryStats(statsData.stats);

        // Fetch top fastest growing reels for spotlight
        const fastestData = await fetchReels({
          category: selectedCategory.slug,
          filterMode: 'fastest_growing',
          limit: 3
        });
        setFastestGrowingReels(fastestData.items);
      } catch (err) {
        console.error('Failed to load category data:', err);
      }
    };

    loadCategoryData();
  }, [selectedCategory]);

  // Fetch Reels list based on current filter, sort, search
  const loadReels = useCallback(async () => {
    if (!selectedCategory) return;
    try {
      setLoadingReels(true);
      const data = await fetchReels({
        category: selectedCategory.slug,
        filterMode: filterMode,
        sortBy: sortBy,
        limit: filterMode === 'top_100' ? 100 : 50,
        search: searchTerm || null
      });
      setReels(data.items);
      setTotalCount(data.total_count);
    } catch (err) {
      console.error('Failed to load reels:', err);
    } finally {
      setLoadingReels(false);
    }
  }, [selectedCategory, filterMode, sortBy, searchTerm]);

  useEffect(() => {
    loadReels();
  }, [loadReels]);

  // Handle Quick Sync
  const handleQuickSync = async () => {
    if (!activeDataSource) return;
    try {
      setIsSyncing(true);
      await triggerSync(activeDataSource.id, selectedCategory?.slug);
      showToast(`Synchronized fresh reels for ${selectedCategory?.name}!`);
      
      // Reload stats and reels
      const [cats, statsData] = await Promise.all([
        fetchCategories(),
        fetchCategoryStats(selectedCategory.slug)
      ]);
      setCategories(cats);
      setCategoryStats(statsData.stats);
      await loadReels();
    } catch (err) {
      alert('Sync failed: ' + err.message);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleCategorySwitch = (cat) => {
    setSelectedCategory(cat);
    // Keep user's current filter selection
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex flex-col font-sans">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-2 text-sm font-semibold border border-purple-400/30 animate-bounce">
          <Sparkles className="w-4 h-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Top Header */}
      <Header
        categories={categories}
        selectedCategory={selectedCategory}
        onSelectCategory={handleCategorySwitch}
        activeDataSource={activeDataSource}
        onOpenDataSources={() => setIsDataSourcesOpen(true)}
        onSyncCurrent={handleQuickSync}
        isSyncing={isSyncing}
      />

      {/* Dashboard Main View Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {loading || !selectedCategory ? (
          <div className="flex flex-col items-center justify-center py-28 text-center space-y-4">
            <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
            <p className="text-slate-400 text-sm">Initializing Reels Intelligence Engine...</p>
          </div>
        ) : (
          <>
            {/* Category KPIs & Overview */}
            <CategoryStatsBanner
              category={selectedCategory}
              stats={categoryStats}
            />

            {/* Spotlight Section: Fastest Growing Reels */}
            <FastestGrowingSpotlight
              reels={fastestGrowingReels}
              onSelectReel={(reel) => setSelectedReel(reel)}
            />

            {/* Filter Navigation Bar (Last 24 Hours, Fastest Growing, Top 100, All) */}
            <FilterBar
              activeFilter={filterMode}
              onChangeFilter={(mode) => setFilterMode(mode)}
              sortBy={sortBy}
              onChangeSort={(sort) => setSortBy(sort)}
              searchTerm={searchTerm}
              onChangeSearch={(val) => setSearchTerm(val)}
              totalItems={totalCount}
            />

            {/* Reels Grid */}
            {loadingReels ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 py-12">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="aspect-[9/14] bg-slate-900/60 rounded-2xl animate-pulse border border-slate-800" />
                ))}
              </div>
            ) : reels.length === 0 ? (
              <div className="text-center py-20 bg-slate-900/40 rounded-3xl border border-slate-800/80 p-8 space-y-4">
                <AlertCircle className="w-12 h-12 text-slate-500 mx-auto" />
                <h3 className="text-base font-bold text-white">No Reels Found</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  No content matching the selected filter in {selectedCategory.name}. Try adjusting your search query or trigger a live data sync.
                </p>
                <button
                  onClick={handleQuickSync}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white shadow"
                >
                  Sync Permitted Feed
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {reels.map((reel, idx) => (
                  <ReelCard
                    key={reel.id}
                    reel={reel}
                    rank={reel.latest_trending?.rank || (idx + 1)}
                    onSelect={(r) => setSelectedReel(r)}
                  />
                ))}
              </div>
            )}
          </>
        )}

      </main>

      {/* Reel Detail Modal */}
      {selectedReel && (
        <ReelDetailModal
          reel={selectedReel}
          onClose={() => setSelectedReel(null)}
        />
      )}

      {/* Data Source Configuration Modal */}
      <DataSourceModal
        isOpen={isDataSourcesOpen}
        onClose={() => setIsDataSourcesOpen(false)}
        onSyncComplete={async () => {
          showToast('Data ingestion completed!');
          const [cats, statsData] = await Promise.all([
            fetchCategories(),
            fetchCategoryStats(selectedCategory.slug)
          ]);
          setCategories(cats);
          setCategoryStats(statsData.stats);
          await loadReels();
        }}
      />

      {/* Modern Dashboard Footer */}
      <footer className="mt-16 border-t border-slate-800/80 bg-slate-950/80 py-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Compliant Data-Source Architecture (Meta Graph API / Permitted Feeds)</span>
          </div>
          <div>
            Built for High-Growth Instagram Reels Discovery & Velocity Intelligence
          </div>
        </div>
      </footer>
    </div>
  );
}
