const API = '';
let currentTab = 'login';

window.onload = function () {
    const token = localStorage.getItem('token');
    const email = localStorage.getItem('email');
    if (token && email) showApp(email);
};

/* ── Auth ──────────────────────────────────────────────────── */
function switchTab(tab) {
    currentTab = tab;
    document.getElementById('loginTab').classList.toggle('active', tab === 'login');
    document.getElementById('signupTab').classList.toggle('active', tab === 'signup');
    document.getElementById('authBtn').innerText = tab === 'login' ? 'Login' : 'Create Account';
    document.getElementById('switchText').innerText = tab === 'login' ? "Don't have an account?" : "Already have an account?";
    document.getElementById('switchLink').innerText = tab === 'login' ? 'Sign up free' : 'Login';
    hideAuthError();
}
function showAuthError(msg) { const e = document.getElementById('authError'); e.innerText = msg; e.style.display = 'block'; }
function hideAuthError() { document.getElementById('authError').style.display = 'none'; }

async function submitAuth() {
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    const btn = document.getElementById('authBtn');
    hideAuthError();
    if (!email || !password) { showAuthError('Please fill in all fields.'); return; }
    btn.disabled = true;
    btn.innerText = currentTab === 'login' ? 'Logging in...' : 'Creating account...';
    try {
        const res = await fetch(API + (currentTab === 'login' ? '/login' : '/signup'), {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) { showAuthError(data.detail || 'Something went wrong.'); return; }
        localStorage.setItem('token', data.token);
        localStorage.setItem('email', data.email);
        showApp(data.email);
    } catch (e) {
        showAuthError('Cannot connect to server. Make sure app.py is running.');
    } finally {
        btn.disabled = false;
        btn.innerText = currentTab === 'login' ? 'Login' : 'Create Account';
    }
}

/* ── App lifecycle ─────────────────────────────────────────── */
function showApp(email) {
    document.getElementById('authScreen').style.display = 'none';
    document.getElementById('appScreen').style.display  = 'block';
    document.getElementById('userEmailDisplay').innerText = email;
    const initial = email.charAt(0).toUpperCase();
    document.getElementById('headerAvatar').innerText = initial;
    document.getElementById('panelAvatar').innerText  = initial;
    document.getElementById('panelEmail').innerText   = email;
    clearWorkspace();
    clearSidebar();
    loadHistory();
}

function clearWorkspace() {
    document.getElementById('topicInput').value = '';
    document.getElementById('thinkingContainer').style.display = 'none';
    document.getElementById('logBody').innerHTML = '';
    document.getElementById('logLoader').style.display = 'inline-block';
    document.getElementById('reportContainer').style.display = 'none';
    document.getElementById('reportTopicTag').innerText = '';
    document.getElementById('reportContent').innerHTML = '';
    document.getElementById('welcomeState').style.display = 'block';
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
}

function clearSidebar() {
    document.getElementById('historyList').innerHTML =
        '<div class="no-history">No research yet.<br>Start your first search!</div>';
}

function newSearch() { clearWorkspace(); document.getElementById('topicInput').focus(); }

function logout() {
    closeAccountPanel();
    clearWorkspace();
    clearSidebar();
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    document.getElementById('appScreen').style.display  = 'none';
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('authEmail').value = '';
    document.getElementById('authPassword').value = '';
    switchTab('login');
}

function getHeaders() {
    return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` };
}

/* ── Account Panel ─────────────────────────────────────────── */
function openAccountPanel() {
    const count = document.querySelectorAll('.history-item').length;
    document.getElementById('panelResearchCount').innerText = count;
    document.getElementById('panelOverlay').classList.add('open');
    document.getElementById('accountPanel').classList.add('open');
}
function closeAccountPanel() {
    document.getElementById('panelOverlay').classList.remove('open');
    document.getElementById('accountPanel').classList.remove('open');
}

async function deleteAccount() {
    const ok = confirm('⚠️ Are you absolutely sure?\n\nThis permanently deletes your account and ALL research history. This cannot be undone.');
    if (!ok) return;
    const btn = document.getElementById('deleteAccountBtn');
    btn.disabled = true; btn.innerText = 'Deleting...';
    try {
        const res = await fetch(API + '/user', { method: 'DELETE', headers: getHeaders() });
        if (!res.ok) {
            const err = await res.json();
            alert('Error: ' + (err.detail || 'Could not delete account.'));
            btn.disabled = false; btn.innerText = '🗑  Delete My Account';
            return;
        }
        logout();
    } catch (e) {
        alert('Connection error. Make sure the server is running.');
        btn.disabled = false; btn.innerText = '🗑  Delete My Account';
    }
}

/* ── History ───────────────────────────────────────────────── */
async function loadHistory() {
    try {
        const res = await fetch(API + '/history', { headers: getHeaders() });
        if (res.status === 401) { logout(); return; }
        const data = await res.json();
        renderHistorySidebar(data.history || []);
    } catch (e) { console.error('Failed to load history', e); }
}

function renderHistorySidebar(items) {
    const list = document.getElementById('historyList');
    if (!items.length) {
        list.innerHTML = '<div class="no-history">No research yet.<br>Start your first search!</div>';
        return;
    }
    list.innerHTML = items.map(item => {
        const date = new Date(item.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
        return `
        <div class="history-item" id="hist-${item.id}" onclick="loadHistoryItem('${item.id}')">
            <div style="flex:1; min-width:0;">
                <div class="history-topic" title="${escapeAttr(item.topic)}">${escapeHtml(item.topic)}</div>
                <div class="history-date">${date}</div>
            </div>
            <button class="delete-btn" onclick="deleteHistoryItem(event,'${item.id}')">🗑 Delete</button>
        </div>`;
    }).join('');
}

function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escapeAttr(s) { return s.replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }

async function loadHistoryItem(id) {
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    const el = document.getElementById(`hist-${id}`);
    if (el) el.classList.add('active');
    try {
        const res = await fetch(`${API}/history/${id}`, { headers: getHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        document.getElementById('topicInput').value = data.topic;
        document.getElementById('logBody').innerHTML = (data.logs || []).map(l =>
            `<div class="log-entry"><span style="color:#93c5fd">>></span> ${escapeHtml(l)}</div>`
        ).join('');
        document.getElementById('logLoader').style.display = 'none';
        document.getElementById('thinkingContainer').style.display = 'block';
        document.getElementById('reportTopicTag').innerText   = '🔍 ' + data.topic;
        document.getElementById('reportContent').innerHTML    = data.final_report;
        document.getElementById('reportContainer').style.display = 'block';
        document.getElementById('welcomeState').style.display    = 'none';
    } catch (e) { console.error('Failed to load history item', e); }
}

async function deleteHistoryItem(event, id) {
    event.stopPropagation();
    if (!confirm('Delete this research from history?')) return;
    try {
        await fetch(`${API}/history/${id}`, { method: 'DELETE', headers: getHeaders() });
        await loadHistory();
        clearWorkspace();
    } catch (e) { console.error('Failed to delete', e); }
}

/* ── Research ──────────────────────────────────────────────── */
async function startResearch() {
    const topic = document.getElementById('topicInput').value.trim();
    if (!topic) return;
    const btn = document.getElementById('researchBtn');
    const logBody = document.getElementById('logBody');
    const thinkingC = document.getElementById('thinkingContainer');
    const reportC = document.getElementById('reportContainer');
    const logLoader = document.getElementById('logLoader');

    btn.disabled = true; btn.innerText = 'Researching...';
    logBody.innerHTML = '<div class="log-entry"><span style="color:#93c5fd">>></span> Initializing agent ...</div>';
    logLoader.style.display = 'inline-block';
    thinkingC.style.display = 'block';
    reportC.style.display = 'none';
    document.getElementById('welcomeState').style.display = 'none';
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));

    try {
        setTimeout(() => addLog('Sending topic to agent...'), 600);
        const res = await fetch(API + '/research', {
            method: 'POST', headers: getHeaders(), body: JSON.stringify({ topic })
        });
        if (res.status === 401) { logout(); return; }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || `Server error: ${res.status}`); }
        const data = await res.json();
        data.logs.forEach((log, i) => setTimeout(() => addLog(log), (i + 1) * 700));
        setTimeout(() => {
            document.getElementById('reportTopicTag').innerText = '🔍 ' + topic;
            document.getElementById('reportContent').innerHTML  = data.final_report;
            reportC.style.display = 'block';
            logLoader.style.display = 'none';
            addLog('✓ Report compilation complete.');
            btn.disabled = false; btn.innerText = 'Research';
            loadHistory();
        }, (data.logs.length + 1) * 700);
    } catch (e) {
        addLog('❌ Error: ' + e.message);
        btn.disabled = false; btn.innerText = 'Research';
        logLoader.style.display = 'none';
    }
}

function addLog(msg) {
    const logBody = document.getElementById('logBody');
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span style="color:#93c5fd">>></span> ${escapeHtml(msg)}`;
    logBody.appendChild(div);
    logBody.scrollTop = logBody.scrollHeight;
}