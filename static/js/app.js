/**
 * EduPlatform — Shared JavaScript Utilities
 * Common API calls, auth, toast, helpers
 */

const API_BASE = '/api/v1';

// ═══════ AUTH HELPERS ═══════
function getToken() { return localStorage.getItem('token'); }
function getUser()  { try { return JSON.parse(localStorage.getItem('user')); } catch { return null; } }

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

function requireAuth(allowedRoles) {
    const token = getToken();
    const user = getUser();
    if (!token || !user) { window.location.href = '/'; return null; }
    if (allowedRoles && !allowedRoles.includes(user.role)) { window.location.href = '/'; return null; }
    return user;
}

// ═══════ API WRAPPER ═══════
async function api(path, options = {}) {
    const token = getToken();
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers,
        },
        ...options,
    };
    if (options.body && typeof options.body === 'object') {
        config.body = JSON.stringify(options.body);
    }
    try {
        const res = await fetch(API_BASE + path, config);
        if (res.status === 401) { logout(); return null; }
        if (res.status === 204) return true;
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Request failed');
        return data;
    } catch (err) {
        console.error('API Error:', err);
        throw err;
    }
}

// ═══════ TOAST NOTIFICATIONS ═══════
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100px)'; setTimeout(() => toast.remove(), 300); }, 4000);
}

// ═══════ ALERT MESSAGES (inline) ═══════
function showAlert(elementId, message, type = 'error') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = `alert alert-${type} show`;
    el.textContent = message;
    if (type === 'success') setTimeout(() => el.classList.remove('show'), 4000);
}

function hideAlert(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.classList.remove('show');
}

// ═══════ UI HELPERS ═══════
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('uz-UZ', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('uz-UZ', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatDuration(seconds) {
    if (!seconds) return '0s';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}s ${m}d`;
    if (m > 0) return `${m}d ${s}s`;
    return `${s}s`;
}

function gradeClass(grade) {
    return `grade-badge grade-${grade || 'PENDING'}`;
}

function rankBadge(rank) {
    if (rank === 1) return 'rank-gold';
    if (rank === 2) return 'rank-silver';
    if (rank === 3) return 'rank-bronze';
    return 'rank-normal';
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function setNavbar(user) {
    const nameEl = document.getElementById('user-name');
    const avatarEl = document.getElementById('user-avatar');
    const roleBadgeEl = document.getElementById('user-role-badge');

    // Body role class (for role-specific accent colors)
    if (document.body) {
        document.body.classList.remove('role-admin', 'role-teacher', 'role-student');
        if (user.role === 'admin') document.body.classList.add('role-admin');
        if (user.role === 'teacher') document.body.classList.add('role-teacher');
        if (user.role === 'student') document.body.classList.add('role-student');
    }

    if (nameEl) nameEl.textContent = user.full_name || user.username;
    if (avatarEl) {
        if (user.avatar_url) {
            avatarEl.innerHTML = `<img src="${user.avatar_url}" alt="${user.username}">`;
        } else {
            avatarEl.textContent = getInitials(user.full_name || user.username);
        }
    }
    if (roleBadgeEl) {
        roleBadgeEl.textContent = user.role;
        roleBadgeEl.className = `role-badge role-badge-${user.role}`;
    }
}

// ═══════ EXAM TYPE LABELS ═══════
function examTypeLabel(type) {
    const labels = {
        'multiple_choice': '📝 Test',
        'code_editor': '💻 Code Editor',
        'kahoot_game': '🎮 Kahoot',
        'essay': '✍️ Essay',
        'mixed': '🔀 Aralash',
        'fill_blank': '📄 Bo\'sh joy',
        'true_false': '✅ To\'g\'ri/Noto\'g\'ri',
    };
    return labels[type] || type;
}

function assignmentTypeLabel(type) {
    const labels = {
        'homework': '📚 Uy vazifasi',
        'classwork': '🏫 Dars vazifasi',
        'midterm': '📋 Oraliq imtihon',
        'final': '🎯 Yakuniy imtihon',
        'practice': '🔄 Mashq',
        'quiz': '⚡ Quiz',
    };
    return labels[type] || type;
}

// ═══════ PERCENTAGE COLOR ═══════
function percentColor(pct) {
    if (pct >= 90) return '#10b981';
    if (pct >= 61) return '#3b82f6';
    if (pct >= 60) return '#f59e0b';
    return '#ef4444';
}
