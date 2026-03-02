/**
 * EduPlatform — Login & Register Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect to dashboard
    const token = getToken();
    const user = getUser();
    if (token && user) {
        redirectToDashboard(user.role);
        return;
    }
});

function showTab(tab) {
    const loginForm = document.getElementById('login-form');
    const regForm = document.getElementById('register-form');
    const tabs = document.querySelectorAll('.tab');

    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        regForm.classList.add('hidden');
        tabs[0].classList.add('active');
    } else {
        loginForm.classList.add('hidden');
        regForm.classList.remove('hidden');
        tabs[1].classList.add('active');
    }
    hideAlert('alert-msg');
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showAlert('alert-msg', 'Username va parolni kiriting', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px;"></div> Kirish...';

    try {
        const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();

        if (!res.ok) {
            showAlert('alert-msg', data.detail || 'Login xatolik', 'error');
            return;
        }

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        showAlert('alert-msg', 'Muvaffaqiyatli kirdingiz! ✓', 'success');

        setTimeout(() => redirectToDashboard(data.user.role), 500);
    } catch (err) {
        showAlert('alert-msg', 'Server bilan bog\'lanib bo\'lmadi', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Kirish';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('reg-btn');
    const email = document.getElementById('reg-email').value.trim();
    const username = document.getElementById('reg-username').value.trim();
    const fullname = document.getElementById('reg-fullname').value.trim();
    const password = document.getElementById('reg-password').value;
    const role = document.getElementById('reg-role').value;

    if (!email || !username || !password) {
        showAlert('alert-msg', 'Barcha maydonlarni to\'ldiring', 'error');
        return;
    }

    if (password.length < 6) {
        showAlert('alert-msg', 'Parol kamida 6 belgidan iborat bo\'lishi kerak', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px;"></div> Yuborilmoqda...';

    try {
        const res = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                username,
                full_name: fullname || null,
                password,
                role,
            }),
        });
        const data = await res.json();

        if (!res.ok) {
            showAlert('alert-msg', data.detail || 'Ro\'yxatdan o\'tish xatolik', 'error');
            return;
        }

        showAlert('alert-msg', 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz! Endi kiring.', 'success');
        setTimeout(() => showTab('login'), 1500);
    } catch (err) {
        showAlert('alert-msg', 'Server bilan bog\'lanib bo\'lmadi', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Ro\'yxatdan o\'tish';
    }
}

function googleLogin() {
    const role = document.getElementById('reg-role')?.value || 'student';
    window.location.href = `/api/v1/auth/google/login?role=${role}`;
}

function redirectToDashboard(role) {
    const routes = {
        admin: '/dashboard/admin',
        teacher: '/dashboard/teacher',
        student: '/dashboard/student',
    };
    window.location.href = routes[role] || '/dashboard/student';
}
