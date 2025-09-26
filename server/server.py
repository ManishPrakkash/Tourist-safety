from flask import Flask, request, jsonify, render_template_string

# Flask app and in-memory storage
app = Flask(__name__)
device_data = {}

# Modern HTML template with light/dark theme and searchable sidebar
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tourist Safety Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
    <style>
        :root { color-scheme: light; --bg:#f5f7fb; --surface:#ffffff; --text:#222; --muted:#6b7280; --primary:#2563eb; --primary-strong:#1d4ed8; --success:#22c55e; --danger:#ef4444; --border:#e5e7eb; --shadow: 0 6px 18px rgba(0,0,0,.08); }
        :root[data-theme="dark"] { color-scheme: dark; --bg:#0f172a; --surface:#111827; --text:#e5e7eb; --muted:#9ca3af; --primary:#60a5fa; --primary-strong:#3b82f6; --success:#22c55e; --danger:#f87171; --border:#1f2937; --shadow: 0 8px 22px rgba(0,0,0,.35); }
        html, body { height:100% }
        body { margin:0; font-family: Roboto, system-ui, -apple-system, Segoe UI, Arial, sans-serif; background:var(--bg); color:var(--text); }
        #map { height:100vh; width:100%; }
        .header { position:fixed; inset:0 0 auto 0; background: color-mix(in oklab, var(--surface) 94%, transparent); backdrop-filter: blur(6px); z-index:1200; padding: 12px 18px; box-shadow: var(--shadow); display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--border); }
        .subtitle { color:var(--muted); font-size:13px; }
        .controls { display:flex; gap:8px; align-items:center; }
        .btn { background: linear-gradient(135deg, var(--primary), var(--primary-strong)); color:#fff; border:0; padding:8px 12px; border-radius:10px; cursor:pointer; }
        .btn.secondary { background:transparent; color:var(--text); border:1px solid var(--border); }
        #sidebar { position:fixed; top:64px; right:-420px; width:420px; height: calc(100vh - 64px); background:var(--surface); border-left:3px solid var(--primary); box-shadow:-8px 0 22px rgba(0,0,0,.15); transition:right .28s ease; z-index:2000; overflow-y:auto; }
        #sidebar.open { right:0; }
        .side-header { padding: 12px 14px; display:flex; align-items:center; justify-content:space-between; gap:8px; border-bottom:1px solid var(--border); }
        .search { display:flex; align-items:center; gap:8px; padding: 10px 14px; border-bottom:1px solid var(--border); }
        .search input { flex:1; padding:10px 12px; border:1px solid var(--border); border-radius:10px; background:transparent; color:var(--text); outline:none; }
        #userList { padding: 12px 14px; display:flex; flex-direction:column; gap:12px; }
        .entry { border:1px solid var(--border); border-left:4px solid var(--primary); border-radius:12px; padding:10px; background:var(--surface); box-shadow: var(--shadow); }
        .row { display:flex; gap:10px; align-items:center; cursor:pointer; }
        .avatar { width:36px; height:36px; display:grid; place-items:center; background: color-mix(in srgb, var(--primary) 16%, var(--surface) 84%); color: var(--primary-strong); border-radius:8px; }
        .pill { font-size:12px; padding:2px 8px; border-radius:999px; background: color-mix(in srgb, var(--primary) 12%, transparent); color: var(--primary-strong); border:1px solid var(--border); }
        .meta { color:var(--muted); font-size: 12px; margin-top:2px; }
        #overlay { position:fixed; top:64px; left:0; right:0; bottom:0; background: rgba(0,0,0,.45); display:none; z-index:1500; }
        #overlay.show { display:block; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div style="display:flex; align-items:center; gap:8px">
                <i class="fa-solid fa-location-dot" style="color:var(--primary)"></i>
                <h2 style="margin:0">Tourist Safety Dashboard</h2>
            </div>
            <div class="subtitle">Real-time monitoring of tourist locations and safety</div>
        </div>
        <div class="controls">
            <button id="themeBtn" class="btn secondary" title="Toggle theme"><i class="fa-solid fa-moon"></i></button>
            <button id="toggleBtn" class="btn"><i class="fa-solid fa-users"></i> Users</button>
        </div>
    </div>

    <div id="map"></div>
    <div id="overlay"></div>

    <aside id="sidebar">
        <div class="side-header">
            <div style="display:flex; align-items:center; gap:8px">
                <i class="fa-solid fa-users"></i>
                <strong>Active Users</strong>
                <span id="userCount" class="meta"></span>
            </div>
            <button id="closeBtn" class="btn secondary" title="Close"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div class="search">
            <i class="fa-solid fa-magnifying-glass" style="color:var(--muted)"></i>
            <input id="searchInput" placeholder="Search by name, phone, address or emergency"/>
            <button id="clearSearch" class="btn secondary" title="Clear"><i class="fa-solid fa-eraser"></i></button>
            <button id="fitBtn" class="btn secondary" title="Fit markers"><i class="fa-solid fa-location-crosshairs"></i></button>
        </div>
        <div id="userList"></div>
    </aside>

    <script>
        // Theme persistence
        const root = document.documentElement;
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') root.setAttribute('data-theme','dark');
        const themeBtn = document.getElementById('themeBtn');
        function updateThemeIcon(){ themeBtn.innerHTML = root.getAttribute('data-theme')==='dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>'; }
        updateThemeIcon();
        themeBtn.addEventListener('click', ()=>{
            const dark = root.getAttribute('data-theme')==='dark';
            if (dark) root.removeAttribute('data-theme'); else root.setAttribute('data-theme','dark');
            localStorage.setItem('theme', root.getAttribute('data-theme')==='dark' ? 'dark' : 'light');
            updateThemeIcon();
        });

        // Map init with a constant (light) tile layer regardless of theme
        const map = L.map('map').setView([20.5937, 78.9629], 5);
        const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        });
        tileLayer.addTo(map);

        // Sidebar + overlay
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const toggleBtn = document.getElementById('toggleBtn');
        const closeBtn = document.getElementById('closeBtn');
        toggleBtn.onclick = ()=>{ sidebar.classList.add('open'); overlay.classList.add('show'); toggleBtn.style.display='none'; };
        closeBtn.onclick = ()=>{ sidebar.classList.remove('open'); overlay.classList.remove('show'); toggleBtn.style.display='inline-flex'; };
        overlay.onclick = closeBtn.onclick;

        // Data + search
        const markers = {};
        let dataCache = {};
        let searchTerm = '';

        function toNum(v, d){ const n = Number(v); return Number.isFinite(n) ? n : d; }

        function render(){
            const list = document.getElementById('userList');
            const term = searchTerm.trim().toLowerCase();
            const phones = Object.keys(dataCache).sort();
            let html = '';
            let shown = 0;
            for (const phone of phones){
                const u = dataCache[phone]||{};
                const blob = `${u.name||''} ${phone} ${u.address||''} ${u.emergency||''}`.toLowerCase();
                if (term && !blob.includes(term)) continue;
                shown++;
                const lat = toNum(u.lat, 20.5937), lon = toNum(u.lon, 78.9629);
                if (!markers[phone]){
                    const m = L.marker([lat, lon]).addTo(map);
                    m.bindPopup(`<b>${u.name||'Unknown'}</b><br/>📱 ${phone}<br/>${u.address||''}`);
                    markers[phone] = m;
                } else {
                    markers[phone].setLatLng([lat, lon]);
                }
                html += `
                    <div class="entry">
                        <div class="row" onclick="focusUser('${phone}')">
                            <div class="avatar"><i class="fa-solid fa-user"></i></div>
                            <div style="flex:1">
                                <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
                                    <div style="font-weight:600">${u.name || 'Unknown'}</div>
                                    <span class="pill">${u.gender||'-'}</span>
                                </div>
                                <div class="meta">📱 ${phone}</div>
                                <div class="meta">📍 ${u.address || '-'}</div>
                            </div>
                        </div>
                        <div class="meta" style="margin-top:8px">Lat/Lon: ${u.lat ?? '-'}, ${u.lon ?? '-'}</div>
                        <div class="meta">SOS: <span style="color:${(u.emergency||'').toLowerCase()==='yes' ? 'var(--danger)' : 'var(--muted)'}">${u.emergency || 'No'}</span></div>
                    </div>`;
            }
            list.innerHTML = html || '<div class="meta" style="padding:16px">No users match your search.</div>';
            document.getElementById('userCount').textContent = `${Object.keys(dataCache).length} total · ${shown} shown`;
        }

        async function updateData(){
            try {
                const res = await fetch('/latest_data');
                dataCache = await res.json();
                Object.keys(markers).forEach(p => { if (!dataCache[p]) { map.removeLayer(markers[p]); delete markers[p]; } });
                render();
            } catch(e) { console.error(e); }
        }

        function focusUser(phone){
            const u = dataCache[phone]; if (!u) return;
            const lat = toNum(u.lat, 20.5937), lon = toNum(u.lon, 78.9629);
            map.setView([lat, lon], 13, { animate: true });
            const m = markers[phone]; if (m) m.openPopup();
        }
        window.focusUser = focusUser;

        const input = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearSearch');
        const fitBtn = document.getElementById('fitBtn');
        input.addEventListener('input', e => { searchTerm = e.target.value; render(); });
        clearBtn.addEventListener('click', ()=>{ input.value=''; searchTerm=''; render(); });
        fitBtn.addEventListener('click', ()=>{
            const group = new L.featureGroup(Object.values(markers));
            if (Object.values(markers).length) map.fitBounds(group.getBounds().pad(0.2));
        });

        updateData();
        setInterval(updateData, 5000);
    </script>
</body>
</html>
"""

@app.route("/receive_sms", methods=["POST"])
def receive_sms():
    data = request.get_json()
    phone = data.get("sender")
    device_data[phone] = {
        "name": data.get("name"),
        "aadhar": data.get("aadhar"),
        "age": data.get("age"),
        "gender": data.get("gender"),
        "emergency": data.get("emergency"),
        "address": data.get("address"),
        "lat": float(data.get("latitude")),
        "lon": float(data.get("longitude")),
        "message": data.get("message"),
    }
    return {"status": "success"}

@app.route('/latest_data')
def latest_data():
    return jsonify(device_data)

@app.route('/show_location')
def show_location():
    return render_template_string(HTML_TEMPLATE)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

@app.route("/")
def index():
    return {"status": "ok", "dashboard": "/show_location"}

if __name__ == "__main__":
    # Run only on localhost (127.0.0.1) for local development, without the reloader
    app.run(host="127.0.0.1", port=5000, debug=False)
