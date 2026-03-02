/**
 * EduPlatform — Teacher Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth(['admin', 'teacher']);
    if (!user) return;
    setNavbar(user);
    loadTeacherDashboard();
    loadMySubjects();
    loadPendingSubmissions();
});

async function loadTeacherDashboard() {
    try {
        const dash = await api('/dashboard/teacher');
        if (!dash) return;
        setText('s-subjects', dash.total_subjects || 0);
        setText('s-assignments', dash.total_assignments || 0);
        setText('s-students', dash.total_students || 0);
        setText('s-pending', dash.pending_reviews || 0);
        setText('s-flagged', dash.ai_flagged_count || 0);
    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

async function loadMySubjects() {
    try {
        const subjects = await api('/subjects/');
        const container = document.getElementById('subjects-grid');
        if (!container) return;

        if (!subjects || !subjects.length) {
            container.innerHTML = `<div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-title">Hali fan yaratilmagan</div>
                <div class="empty-state-desc">API (/docs) orqali yoki quyidagi tugma orqali fan yarating</div>
            </div>`;
            return;
        }

        container.innerHTML = subjects.map(s => `
            <div class="subject-card">
                <div class="subject-card-header">
                    <span class="subject-card-name">${s.name}</span>
                    <span class="subject-card-code">${s.code}</span>
                </div>
                <div class="subject-card-meta">
                    <span>${examTypeLabel(s.default_exam_type)}</span>
                    <span>👥 ${s.enrolled_count || 0} talaba</span>
                    <span>📅 ${s.semester || '—'}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Subjects load error:', e);
    }
}

async function loadPendingSubmissions() {
    try {
        const submissions = await api('/submissions/pending-review');
        const tbody = document.getElementById('pending-table');
        if (!tbody) return;

        if (!submissions || !submissions.length) {
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-state-icon">✅</div><div class="empty-state-title">Tekshirish uchun topshiriq yo\'q</div></div></td></tr>';
            return;
        }

        tbody.innerHTML = submissions.map(s => `
            <tr>
                <td><strong>${s.assignment_title || 'Topshiriq #' + s.assignment_id}</strong></td>
                <td>${s.student_name || 'Student #' + s.student_id}</td>
                <td>${(s.percentage || 0).toFixed(1)}%</td>
                <td><span class="${gradeClass(s.grade)}">${s.grade || 'PENDING'}</span></td>
                <td>${formatDateTime(s.submitted_at)}</td>
            </tr>
        `).join('');
    } catch (e) {
        // Endpoint may not exist yet — OK
        const tbody = document.getElementById('pending-table');
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted);text-align:center;padding:2rem;">API endpoint yuklanmoqda...</td></tr>';
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
