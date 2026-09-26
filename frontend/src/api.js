const API_BASE = '/api';

export async function fetchCategories() {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

export async function fetchCategoryStats(slugOrId) {
  const res = await fetch(`${API_BASE}/categories/${slugOrId}`);
  if (!res.ok) throw new Error('Failed to fetch category stats');
  return res.json();
}

export async function fetchReels({
  category,
  filterMode = 'all',
  sortBy = null,
  limit = 50,
  offset = 0,
  search = null,
}) {
  const params = new URLSearchParams({
    category,
    filter_mode: filterMode,
    limit: limit.toString(),
    offset: offset.toString(),
  });
  if (sortBy) params.append('sort_by', sortBy);
  if (search) params.append('search', search);

  const res = await fetch(`${API_BASE}/reels?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch reels');
  return res.json();
}

export async function fetchReelById(reelId) {
  const res = await fetch(`${API_BASE}/reels/${reelId}`);
  if (!res.ok) throw new Error('Failed to fetch reel details');
  return res.json();
}

export async function fetchReelMetricsHistory(reelId) {
  const res = await fetch(`${API_BASE}/reels/${reelId}/metrics-history`);
  if (!res.ok) throw new Error('Failed to fetch reel metrics history');
  return res.json();
}

export async function fetchDataSources() {
  const res = await fetch(`${API_BASE}/data-sources`);
  if (!res.ok) throw new Error('Failed to fetch data sources');
  return res.json();
}

export async function fetchDataSourceHealth() {
  const res = await fetch(`${API_BASE}/data-sources/health`);
  if (!res.ok) throw new Error('Failed to fetch data source health');
  return res.json();
}

export async function activateDataSource(sourceId) {
  const res = await fetch(`${API_BASE}/data-sources/${sourceId}/activate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to activate data source');
  return res.json();
}

export async function updateDataSourceConfig(sourceId, payload) {
  const res = await fetch(`${API_BASE}/data-sources/${sourceId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update data source');
  return res.json();
}

export async function triggerSync(sourceId, categorySlug = null) {
  const url = categorySlug 
    ? `${API_BASE}/data-sources/${sourceId}/sync?category_slug=${encodeURIComponent(categorySlug)}`
    : `${API_BASE}/data-sources/${sourceId}/sync`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger data sync');
  return res.json();
}
