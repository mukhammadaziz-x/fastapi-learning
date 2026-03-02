/**
 * EduPlatform — Student Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth(['admin', 'teacher', 'student']);
    if (!user) return;
    setNavbar(user);
    loadStudentAnalytics();
    loadRecentResults();
    loadLeaderboardPreview();
    loadSubjectStrengths();
});

async function loadStudentAnalytics() {
    try {
        const a = await api('/analytics/my');
        if (!a) return;
        setText('s-score', Math.round(a.average_percentage || 0) + '%');
        setText('s-rank', a.global_rank ? '#' + a.global_rank : '—');
        setText('s-completed', a.completed_assignments || 0);
        setText('s-total', a.total_assignments || 0);
        setText('s-points', Math.round(a.ranking_points || 0));
        setText('s-streak', a.streak_days || 0);
        setText('s-time', formatDuration(Math.round((a.total_time_spent_minutes || 0) * 60)));

        // Grade distribution
        renderGradeDistribution(a.grade_distribution || {});

        // Completion progress
        const totalA = a.total_assignments || 1;
        const completedA = a.completed_assignments || 0;
        const completionPct = Math.round((completedA / totalA) * 100);
        const progressEl = document.getElementById('completion-progress');
        if (progressEl) progressEl.style.width = completionPct + '%';
        setText('completion-text', `${completedA} / ${totalA} (${completionPct}%)`);

    } catch (e) {
        console.error('Analytics load error:', e);
    }
}

function renderGradeDistribution(dist) {
    const container = document.getElementById('grade-dist');
    if (!container) return;
    const grades = ['DISTINCTION', 'MERIT', 'PASS', 'FAIL'];
    const total = Object.values(dist).reduce((s, v) => s + v, 0) || 1;

    container.innerHTML = grades.map(g => {
        const count = dist[g] || 0;
        const pct = Math.round((count / total) * 100);
        return `
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">
                <span class="${gradeClass(g)}" style="min-width:100px;text-align:center;">${g}</span>
                <div class="progress-bar" style="flex:1;">
                    <div class="progress-fill" style="width:${pct}%;background:${percentColor(g === 'DISTINCTION' ? 90 : g === 'MERIT' ? 75 : g === 'PASS' ? 60 : 30)};"></div>
                </div>
                <span style="font-size:0.85rem;color:var(--text-secondary);min-width:40px;text-align:right;">${count}</span>
            </div>
        `;
    }).join('');
}

async function loadRecentResults() {
    try {
        const subs = await api('/submissions/my');
        const tbody = document.getElementById('results-table');
        if (!tbody) return;

        if (!subs || !subs.length) {
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-state-icon">📝</div><div class="empty-state-title">Hali natija yo\'q</div><div class="empty-state-desc">Topshiriqlarni bajarib, natijalaringizni ko\'ring</div></div></td></tr>';
            return;
        }

        tbody.innerHTML = subs.slice(0, 10).map(s => `
            <tr>
                <td><strong>${s.assignment_title || 'Topshiriq #' + s.assignment_id}</strong></td>
                <td>${s.score}/${s.max_score}</td>
                <td style="color:${percentColor(s.percentage)};font-weight:700;">${s.percentage.toFixed(1)}%</td>
                <td><span class="${gradeClass(s.grade)}">${s.grade || '—'}</span></td>
                <td>${formatDateTime(s.submitted_at)}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Results load error:', e);
    }
}

async function loadLeaderboardPreview() {
    try {
        const lb = await api('/leaderboard?scope=global&limit=5');
        const container = document.getElementById('leaderboard-preview');
        if (!container || !lb) return;

        const user = getUser();
        if (lb.my_rank) setText('s-rank', '#' + lb.my_rank);

        if (!lb.entries || !lb.entries.length) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🏆</div><div class="empty-state-title">Reyting hali mavjud emas</div></div>';
            return;
        }

        container.innerHTML = lb.entries.map((e, i) => `
            <div style="display:flex;align-items:center;gap:1rem;padding:0.75rem 0;${i < lb.entries.length - 1 ? 'border-bottom:1px solid var(--border-light);' : ''}${e.user_id === user?.id ? 'background:rgba(99,102,241,0.06);margin:0 -1rem;padding-left:1rem;padding-right:1rem;border-radius:8px;' : ''}">
                <span class="rank-display ${rankBadge(e.rank)}" style="min-width:40px;justify-content:center;padding:4px 10px;font-size:0.85rem;">${e.rank <= 3 ? ['🥇','🥈','🥉'][e.rank-1] : '#' + e.rank}</span>
                <div class="navbar-avatar" style="width:32px;height:32px;font-size:0.75rem;">${getInitials(e.full_name || e.username)}</div>
                <div style="flex:1;">
                    <div style="font-weight:600;font-size:0.9rem;">${e.full_name || e.username}${e.user_id === user?.id ? ' (Siz)' : ''}</div>
                    <div style="font-size:0.75rem;color:var(--text-muted);">${e.average_percentage.toFixed(1)}% · ${e.assignments_completed} topshiriq</div>
                </div>
                <div style="font-weight:700;color:var(--primary-light);font-size:0.9rem;">${Math.round(e.ranking_points)} pt</div>
            </div>
        `).join('');

    } catch (e) {
        console.error('Leaderboard load error:', e);
    }
}

async function loadSubjectStrengths() {
    try {
        const user = getUser();
        const a = await api(`/analytics/student/${user.id}`);
        const container = document.getElementById('subject-strengths');
        if (!container || !a || !a.subject_scores || !a.subject_scores.length) {
            if (container) container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><div class="empty-state-title">Statistika uchun ko\'proq topshiriq bajaring</div></div>';
            return;
        }

        container.innerHTML = a.subject_scores.map(s => {
            const pct = s.avg_score || 0;
            const strength = pct >= 80 ? 'Yaxshi' : pct >= 60 ? 'O\'rtacha' : 'Yaxshilash kerak';
            const color = percentColor(pct);
            return `
                <div style="margin-bottom:1rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                        <span style="font-weight:600;font-size:0.9rem;">${s.subject}</span>
                        <span style="font-size:0.8rem;color:${color};font-weight:600;">${pct.toFixed(0)}% — ${strength}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${pct}%;background:${color};"></div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        console.error('Subject strengths load error:', e);
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
