export function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  if (num >= 1_000_000_000) {
    return (num / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B';
  }
  if (num >= 1_000_000) {
    return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  }
  if (num >= 1_000) {
    return (num / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
  }
  return num.toLocaleString();
}

export function formatRelativeTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.max(0, Math.floor((now - date) / 1000));

  if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 30) return `${diffInDays}d ago`;
  const diffInMonths = Math.floor(diffInDays / 30);
  return `${diffInMonths}mo ago`;
}

export function formatDateTime(dateString) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}

export function getEngagementBadge(rate) {
  if (rate >= 9.0) {
    return {
      bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      label: 'Ultra High'
    };
  }
  if (rate >= 6.0) {
    return {
      bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
      label: 'High'
    };
  }
  if (rate >= 3.0) {
    return {
      bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
      label: 'Good'
    };
  }
  return {
    bg: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    label: 'Standard'
  };
}
