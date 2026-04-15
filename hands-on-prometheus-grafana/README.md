# Hands-On: Monitoring Web Server dengan Prometheus & Grafana

> **Mata Kuliah:** Administrasi Server  
> **Topik:** Observability — Metrics Collection & Visualization  
> **Tools:** Docker, Docker Compose, Prometheus, Grafana, Flask/Python

---

## Arsitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network: monitoring               │
│                                                                 │
│  ┌─────────────┐    scrape /metrics    ┌───────────────────┐   │
│  │ webserver1  │◄──────────────────────│                   │   │
│  │ :5000       │                       │   prometheus      │   │
│  └─────────────┘                       │   :9090           │   │
│                                        │                   │   │
│  ┌─────────────┐    scrape /metrics    │                   │   │
│  │ webserver2  │◄──────────────────────│                   │   │
│  │ :5000       │                       └────────┬──────────┘   │
│  └─────────────┘                                │ query        │
│                                                 ▼              │
│  ┌──────────────────┐                  ┌───────────────────┐   │
│  │ traffic-generator│──HTTP requests──►│    grafana        │   │
│  │ (auto curl loop) │                  │    :3000          │   │
│  └──────────────────┘                  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Container yang Berjalan

| Container           | Image             | Port Host | Deskripsi                          |
|---------------------|-------------------|-----------|------------------------------------|
| `webserver1`        | custom (Flask)    | 5001      | Web server 1 dengan /metrics       |
| `webserver2`        | custom (Flask)    | 5002      | Web server 2 dengan /metrics       |
| `prometheus`        | prom/prometheus   | 9090      | Scrape & simpan metrics            |
| `grafana`           | grafana/grafana   | 3000      | Visualisasi dashboard              |
| `traffic-generator` | alpine            | —         | Generate traffic otomatis (curl)   |

---

## Prasyarat

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) terinstall
- Port **3000**, **5001**, **5002**, **9090** tidak dipakai proses lain

---

## Cara Menjalankan

### 1. Clone / buka folder ini

```bash
cd hands-on-prometheus-grafana
```

### 2. Jalankan semua container

```bash
docker compose up -d --build
```

Tunggu ~30 detik hingga semua container `Running`.

### 3. Periksa status container

```bash
docker compose ps
```

Output yang diharapkan:
```
NAME                STATUS
webserver1          Up
webserver2          Up
prometheus          Up
grafana             Up
traffic-generator   Up
```

---

## Mengakses Layanan

| Layanan    | URL                        | Kredensial           |
|------------|----------------------------|----------------------|
| WebServer1 | http://localhost:5001      | —                    |
| WebServer2 | http://localhost:5002      | —                    |
| Prometheus | http://localhost:9090      | —                    |
| Grafana    | http://localhost:3000      | admin / admin123     |

---

## Struktur Proyek

```
hands-on-prometheus-grafana/
├── docker-compose.yml
├── generate-traffic.sh          # Script manual untuk generate traffic
│
├── webserver1/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py                   # Flask + prometheus_client
│
├── webserver2/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py                   # Flask + prometheus_client (slower /slow)
│
├── prometheus/
│   ├── prometheus.yml           # Scrape config
│   └── alert_rules.yml          # Alerting rules
│
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml   # Auto-configure Prometheus datasource
        └── dashboards/
            ├── dashboards.yml   # Dashboard provider config
            └── webservers-dashboard.json  # Pre-built dashboard
```

---

## Endpoint Web Server

### WebServer 1 (port 5001)

| Endpoint     | Method | Deskripsi                              |
|--------------|--------|----------------------------------------|
| `/`          | GET    | Halaman utama                          |
| `/health`    | GET    | Health check → 200 OK                  |
| `/api/data`  | GET    | Mengambil data JSON (random)           |
| `/slow`      | GET    | Respons lambat 0.1–1.5 detik           |
| `/error`     | GET    | Selalu mengembalikan HTTP 500          |
| `/metrics`   | GET    | **Endpoint Prometheus** (jangan dihapus) |

### WebServer 2 (port 5002)

| Endpoint        | Method | Deskripsi                              |
|-----------------|--------|----------------------------------------|
| `/`             | GET    | Halaman utama                          |
| `/health`       | GET    | Health check → 200 OK                  |
| `/api/users`    | GET    | Data pengguna (JSON)                   |
| `/api/products` | GET    | Data produk — lebih besar + lambat     |
| `/slow`         | GET    | Respons lambat **0.5–3.0 detik** (lebih lambat dari ws1) |
| `/error`        | GET    | Selalu mengembalikan HTTP 500          |
| `/metrics`      | GET    | **Endpoint Prometheus**                |

---

## Metrics yang Di-collect

| Metric                                  | Tipe      | Label                              |
|-----------------------------------------|-----------|------------------------------------|
| `http_requests_total`                   | Counter   | server, method, endpoint, http_status |
| `http_request_duration_seconds`         | Histogram | server, method, endpoint           |
| `http_requests_in_progress`             | Gauge     | server                             |

---

## Latihan / Tugas

### Lab 1 — Menjelajahi Prometheus

1. Buka http://localhost:9090
2. Klik menu **Status → Targets** dan verifikasi semua target `UP`
3. Coba query berikut di tab **Graph**:

```promql
# Total request semua server
http_requests_total

# Rate request per detik per server (1 menit terakhir)
sum by (server) (rate(http_requests_total[1m]))

# Error rate (persentase 5xx)
sum by (server) (rate(http_requests_total{http_status=~"5.."}[1m]))
/ sum by (server) (rate(http_requests_total[1m]))

# P95 latency per server
histogram_quantile(0.95, sum by (server, le) (rate(http_request_duration_seconds_bucket[5m])))
```

### Lab 2 — Menjelajahi Grafana Dashboard

1. Buka http://localhost:3000, login dengan `admin` / `admin123`
2. Klik menu **Dashboards** → **Web Server Monitoring** → **Web Server Monitoring**
3. Amati panel-panel berikut:
   - **Total Requests** per server  
   - **Request Rate** (req/s)  
   - **Latency P50 / P95 / P99** — bandingkan webserver1 vs webserver2  
   - **Error Rate** — seharusnya ada karena `/error` di-hit oleh traffic-generator  
   - **Status Codes** — lihat proporsi 2xx vs 5xx

### Lab 3 — Generate Traffic Manual

```bash
chmod +x generate-traffic.sh
./generate-traffic.sh 30   # 30 requests per endpoint
```

Lalu refresh dashboard Grafana dan amati perubahan grafik.

### Lab 4 — Simulasi Server Down

1. Matikan webserver1:
   ```bash
   docker compose stop webserver1
   ```
2. Buka Prometheus → **Status → Targets** — amati status berubah ke `DOWN`
3. Buka **Alerts** di Prometheus — alert `WebServerDown` akan aktif setelah 30 detik
4. Hidupkan kembali:
   ```bash
   docker compose start webserver1
   ```

### Lab 5 — Membuat Panel Grafana Baru (Eksplorasi)

1. Di Grafana, buka dashboard → klik **Edit** → **Add panel**
2. Buat panel baru dengan query:
   ```promql
   sum by (server) (http_requests_in_progress)
   ```
3. Pilih visualisasi **Gauge** dan simpan

---

## Alerting Rules (Prometheus)

File `prometheus/alert_rules.yml` mendefinisikan 3 alert:

| Alert           | Kondisi                           | Severity |
|-----------------|-----------------------------------|----------|
| `WebServerDown` | Target tidak dapat di-scrape 30s  | critical |
| `HighErrorRate` | Error rate > 10% selama 1 menit   | warning  |
| `HighLatency`   | P95 latency > 2 detik selama 2 menit | warning |

Cek status alert di: http://localhost:9090/alerts

---

## Menghentikan Lab

```bash
# Hentikan semua container (data tetap tersimpan)
docker compose stop

# Hentikan dan hapus container + network
docker compose down

# Hentikan dan hapus SEMUA termasuk volume (data hilang)
docker compose down -v
```

---

## Troubleshooting

**Container tidak mau start:**
```bash
docker compose logs <service-name>
# contoh:
docker compose logs webserver1
```

**Port sudah dipakai:**
```bash
lsof -i :3000   # cek siapa pakai port 3000
```

**Metrics tidak muncul di Prometheus:**
- Pastikan network `monitoring` sudah terbentuk
- Cek `docker compose ps` — semua container harus `Up`
- Buka langsung http://localhost:5001/metrics untuk verifikasi

**Reset Grafana:**
```bash
docker compose down -v
docker compose up -d --build
```
