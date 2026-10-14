import os
import csv
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser
import threading

BASE_DIR = Path(__file__).resolve().parent
READINGS_FILE = BASE_DIR / "sentinel_readings.csv"
ALERTS_FILE = BASE_DIR / "sentinel_alerts.csv"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8765))

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project Sentinel</title>
<style>
:root {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #172033;
  background: #eef2f6;
}
* { box-sizing: border-box; }
body { margin: 0; }
header {
  background: #14243a;
  color: white;
  padding: 22px max(18px, calc((100% - 1200px)/2));
}
header h1 { margin: 0; font-size: 25px; }
header p { margin: 6px 0 0; color: #cbd5e1; }
main { max-width: 1200px; margin: auto; padding: 20px; }
nav { display: flex; gap: 8px; margin-bottom: 18px; }
button, select, input {
  font: inherit; padding: 10px 13px; border-radius: 8px;
  border: 1px solid #cbd5e1; background: white; color: #172033;
}
button { cursor: pointer; font-weight: 600; }
button.active { background: #14243a; color: white; }
.panel {
  background: white; border-radius: 12px; padding: 20px;
  margin-bottom: 18px; box-shadow: 0 2px 8px #1720330d;
}
.status {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
}
.status h2 { margin: 0 0 5px; }
.status p { margin: 0; color: #64748b; }
.pill {
  display: inline-block; padding: 8px 13px; border-radius: 20px;
  font-weight: 700; background: #e2e8f0; color: #334155;
}
.normal { background: #dcfce7; color: #166534; }
.warning { background: #fef3c7; color: #92400e; }
.critical { background: #fee2e2; color: #991b1b; }
.grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px; margin-bottom: 18px;
}
.metric { background: white; border-radius: 12px; padding: 18px; }
.metric .name { color: #64748b; font-size: 14px; }
.metric .value { font-size: 27px; font-weight: 750; margin-top: 8px; }
.metric .unit { font-size: 13px; color: #64748b; }
h2, h3 { margin-top: 0; }
.note { color: #64748b; font-size: 13px; }
.toolbar { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.toolbar input { flex: 1; min-width: 180px; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 12px 10px; border-bottom: 1px solid #e2e8f0; }
th { color: #64748b; background: #f8fafc; }
td.message { min-width: 220px; }
tr.alert-row { cursor: pointer; }
tr.alert-row:hover { background: #f8fafc; }
.hidden { display: none; }
#details { white-space: pre-wrap; line-height: 1.6; }
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  min-width: 0;
}

.chart-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
}

.chart-card canvas {
  display: block;
  width: 100%;
  height: 190px;
}

@media(max-width: 700px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
@media(max-width: 700px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  main { padding: 12px; }
  .metric { padding: 14px; }
  .metric .value { font-size: 23px; }
}
</style>
</head>
<body>
<header>
  <h1>PROJECT SENTINEL</h1>
  <p>Equipment Monitoring Dashboard</p>
</header>
<main>
  <nav>
    <button id="liveTab" class="active" onclick="showTab('live')">Live Dashboard</button>
    <button id="historyTab" onclick="showTab('history')">Alert History</button>
  </nav>

  <section id="live">
    <div class="panel status">
      <div>
        <h2 id="statusTitle">Waiting for readings</h2>
        <p id="statusMessage">Looking for saved sensor data...</p>
      </div>
      <span id="statusBadge" class="pill">WAITING</span>
    </div>

    <div class="grid">
      <div class="metric">
        <div class="name">Temperature</div>
        <div id="temperature" class="value">--</div>
        <div class="unit">Sensor units</div>
      </div>
      <div class="metric">
        <div class="name">Vibration</div>
        <div id="vibration" class="value">--</div>
        <div class="unit">Sensor units</div>
      </div>
      <div class="metric">
        <div class="name">Pressure</div>
        <div id="pressure" class="value">--</div>
        <div class="unit">Sensor units</div>
      </div>
      <div class="metric">
        <div class="name">Power</div>
        <div id="power" class="value">--</div>
        <div class="unit">Sensor units</div>
      </div>
    </div>

   <div class="chart-grid">
  <div class="chart-card">
    <h3>Temperature Trend</h3>
    <canvas id="temperatureChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>Vibration Trend</h3>
    <canvas id="vibrationChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>Pressure Trend</h3>
    <canvas id="pressureChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>Power Trend</h3>
    <canvas id="powerChart"></canvas>
  </div>
</div> <div class="panel">
      <h3>Latest Reading</h3>
      <p>Recorded at: <strong id="readingTime">Waiting for data</strong></p>
      <p id="connection">Connecting to local project files...</p>
      <p class="note">The display refreshes every two seconds. Sensor units and thresholds depend on your simulator configuration.</p>
    </div>
  </section>

  <section id="history" class="hidden">
    <div class="grid">
      <div class="metric">
        <div class="name">Alerts Found</div>
        <div id="alertCount" class="value">0</div>
      </div>
      <div class="metric">
        <div class="name">Warnings</div>
        <div id="warningCount" class="value">0</div>
      </div>
      <div class="metric">
        <div class="name">Critical Alerts</div>
        <div id="criticalCount" class="value">0</div>
      </div>
      <div class="metric">
        <div class="name">Showing</div>
        <div id="shownCount" class="value">0</div>
      </div>
    </div>

    <div class="panel">
      <h2>Alert History Log</h2>
      <p class="note">Only warnings, spikes, trends, and critical alerts are listed here. Normal readings remain saved in the readings file.</p>
      <div class="toolbar">
        <input id="search" placeholder="Search alerts, dates, or sensor values..." oninput="renderAlerts()">
        <select id="severity" onchange="renderAlerts()">
          <option value="ALL">All severities</option>
          <option value="WARNING">Warnings</option>
          <option value="CRITICAL">Critical only</option>
        </select>
        <button onclick="loadAlerts()">Refresh History</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Time</th><th>Severity</th><th>Alert</th></tr>
          </thead>
          <tbody id="alertRows">
            <tr><td colspan="3">Loading saved alerts...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <h3>Selected Alert Details</h3>
      <div id="details">Select an alert above to see its sensor readings.</div>
    </div>
  </section>
</main>

<script>
let alerts = [];

function showTab(name) {
  document.getElementById('live').classList.toggle('hidden', name !== 'live');
  document.getElementById('history').classList.toggle('hidden', name !== 'history');
  document.getElementById('liveTab').classList.toggle('active', name === 'live');
  document.getElementById('historyTab').classList.toggle('active', name === 'history');
  if (name === 'history') loadAlerts();
}

function setText(id, value) {
  document.getElementById(id).textContent =
    value === undefined || value === null || value === '' ? '--' : value;
}

function prettyStatus(raw) {
  const value = String(raw || 'UNKNOWN').toUpperCase();
  if (value.includes('CRITICAL')) return 'CRITICAL';
  if (value.includes('WARNING')) return 'WARNING';
  if (value === 'NORMAL') return 'NORMAL';
  return value;
}

function explainStatus(status) {
  if (status === 'CRITICAL') return 'A critical threshold was reached. Check the alert history.';
  if (status === 'WARNING') return 'A warning condition was recorded. Review the alert history.';
  if (status === 'NORMAL') return 'The latest saved reading is marked normal by the simulator.';
  return 'No recognized status is available in the latest saved reading.';
}

function drawCharts(readings) {
  const charts = [
    {key: 'temperature', id: 'temperatureChart', color: '#2563eb'},
    {key: 'vibration', id: 'vibrationChart', color: '#d97706'},
    {key: 'pressure', id: 'pressureChart', color: '#0d9488'},
    {key: 'power', id: 'powerChart', color: '#7c3aed'}
  ];

  charts.forEach(chart => {
    const canvas = document.getElementById(chart.id);
    if (!canvas) return;

    const width = canvas.clientWidth || 300;
    const height = 190;
    const ratio = window.devicePixelRatio || 1;

    canvas.width = width * ratio;
    canvas.height = height * ratio;

    const ctx = canvas.getContext('2d');
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#64748b';

    const values = readings
      .map(r => Number(r[chart.key]))
      .filter(v => Number.isFinite(v));

    if (values.length < 2) {
      ctx.fillText('Waiting for more readings...', 12, 30);
      return;
    }

    let min = Math.min(...values);
    let max = Math.max(...values);

    if (min === max) {
      min -= 1;
      max += 1;
    }

    const padding = {left: 42, right: 12, top: 18, bottom: 28};
    const plotW = width - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;

    const x = i => padding.left +
      (i / (values.length - 1)) * plotW;
    const y = v => padding.top +
      ((max - v) / (max - min)) * plotH;

    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
      const yy = padding.top + (plotH * i / 4);
      const value = max - (max - min) * i / 4;

      ctx.beginPath();
      ctx.moveTo(padding.left, yy);
      ctx.lineTo(width - padding.right, yy);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(1), padding.left - 7, yy + 4);
    }

    ctx.beginPath();
    values.forEach((value, i) => {
      if (i === 0) ctx.moveTo(x(i), y(value));
      else ctx.lineTo(x(i), y(value));
    });

    ctx.strokeStyle = chart.color;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();

    ctx.fillStyle = chart.color;
    ctx.beginPath();
    ctx.arc(x(values.length - 1), y(values[values.length - 1]),
      4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'left';
    ctx.fillText('Older', padding.left, height - 7);
    ctx.textAlign = 'right';
    ctx.fillText('Latest', width - padding.right, height - 7);
  });
}

async function loadLive() {
  try {
    const response = await fetch('/api/status', {cache: 'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not read sensor file');

    if (!data.reading) {
      setText('statusTitle', 'No readings yet');
      setText('statusMessage', 'Start the sensor simulator to create readings.');
      setText('statusBadge', 'WAITING');
      document.getElementById('statusBadge').className = 'pill';
      setText('connection', data.message || 'Readings file is empty.');
      return;
    }

    const r = data.reading;
    drawCharts(data.recent || []);
    const status = prettyStatus(r.status);
    setText('statusTitle', status === 'NORMAL' ? 'System Normal' :
      status === 'WARNING' ? 'Warning Detected' :
      status === 'CRITICAL' ? 'Critical Alert' : 'Status: ' + status);
    setText('statusMessage', explainStatus(status));
    setText('statusBadge', status);
    document.getElementById('statusBadge').className =
      'pill ' + (status === 'NORMAL' ? 'normal' :
      status === 'WARNING' ? 'warning' :
      status === 'CRITICAL' ? 'critical' : '');
    ['temperature','vibration','pressure','power'].forEach(k =>
      setText(k, r[k]));
    setText('readingTime', r.time);
    setText('connection', 'Connected • ' + data.total + ' saved readings');
  } catch (error) {
    setText('connection', 'Could not load readings: ' + error.message);
  }
}

async function loadAlerts() {
  try {
    const response = await fetch('/api/alerts', {cache: 'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not read alerts file');
    alerts = data.alerts || [];
    renderAlerts();
  } catch (error) {
    document.getElementById('alertRows').innerHTML =
      '<tr><td colspan="3">Could not load alert history: ' +
      escapeHtml(error.message) + '</td></tr>';
  }
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[ch]));
}

function renderAlerts() {
  const query = document.getElementById('search').value.toLowerCase().trim();
  const severity = document.getElementById('severity').value;

  const filtered = alerts.filter(a => {
    const sev = String(a.severity || '').toUpperCase();
    const msg = String(a.message || '').toUpperCase();
    const relevant = sev.includes('WARNING') || sev.includes('CRITICAL') ||
      /SPIKE|RISING|TREND|WARNING|CRITICAL/.test(msg);
    const severityMatch = severity === 'ALL' ||
      (severity === 'WARNING' ? sev.includes('WARNING') :
       sev.includes('CRITICAL'));
    return relevant && severityMatch &&
      Object.values(a).join(' ').toLowerCase().includes(query);
  });

  setText('alertCount', alerts.filter(a =>
    /WARNING|CRITICAL|SPIKE|RISING|TREND/i.test(
      (a.severity || '') + ' ' + (a.message || '')
    )).length);
  setText('warningCount', alerts.filter(a =>
    /WARNING/i.test(a.severity || '')).length);
  setText('criticalCount', alerts.filter(a =>
    /CRITICAL/i.test(a.severity || '')).length);
  setText('shownCount', filtered.length);

  const body = document.getElementById('alertRows');
  if (!filtered.length) {
    body.innerHTML = '<tr><td colspan="3">No matching alerts found.</td></tr>';
    return;
  }

  body.innerHTML = filtered.slice().reverse().map((a, index) => {
    const originalIndex = alerts.indexOf(a);
    const sev = String(a.severity || 'WARNING').toUpperCase();
    const cls = sev.includes('CRITICAL') ? 'critical' : 'warning';
    return `<tr class="alert-row" data-index="${originalIndex}">
      <td>${escapeHtml(a.time)}</td>
      <td><span class="pill ${cls}">${escapeHtml(sev)}</span></td>
      <td class="message">${escapeHtml(a.message)}</td>
    </tr>`;
  }).join('');

  body.querySelectorAll('tr[data-index]').forEach(row => {
    row.addEventListener('click', () => {
      const a = alerts[Number(row.dataset.index)];
      document.getElementById('details').textContent =
        'Time: ' + (a.time || '--') + '\n' +
        'Severity: ' + (a.severity || '--') + '\n' +
        'Alert: ' + (a.message || '--') + '\n\n' +
        'Temperature: ' + (a.temperature || '--') + '\n' +
        'Vibration: ' + (a.vibration || '--') + '\n' +
        'Pressure: ' + (a.pressure || '--') + '\n' +
        'Power: ' + (a.power || '--');
    });
  });
}

loadLive();
loadAlerts();
setInterval(loadLive, 2000);
setInterval(loadAlerts, 10000);
</script>
</body>
</html>"""


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


class SentinelHandler(BaseHTTPRequestHandler):
    def send_content(self, content, content_type="text/html; charset=utf-8",
                     status=200):
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def send_json(self, data, status=200):
        self.send_content(
            json.dumps(data),
            "application/json; charset=utf-8",
            status
        )

    def do_GET(self):
        if self.path == "/":
            self.send_content(PAGE)
            return

        if self.path == "/api/status":
            if not READINGS_FILE.exists():
                self.send_json({
                    "reading": None,
                    "total": 0,
                    "message": "Start the simulator to create the readings file."
                })
                return
            try:
                rows = read_csv(READINGS_FILE)
                self.send_json({
                    "reading": rows[-1] if rows else None,
                    "total": len(rows),
                    "recent": rows[-60:],
                    "message": "No readings have been saved yet."
                })
            except (OSError, csv.Error) as error:
                self.send_json({"error": str(error)}, 500)
            return

        if self.path == "/api/alerts":
            try:
                rows = read_csv(ALERTS_FILE)
                self.send_json({"alerts": rows})
            except (OSError, csv.Error) as error:
                self.send_json({"error": str(error)}, 500)
            return

        self.send_json({"error": "Page not found"}, 404)

    def log_message(self, format_string, *args):
        print("Sentinel web:", format_string % args)


def main():
    server = ThreadingHTTPServer((HOST, PORT), SentinelHandler)
    url = "http://127.0.0.1:" + str(PORT)
    print("PROJECT SENTINEL dashboard is ready.")
    print("Open this address in your browser:", url)
    print("Keep this Terminal window open while using the dashboard.")
    print("Press Control+C to stop the dashboard.")

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping the dashboard...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

