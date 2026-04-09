# UJIAN TENGAH SEMESTER PRAKTIK
## Mata Kuliah: Administrasi Server
## Topik: Docker-Based Server Administration

---

**Program Studi :** Teknik Informatika / Sistem Informasi  
**Semester       :** Genap 2025/2026  
**Waktu          :** 60 Menit  
**Sifat          :** Praktik (Open Tools, Closed Communication)

---

### Petunjuk Umum

1. Kerjakan semua soal secara berurutan.
2. Setiap konfigurasi file harus disimpan di dalam direktori kerja yang sudah ditentukan.
3. Gunakan Docker dan Docker Compose untuk semua implementasi.
4. Screenshot **setiap hasil pengujian** dan sertakan dalam laporan singkat (file `laporan.pdf`).
5. Pastikan semua container berjalan (status `Up`) saat penilaian berlangsung.
6. Direktori kerja: `~/uts-adser/<NIM>/`

---

## SOAL 1 — Pengelolaan Web Server (25 Poin)

### Latar Belakang
Anda diminta membangun infrastruktur web server untuk perusahaan **PT. Nusantara Digital** yang memiliki dua website berbeda dalam satu server menggunakan konsep **Virtual Host**.

### Tugas

#### 1.1 Struktur Direktori (5 Poin)
Buat struktur direktori berikut di dalam `soal1/`:

```
soal1/
├── docker-compose.yml
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
│       ├── site-a.conf
│       └── site-b.conf
└── html/
    ├── site-a/
    │   └── index.html
    └── site-b/
        └── index.html
```

#### 1.2 Konfigurasi Virtual Host (10 Poin)

Konfigurasikan **Nginx** dengan dua virtual host:

| Virtual Host | Domain              | Port | Isi Halaman                          |
|-------------|---------------------|------|--------------------------------------|
| Site A      | `www.nusantara.local` | 8080 | "Selamat Datang di Nusantara Digital" |
| Site B      | `dev.nusantara.local` | 8080 | "Development Server - Authorized Only"|

Persyaratan konfigurasi:
- Kedua virtual host berjalan dalam **satu container Nginx**.
- Gunakan image `nginx:alpine`.
- Header response harus menyertakan `X-Powered-By: NusantaraServer/1.0`.
- Aktifkan **gzip compression** untuk response berukuran > 1kb.

#### 1.3 Docker Compose (5 Poin)

Buat `docker-compose.yml` yang:
- Mendefinisikan service `webserver`.
- Memetakan port host `8080` ke container port `80`.
- Menggunakan **named volume** `web-logs` untuk menyimpan access log Nginx.
- Menyertakan `healthcheck` yang mengecek endpoint `/` setiap 30 detik.

#### 1.4 Pengujian (5 Poin)

Jalankan perintah berikut dan sertakan **screenshot outputnya**:

```bash
# Tambahkan entri ke /etc/hosts terlebih dahulu:
# 127.0.0.1 www.nusantara.local dev.nusantara.local

curl -H "Host: www.nusantara.local" http://localhost:8080
curl -H "Host: dev.nusantara.local" http://localhost:8080
docker compose -f soal1/docker-compose.yml ps
```

---

## SOAL 2 — Pengelolaan DNS Server (25 Poin)

### Latar Belakang
Perusahaan membutuhkan **DNS Server internal** untuk resolusi nama domain lokal `nusantara.local` agar semua layanan dapat saling berkomunikasi menggunakan nama host, bukan IP.

### Tugas

#### 2.1 Struktur Direktori (3 Poin)

```
soal2/
├── docker-compose.yml
└── bind/
    ├── named.conf
    ├── named.conf.options
    ├── named.conf.local
    └── zones/
        ├── db.nusantara.local
        └── db.reverse
```

#### 2.2 Konfigurasi BIND9 (12 Poin)

Gunakan image `internetsystemsconsortium/bind9:9.18` untuk menjalankan DNS server.

Buat zone file `db.nusantara.local` dengan record berikut:

| Hostname         | Tipe  | Value / IP      | Keterangan           |
|-----------------|-------|-----------------|----------------------|
| `@`             | SOA   | ns1             | Serial: `2026040901` |
| `ns1`           | A     | `172.20.0.10`   | Name Server          |
| `www`           | A     | `172.20.0.20`   | Web Server           |
| `dev`           | A     | `172.20.0.21`   | Dev Server           |
| `cache`         | A     | `172.20.0.30`   | Cache Server         |
| `mail`          | A     | `172.20.0.40`   | Mail Server          |
| `nusantara.local`| MX   | `mail`          | Priority: 10         |
| `www`           | CNAME | `www`           | Alias: `portal`      |

Buat juga zone **reverse lookup** (`db.reverse`) untuk subnet `172.20.0.0/24`.

#### 2.3 Konfigurasi Forwarder (5 Poin)

Di `named.conf.options`, konfigurasikan:
- **Forwarder** ke `8.8.8.8` dan `1.1.1.1` untuk domain yang tidak ada di zone lokal.
- Izinkan query hanya dari subnet `172.20.0.0/24` dan `127.0.0.1`.
- Nonaktifkan **recursion** untuk semua klien di luar subnet yang diizinkan.

#### 2.4 Docker Compose & Jaringan (3 Poin)

- Buat custom network `dns-net` dengan subnet `172.20.0.0/24`.
- Assign IP statis `172.20.0.10` untuk container DNS.

#### 2.5 Pengujian (2 Poin)

Jalankan perintah berikut dan sertakan screenshot:

```bash
# Query dari luar container
docker run --rm --network soal2_dns-net \
  --dns 172.20.0.10 \
  alpine nslookup www.nusantara.local 172.20.0.10

docker run --rm --network soal2_dns-net \
  --dns 172.20.0.10 \
  alpine nslookup google.com 172.20.0.10

# Reverse lookup
docker run --rm --network soal2_dns-net \
  --dns 172.20.0.10 \
  alpine nslookup 172.20.0.20 172.20.0.10
```

---

## SOAL 3 — Cache Server (25 Poin)

### Latar Belakang
Untuk meningkatkan performa aplikasi, Anda diminta membangun **dua jenis cache server**:
- **Redis** sebagai in-memory data store dan cache aplikasi.
- **Squid** sebagai HTTP Proxy Cache.

### Bagian A — Redis Cache (13 Poin)

#### 3.A.1 Struktur Direktori

```
soal3/
├── docker-compose.yml
├── redis/
│   └── redis.conf
└── squid/
    └── squid.conf
```

#### 3.A.2 Konfigurasi Redis (8 Poin)

Buat `redis/redis.conf` dengan konfigurasi:

```
# Wajib dikonfigurasi:
bind 0.0.0.0
protected-mode yes
requirepass NusantaraR3dis!

maxmemory 256mb
maxmemory-policy allkeys-lru

save 900 1
save 300 10
save 60 10000

appendonly yes
appendfsync everysec
```

#### 3.A.3 Docker Compose untuk Redis (5 Poin)

- Gunakan image `redis:7-alpine`.
- Mount `redis/redis.conf` ke `/usr/local/etc/redis/redis.conf`.
- Jalankan Redis dengan flag `--requirepass` dari environment variable `REDIS_PASSWORD`.
- Gunakan **named volume** `redis-data` untuk persistensi data.
- Port: `6379` (jangan expose ke host, hanya internal network).

#### 3.A.4 Pengujian Redis

```bash
docker exec -it <redis-container> redis-cli -a NusantaraR3dis! ping
docker exec -it <redis-container> redis-cli -a NusantaraR3dis! SET user:1 "Andi Pratama"
docker exec -it <redis-container> redis-cli -a NusantaraR3dis! GET user:1
docker exec -it <redis-container> redis-cli -a NusantaraR3dis! INFO memory | grep used_memory_human
```

### Bagian B — Squid HTTP Proxy Cache (12 Poin)

#### 3.B.1 Konfigurasi Squid (7 Poin)

Buat `squid/squid.conf` dengan ketentuan:

- Port proxy: `3128`.
- Cache ukuran maksimal: `2 GB` di direktori `/var/spool/squid`.
- Objek cache maksimal: `512 MB`.
- Objek cache minimal: `0 KB`.
- **Blokir** akses ke domain berikut (buat ACL `blocked_sites`):
  - `facebook.com`
  - `tiktok.com`
  - `instagram.com`
- Izinkan akses dari network `172.20.0.0/24`.
- Tambahkan custom header: `request_header_add X-Cache-Node NusantaraProxy/1.0`.

#### 3.B.2 Docker Compose untuk Squid (5 Poin)

- Gunakan image `ubuntu/squid:latest` atau `sameersbn/squid:latest`.
- Port: `3128` di-expose ke host.
- Mount `squid/squid.conf` ke konfigurasi squid.
- Gunakan named volume `squid-cache` untuk direktori cache.

#### 3.B.3 Pengujian Squid

```bash
# Test akses normal (harus berhasil)
curl -x http://localhost:3128 http://example.com -I

# Test akses ke domain yang diblokir (harus gagal/denied)
curl -x http://localhost:3128 http://facebook.com -I

# Cek log cache
docker exec -it <squid-container> tail -f /var/log/squid/access.log
```

---

## SOAL 4 — High Availability (25 Poin)

### Latar Belakang
PT. Nusantara Digital membutuhkan infrastruktur yang **highly available** untuk web service mereka. Anda diminta mengimplementasikan arsitektur **Load Balancer + Multiple Backend + Health Check** menggunakan HAProxy dan Nginx.

### Arsitektur Target

```
                    ┌─────────────────────────────────┐
                    │         INTERNET / CLIENT        │
                    └────────────────┬────────────────┘
                                     │ :80
                    ┌────────────────▼────────────────┐
                    │     HAProxy (Load Balancer)      │
                    │         172.20.1.10              │
                    └───────┬──────────────┬───────────┘
                            │              │
               ┌────────────▼──┐    ┌──────▼────────────┐
               │  Backend-1    │    │    Backend-2       │
               │ Nginx:alpine  │    │   Nginx:alpine     │
               │ 172.20.1.21   │    │   172.20.1.22      │
               └───────────────┘    └────────────────────┘
```

### Tugas

#### 4.1 Struktur Direktori (3 Poin)

```
soal4/
├── docker-compose.yml
├── haproxy/
│   └── haproxy.cfg
├── backend1/
│   ├── Dockerfile
│   └── index.html
└── backend2/
    ├── Dockerfile
    └── index.html
```

#### 4.2 Backend Servers (5 Poin)

Buat dua backend Nginx dengan konten yang dapat dibedakan:

**`backend1/index.html`:**
```html
<!DOCTYPE html>
<html>
<head><title>Backend 1</title></head>
<body>
  <h1>Response dari Backend Server 1</h1>
  <p>IP: 172.20.1.21 | Hostname: backend-1</p>
</body>
</html>
```

**`backend2/index.html`:**
```html
<!DOCTYPE html>
<html>
<head><title>Backend 2</title></head>
<body>
  <h1>Response dari Backend Server 2</h1>
  <p>IP: 172.20.1.22 | Hostname: backend-2</p>
</body>
</html>
```

Buat `Dockerfile` masing-masing yang meng-copy `index.html` ke Nginx web root (`FROM nginx:alpine`).

#### 4.3 Konfigurasi HAProxy (12 Poin)

Buat `haproxy/haproxy.cfg` dengan ketentuan:

**Global & Default:**
- Log ke stdout.
- Timeout connect: `5s`, timeout client: `30s`, timeout server: `30s`.
- Mode: `http`.

**Frontend (`frontend_http`):**
- Bind port `80`.
- Default backend: `backend_web`.

**Backend (`backend_web`):**
- Algoritma load balancing: **`roundrobin`**.
- Health check menggunakan HTTP `GET /` setiap `5 detik`.
- Jika backend tidak merespons dalam `3 detik`, tandai sebagai **down**.
- Tambahkan header `X-Forwarded-For` pada semua request.
- Backend server:
  - `backend-1 172.20.1.21:80 check`
  - `backend-2 172.20.1.22:80 check`

**Statistics (Monitoring):**
- Aktifkan HAProxy stats di URI `/haproxy-stats`.
- Akses melalui port `8404`.
- Auth: username `admin`, password `adserver2026`.
- Refresh: setiap 10 detik.

#### 4.4 Docker Compose (5 Poin)

Buat `docker-compose.yml` yang:
- Mendefinisikan service: `haproxy`, `backend-1`, `backend-2`.
- Menggunakan custom network `ha-net` dengan subnet `172.20.1.0/24`.
- Assign IP statis:
  - `haproxy`: `172.20.1.10`
  - `backend-1`: `172.20.1.21`
  - `backend-2`: `172.20.1.22`
- Expose port `80` dan `8404` dari `haproxy` ke host.
- `backend-1` dan `backend-2` menggunakan image yang di-build dari Dockerfile lokal.
- HAProxy harus `depend_on` kedua backend.

#### 4.5 Pengujian High Availability (5 Poin — WAJIB SEMUA)

**Uji 1 — Load Balancing:**
Jalankan 6 request berturut-turut dan amati distribusi response:
```bash
for i in {1..6}; do curl -s http://localhost | grep "Response dari"; done
```
> Output harus bergantian antara Backend 1 dan Backend 2.

**Uji 2 — Failover:**
```bash
# Matikan backend-1
docker compose -f soal4/docker-compose.yml stop backend-1

# Test akses (harus tetap bisa diakses melalui backend-2)
curl http://localhost
```

**Uji 3 — Recovery:**
```bash
# Nyalakan kembali backend-1
docker compose -f soal4/docker-compose.yml start backend-1

# Tunggu health check (±10 detik), lalu test kembali
sleep 15
for i in {1..4}; do curl -s http://localhost | grep "Response dari"; done
```

**Uji 4 — HAProxy Statistics:**
Akses dashboard di `http://localhost:8404/haproxy-stats` dan screenshot halaman statistik.

---

## RUBRIK PENILAIAN

| Soal | Komponen                          | Poin |
|------|-----------------------------------|------|
| 1    | Web Server (Virtual Host + Nginx) | 25   |
| 2    | DNS Server (BIND9 + Zones)        | 25   |
| 3    | Cache Server (Redis + Squid)      | 25   |
| 4    | High Availability (HAProxy)       | 25   |
| **Total** |                            | **100** |

### Kriteria Deduction (Pengurangan Nilai)
- Container tidak berjalan saat penilaian: **-5 poin per soal**
- Tidak ada screenshot pengujian: **-3 poin per soal**
- Konfigurasi copy-paste tanpa penyesuaian (identik antar mahasiswa): **nilai 0 untuk soal tersebut**
- Direktori kerja tidak sesuai format `~/uts-adser/<NIM>/`: **-5 poin total**

---

## PENGUMPULAN

1. Buat archive dari direktori kerja:
   ```bash
   tar -czvf UTS-ADSER-<NIM>-<NAMA>.tar.gz ~/uts-adser/<NIM>/
   ```
2. Upload ke LMS/portal yang telah ditentukan sebelum waktu habis.
3. Sertakan file `laporan.md` berisi screenshot dan penjelasan singkat setiap pengujian.

---

*Selamat mengerjakan.*
