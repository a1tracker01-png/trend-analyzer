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
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to update data source');
  }
  return res.json();
}

export async function triggerSync(sourceId, categorySlug = null, apiToken = null) {
  const url = categorySlug 
    ? `${API_BASE}/data-sources/${sourceId}/sync?category_slug=${encodeURIComponent(categorySlug)}`
    : `${API_BASE}/data-sources/${sourceId}/sync`;

  const headers = {};
  let body = undefined;
  if (apiToken || categorySlug) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify({
      api_token: apiToken ? apiToken.trim() : undefined,
      category_slug: categorySlug || undefined,
    });
  }

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body,
  });

  if (!res.ok) {
    let errMsg = 'Failed to trigger data sync';
    try {
      const data = await res.json();
      errMsg = data.detail || data.message || JSON.stringify(data);
    } catch (_) {
      try {
        const text = await res.text();
        if (text) errMsg = text;
      } catch (__) {}
    }
    throw new Error(errMsg);
  }

  return res.json();
}

export async function purgeMockData() {
  const res = await fetch(`${API_BASE}/data-sources/purge-mock-data`, {
    method: 'POST',
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || data.message || 'Failed to purge mock data');
  }
  return res.json();
}

export async function triggerFreshScrape(sourceId, categorySlug = null, apiToken = null, limit = 15) {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (categorySlug && categorySlug !== 'all') {
    params.append('category_slug', categorySlug);
  }
  const url = `${API_BASE}/data-sources/${sourceId}/scrape-fresh?${params.toString()}`;

  const headers = {};
  let body = undefined;
  if (apiToken || categorySlug) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify({
      api_token: apiToken ? apiToken.trim() : undefined,
      category_slug: categorySlug && categorySlug !== 'all' ? categorySlug : undefined,
    });
  }

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body,
  });

  if (!res.ok) {
    let errMsg = 'Failed to trigger fresh Instagram scrape';
    try {
      const data = await res.json();
      errMsg = data.detail || data.message || JSON.stringify(data);
    } catch (_) {
      try {
        const text = await res.text();
        if (text) errMsg = text;
      } catch (__) {}
    }
    throw new Error(errMsg);
  }

  return res.json();
}

