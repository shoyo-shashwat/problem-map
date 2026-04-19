/* ═══════════════════════════════════════════════════════════
   PROBLEM MAP DELHI — Global Script
   All page JS consolidated here. Each section is guarded
   by a check for a page-specific element so functions only
   run on the pages that need them.
   ═══════════════════════════════════════════════════════════ */

/* ──────────────────────────────────────────────────────────
   SHARED GLOBALS (available on every page)
   ────────────────────────────────────────────────────────── */

function showToast(msg, type, duration) {
  duration = duration || 3500;
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = type ? 'show ' + type : 'show';
  setTimeout(function() { t.classList.remove('show', type); }, duration);
}

function timeAgo(ts) {
  var diff = Date.now() / 1000 - ts;
  if (diff < 60)    return 'just now';
  if (diff < 3600)  return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  return Math.floor(diff / 86400) + 'd ago';
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function truncate(s, n) {
  return s && s.length > n ? s.slice(0, n) + '…' : s || '';
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

var TAG_ICONS = {
  pothole:'⬛', water:'◉', garbage:'▣', streetlight:'◎',
  traffic:'▶', noise:'◈', sewage:'⬡', electricity:'◆', tree:'◑', other:'○'
};
var TAG_LABELS = {
  pothole:'Pothole', water:'Water', garbage:'Garbage', streetlight:'Streetlight',
  traffic:'Traffic', noise:'Noise', sewage:'Sewage', electricity:'Electricity',
  tree:'Tree', other:'Other'
};

// Active nav highlight
(function() {
  var path = window.location.pathname;
  var navMap = {
    '/':               'nav-home',
    '/issues-page':    'nav-issues',
    '/my-issues':      'nav-my',
    '/community-page': 'nav-community',
    '/ngo-page':       'nav-ngo',
    '/reputation':     'nav-rep',
    '/ai-assistant':   'nav-ai',
  };
  var activeId = navMap[path];
  if (activeId) {
    var el = document.getElementById(activeId);
    if (el) el.classList.add('active');
  }
})();

// Modal overlay click-outside to close
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.modal-overlay').forEach(function(el) {
    el.addEventListener('click', function(e) {
      if (e.target === el) el.classList.remove('open');
    });
  });
});


/* ──────────────────────────────────────────────────────────
   HOME / INDEX PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('map')) return;

  var CURRENT_USER = window.CURRENT_USER || '';

  // Map init
  var map = L.map('map', { zoomControl: false }).setView([28.6139, 77.2090], 11);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO', maxZoom: 19
  }).addTo(map);
  L.control.zoom({ position: 'bottomright' }).addTo(map);

  var heatmapVisible = false, heatCircles = [];
  var markerLayer = L.layerGroup().addTo(map);
  var allIssues   = [];

  // Area loader for report modal
  fetch('/areas').then(function(r) { return r.json(); }).then(function(areas) {
    var sel = document.getElementById('r-area');
    areas.forEach(function(a) {
      var o = document.createElement('option');
      o.value = a; o.textContent = a; sel.appendChild(o);
    });
  });

  // Load issues
  function loadIssues() {
    var tag    = document.getElementById('filter-tag').value;
    var status = document.getElementById('filter-status').value;
    var url = '/issues?';
    if (tag)    url += 'tag=' + encodeURIComponent(tag) + '&';
    if (status) url += 'status=' + encodeURIComponent(status) + '&';

    fetch(url).then(function(r) { return r.json(); }).then(function(issues) {
      allIssues = issues;
      renderSidebar(issues);
      renderMarkers(issues);
      updateStats(issues);
    }).catch(function() {
      document.getElementById('sidebar-list').innerHTML =
        '<div class="empty-state"><div>Could not load issues</div></div>';
    });
  }

  window.applyFilters = function() { loadIssues(); };

  function updateStats(issues) {
    document.getElementById('stat-total').textContent    = issues.length;
    document.getElementById('stat-resolved').textContent = issues.filter(function(i) { return i.status === 'resolved'; }).length;
    document.getElementById('stat-open').textContent     = issues.filter(function(i) { return !i.status || i.status === 'open'; }).length;
  }

  // Sidebar rendering
  function renderSidebar(issues) {
    var el = document.getElementById('sidebar-list');
    if (!issues.length) {
      el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">○</div><div class="empty-state-title">No issues found</div></div>';
      return;
    }
    el.innerHTML = issues.slice(0, 60).map(function(issue) {
      return '<div class="issue-card" onclick="openDetail(' + issue.id + ')">' +
        '<div class="issue-card-header">' +
          '<span class="badge tag-' + (issue.tag||'other') + '">' + (TAG_LABELS[issue.tag]||'Other') + '</span>' +
          '<span class="badge badge-' + (issue.status||'open') + '">' + (issue.status||'open') + '</span>' +
        '</div>' +
        '<div class="issue-card-desc">' + escHtml(truncate(issue.description, 80)) + '</div>' +
        '<div class="issue-card-meta">' +
          '<span class="issue-area">📍 ' + escHtml(issue.area) + '</span>' +
          '<span class="text-sm text-muted">' + timeAgo(issue.timestamp) + '</span>' +
          '<button class="upvote-btn" onclick="event.stopPropagation(); quickUpvote(' + issue.id + ', this)">▲ <span>' + (issue.upvotes||0) + '</span></button>' +
          (issue.severity === 'high' ? '<span class="badge badge-high">High</span>' : '') +
        '</div>' +
      '</div>';
    }).join('');
  }

  // Map markers
  var TAG_COLORS = {
    pothole:'#A04000', water:'#1A5276', garbage:'#1D6A39', streetlight:'#5D6D7E',
    traffic:'#922B21', noise:'#7D3C98', sewage:'#9A7D0A', electricity:'#935116',
    tree:'#1D6A39', other:'#5D6D7E'
  };

  function makeIcon(tag, status) {
    var color = status === 'resolved' ? '#2D6A4F' : (TAG_COLORS[tag] || '#666');
    var s = 10;
    return L.divIcon({
      html: '<div style="width:' + s + 'px;height:' + s + 'px;background:' + color + ';border:2px solid white;border-radius:50%;box-shadow:0 1px 4px rgba(0,0,0,.3)"></div>',
      className:'', iconSize:[s,s], iconAnchor:[s/2, s/2]
    });
  }

  function renderMarkers(issues) {
    markerLayer.clearLayers();
    issues.forEach(function(issue) {
      if (!issue.lat || !issue.lng) return;
      var m = L.marker([issue.lat, issue.lng], { icon: makeIcon(issue.tag, issue.status) });
      m.bindPopup(
        '<div style="min-width:180px;font-family:\'DM Sans\',sans-serif">' +
          '<div style="font-weight:600;margin-bottom:4px">' + escHtml(issue.area) + '</div>' +
          '<div style="font-size:12px;color:#555;margin-bottom:8px">' + escHtml(truncate(issue.description, 80)) + '</div>' +
          '<button onclick="openDetail(' + issue.id + ')" style="font-size:12px;padding:5px 10px;background:var(--accent);color:white;border:none;border-radius:6px;cursor:pointer;font-family:inherit">View Details</button>' +
        '</div>'
      );
      markerLayer.addLayer(m);
    });
  }

  // Heatmap
  window.toggleHeatmap = function() {
    if (heatmapVisible) {
      heatCircles.forEach(function(c) { map.removeLayer(c); });
      heatCircles = []; heatmapVisible = false; return;
    }
    fetch('/map-data').then(function(r) { return r.json(); }).then(function(data) {
      data.forEach(function(d) {
        var color = d.heat === 'high' ? '#C84B31' : d.heat === 'medium' ? '#E8773F' : '#2D6A4F';
        var c = L.circle([d.lat, d.lng], { radius:800, color:color, fillColor:color, fillOpacity:.25, weight:1 })
          .addTo(map).bindPopup('<b>' + d.area + '</b><br>' + d.count + ' issue' + (d.count !== 1 ? 's' : ''));
        heatCircles.push(c);
      });
      heatmapVisible = true;
    });
  };

  // Geolocation
  window.locateMe = function() {
    if (!navigator.geolocation) { showToast('Geolocation not supported'); return; }
    navigator.geolocation.getCurrentPosition(function(pos) {
      var lat = pos.coords.latitude, lng = pos.coords.longitude;
      map.setView([lat, lng], 14);
      document.getElementById('r-lat').value = lat;
      document.getElementById('r-lng').value = lng;
      L.marker([lat, lng], { icon: L.divIcon({
        html: '<div style="width:14px;height:14px;background:#1B4F72;border:3px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>',
        className:'', iconSize:[14,14], iconAnchor:[7,7]
      })}).addTo(map).bindPopup('Your location').openPopup();
      showToast('Location found!');
    }, function() { showToast('Could not get location'); });
  };

  map.on('click', function(e) {
    document.getElementById('r-lat').value = e.latlng.lat.toFixed(6);
    document.getElementById('r-lng').value = e.latlng.lng.toFixed(6);
  });

  // Report modal
  window.setSeverity = function(sev, btn) {
    document.getElementById('r-severity').value = sev;
    document.querySelectorAll('.sev-btn').forEach(function(b) {
      b.className = 'sev-btn';
      if (b === btn) b.classList.add('active-' + sev);
    });
  };

  window.openReportModal = function() {
    document.getElementById('report-modal').classList.add('open');
  };

  window.previewImage = function(input) {
    var file = input.files[0]; if (!file) return;
    var reader = new FileReader();
    reader.onload = function(e) {
      var img = document.getElementById('r-preview');
      img.src = e.target.result; img.style.display = 'block';
      document.getElementById('upload-placeholder').style.display = 'none';
    };
    reader.readAsDataURL(file);
  };

  window.submitReport = async function() {
    var desc     = document.getElementById('r-desc').value.trim();
    var area     = document.getElementById('r-area').value;
    var user     = document.getElementById('r-user').value.trim() || 'anonymous';
    var landmark = document.getElementById('r-landmark').value.trim();
    var contact  = document.getElementById('r-contact').value.trim();
    var lat      = document.getElementById('r-lat').value;
    var lng      = document.getElementById('r-lng').value;
    var severity = document.getElementById('r-severity').value || 'high';

    if (!desc || desc.length < 10) { showToast('Please add a description (at least 10 chars)'); return; }
    if (!area)                      { showToast('Please select an area'); return; }

    var btn     = document.getElementById('submit-btn');
    var aiStrip = document.getElementById('ai-status');
    btn.disabled = true;
    btn.textContent = 'Submitting…';
    aiStrip.className = 'checking';
    aiStrip.textContent = '✦ AI is checking your report…';
    aiStrip.style.display = 'block';

    var formData = new FormData();
    formData.append('user', user); formData.append('area', area);
    formData.append('description', desc); formData.append('severity', severity);
    formData.append('landmark', landmark); formData.append('contact', contact);
    if (lat) formData.append('lat', lat);
    if (lng) formData.append('lng', lng);
    var imageFile = document.getElementById('r-image').files[0];
    if (imageFile) formData.append('image', imageFile);

    try {
      var resp = await fetch('/report', { method: 'POST', body: formData });
      var data = await resp.json();

      if (data.status === 'spam') {
        aiStrip.className = ''; aiStrip.style.display = 'none';
        var alertDiv = document.createElement('div');
        alertDiv.className = 'spam-alert';
        alertDiv.innerHTML = '<strong>⚠ Report Flagged as Spam</strong>' + escHtml(data.reason || 'Your submission was flagged by our AI.') +
          '<div style="margin-top:8px;font-size:12px;color:#7F1D1D">If you believe this is an error, please rephrase your description and try again.</div>';
        aiStrip.parentNode.insertBefore(alertDiv, aiStrip.nextSibling);
        btn.disabled = false; btn.textContent = 'Submit Report'; return;
      }

      if (data.status === 'ok') {
        var msg = 'Reported! +' + data.points_earned + ' pts. Category: ' + data.tag;
        var corr = data.spelling_corrections || [];
        if (corr.length) {
          aiStrip.className = 'ok';
          aiStrip.innerHTML = '<strong>✦ AI spell-corrected your report:</strong> ' + corr.map(function(c) { return '<span class="spell-tag">' + escHtml(c) + '</span>'; }).join(' ');
          aiStrip.style.display = 'block';
          setTimeout(function() { aiStrip.style.display = 'none'; }, 5000);
        } else {
          aiStrip.style.display = 'none';
        }
        showToast(msg);
        closeModal('report-modal');
        loadIssues();
        document.getElementById('r-desc').value = '';
      } else {
        aiStrip.style.display = 'none';
        showToast(data.error || 'Error submitting report');
      }
    } catch(e) {
      aiStrip.style.display = 'none';
      showToast('Network error. Please try again.');
    } finally {
      btn.disabled = false; btn.textContent = 'Submit Report';
    }
  };

  // Detail modal
  window.openDetail = function(id) {
    var issue = allIssues.find(function(i) { return i.id === id; });
    if (!issue) return;
    var statusColors = { open:'badge-open', resolved:'badge-resolved', escalated:'badge-escalated', verified:'badge-verified' };
    var sc = statusColors[issue.status||'open'] || 'badge-open';
    document.getElementById('detail-content').innerHTML =
      '<button class="modal-close" onclick="closeModal(\'detail-modal\')">✕</button>' +
      (issue.image ? '<img src="' + issue.image + '" class="detail-image"/>' : '') +
      '<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap">' +
        '<span class="badge tag-' + (issue.tag||'other') + '">' + (TAG_LABELS[issue.tag]||'Other') + '</span>' +
        '<span class="badge ' + sc + '">' + (issue.status||'open') + '</span>' +
        (issue.severity ? '<span class="badge badge-' + issue.severity + '">' + issue.severity + '</span>' : '') +
      '</div>' +
      '<div style="font-size:15px;font-weight:500;margin-bottom:14px">' + escHtml(issue.description) + '</div>' +
      '<div class="detail-meta">' +
        '<div class="detail-meta-item"><label>Area</label><value>' + escHtml(issue.area) + '</value></div>' +
        '<div class="detail-meta-item"><label>Reported by</label><value>' + escHtml(issue.user||'anonymous') + '</value></div>' +
        '<div class="detail-meta-item"><label>Reported</label><value>' + timeAgo(issue.timestamp) + '</value></div>' +
        '<div class="detail-meta-item"><label>Upvotes</label><value>' + (issue.upvotes||0) + '</value></div>' +
        (issue.landmark ? '<div class="detail-meta-item"><label>Landmark</label><value>' + escHtml(issue.landmark) + '</value></div>' : '') +
        (issue.assigned_to ? '<div class="detail-meta-item"><label>Assigned to</label><value>' + escHtml(issue.assigned_to) + '</value></div>' : '') +
      '</div>' +
      '<div style="display:flex;gap:8px;margin-top:16px">' +
        '<button class="btn btn-outline" onclick="upvoteDetail(' + issue.id + ')">▲ Upvote (' + (issue.upvotes||0) + ')</button>' +
        '<a href="/issues-page" class="btn btn-ghost">View All Issues</a>' +
      '</div>';
    document.getElementById('detail-modal').classList.add('open');
  };

  window.upvoteDetail = async function(id) {
    var r = await fetch('/upvote/' + id, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user: CURRENT_USER||'anonymous'}) });
    var d = await r.json();
    if (d.status === 'ok') { showToast('+2 pts'); loadIssues(); closeModal('detail-modal'); }
  };

  window.quickUpvote = async function(id, btn) {
    var r = await fetch('/upvote/' + id, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user: CURRENT_USER||'anonymous'}) });
    var d = await r.json();
    if (d.status === 'ok') {
      showToast('+2 pts');
      var span = btn.querySelector('span');
      if (span) span.textContent = parseInt(span.textContent||0) + 1;
    }
  };

  loadIssues();
})();


/* ──────────────────────────────────────────────────────────
   AI ASSISTANT PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('ai-map')) return;

  var CURRENT_USER = window.CURRENT_USER || null;

  // Map setup
  var map = L.map('ai-map', { zoomControl: true }).setView([28.6139, 77.2090], 11);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© CartoDB', maxZoom: 19
  }).addTo(map);

  var heatmarkers = [], pinmarkers = [], highlightCircles = [];

  function clearPins() {
    pinmarkers.forEach(function(m) { map.removeLayer(m); }); pinmarkers = [];
    highlightCircles.forEach(function(c) { map.removeLayer(c); }); highlightCircles = [];
  }

  // Load base heatmap
  fetch('/map-data').then(function(r) { return r.json(); }).then(function(data) {
    data.forEach(function(d) {
      var colors = { high:'#C84B31', medium:'#E8773F', low:'#2D6A4F' };
      var sizes  = { high: 22, medium: 16, low: 11 };
      var color  = colors[d.heat] || '#888';
      var size   = sizes[d.heat]  || 11;
      var icon = L.divIcon({
        html: '<div style="background:' + color + ';width:' + size + 'px;height:' + size + 'px;border-radius:50%;border:2px solid rgba(255,255,255,.4);opacity:.85"></div>',
        className: '', iconSize: [size, size]
      });
      var m = L.marker([d.lat, d.lng], { icon: icon }).addTo(map);
      m.bindPopup('<div class="map-popup-title">' + d.area + '</div><div class="map-popup-stat">' + d.count + ' issue' + (d.count > 1 ? 's' : '') + '</div><span class="map-popup-heat heat-' + d.heat + '">' + d.heat.toUpperCase() + '</span>');
      heatmarkers.push(m);
    });
  });

  // Chat state
  var history = [];

  window.autoResize = function(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  window.handleKey = function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  window.sendQuick = function(text) {
    document.getElementById('chatInput').value = text;
    sendMessage();
  };

  window.sendMessage = async function() {
    var input = document.getElementById('chatInput');
    var text  = input.value.trim();
    if (!text) return;
    input.value = ''; input.style.height = 'auto';

    appendMsg('user', text);
    history.push({ role: 'user', content: text });

    var typingId = appendTyping();
    try {
      var res  = await fetch('/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history.slice(-8) })
      });
      var data = await res.json();
      removeTyping(typingId);
      handleAIResponse(data);
      history.push({ role: 'assistant', content: data.message || '' });
    } catch(e) {
      removeTyping(typingId);
      appendMsg('ai', '⚠ Connection error. Please try again.');
    }
  };

  function handleAIResponse(data) {
    var extras = [];
    if (data.spelling_corrections && data.spelling_corrections.length) extras.push({ type: 'spell', items: data.spelling_corrections });
    if (data.status === 'spam') extras.push({ type: 'spam', reason: data.reason });
    if (data.pinpoints && data.pinpoints.length) { extras.push({ type: 'pins', pins: data.pinpoints }); renderPins(data.pinpoints); }
    if (data.action) executeMapAction(data.action);
    if (data.table && data.table.length) { renderTable(data.table); extras.push({ type: 'table-hint' }); }
    appendMsg('ai', data.message || '…', extras);
  }

  function renderPins(pins) {
    clearPins();
    var bounds = [];
    pins.forEach(function(p) {
      if (!p.lat || !p.lng) return;
      var colors = { high:'#C84B31', medium:'#E8773F', low:'#2D6A4F' };
      var color  = colors[p.heat] || '#C84B31';
      var icon   = L.divIcon({
        html: '<div style="background:' + color + ';width:18px;height:18px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4);animation:pulse 1.5s infinite"></div><style>@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}</style>',
        className: '', iconSize: [18, 18]
      });
      var m = L.marker([p.lat, p.lng], { icon: icon }).addTo(map);
      m.bindPopup('<div class="map-popup-title">📍 ' + (p.label||p.area) + '</div>').openPopup();
      pinmarkers.push(m);
      bounds.push([p.lat, p.lng]);
    });
    if      (bounds.length === 1) map.setView(bounds[0], 13, { animate: true });
    else if (bounds.length  >  1) map.fitBounds(bounds, { padding: [40, 40], animate: true });
  }

  function executeMapAction(action) {
    if (action.type === 'zoom_to') {
      map.setView([action.lat, action.lng], action.zoom || 13, { animate: true });
    } else if (action.type === 'highlight_areas') {
      clearPins();
      fetch('/map-data').then(function(r) { return r.json(); }).then(function(data) {
        var bounds = [];
        action.areas.forEach(function(areaName) {
          var d = data.find(function(x) { return x.area === areaName; });
          if (!d) return;
          var circle = L.circle([d.lat, d.lng], { radius:600, color:'#C84B31', fillColor:'#C84B31', fillOpacity:.2, weight:2 }).addTo(map);
          highlightCircles.push(circle);
          bounds.push([d.lat, d.lng]);
        });
        if      (bounds.length > 1) map.fitBounds(bounds, { padding: [60, 60], animate: true });
        else if (bounds.length === 1) map.setView(bounds[0], 12, { animate: true });
      });
    } else if (action.type === 'show_heatmap') {
      map.setView([28.6139, 77.2090], 11, { animate: true });
    }
  }

  function renderTable(rows) {
    if (!rows || !rows.length) return;
    var panel = document.getElementById('dataPanel');
    var title = document.getElementById('dataPanelTitle');
    var cont  = document.getElementById('dataPanelContent');
    title.textContent = rows[0].area ? 'Area Comparison' : 'Data Table';
    panel.classList.add('show');
    var skip  = ['lat', 'lng'];
    var keys  = Object.keys(rows[0]).filter(function(k) { return !skip.includes(k); });
    var labels = { area:'Area', total:'Total', high_severity:'High Sev.', resolved:'Resolved', open_issues:'Open', upvotes:'Upvotes', resolution_rate:'Resolved %', most_common_tag:'Top Issue', rank:'Rank', severity_score:'Sev. Score', unresolved:'Unresolved', last_report:'Last Report' };
    cont.innerHTML =
      '<table class="compare-table"><thead><tr>' + keys.map(function(k) { return '<th>' + (labels[k]||k) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      rows.map(function(row) {
        return '<tr>' + keys.map(function(k) {
          var v = row[k];
          if (k === 'area')            return '<td><strong>' + escHtml(String(v)) + '</strong></td>';
          if (k === 'resolution_rate') return '<td class="num">' + v + '%</td>';
          if (k === 'most_common_tag') return '<td><span class="badge tag-' + (v||'other') + '">' + (TAG_LABELS[v]||v||'—') + '</span></td>';
          if (k === 'last_report' && v) return '<td>' + timeAgo(v) + '</td>';
          if (typeof v === 'number')   return '<td class="num">' + v + '</td>';
          return '<td>' + escHtml(String(v != null ? v : '—')) + '</td>';
        }).join('') + '</tr>';
      }).join('') + '</tbody></table>';
  }

  // Message rendering
  var typingCounter = 0;

  function appendTyping() {
    var id = 'typing-' + (++typingCounter);
    var el = document.createElement('div');
    el.className = 'msg ai'; el.id = id;
    el.innerHTML = '<div class="msg-avatar">AI</div><div class="msg-body"><div class="typing"><span></span><span></span><span></span></div></div>';
    document.getElementById('messages').appendChild(el);
    scrollDown(); return id;
  }

  function removeTyping(id) {
    var el = document.getElementById(id); if (el) el.remove();
  }

  function appendMsg(role, text, extras) {
    extras = extras || [];
    var msgs = document.getElementById('messages');
    var wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    var initials = role === 'user' ? (CURRENT_USER ? CURRENT_USER[0].toUpperCase() : 'U') : 'AI';
    var formatted = escHtml(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`(.+?)`/g, '<code>$1</code>').replace(/\n/g, '<br>');
    var extrasHTML = '';
    extras.forEach(function(ex) {
      if (ex.type === 'spell') {
        extrasHTML += '<div class="spell-chip"><span style="font-size:11px;color:var(--text2);margin-right:3px">✏ Corrected:</span>' + ex.items.map(function(s) { return '<span class="spell-item">' + escHtml(s) + '</span>'; }).join('') + '</div>';
      } else if (ex.type === 'spam') {
        extrasHTML += '<div class="spam-alert-msg"><strong>⚠ Spam Detected</strong>' + escHtml(ex.reason) + '</div>';
      } else if (ex.type === 'pins') {
        extrasHTML += '<div class="pin-chips">' + ex.pins.map(function(p) { return '<span class="pin-chip" onclick="aiMap.setView([' + p.lat + ',' + p.lng + '],14,{animate:true})">📍 ' + escHtml(p.area||p.label||'') + '</span>'; }).join('') + '</div>';
      } else if (ex.type === 'table-hint') {
        extrasHTML += '<div class="table-hint">📊 Table shown below map ↙</div>';
      }
    });
    wrap.innerHTML = '<div class="msg-avatar">' + initials + '</div><div class="msg-body"><div class="msg-bubble">' + formatted + '</div>' + extrasHTML + '</div>';
    msgs.appendChild(wrap);
    scrollDown();
  }

  function scrollDown() {
    var msgs = document.getElementById('messages');
    msgs.scrollTop = msgs.scrollHeight;
  }

  // Expose map for pin chips
  window.aiMap = map;

  // Close data panel
  window.closeDataPanel = function() {
    document.getElementById('dataPanel').classList.remove('show');
  };
})();


/* ──────────────────────────────────────────────────────────
   COMMUNITY PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('feed-posts')) return;

  var CURRENT_USER = window.CURRENT_USER || '';
  var currentArea = '';
  var TYPE_ICONS  = { update: '○', question: '?', alert: '!', resolved: '✓' };
  var TYPE_COLORS = { update: 'var(--blue)', question: 'var(--amber)', alert: 'var(--accent)', resolved: 'var(--green)' };

  window.setChannel = function(name, el) {
    document.querySelectorAll('.channel-item').forEach(function(c) { c.classList.remove('active'); });
    el.classList.add('active');
    currentArea = el.dataset.area || '';
    document.getElementById('feed-title').textContent = name;
    document.getElementById('feed-sub').textContent = currentArea ? currentArea + ' community posts' : 'All Delhi civic updates';
    loadPosts();
  };

  function loadPosts() {
    var url = '/community/posts?limit=50';
    if (currentArea) url += '&area=' + encodeURIComponent(currentArea);
    fetch(url).then(function(r) { return r.json(); }).then(function(posts) {
      posts.sort(function(a, b) { return b.timestamp - a.timestamp; });
      document.getElementById('post-count').textContent = posts.length + ' post' + (posts.length !== 1 ? 's' : '');
      renderPosts(posts);
      buildTopPosters(posts);
    }).catch(function() {
      document.getElementById('feed-posts').innerHTML = '<div class="empty-state"><div>Error loading posts</div></div>';
    });
  }

  function renderPosts(posts) {
    var el = document.getElementById('feed-posts');
    if (!posts.length) {
      el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">○</div><div class="empty-state-title">No posts yet</div><div>Be the first to post in this channel!</div></div>';
      return;
    }
    el.innerHTML = posts.map(function(p) {
      var initials = (p.user||'A').slice(0,2).toUpperCase();
      var icon  = TYPE_ICONS[p.post_type||'update'] || '○';
      var color = TYPE_COLORS[p.post_type||'update'] || 'var(--blue)';
      var bgColor = p.post_type==='alert' ? '#FFF5F5' : p.post_type==='resolved' ? '#F0FFF4' : 'var(--surface)';
      return '<div class="post-card" style="background:' + bgColor + '">' +
        '<div class="post-header">' +
          '<div class="post-avatar" style="background:' + color + '">' + initials + '</div>' +
          '<div class="post-meta">' +
            '<div class="post-user">' + escHtml(p.user||'Anonymous') + '</div>' +
            '<div class="post-time">' + timeAgo(p.timestamp) + ' · ' + escHtml(p.area||'Delhi') + '</div>' +
          '</div>' +
          '<span class="badge" style="background:' + color + '22;color:' + color + ';font-size:11px">' + icon + ' ' + (p.post_type||'update') + '</span>' +
        '</div>' +
        '<div class="post-body">' + escHtml(p.message) + '</div>' +
        '<div class="post-footer">' +
          '<button class="like-btn" onclick="likePost(' + p.id + ', this)">♥ <span>' + (p.likes||0) + '</span></button>' +
          '<span class="text-sm text-muted">' + (p.likes||0) + ' like' + (p.likes!==1?'s':'') + '</span>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function buildTopPosters(posts) {
    var counts = {};
    posts.forEach(function(p) { counts[p.user||'Anonymous'] = (counts[p.user||'Anonymous']||0) + 1; });
    var sorted = Object.entries(counts).sort(function(a,b) { return b[1]-a[1]; }).slice(0,5);
    document.getElementById('top-posters').innerHTML = sorted.map(function(entry, i) {
      var user = entry[0], count = entry[1];
      return '<div class="top-poster"><span class="poster-rank">' + (i+1) + '</span>' +
        '<div class="post-avatar" style="width:22px;height:22px;font-size:9px;flex-shrink:0">' + user.slice(0,2).toUpperCase() + '</div>' +
        '<span style="flex:1;font-size:12.5px">' + escHtml(user) + '</span>' +
        '<span class="text-sm text-muted">' + count + '</span></div>';
    }).join('') || '<div class="text-sm text-muted">No posts yet</div>';
  }

  window.likePost = async function(id, btn) {
    var user = CURRENT_USER || document.getElementById('compose-user').value.trim();
    if (!user) { showToast('Please enter your name first'); return; }
    var r = await fetch('/community/like/' + id, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user: user}) });
    var d = await r.json();
    if (d.status === 'ok') {
      var span = btn.querySelector('span');
      if (span) span.textContent = parseInt(span.textContent||0) + 1;
      btn.style.color = 'var(--accent)'; btn.style.borderColor = 'var(--accent)';
    } else { showToast(d.error || 'Already liked'); }
  };

  window.submitPost = async function() {
    var message = document.getElementById('compose-text').value.trim();
    var user    = document.getElementById('compose-user').value.trim() || CURRENT_USER;
    var type    = document.getElementById('compose-type').value;
    if (!message || message.length < 5) { showToast('Please write a message (min 5 chars)'); return; }
    if (!user) { showToast('Please enter your name'); return; }
    var r = await fetch('/community/post', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user: user, message: message, area: currentArea || 'Delhi', type: type }) });
    var d = await r.json();
    if (d.status === 'ok') {
      showToast('Posted! +' + d.points_earned + ' pts');
      document.getElementById('compose-text').value = '';
      loadPosts();
    } else { showToast(d.error || 'Error posting'); }
  };

  loadPosts();
  setInterval(loadPosts, 30000);
})();


/* ──────────────────────────────────────────────────────────
   ISSUES PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('issues-grid')) return;

  var CURRENT_USER = window.CURRENT_USER || '';
  var activeTag = '', activeStatus = '', activeSev = '', searchQ = '';
  var allIssues = [];

  window.setTag = function(el, val) {
    activeTag = val;
    document.querySelectorAll('#tag-chips .chip').forEach(function(c) { c.classList.remove('active'); });
    el.classList.add('active'); loadIssues();
  };
  window.setStatus = function(el, val) {
    activeStatus = val;
    document.querySelectorAll('#status-chips .chip').forEach(function(c) { c.classList.remove('active'); });
    el.classList.add('active'); loadIssues();
  };
  window.setSev = function(el, val) {
    activeSev = val;
    document.querySelectorAll('#sev-chips .chip').forEach(function(c) { c.classList.remove('active'); });
    el.classList.add('active'); loadIssues();
  };

  var searchTimer;
  window.debounceSearch = function() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function() { searchQ = document.getElementById('search-input').value.trim(); loadIssues(); }, 300);
  };

  function loadIssues() {
    var url = '/issues?';
    if (activeTag)    url += 'tag=' + encodeURIComponent(activeTag) + '&';
    if (activeStatus) url += 'status=' + encodeURIComponent(activeStatus) + '&';
    if (searchQ)      url += 'q=' + encodeURIComponent(searchQ) + '&';

    fetch(url).then(function(r) { return r.json(); }).then(function(issues) {
      allIssues = issues;
      var filtered = activeSev ? issues.filter(function(i) { return (i.severity||'medium') === activeSev; }) : issues;
      var sort = document.getElementById('sort-by').value;
      if (sort === 'upvotes') filtered.sort(function(a,b) { return (b.upvotes||0)-(a.upvotes||0); });
      else if (sort === 'priority') filtered.sort(function(a,b) { return (b.priority||0)-(a.priority||0); });
      else filtered.sort(function(a,b) { return b.timestamp-a.timestamp; });
      renderStatusBar(issues);
      renderGrid(filtered);
      document.getElementById('issues-count').textContent = filtered.length + ' issue' + (filtered.length!==1?'s':'') + ' found';
    }).catch(function() {
      document.getElementById('issues-grid').innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--text2); padding:40px">Error loading issues</div>';
    });
  }

  function renderStatusBar(issues) {
    var counts = { open:0, resolved:0, escalated:0, verified:0 };
    issues.forEach(function(i) { var s = i.status||'open'; if(counts[s]!==undefined) counts[s]++; });
    var colors = { open:'#1B4F72', resolved:'#2D6A4F', escalated:'#B7770D', verified:'#5D6D7E' };
    document.getElementById('status-bar').innerHTML = Object.entries(counts).map(function(entry) {
      var s = entry[0], c = entry[1];
      return '<div class="status-count"><div class="status-dot" style="background:' + colors[s] + '"></div><strong>' + c + '</strong> ' + s + '</div>';
    }).join('<span style="color:var(--border)">|</span>');
  }

  function renderGrid(issues) {
    var grid = document.getElementById('issues-grid');
    if (!issues.length) {
      grid.innerHTML = '<div style="grid-column:1/-1"><div class="empty-state"><div class="empty-state-icon">○</div><div class="empty-state-title">No issues found</div><div>Try different filters</div></div></div>';
      return;
    }
    grid.innerHTML = issues.map(function(issue) {
      var statusBadge = '<span class="badge badge-' + (issue.status||'open') + '">' + (issue.status||'open') + '</span>';
      var sevBadge = issue.severity ? '<span class="badge badge-' + issue.severity + '">' + issue.severity + '</span>' : '';
      return '<div class="issue-full-card" onclick="openIssueDetail(' + issue.id + ')">' +
        (issue.image ? '<img src="' + issue.image + '" class="issue-full-card-img" loading="lazy"/>' : '') +
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">' +
          '<span class="badge tag-' + (issue.tag||'other') + '">' + (TAG_LABELS[issue.tag]||'Other') + '</span>' + statusBadge + sevBadge +
        '</div>' +
        '<div class="issue-desc">' + escHtml(truncate(issue.description, 100)) + '</div>' +
        '<div class="issue-footer">' +
          '<div>' +
            '<div style="font-size:12px;color:var(--text2)">📍 ' + escHtml(issue.area) + '</div>' +
            '<div style="font-size:11.5px;color:var(--text3);margin-top:2px">' + timeAgo(issue.timestamp) + ' · by ' + escHtml(issue.user||'anon') + '</div>' +
          '</div>' +
          '<button class="btn btn-outline btn-sm" onclick="event.stopPropagation();issueQuickUpvote(' + issue.id + ',this)">▲ ' + (issue.upvotes||0) + '</button>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  window.issueQuickUpvote = async function(id, btn) {
    var r = await fetch('/upvote/' + id, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user:CURRENT_USER||'anonymous'})});
    var d = await r.json();
    if (d.status==='ok') { showToast('+2 pts'); btn.textContent = '▲ ' + (parseInt(btn.textContent.replace('▲','').trim()||0)+1); }
  };

  window.openIssueDetail = function(id) {
    var issue = allIssues.find(function(i) { return i.id === id; });
    if (!issue) return;
    var statusColors = { open:'badge-open', resolved:'badge-resolved', escalated:'badge-escalated', verified:'badge-verified' };
    document.getElementById('detail-content').innerHTML =
      '<button class="modal-close" onclick="closeModal(\'detail-modal\')">✕</button>' +
      (issue.image ? '<img src="' + issue.image + '" style="width:100%;border-radius:8px;margin-bottom:16px;max-height:220px;object-fit:cover"/>' : '') +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">' +
        '<span class="badge tag-' + (issue.tag||'other') + '">' + (TAG_LABELS[issue.tag]||'Other') + '</span>' +
        '<span class="badge ' + (statusColors[issue.status||'open']||'badge-open') + '">' + (issue.status||'open') + '</span>' +
        (issue.severity ? '<span class="badge badge-' + issue.severity + '">' + issue.severity + '</span>' : '') +
        (issue.verified ? '<span class="badge badge-verified">Verified</span>' : '') +
      '</div>' +
      '<div style="font-size:15px;font-weight:500;line-height:1.5;margin-bottom:14px">' + escHtml(issue.description) + '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0">' +
        '<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--text3)">Area</div><div style="font-weight:500;margin-top:2px">' + escHtml(issue.area) + '</div></div>' +
        '<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--text3)">Reported by</div><div style="font-weight:500;margin-top:2px">' + escHtml(issue.user||'anonymous') + '</div></div>' +
        '<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--text3)">Reported</div><div style="font-weight:500;margin-top:2px">' + timeAgo(issue.timestamp) + '</div></div>' +
        '<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--text3)">Upvotes</div><div style="font-weight:500;margin-top:2px">' + (issue.upvotes||0) + '</div></div>' +
        (issue.landmark ? '<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--text3)">Landmark</div><div style="font-weight:500;margin-top:2px">' + escHtml(issue.landmark) + '</div></div>' : '') +
        (issue.assigned_to ? '<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--text3)">Assigned to</div><div style="font-weight:500;margin-top:2px">' + escHtml(issue.assigned_to) + '</div></div>' : '') +
      '</div>' +
      '<div style="display:flex;gap:8px;margin-top:16px">' +
        '<button class="btn btn-primary" onclick="issuesUpvoteDetail(' + issue.id + ')">▲ Upvote</button>' +
        '<button class="btn btn-outline" onclick="closeModal(\'detail-modal\')">Close</button>' +
      '</div>';
    document.getElementById('detail-modal').classList.add('open');
  };

  window.issuesUpvoteDetail = async function(id) {
    var r = await fetch('/upvote/' + id, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user:CURRENT_USER||'anonymous'})});
    var d = await r.json();
    if (d.status==='ok') { showToast('+2 pts'); loadIssues(); closeModal('detail-modal'); }
  };

  loadIssues();
})();


/* ──────────────────────────────────────────────────────────
   LOGIN PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('tab-quick')) return;

  window.switchTab = function(tab) {
    document.querySelectorAll('.tab-btn').forEach(function(b, i) {
      b.classList.toggle('active', (i===0 && tab==='quick') || (i===1 && tab==='email'));
    });
    document.getElementById('tab-quick').classList.toggle('active', tab==='quick');
    document.getElementById('tab-email').classList.toggle('active', tab==='email');
  };

  window.handleEmailLogin = function(e) {
    e.preventDefault();
    var email = document.getElementById('email-field').value.trim();
    var pass  = document.getElementById('password-field').value;
    if (!email || !pass) { showToast('Please fill in all fields'); return; }
    var name = email.split('@')[0].replace(/[._]/g,' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    var form = document.createElement('form');
    form.method = 'POST'; form.action = '/login';
    var inp = document.createElement('input');
    inp.name = 'name'; inp.value = name;
    form.appendChild(inp); document.body.appendChild(form); form.submit();
  };

  window.handleRegister = function(e) {
    e.preventDefault();
    showToast('Registration coming soon — use Quick Sign In for now');
  };
})();


/* ──────────────────────────────────────────────────────────
   MY ISSUES PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('issues-list')) return;
  // Guard: only run on my-issues page (has stats-row but not issues-grid)
  if (document.getElementById('issues-grid')) return;

  var CURRENT_USER = window.CURRENT_USER || '';

  function getStatusSteps(status) {
    var steps = ['open', 'verified', 'escalated', 'resolved'];
    var idx = steps.indexOf(status || 'open');
    return steps.map(function(s, i) {
      return { label: s.charAt(0).toUpperCase() + s.slice(1), state: i < idx ? 'done' : i === idx ? 'active' : 'pending' };
    });
  }

  async function load() {
    var issueRes = await fetch('/my-issues-data?user=' + encodeURIComponent(CURRENT_USER));
    var statsRes = await fetch('/user/stats?name=' + encodeURIComponent(CURRENT_USER));
    var issues   = await issueRes.json();
    var stats    = await statsRes.json();

    document.getElementById('s-total').textContent    = stats.total_reported || 0;
    document.getElementById('s-resolved').textContent = stats.total_resolved || 0;
    document.getElementById('s-open').textContent     = (stats.total_reported||0) - (stats.total_resolved||0);
    document.getElementById('s-points').textContent   = stats.points || 0;

    var list = document.getElementById('issues-list');
    if (!issues.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">○</div><div class="empty-state-title">No reports yet</div><div>Start by reporting a civic issue in your area.</div><br><a href="/" class="btn btn-primary">Report an Issue</a></div>';
      return;
    }

    var statusColors = { open:'badge-open', resolved:'badge-resolved', escalated:'badge-escalated', verified:'badge-verified' };
    list.innerHTML = issues.map(function(issue) {
      var steps = getStatusSteps(issue.status);
      return '<div class="my-issue-card">' +
        (issue.image ? '<img class="my-issue-card-img" src="' + issue.image + '" loading="lazy"/>' : '<div class="my-issue-img-placeholder">○</div>') +
        '<div class="my-issue-body">' +
          '<div class="my-issue-header">' +
            '<div style="display:flex;gap:6px;flex-wrap:wrap">' +
              '<span class="badge tag-' + (issue.tag||'other') + '">' + (TAG_LABELS[issue.tag]||'Other') + '</span>' +
              '<span class="badge ' + (statusColors[issue.status||'open']||'badge-open') + '">' + (issue.status||'open') + '</span>' +
              (issue.severity ? '<span class="badge badge-' + issue.severity + '">' + issue.severity + '</span>' : '') +
            '</div>' +
            '<span class="text-sm text-muted">' + timeAgo(issue.timestamp) + '</span>' +
          '</div>' +
          '<div class="my-issue-desc">' + escHtml(issue.description) + '</div>' +
          '<div class="my-issue-meta">' +
            '<span class="text-sm text-muted">📍 ' + escHtml(issue.area) + '</span>' +
            '<span class="text-sm text-muted">▲ ' + (issue.upvotes||0) + ' upvotes</span>' +
            (issue.assigned_to ? '<span class="text-sm text-muted">→ ' + escHtml(issue.assigned_to) + '</span>' : '') +
          '</div>' +
          '<div class="status-timeline">' +
            steps.map(function(step, i) {
              return (i > 0 ? '<div class="timeline-line"></div>' : '') +
                '<div class="timeline-step">' +
                  '<div class="timeline-dot ' + step.state + '"></div>' +
                  '<span style="color:' + (step.state==='active'?'var(--accent)':step.state==='done'?'var(--green)':'var(--text3)') + ';font-weight:' + (step.state!=='pending'?'500':'400') + '">' + step.label + '</span>' +
                '</div>';
            }).join('') +
          '</div>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  load();
})();


/* ──────────────────────────────────────────────────────────
   NGOs PAGE
   ────────────────────────────────────────────────────────── */

(function() {
  if (!document.getElementById('ngo-map')) return;

  var CURRENT_USER = window.CURRENT_USER || '';
  var currentTab = 'nearby';
  var userLat = 28.6139, userLng = 77.2090;
  var ngoMarkers = [];

  var ngoMap = L.map('ngo-map', { zoomControl: false }).setView([28.6139, 77.2090], 11);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO', maxZoom: 19
  }).addTo(ngoMap);
  L.control.zoom({ position: 'bottomright' }).addTo(ngoMap);

  // Get user location
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(pos) {
      userLat = pos.coords.latitude; userLng = pos.coords.longitude;
      ngoMap.setView([userLat, userLng], 12);
      L.circleMarker([userLat, userLng], { radius:7, color:'#1B4F72', fillColor:'#1B4F72', fillOpacity:1, weight:3 }).addTo(ngoMap).bindPopup('Your location');
      if (currentTab === 'nearby') loadCurrentTab();
    }, function() {});
  }

  window.switchTab = function(tab, el) {
    currentTab = tab;
    document.querySelectorAll('.ngos-tab').forEach(function(t) { t.classList.remove('active'); });
    el.classList.add('active');
    loadCurrentTab();
  };

  function loadCurrentTab() {
    if (currentTab === 'nearby') loadNearby();
    else if (currentTab === 'ranking') loadRanking();
    else loadGovt();
  }
  window.loadCurrentTab = loadCurrentTab;

  function loadNearby() {
    var tag = document.getElementById('ngo-tag-filter').value;
    var url = '/ngo/nearby?lat=' + userLat + '&lng=' + userLng;
    if (tag) url += '&tag=' + encodeURIComponent(tag);
    fetch(url).then(function(r) { return r.json(); }).then(function(ngos) { renderNGOs(ngos, true); plotNGOMarkers(ngos); });
  }

  function loadRanking() {
    var tag  = document.getElementById('ngo-tag-filter').value;
    var sort = document.getElementById('ngo-sort').value;
    var url  = '/ngo/all?sort=' + sort;
    if (tag) url += '&tag=' + encodeURIComponent(tag);
    fetch(url).then(function(r) { return r.json(); }).then(function(ngos) { renderNGOs(ngos, false, true); plotNGOMarkers(ngos); });
  }

  function loadGovt() {
    var tag = document.getElementById('ngo-tag-filter').value;
    var url = '/gov/all?' + (tag ? 'tag=' + encodeURIComponent(tag) : '');
    fetch(url).then(function(r) { return r.json(); }).then(function(agencies) {
      renderGovt(agencies);
      plotNGOMarkers(agencies.map(function(a) { return Object.assign({}, a, {issues_resolved: a.issues_resolved||0, rating:4.0}); }));
    });
  }

  function stars(rating) {
    var full = Math.floor(rating), half = rating - full >= 0.5 ? 1 : 0;
    return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(5 - full - half);
  }

  function escJs(s) { if(!s)return''; return String(s).replace(/'/g,"\\'"); }

  function renderNGOs(ngos, showDist, showRank) {
    var el = document.getElementById('ngos-content');
    if (!ngos.length) { el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">○</div><div class="empty-state-title">No NGOs found</div></div>'; return; }
    el.innerHTML = ngos.map(function(ngo, i) {
      var rank = i + 1;
      var rankClass = rank <= 3 ? 'rank-' + rank : 'rank-n';
      return '<div class="ngo-card" onclick="focusNGO(' + ngo.lat + ',' + ngo.lng + ',\'' + escJs(ngo.name) + '\')">' +
        '<div class="ngo-card-header">' +
          (showRank ? '<div class="rank-badge ' + rankClass + '">' + rank + '</div>' : '') +
          '<div class="ngo-icon-box">' + (ngo.icon||'○') + '</div>' +
          '<div class="ngo-info">' +
            '<div class="ngo-name">' + escHtml(ngo.name) + '</div>' +
            '<div class="ngo-focus">' + escHtml(ngo.focus||'') + '</div>' +
            '<div style="margin-top:4px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">' +
              '<span class="badge tag-' + (ngo.tag||'other') + '">' + (TAG_LABELS[ngo.tag]||'Other') + '</span>' +
              (showDist && ngo.distance_km != null ? '<span class="nearby-badge">◎ ' + ngo.distance_km + ' km away</span>' : '') +
              '<span class="rating-stars">' + stars(ngo.rating||4) + '</span>' +
              '<span style="font-size:11.5px;color:var(--text2)">' + (ngo.rating||4).toFixed(1) + '</span>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div class="ngo-stats">' +
          '<div class="ngo-stat"><div class="ngo-stat-num" style="color:var(--green)">' + (ngo.issues_resolved||0) + '</div><div class="ngo-stat-lbl">Resolved</div></div>' +
          '<div class="ngo-stat"><div class="ngo-stat-num" style="color:var(--amber)">' + (ngo.issues_escalated||0) + '</div><div class="ngo-stat-lbl">Escalated</div></div>' +
          '<div class="ngo-stat"><div class="ngo-stat-num" style="color:var(--blue)">' + (ngo.rating||4).toFixed(1) + '</div><div class="ngo-stat-lbl">Rating</div></div>' +
        '</div>' +
        '<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">' +
          (ngo.phone ? '<a href="tel:' + ngo.phone + '" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">Call</a>' : '') +
          (ngo.email ? '<a href="mailto:' + ngo.email + '" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">Email</a>' : '') +
          '<span style="font-size:12px;color:var(--text2);display:flex;align-items:center">📍 ' + escHtml(ngo.area||'') + '</span>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function renderGovt(agencies) {
    var el = document.getElementById('ngos-content');
    if (!agencies.length) { el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">○</div><div class="empty-state-title">No agencies found</div></div>'; return; }
    el.innerHTML = agencies.map(function(a) {
      return '<div class="ngo-card" onclick="focusNGO(' + a.lat + ',' + a.lng + ',\'' + escJs(a.name) + '\')">' +
        '<div class="ngo-card-header">' +
          '<div class="ngo-icon-box">' + (a.icon||'○') + '</div>' +
          '<div class="ngo-info">' +
            '<div class="ngo-name">' + escHtml(a.name) + '</div>' +
            '<div class="ngo-focus">' + escHtml(a.focus||'') + '</div>' +
            '<div style="margin-top:4px;display:flex;gap:8px;flex-wrap:wrap">' +
              '<span class="badge tag-' + (a.tag||'other') + '">' + (TAG_LABELS[a.tag]||'Other') + '</span>' +
              '<span style="font-size:11.5px;color:var(--text2)">' + escHtml(a.department||'') + '</span>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">' +
          (a.phone ? '<a href="tel:' + a.phone + '" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">📞 ' + escHtml(a.phone) + '</a>' : '') +
          (a.email ? '<a href="mailto:' + a.email + '" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">✉ Email</a>' : '') +
        '</div>' +
      '</div>';
    }).join('');
  }

  function plotNGOMarkers(ngos) {
    ngoMarkers.forEach(function(m) { ngoMap.removeLayer(m); }); ngoMarkers = [];
    ngos.forEach(function(ngo) {
      if (!ngo.lat || !ngo.lng) return;
      var m = L.circleMarker([ngo.lat, ngo.lng], { radius:8, color:'#2D6A4F', fillColor:'#2D6A4F', fillOpacity:0.8, weight:2 }).addTo(ngoMap).bindPopup('<b>' + ngo.name + '</b><br><small>' + (ngo.area||'') + '</small>');
      ngoMarkers.push(m);
    });
  }

  window.focusNGO = function(lat, lng, name) {
    if (!lat || !lng) return;
    ngoMap.setView([lat, lng], 14);
    var card = document.getElementById('ngo-detail-card');
    card.innerHTML = '<div style="font-weight:600;margin-bottom:4px">' + escHtml(name) + '</div><div style="font-size:12px;color:var(--text2)">Focused on map</div>';
    card.style.display = 'block';
    setTimeout(function() { card.style.display = 'none'; }, 3000);
  };

  loadCurrentTab();
})();