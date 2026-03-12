
# Praktikum: Web Server Caching dengan Nginx


**Topik**       : Caching — Browser Cache, Proxy Cache, Conditional Request  
**Prasyarat**   : Nginx 1.24 sudah terinstal, Python 3.10+  

---

## Struktur Materi

```
cache/
├── README.md                      ← panduan ini
├── setup.sh                       ← skrip persiapan lingkungan
├── backend/
│   ├── server.py                  ← backend demo (Python stdlib)
│   └── static/
│       ├── index.html             ← UI interaktif
│       └── style.css
├── nginx/
│   ├── 1-browser-cache.conf       ← konfigurasi A: browser cache headers
│   └── 2-proxy-cache.conf         ← konfigurasi B: nginx proxy cache
└── hands-on/
    └── hands-on-cache.ipynb       ← notebook utama
```

---

## Konsep yang Dipelajari

| Konsep | Keterangan |
|--------|-----------|
| **Browser Cache** | Browser menyimpan respons di disk/memori klien |
| `Cache-Control: max-age` | Cache valid selama N detik |
| `Cache-Control: no-store` | Larang cache sama sekali |
| **ETag** | Fingerprint konten untuk conditional request (304) |
| **Last-Modified** | Timestamp untuk conditional request (304) |
| **Nginx Proxy Cache** | Nginx menyimpan cache di server (bukan di browser) |
| `X-Cache-Status` | Status cache nginx: MISS / HIT / EXPIRED / STALE |
| **Cache Busting** | Teknik memaksa cache diperbarui |

---

## Cara Memulai

### Langkah 1 — Jalankan Backend Server

Buka terminal, jalankan:

```bash
python3 /home/momotaro/cache/backend/server.py
```

Server berjalan di `http://localhost:8181`. Biarkan terminal ini terbuka.

### Langkah 2 — Aktifkan Nginx

Buka terminal baru:

```bash
bash /home/momotaro/cache/setup.sh
```

Pilih konfigurasi:
- **Opsi 1** → Browser Cache Headers (mulai dari sini)
- **Opsi 2** → Nginx Proxy Cache (bagian lanjutan)

Nginx kini mendengarkan di port **8080**.

### Langkah 3 — Buka Notebook

Buka file `hands-on/hands-on-cache.ipynb` di VS Code, jalankan sel dari atas ke bawah.

---

## Endpoint Backend

| Endpoint | Header Cache | Deskripsi |
|----------|-------------|-----------|
| `GET /api/nocache` | `no-store` | Selalu baru, tidak boleh cache |
| `GET /api/cacheable` | `max-age=30` | Cache valid 30 detik |
| `GET /api/etag` | `ETag` | Conditional request via ETag |
| `GET /api/lastmod` | `Last-Modified` | Conditional request via timestamp |
| `GET /api/slow` | `max-age=20` | Simulasi respons lambat 1,5 detik |
| `GET /api/counter` | `no-store` | Statistik kunjungan ke backend |
| `GET /api/reset` | `no-store` | Reset semua counter |

---

## Pengujian Cepat via `curl`

```bash
# Lihat semua header respons
curl -v http://localhost:8080/api/cacheable 2>&1 | grep -E "< (HTTP|cache|etag|age|x-cache)"

# Kirim 3 request berturut — amati X-Cache-Status
for i in 1 2 3; do
  echo "--- Request $i ---"
  curl -si http://localhost:8080/api/slow | grep -i "x-cache\|elapsed\|kunjungan"
done

# Conditional request ETag manual
ETAG=$(curl -si http://localhost:8080/api/etag | grep -i etag | awk '{print $2}' | tr -d '\r')
echo "ETag: $ETAG"
curl -si -H "If-None-Match: $ETAG" http://localhost:8080/api/etag | head -3
```

---

## Melihat & Membersihkan Cache Nginx

```bash
# Lihat file cache di disk
ls -lhR /var/cache/nginx/cache_demo/

# Ukuran total cache
du -sh /var/cache/nginx/cache_demo/

# Bersihkan semua cache
sudo rm -rf /var/cache/nginx/cache_demo/*
sudo systemctl reload nginx

# Lihat log akses nginx
tail -f /var/log/nginx/cache_demo_access.log
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `Connection refused` di port 8080 | Jalankan `sudo systemctl start nginx` |
| `Connection refused` di port 8181 | Jalankan `server.py` |
| `nginx -t` gagal | Periksa sintaks dengan `sudo nginx -t 2>&1` |
| `X-Cache-Status` tidak muncul | Pastikan menggunakan konfigurasi opsi 2 |
| Cache tidak kena walau sudah 30 detik | Cek `proxy_cache_valid` di config nginx |
| Permission denied di `/var/cache/nginx` | Jalankan `sudo chown -R www-data:www-data /var/cache/nginx/cache_demo` |
