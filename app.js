/* ============================================
   Poultry Health AI — App Logic
   Mobile-first + Dark Mode
   ============================================ */

const API_BASE = '';
let conversationHistory = [];
let selectedSymptoms = [];
let currentImageFile = null;
let sessionCount = 0;

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  // Splash intro — fade out after 2.2s
  const splash = document.getElementById('splashScreen');
  if (splash) {
    setTimeout(() => {
      splash.classList.add('fade-out');
      setTimeout(() => splash.remove(), 600);
    }, 2200);
  }

  initTheme();
  initNavigation();
  initChatInput();
  initImageUpload();
  loadSymptoms();
  loadBreeds();
  checkApiStatus();
});

// ══════════════════════════════════════
//   DARK MODE
// ══════════════════════════════════════

function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  applyTheme(theme);

  document.getElementById('themeToggle').addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('theme', next);
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('themeToggle');
  btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  btn.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'dark' ? '#0F1117' : '#FFFFFF';
}

// ══════════════════════════════════════
//   NAVIGATION
// ══════════════════════════════════════

function initNavigation() {
  document.querySelectorAll('.sidebar-nav-item[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
  document.querySelectorAll('.mobile-nav-item[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.sidebar-nav-item').forEach(el => el.classList.remove('active'));
  const sidebarItem = document.querySelector(`.sidebar-nav-item[data-tab="${tabId}"]`);
  if (sidebarItem) sidebarItem.classList.add('active');

  document.querySelectorAll('.mobile-nav-item').forEach(el => el.classList.remove('active'));
  const mobileItem = document.querySelector(`.mobile-nav-item[data-tab="${tabId}"]`);
  if (mobileItem) mobileItem.classList.add('active');

  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  const panel = document.getElementById(`panel-${tabId}`);
  if (panel) panel.classList.add('active');
}

// ══════════════════════════════════════
//   API STATUS
// ══════════════════════════════════════

async function checkApiStatus() {
  const statusText = document.getElementById('apiStatusText');
  const statusBar = document.getElementById('apiStatusBar');
  try {
    const res = await fetch(`${API_BASE}/api/symptoms`);
    if (res.ok) {
      statusText.textContent = 'Connected';
      statusText.style.color = '#22C55E';
      statusBar.style.width = '100%';
      statusBar.style.background = '#22C55E';
    }
  } catch (_) {
    statusText.textContent = 'Offline';
    statusText.style.color = '#EF4444';
    statusBar.style.width = '100%';
    statusBar.style.background = '#EF4444';
  }
}

// ══════════════════════════════════════
//   CHAT
// ══════════════════════════════════════

function initChatInput() {
  const input = document.getElementById('chatInput');
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });
}

function sendQuickMessage(text) {
  document.getElementById('chatInput').value = text;
  sendChatMessage();
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  input.style.height = 'auto';

  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.remove();

  appendChatMessage('user', message);
  sessionCount++;
  updateSessionCount();

  const typingId = showTyping();
  conversationHistory.push({ role: 'user', content: message });

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        bird_type: 'broiler',
        conversation_history: conversationHistory.slice(-10)
      })
    });
    removeTyping(typingId);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const data = await res.json();
    const aiResponse = data.response || 'Sorry, I could not process that.';
    conversationHistory.push({ role: 'assistant', content: aiResponse });
    appendChatMessage('ai', aiResponse, data.suggestions);
  } catch (err) {
    removeTyping(typingId);
    appendChatMessage('ai', 'Could not connect to the server. Make sure the backend is running.');
    showToast('Connection error', 'error');
  }
}

function appendChatMessage(type, content, suggestions = []) {
  const container = document.getElementById('chatMessages');
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message ${type}`;
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (type === 'user') {
    msgDiv.innerHTML = `
      <div class="chat-msg-header">
        <div class="chat-msg-avatar human">U</div>
        <span class="chat-msg-name">You</span>
        <span class="chat-msg-time">${now}</span>
      </div>
      <div class="chat-msg-body">${escapeHtml(content)}</div>`;
  } else {
    msgDiv.innerHTML = `
      <div class="chat-msg-header">
        <div class="chat-msg-avatar ai">🐔</div>
        <span class="chat-msg-name">FlockDoc</span>
        <span class="chat-msg-time">${now}</span>
      </div>
      <div class="chat-msg-body">${parseAIResponse(content)}</div>`;

    if (suggestions && suggestions.length > 0) {
      const sugDiv = document.createElement('div');
      sugDiv.className = 'chat-suggestions';
      suggestions.forEach(s => {
        const pill = document.createElement('button');
        pill.className = 'suggestion-pill';
        pill.textContent = s;
        pill.onclick = () => sendQuickMessage(s);
        sugDiv.appendChild(pill);
      });
      msgDiv.appendChild(sugDiv);
    }
  }
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function parseAIResponse(text) {
  const sectionMap = {
    'GREETING': { icon: '👋', cls: 'greeting', label: 'Greeting' },
    'ANALYSIS': { icon: '🔍', cls: 'analysis', label: 'Analysis' },
    'DIAGNOSIS': { icon: '🩺', cls: 'diagnosis', label: 'Diagnosis' },
    'TREATMENT': { icon: '💊', cls: 'treatment', label: 'Treatment' },
    'WARNING': { icon: '⚠️', cls: 'warning', label: 'Warning' },
    'PREVENTION': { icon: '🛡️', cls: 'prevention', label: 'Prevention' },
    'QUESTION': { icon: '❓', cls: 'question', label: 'Follow-up' },
    'EMERGENCY': { icon: '🚨', cls: 'emergency', label: 'Emergency' },
    'FACTS': { icon: '📋', cls: 'analysis', label: 'Facts' },
    'SUGGESTIONS': { icon: '💡', cls: 'prevention', label: 'Suggestions' },
  };
  const parts = text.split(/\[([A-Z_]+)\]/g);
  if (parts.length <= 1) return formatPlainText(text);

  let html = '';
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim();
    if (!part) continue;
    const info = sectionMap[part];
    if (info) {
      const content = (parts[i + 1] || '').trim();
      i++;
      if (content) {
        html += `<div class="response-section">
            <div class="section-header ${info.cls}"><span>${info.icon}</span> ${info.label}</div>
            <div class="section-content">${formatPlainText(content)}</div>
          </div>`;
      }
    } else if (i === 0) {
      html += `<div class="section-content">${formatPlainText(part)}</div>`;
    }
  }
  return html || formatPlainText(text);
}

function formatPlainText(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/^[•\-\*]\s+(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/gs, '<ul>$&</ul>');
  html = html.replace(/\n/g, '<br>');
  return html;
}

function showTyping() {
  const container = document.getElementById('chatMessages');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-message';
  div.innerHTML = `
    <div class="chat-msg-header">
      <div class="chat-msg-avatar ai">🐔</div>
      <span class="chat-msg-name">FlockDoc</span>
    </div>
    <div class="typing-indicator">
      <div class="typing-dots"><span></span><span></span><span></span></div>
      <span style="font-size:12px;color:var(--text-muted);">Thinking...</span>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function updateSessionCount() {
  const el = document.getElementById('sessionCount');
  if (el) el.textContent = sessionCount;
}

// ══════════════════════════════════════
//   DISEASE PREDICTION
// ══════════════════════════════════════

async function loadSymptoms() {
  try {
    const res = await fetch(`${API_BASE}/api/symptoms`);
    if (!res.ok) throw new Error('Failed');
    const data = await res.json();
    const container = document.getElementById('symptomContainer');
    container.innerHTML = '';

    if (data.categories) {
      Object.entries(data.categories).forEach(([category, symptoms]) => {
        const group = document.createElement('div');
        group.className = 'symptom-group';
        group.innerHTML = `<div class="symptom-group-label">${category}</div>`;
        const pills = document.createElement('div');
        pills.className = 'symptom-pills';
        symptoms.forEach(symptom => {
          const pill = document.createElement('button');
          pill.className = 'symptom-pill';
          pill.textContent = symptom;
          pill.onclick = () => toggleSymptom(pill, symptom);
          pills.appendChild(pill);
        });
        group.appendChild(pills);
        container.appendChild(group);
      });
    }
  } catch (_) {
    document.getElementById('symptomContainer').innerHTML =
      '<p class="text-muted" style="font-size:13px;">Could not load symptoms. Is the server running?</p>';
  }
}

function toggleSymptom(el, symptom) {
  el.classList.toggle('selected');
  if (selectedSymptoms.includes(symptom)) {
    selectedSymptoms = selectedSymptoms.filter(s => s !== symptom);
  } else {
    selectedSymptoms.push(symptom);
  }
}

function toggleSymptomsCard() {
  const body = document.getElementById('symptomContainer');
  const arrow = document.getElementById('symptomsArrow');
  body.classList.toggle('hidden');
  arrow.textContent = body.classList.contains('hidden') ? '▶' : '▼';
}

function loadBreeds() {
  const breedMap = {
    broiler: [
      'Cobb 500', 'Ross 308', 'Hubbard Classic', 'Arbor Acres Plus',
      'Lohmann Meat', 'Sasso', 'Vencobb 400'
    ],
    layer: [
      'Lohmann Brown', 'Hy-Line W-36', 'ISA Brown', 'Bovans White',
      'BV-300', 'Novogen Brown', 'Dekalb White'
    ],
    broiler_breeder: [
      'Cobb 500 Breeder', 'Ross 308 Breeder', 'Hubbard Breeder',
      'Arbor Acres Breeder', 'Indian River', 'Aviagen Breeder'
    ],
    layer_breeder: [
      'Lohmann LSL Breeder', 'Hy-Line Breeder', 'ISA Breeder',
      'Bovans Breeder', 'Novogen Breeder', 'Dekalb Breeder'
    ]
  };

  const birdType = document.getElementById('birdType');
  const breedSelect = document.getElementById('breedSelect');

  function populateBreeds() {
    const type = birdType.value;
    const breeds = breedMap[type] || breedMap.broiler;
    breedSelect.innerHTML = '<option value="">Select breed...</option>';
    breeds.forEach(b => {
      breedSelect.innerHTML += `<option value="${b}">${b}</option>`;
    });
    breedSelect.innerHTML += '<option value="other">Don\'t Know / Other</option>';
  }

  birdType.addEventListener('change', populateBreeds);
  populateBreeds();
}

async function submitPrediction() {
  if (selectedSymptoms.length === 0) {
    showToast('Select at least one symptom', 'warning');
    return;
  }

  const btn = document.getElementById('predictBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Analyzing...';

  const payload = {
    bird_type: document.getElementById('birdType').value,
    breed: document.getElementById('breedSelect').value || 'unknown',
    age_days: parseInt(document.getElementById('ageDays').value) || 30,
    flock_size: parseInt(document.getElementById('flockSize').value) || 100,
    mortality_rate: parseFloat(document.getElementById('mortalityRate').value) || 0,
    symptoms: selectedSymptoms,
    additional_info: ''
  };

  try {
    // Run symptom prediction
    const predRes = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!predRes.ok) throw new Error(`API error: ${predRes.status}`);
    const predData = await predRes.json();

    // If image uploaded, also run image analysis
    let imageData = null;
    if (currentImageFile) {
      try {
        const formData = new FormData();
        formData.append('image', currentImageFile);
        formData.append('bird_type', document.getElementById('birdType').value);
        const imgRes = await fetch(`${API_BASE}/api/analyze-image`, { method: 'POST', body: formData });
        if (imgRes.ok) imageData = await imgRes.json();
      } catch (_) { /* image analysis optional */ }
    }

    renderPredictionResults(predData, imageData);
    showToast('Prediction complete', 'success');
  } catch (_) {
    showToast('Prediction failed. Check server.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔬 Run Prediction';
  }
}

function renderPredictionResults(data, imageData) {
  const container = document.getElementById('predictionResults');
  let html = '';

  // Overall severity
  if (data.severity) {
    const sev = data.severity.toLowerCase();
    html += `<div class="severity-strip ${sev}" style="border-radius:var(--radius);margin-bottom:12px;">
      <span>⚠️</span> Overall Severity: <strong>${data.severity}</strong></div>`;
  }

  // Disease cards
  if (data.diseases && data.diseases.length > 0) {
    data.diseases.forEach(d => {
      const sc = d.match_score >= 70 ? 'high' : d.match_score >= 40 ? 'medium' : 'low';
      const tags = (d.matched_symptoms || []).map(s => `<span class="symptom-tag">${s}</span>`).join('');

      html += `
        <div class="disease-card">
          <div class="disease-card-header">
            <h4><span class="status-dot ${d.match_score >= 70 ? 'red' : d.match_score >= 40 ? 'yellow' : 'green'}"></span> ${d.name}</h4>
            <span class="match-score ${sc}">${d.match_score}%</span>
          </div>
          <div class="disease-card-body">
            <div class="disease-detail-row"><span class="detail-label">Category</span><span class="detail-value">${d.category || '—'}</span></div>
            <div class="disease-detail-row"><span class="detail-label">Severity</span><span class="detail-value">${d.severity || '—'}</span></div>
            <div class="disease-detail-row"><span class="detail-label">Mortality</span><span class="detail-value">${d.mortality_rate || '—'}</span></div>
            ${d.causes ? `<div class="disease-detail-row" style="flex-direction:column;gap:4px;"><span class="detail-label">Causes / Deficiency</span><div class="detail-value">${Array.isArray(d.causes) ? d.causes.join(', ') : d.causes}</div></div>` : ''}
            ${tags ? `<div class="disease-detail-row" style="flex-direction:column;gap:4px;"><span class="detail-label">Matched Symptoms</span><div class="symptom-tags">${tags}</div></div>` : ''}
          </div>
        </div>`;
    });
  }

  // Treatment
  if (data.treatment) {
    const items = Array.isArray(data.treatment) ? data.treatment
      : typeof data.treatment === 'string' ? data.treatment.split('\n').filter(Boolean) : [];
    if (items.length) {
      html += `<div class="treatment-card"><div class="treatment-card-header">💊 Treatment</div>
        <div class="treatment-card-body"><ul>${items.map(t => `<li>${t}</li>`).join('')}</ul></div></div>`;
    }
  }

  // Deficiency / Causes (top-level)
  if (data.deficiency) {
    const defItems = Array.isArray(data.deficiency) ? data.deficiency
      : typeof data.deficiency === 'string' ? [data.deficiency] : [];
    if (defItems.length) {
      html += `<div class="info-card"><div class="info-card-title" style="color:var(--warning);">⚡ Deficiency / Nutritional Cause</div>
        <div class="info-card-content"><ul>${defItems.map(d => `<li>${d}</li>`).join('')}</ul></div></div>`;
    }
  }

  if (data.causes) {
    const causeItems = Array.isArray(data.causes) ? data.causes
      : typeof data.causes === 'string' ? [data.causes] : [];
    if (causeItems.length) {
      html += `<div class="info-card"><div class="info-card-title">� Causes</div>
        <div class="info-card-content"><ul>${causeItems.map(c => `<li>${c}</li>`).join('')}</ul></div></div>`;
    }
  }

  // Prevention
  if (data.prevention && data.prevention.length) {
    html += `<div class="info-card"><div class="info-card-title">�️ Prevention</div>
      <div class="info-card-content"><ul>${data.prevention.map(p => `<li>${p}</li>`).join('')}</ul></div></div>`;
  }

  // Facts
  if (data.facts && data.facts.length) {
    html += `<div class="info-card"><div class="info-card-title">📋 Facts</div>
      <div class="info-card-content"><ul>${data.facts.map(f => `<li>${f}</li>`).join('')}</ul></div></div>`;
  }

  // Vet alert
  if (data.call_vet) {
    html += `<div class="severity-strip critical" style="border-radius:var(--radius);">
      <span>🚨</span> <strong>Immediate veterinary attention recommended!</strong></div>`;
  }

  // Image analysis results (if droppings photo was included)
  if (imageData) {
    html += '<div style="margin-top:16px;"><h3 style="font-size:14px;font-weight:600;margin-bottom:10px;">📸 Droppings Analysis</h3>';

    if (imageData.droppings_type || imageData.color_analysis) {
      html += `<div class="info-card"><div class="info-card-title">💩 Droppings Details</div>
        <div class="info-card-content">
          ${imageData.droppings_type ? `<p><strong>Type:</strong> ${imageData.droppings_type}</p>` : ''}
          ${imageData.color_analysis ? `<p><strong>Color:</strong> ${imageData.color_analysis}</p>` : ''}
          ${imageData.consistency ? `<p><strong>Consistency:</strong> ${imageData.consistency}</p>` : ''}
        </div></div>`;
    }

    if (imageData.health_indicators && imageData.health_indicators.length) {
      html += `<div class="info-card"><div class="info-card-title">🩺 Health Indicators</div>
        <div class="info-card-content"><ul>${imageData.health_indicators.map(h => `<li>${h}</li>`).join('')}</ul></div></div>`;
    }

    if (imageData.possible_conditions && imageData.possible_conditions.length) {
      html += `<div class="info-card"><div class="info-card-title" style="color:var(--warning);">⚠️ Possible Conditions</div>
        <div class="info-card-content"><ul>${imageData.possible_conditions.map(c => `<li>${typeof c === 'object' ? c.name || JSON.stringify(c) : c}</li>`).join('')}</ul></div></div>`;
    }

    if (imageData.recommendations && imageData.recommendations.length) {
      html += `<div class="info-card"><div class="info-card-title">💡 Recommendations</div>
        <div class="info-card-content"><ul>${imageData.recommendations.map(r => `<li>${r}</li>`).join('')}</ul></div></div>`;
    }

    html += '</div>';
  }

  container.innerHTML = html || '<p class="text-muted">No diseases matched the selected symptoms.</p>';
}

// ══════════════════════════════════════
//   IMAGE UPLOAD (in predict panel)
// ══════════════════════════════════════

function initImageUpload() {
  const zone = document.getElementById('uploadZone');
  const input = document.getElementById('imageInput');

  input.addEventListener('change', (e) => {
    if (e.target.files[0]) handleImageFile(e.target.files[0]);
  });

  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) handleImageFile(e.dataTransfer.files[0]);
  });
}

function handleImageFile(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Please upload an image', 'warning');
    return;
  }
  currentImageFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('previewImg').src = e.target.result;
    document.getElementById('uploadPreview').classList.remove('hidden');
    document.getElementById('uploadZone').classList.add('hidden');
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  currentImageFile = null;
  document.getElementById('previewImg').src = '';
  document.getElementById('uploadPreview').classList.add('hidden');
  document.getElementById('uploadZone').classList.remove('hidden');
  document.getElementById('imageInput').value = '';
}

// ══════════════════════════════════════
//   UTILITIES
// ══════════════════════════════════════

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-8px)';
    toast.style.transition = 'all 200ms ease';
    setTimeout(() => toast.remove(), 200);
  }, 3000);
}
