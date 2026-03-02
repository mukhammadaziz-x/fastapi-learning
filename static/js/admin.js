/**
 * EduPlatform — Admin Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth(['admin']);
    if (!user) return;
    setNavbar(user);
    loadAdminDashboard();
    loadRecentUsers();
});

async function loadAdminDashboard() {
    try {
        const dash = await api('/dashboard/admin');
        if (!dash) return;
        setText('s-users', dash.total_users || 0);
        setText('s-teachers', dash.total_teachers || 0);
        setText('s-students', dash.total_students || 0);
        setText('s-subjects', dash.total_subjects || 0);
        setText('s-assignments', dash.total_assignments || 0);
        setText('s-submissions', dash.total_submissions || 0);
        setText('s-active', dash.active_assignments || 0);
        setText('s-avg-score', (dash.platform_average_score || 0).toFixed(1) + '%');
    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

async function loadRecentUsers() {
    try {
        const users = await api('/users/?skip=0&limit=15');
        const tbody = document.getElementById('users-table');
        if (!tbody) return;

        if (!users || !users.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><div class="empty-state-icon">👥</div><div class="empty-state-title">Hali foydalanuvchi yo\'q</div></td></tr>';
            return;
        }

        tbody.innerHTML = users.map(u => `
            <tr>
                <td><strong>${u.username}</strong></td>
                <td>${u.email}</td>
                <td>${u.full_name || '—'}</td>
                <td><span class="role-badge role-badge-${u.role}">${u.role}</span></td>
                <td><span class="status-badge ${u.is_active ? 'status-active' : 'status-failed'}">${u.is_active ? '✓ Aktiv' : '✕ Nofaol'}</span></td>
                <td>${formatDate(u.created_at)}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Users load error:', e);
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
