from flask import Flask, request, jsonify, render_template_string
import webbrowser
import threading

app = Flask(__name__)

# Store all device locations + last SMS in memory
device_data = {}

# HTML Template for map
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>📍 Live Device Location</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
</head>
<body>
    <h3>📱 Live Device Tracker</h3>
    <div id="map" style="height: 90vh; width: 100%;"></div>

    <script>
        var map = L.map('map').setView([12.9716, 77.5946], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);

        var marker = L.marker([12.9716, 77.5946]).addTo(map)
            .bindPopup("Waiting for data...")
            .openPopup();

        async function updateData() {
            try {
                let response = await fetch('/latest_data');
                let data = await response.json();
                let lat = data.latitude;
                let lon = data.longitude;
                let phone = data.phone;
                let message = data.message;

                marker.setLatLng([lat, lon])
                      .bindPopup("📱 Phone: " + phone + "<br>📍 Lat: " + lat + ", Lon: " + lon + "<br>💬 SMS: " + message)
                      .openPopup();

                map.setView([lat, lon], 13);
            } catch (err) {
                console.log("Error fetching data:", err);
            }
        }

        updateData();
        setInterval(updateData, 5000);
    </script>
</body>
</html>
"""

# 🔹 Receive SMS forwarded from SMSReceiver app
@app.route("/receive_sms", methods=["POST"])
def receive_sms():
    data = request.get_json()
    phone = data.get("sender")
    lat = data.get("latitude")
    lon = data.get("longitude")
    message = data.get("message")

    # Clean SMS values if they contain LAT:/LON:
    if isinstance(lat, str) and lat.upper().startswith("LAT:"):
        lat = lat.split(":", 1)[1].strip()
    if isinstance(lon, str) and lon.upper().startswith("LON:"):
        lon = lon.split(":", 1)[1].strip()

    try:
        device_data[phone] = {
            "lat": float(lat),
            "lon": float(lon),
            "message": message,
        }
        return {"status": "success", "data": device_data[phone]}
    except Exception as e:
        return {"status": "error", "error": str(e)}, 400


# 🔹 Receive direct location update from app with internet
@app.route('/update_location', methods=['POST'])
def update_location():
    global device_data
    data = request.form if request.form else request.get_json(silent=True) or {}
    print("🌐 Received via Internet:", data)

    phone = data.get("phone", "unknown_device")
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat and lon:
        device_data[phone] = {"lat": float(lat), "lon": float(lon), "message": "Updated via Internet"}
        return jsonify({"status": "ok", "source": "internet"})
    return jsonify({"status": "error", "msg": "Missing lat/lon"}), 400


# 🔹 Latest stored data for map refresh
@app.route('/latest_data')
def latest_data():
    if device_data:
        phone, info = next(iter(device_data.items()))
        return jsonify({
            "phone": phone,
            "latitude": info["lat"],
            "longitude": info["lon"],
            "message": info["message"]
        })
    return jsonify({
        "phone": "none",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "message": "No data yet"
    })


# 🔹 Show live location map
@app.route('/show_location')
def show_location():
    return render_template_string(HTML_TEMPLATE)


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/show_location")


if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
