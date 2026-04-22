# Hands-On Lab: Kubernetes


---

## Prasyarat

Sebelum memulai, pastikan tools berikut sudah terinstal di laptop kamu:

| Tool | Versi Minimum | Cek Instalasi |
|------|--------------|---------------|
| Docker Desktop | 24+ | `docker --version` |
| minikube | 1.33+ | `minikube version` |
| kubectl | 1.29+ | `kubectl version --client` |
| (Opsional) Helm | 3.14+ | `helm version` |

### Instalasi Cepat (macOS)

```bash
# minikube
brew install minikube

# kubectl
brew install kubectl

# helm
brew install helm
```

### Instalasi Cepat (Windows – PowerShell sebagai Admin)

```powershell
# minikube
winget install Kubernetes.minikube

# kubectl
winget install Kubernetes.kubectl

# helm
winget install Helm.Helm
```

---

## Deskripsi Aplikasi

Kita akan men-deploy aplikasi web sederhana bernama **GuestBook App** — sebuah aplikasi buku tamu berbasis Node.js + Redis yang terdiri dari 3 komponen:

```
Browser
   │
   ▼
[Frontend: Node.js]  ──→  [Redis Master]
                    ──→  [Redis Replica]
```

| Komponen | Image | Port |
|----------|-------|------|
| Frontend | `ealen/echo-server` atau custom Node.js | 3000 |
| Redis Master | `redis:7-alpine` | 6379 |
| Redis Replica | `redis:7-alpine` | 6379 |

> **Catatan:** Untuk menyederhanakan, kita akan mulai dari aplikasi **single-container** lalu bertahap naik ke arsitektur multi-komponen.

---

## Struktur Lab

```
Bagian 1  →  Setup Cluster (minikube)
Bagian 2  →  Deploy Aplikasi Web Pertama
Bagian 3  →  Scaling & Self-Healing
Bagian 4  →  Update & Rollback
Bagian 5  →  ConfigMap & Secret
Bagian 6  →  Persistent Storage
Bagian 7  →  Multi-Komponen (GuestBook Full)
```

---

---

# BAGIAN 1 — Setup Cluster

## 1.1 Jalankan Minikube

```bash
# Start cluster dengan 2 CPU dan 4GB RAM
minikube start --cpus=2 --memory=4096 --driver=docker

# Verifikasi cluster berjalan
kubectl cluster-info

# Lihat node yang tersedia
kubectl get nodes
```

Output yang diharapkan:
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.29.x
```

## 1.2 Aktifkan Add-on Berguna

```bash
# Dashboard web Kubernetes
minikube addons enable dashboard

# Metrics server (dibutuhkan untuk HPA)
minikube addons enable metrics-server

# Ingress controller
minikube addons enable ingress

# Lihat semua add-on
minikube addons list
```

## 1.3 Buka Dashboard

```bash
minikube dashboard
```

> Browser akan terbuka otomatis. Eksplorasi UI-nya!

---

---

# BAGIAN 2 — Deploy Aplikasi Web Pertama

## 2.1 Buat Direktori Kerja

```bash
mkdir -p ~/k8s-lab/app && cd ~/k8s-lab/app
```

## 2.2 Buat Manifest: ConfigMap (Halaman Web Kamu)

Buat file `configmap.yaml`. **Ganti nilai `NAMA`, `NIM`, dan `KELAS` dengan data kamu sendiri.**

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-html
data:
  index.html: |
    <!DOCTYPE html>
    <html lang="id">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Kubernetes Lab</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: 'Segoe UI', sans-serif;
          background: #0d1b2a;
          color: #e0e0e0;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
        }
        .card {
          background: #1b2a4a;
          border: 1px solid #326ce5;
          border-radius: 16px;
          padding: 48px 56px;
          text-align: center;
          box-shadow: 0 0 40px rgba(50,108,229,0.3);
          max-width: 480px;
          width: 90%;
        }
        .logo { font-size: 64px; margin-bottom: 16px; }
        h1 { font-size: 1.8em; color: #5fa8d3; margin-bottom: 8px; }
        .name { font-size: 2em; font-weight: bold; color: #ffffff; margin: 16px 0 4px; }
        .nim  { font-size: 1em; color: #8ab4d4; margin-bottom: 4px; }
        .kelas { font-size: 0.9em; color: #8ab4d4; margin-bottom: 24px; }
        .badge {
          display: inline-block;
          background: #326ce5;
          color: #fff;
          border-radius: 20px;
          padding: 6px 18px;
          font-size: 0.85em;
          margin-top: 8px;
        }
        .footer { margin-top: 28px; font-size: 0.75em; color: #4a6a8a; }
      </style>
    </head>
    <body>
      <div class="card">
        <div class="logo">&#9096;</div>
        <h1>Kubernetes Lab</h1>
        <p style="color:#8ab4d4; font-size:0.9em;">Advanced Services &mdash; Universitas Brawijaya</p>
        <div class="name">Nama Mahasiswa</div>
        <div class="nim">NIM: 000000000000</div>
        <div class="kelas">Kelas: A</div>
        <div class="badge">Running on Kubernetes</div>
        <div class="footer">Semester Genap 2025/2026</div>
      </div>
    </body>
    </html>
```

> **Penting:** Ubah baris `Nama Mahasiswa`, `000000000000`, dan `Kelas: A` dengan nama, NIM, dan kelas kamu sebelum apply!

## 2.3 Buat Manifest: Deployment

Buat file `deployment.yaml`:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app: webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        volumeMounts:
        - name: html-volume
          mountPath: /usr/share/nginx/html
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: html-volume
        configMap:
          name: webapp-html
```

## 2.4 Buat Manifest: Service

Buat file `service.yaml`:

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp-svc
spec:
  selector:
    app: webapp
  type: NodePort
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 30080
```

## 2.5 Terapkan ke Cluster

```bash
# Apply semua file sekaligus
kubectl apply -f configmap.yaml -f deployment.yaml -f service.yaml

# Pantau status Pod
kubectl get pods -w

# Lihat detail Deployment
kubectl get deployment webapp

# Lihat Service
kubectl get service webapp-svc
```

## 2.6 Akses Aplikasi

```bash
# Dapatkan URL akses
minikube service webapp-svc --url

# Atau buka langsung di browser
minikube service webapp-svc
```

Kamu akan melihat halaman web dengan **nama kamu sendiri** yang berjalan di dalam Pod Kubernetes.

> **Refresh beberapa kali** — perhatikan bahwa kontennya sama karena berasal dari ConfigMap yang sama, tapi trafik dilayani bergantian oleh 2 replika (cek dengan `kubectl logs`)!

## 2.7 Update Tampilan Tanpa Rebuild Image

Salah satu keunggulan ConfigMap: ubah isi web **tanpa perlu rebuild image**!

```bash
# Edit ConfigMap langsung
kubectl edit configmap webapp-html

# Setelah save, restart deployment agar Pod membaca ConfigMap terbaru
kubectl rollout restart deployment/webapp

# Pantau
kubectl rollout status deployment/webapp
```

## 2.8 Eksplorasi dengan kubectl

```bash
# Lihat log salah satu Pod
kubectl get pods                          # catat nama pod
kubectl logs <nama-pod>

# Masuk ke dalam container
kubectl exec -it <nama-pod> -- /bin/sh

# Di dalam container, coba:
hostname
cat /usr/share/nginx/html/index.html     # lihat isi HTML yang di-mount
exit

# Describe Pod untuk melihat events (termasuk mount volume)
kubectl describe pod <nama-pod>
```

---

---

# BAGIAN 3 — Scaling & Self-Healing

## 3.1 Scale Manual

```bash
# Scale naik ke 5 replika
kubectl scale deployment webapp --replicas=5

# Pantau proses scaling
kubectl get pods -w

# Konfirmasi
kubectl get deployment webapp
```

## 3.2 Uji Self-Healing

```bash
# Di terminal 1: pantau pod
kubectl get pods -w

# Di terminal 2: hapus salah satu pod secara paksa
kubectl delete pod <nama-pod>
```

Amati: K8s langsung membuat Pod pengganti secara otomatis!

## 3.3 Horizontal Pod Autoscaler (HPA)

```bash
# Pastikan metrics-server aktif
kubectl top nodes
kubectl top pods

# Buat HPA
kubectl autoscale deployment webapp \
  --cpu-percent=50 \
  --min=2 \
  --max=10

# Lihat status HPA
kubectl get hpa
```

Buat file `hpa.yaml` untuk versi deklaratif:

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

```bash
kubectl apply -f hpa.yaml
kubectl get hpa -w
```

## 3.4 Simulasi Load (Opsional)

```bash
# Buka terminal baru, jalankan load generator
kubectl run load-generator --image=busybox:1.36 \
  --restart=Never -- /bin/sh -c \
  "while true; do wget -q -O- http://webapp-svc; done"

# Pantau HPA bereaksi (tunggu ~2 menit)
kubectl get hpa -w

# Setelah selesai, hapus load generator
kubectl delete pod load-generator
```

---

---

# BAGIAN 4 — Update & Rollback

## 4.1 Rolling Update via ConfigMap

Karena tampilan web dikontrol oleh ConfigMap, cara paling natural untuk "update" konten adalah dengan mengubah ConfigMap — tetapi untuk melatih rolling update image, kita juga bisa naik versi Nginx-nya.

```bash
# Update image dari nginx:alpine ke nginx:1.27-alpine
kubectl set image deployment/webapp \
  webapp=nginx:1.27-alpine

# Pantau proses update
kubectl rollout status deployment/webapp

# Lihat history
kubectl rollout history deployment/webapp
```

## 4.2 Update Konten Web (tanpa rebuild image)

Edit ConfigMap untuk mengubah tampilan halaman:

```bash
kubectl edit configmap webapp-html
# Ubah teks di bagian HTML, misalnya tambahkan versi: "v2.0"
# Simpan dan keluar

# Restart deployment agar Pod memuat ConfigMap terbaru
kubectl rollout restart deployment/webapp
kubectl rollout status deployment/webapp
```

## 4.3 Update via YAML

Edit `deployment.yaml`, ubah baris image:

```yaml
        image: nginx:1.27-alpine   # ubah dari nginx:alpine
```

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/webapp
```

## 4.3 Rollback

```bash
# Rollback ke versi sebelumnya
kubectl rollout undo deployment/webapp

# Rollback ke revision tertentu
kubectl rollout undo deployment/webapp --to-revision=1

# Cek status
kubectl rollout history deployment/webapp
kubectl get pods
```

---

---

# BAGIAN 5 — ConfigMap & Secret

Di Bagian 2 kita sudah pakai ConfigMap untuk menyimpan HTML. Sekarang kita tambah ConfigMap untuk **environment variable** aplikasi, dan Secret untuk data sensitif.

## 5.1 Buat ConfigMap untuk Environment Variable

```yaml
# configmap-env.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-config
data:
  APP_ENV: "production"
  APP_NAME: "GuestBook K8s Lab"
  APP_VERSION: "1.0.0"
  WELCOME_MESSAGE: "Selamat datang di Kubernetes Lab!"
```

```bash
kubectl apply -f configmap.yaml
kubectl get configmap webapp-config
kubectl describe configmap webapp-config
```

## 5.2 Buat Secret

```bash
# Buat secret dari command line
kubectl create secret generic webapp-secret \
  --from-literal=DB_PASSWORD=supersecret123 \
  --from-literal=API_KEY=myapikey-abc

# Lihat secret (value ter-encode base64)
kubectl get secret webapp-secret -o yaml
```

Atau via file `secret.yaml`:

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: webapp-secret
type: Opaque
stringData:
  DB_PASSWORD: "supersecret123"
  API_KEY: "myapikey-abc"
```

```bash
kubectl apply -f secret.yaml
```

## 5.3 Gunakan ConfigMap & Secret di Deployment

Update `deployment.yaml` untuk menyertakan environment variables:

```yaml
# deployment.yaml (bagian containers, tambahkan di bawah resources)
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: webapp-config
              key: APP_ENV
        - name: APP_NAME
          valueFrom:
            configMapKeyRef:
              name: webapp-config
              key: APP_NAME
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: webapp-secret
              key: DB_PASSWORD
```

```bash
kubectl apply -f deployment.yaml

# Verifikasi env variable masuk ke container
kubectl exec -it <nama-pod> -- env | grep -E "APP_|DB_"
```

---

---

# BAGIAN 6 — Persistent Storage

## 6.1 Buat PersistentVolumeClaim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: webapp-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc
kubectl get pv   # PV dibuat otomatis (dynamic provisioning)
```

## 6.2 Mount PVC ke Pod

Update `deployment.yaml`, tambahkan volume dan mount:

```yaml
# Di spec.template.spec, tambahkan:
      volumes:
      - name: webapp-storage
        persistentVolumeClaim:
          claimName: webapp-pvc

# Di containers, tambahkan:
        volumeMounts:
        - name: webapp-storage
          mountPath: /usr/share/nginx/html/data
```

```bash
kubectl apply -f deployment.yaml

# Tulis data ke storage
kubectl exec -it <nama-pod> -- \
  sh -c "echo 'Data persisten!' > /usr/share/nginx/html/data/test.txt"

# Hapus pod, data tetap ada karena tersimpan di PV
kubectl delete pod <nama-pod>
kubectl exec -it <pod-baru> -- cat /usr/share/nginx/html/data/test.txt
```

---

---

# BAGIAN 7 — Multi-Komponen: GuestBook App

Pada bagian ini kita deploy aplikasi lengkap dengan frontend + Redis.

## 7.1 Struktur File

```bash
mkdir -p ~/k8s-lab/guestbook && cd ~/k8s-lab/guestbook
```

## 7.2 Redis Master

```yaml
# redis-master.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-master
  labels:
    app: redis
    role: master
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
      role: master
  template:
    metadata:
      labels:
        app: redis
        role: master
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--appendonly", "yes"]
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-master
spec:
  selector:
    app: redis
    role: master
  ports:
  - port: 6379
    targetPort: 6379
```

## 7.3 Redis Replica

```yaml
# redis-replica.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-replica
  labels:
    app: redis
    role: replica
spec:
  replicas: 2
  selector:
    matchLabels:
      app: redis
      role: replica
  template:
    metadata:
      labels:
        app: redis
        role: replica
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --replicaof
        - redis-master
        - "6379"
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-replica
spec:
  selector:
    app: redis
    role: replica
  ports:
  - port: 6379
    targetPort: 6379
```

## 7.4 Frontend GuestBook

```yaml
# frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: guestbook
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: guestbook
      tier: frontend
  template:
    metadata:
      labels:
        app: guestbook
        tier: frontend
    spec:
      containers:
      - name: php-redis
        image: gcr.io/google_samples/gb-frontend:v5
        env:
        - name: GET_HOSTS_FROM
          value: dns
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  labels:
    app: guestbook
    tier: frontend
spec:
  selector:
    app: guestbook
    tier: frontend
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30090
```

## 7.5 Deploy Semua Komponen

```bash
kubectl apply -f redis-master.yaml
kubectl apply -f redis-replica.yaml
kubectl apply -f frontend.yaml

# Pantau semua pod
kubectl get pods -l app=redis
kubectl get pods -l app=guestbook

# Lihat semua resource
kubectl get all

# Akses frontend
minikube service frontend
```

## 7.6 Verifikasi Redis Replication

```bash
# Masuk ke Redis Master
kubectl exec -it <redis-master-pod> -- redis-cli

# Di dalam redis-cli:
INFO replication
SET mykey "Hello dari K8s Lab!"
GET mykey
exit

# Cek replica
kubectl exec -it <redis-replica-pod> -- redis-cli
GET mykey    # harus ada nilainya
exit
```

---

---

# BAGIAN 8 — Namespace & Isolasi

```bash
# Buat namespace untuk dev dan staging
kubectl create namespace development
kubectl create namespace staging

# Deploy webapp di namespace development
kubectl apply -f deployment.yaml -f service.yaml -n development

# Deploy webapp di namespace staging (versi berbeda)
kubectl apply -f deployment.yaml -f service.yaml -n staging

# Lihat resource per namespace
kubectl get all -n development
kubectl get all -n staging

# Bandingkan
kubectl get pods --all-namespaces
```

---

---

# BAGIAN 9 — Cleanup

```bash
# Hapus semua resource yang dibuat
kubectl delete -f ~/k8s-lab/app/
kubectl delete -f ~/k8s-lab/guestbook/

# Atau hapus namespace (hapus semua isinya)
kubectl delete namespace development staging

# Stop minikube
minikube stop

# (Opsional) Hapus cluster
minikube delete
```

---

---

# MISSION CARDS

> Setiap mission card adalah tantangan mandiri yang harus diselesaikan mahasiswa.  
> Tandai saat berhasil diselesaikan dan screenshot bukti ke laporan.

---

## Mission 1 — "Hello, Pod!"
**Level:** Pemula | **Estimasi:** 15 menit

**Misi:**  
Deploy sebuah Pod Nginx menggunakan file YAML minimal (tanpa Deployment), lalu akses halaman utamanya.

**Kriteria Berhasil:**
- [ ] Pod berstatus `Running`
- [ ] Bisa mengakses halaman Nginx lewat `kubectl port-forward`
- [ ] Bisa melihat log Pod

**Hint:**  
Gunakan `kubectl port-forward pod/<nama-pod> 8080:80` lalu buka `http://localhost:8080`

**Screenshot yang diperlukan:** Output `kubectl get pod` dan tampilan browser.

---

## Mission 2 — "Scale It Up!"
**Level:** Pemula | **Estimasi:** 20 menit

**Misi:**  
Buat Deployment dengan 1 replika, lalu scale ke 5 replika, kemudian buktikan self-healing bekerja.

**Kriteria Berhasil:**
- [ ] Deployment berhasil dibuat dengan 1 replika
- [ ] Berhasil di-scale ke 5 replika
- [ ] Hapus salah satu Pod → Pod baru otomatis muncul
- [ ] Screenshot terminal menunjukkan Pod baru dibuat

**Hint:**  
Gunakan 2 terminal: satu untuk `kubectl get pods -w`, satu lagi untuk `kubectl delete pod <nama>`.

---

## Mission 3 — "Zero Downtime Update"
**Level:** Menengah | **Estimasi:** 25 menit

**Misi:**  
Lakukan rolling update dari `nginxdemos/hello:latest` ke `nginxdemos/hello:plain-text` tanpa downtime, lalu rollback ke versi sebelumnya.

**Kriteria Berhasil:**
- [ ] Update berhasil menggunakan `kubectl set image`
- [ ] Output `kubectl rollout status` menunjukkan sukses
- [ ] `kubectl rollout history` menunjukkan minimal 2 revision
- [ ] Rollback berhasil ke revision awal

**Pertanyaan Refleksi:** Apa perbedaan yang kamu amati antara tampilan `hello:latest` dan `hello:plain-text`?

---

## Mission 4 — "Config Wizard"
**Level:** Menengah | **Estimasi:** 30 menit

**Misi:**  
Buat sebuah ConfigMap berisi informasi identitas kamu (nama, NIM, angkatan), lalu inject ke dalam Pod sebagai environment variable. Tambahkan juga Secret berisi "password rahasia".

**Kriteria Berhasil:**
- [ ] ConfigMap berisi `STUDENT_NAME`, `STUDENT_NIM`, `STUDENT_YEAR`
- [ ] Secret berisi `SECRET_TOKEN`
- [ ] Environment variable berhasil masuk ke container
- [ ] Verifikasi dengan `kubectl exec ... -- env | grep STUDENT`

**Bonus:** Mount ConfigMap sebagai file (bukan env var) di path `/etc/config/`.

---

## Mission 5 — "Ingress Gateway"
**Level:** Menengah | **Estimasi:** 35 menit

**Misi:**  
Buat 2 Deployment berbeda (app-a dan app-b), kemudian buat satu Ingress yang merutekan:
- `http://lab.local/app-a` → app-a
- `http://lab.local/app-b` → app-b

**Kriteria Berhasil:**
- [ ] Kedua Deployment berjalan
- [ ] Ingress resource berhasil dibuat
- [ ] Routing berbasis path berfungsi (tambahkan entry ke `/etc/hosts`)
- [ ] Kedua path menampilkan aplikasi yang berbeda

**Hint:**  
```bash
echo "$(minikube ip) lab.local" | sudo tee -a /etc/hosts
```

---

## Mission 6 — "Stateful GuestBook"
**Level:** Lanjutan | **Estimasi:** 45 menit

**Misi:**  
Deploy GuestBook App lengkap (frontend + Redis Master + Redis Replica) sesuai Bagian 7, lalu verifikasi bahwa data di Redis Master ter-replikasi ke Redis Replica.

**Kriteria Berhasil:**
- [ ] Semua 3 komponen berjalan (frontend, redis-master, redis-replica)
- [ ] Aplikasi GuestBook bisa diakses di browser
- [ ] Data yang di-SET di redis-master bisa di-GET dari redis-replica
- [ ] Screenshot `INFO replication` dari redis-master

**Bonus:** Scale redis-replica menjadi 3 replika dan verifikasi semua mendapat data replikasi.

---

## Mission 7 — "HPA in Action"
**Level:** Lanjutan | **Estimasi:** 40 menit

**Misi:**  
Buat HPA untuk Deployment kamu, lalu simulasikan beban tinggi menggunakan load generator hingga HPA otomatis scale up.

**Kriteria Berhasil:**
- [ ] HPA berhasil dibuat dengan min=2, max=8, cpu=50%
- [ ] Load generator berjalan
- [ ] `kubectl get hpa -w` menunjukkan REPLICAS bertambah
- [ ] Setelah load dihentikan, replika kembali ke minimum

**Pertanyaan Refleksi:** Berapa lama K8s butuh waktu untuk scale up? Berapa lama untuk scale down (cool-down period)?

---

## Mission 8 — "Namespace Isolation"
**Level:** Lanjutan | **Estimasi:** 40 menit

**Misi:**  
Deploy aplikasi yang sama (webapp) di dua namespace berbeda (`development` dan `production`). Pastikan Service di satu namespace **tidak bisa** diakses dari namespace lain menggunakan NetworkPolicy.

**Kriteria Berhasil:**
- [ ] Namespace `development` dan `production` berhasil dibuat
- [ ] Webapp berjalan di kedua namespace dengan konfigurasi berbeda (gunakan ConfigMap berbeda)
- [ ] NetworkPolicy diterapkan untuk membatasi traffic lintas namespace
- [ ] Verifikasi isolasi dengan `kubectl exec ... -- curl`

**Hint:**  
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-from-other-namespaces
  namespace: production
spec:
  podSelector: {}
  ingress:
  - from:
    - podSelector: {}
```

---

## Mission 9 — "Helm Chart Master"
**Level:** Expert | **Estimasi:** 60 menit

**Misi:**  
Buat Helm Chart sendiri untuk webapp yang kamu buat, dengan `values.yaml` yang memungkinkan konfigurasi `replicaCount`, `image.tag`, `service.type`, dan custom environment variables.

**Kriteria Berhasil:**
- [ ] Helm chart berhasil dibuat dengan struktur yang benar
- [ ] `helm install` berhasil tanpa error
- [ ] Bisa mengubah konfigurasi via `--set` atau `--values`
- [ ] `helm upgrade` berhasil
- [ ] `helm rollback` berhasil

**Struktur yang diharapkan:**
```
webapp-chart/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── hpa.yaml
```

---

## Mission 10 — "Full Stack DevOps Pipeline"
**Level:** Expert | **Estimasi:** 90 menit

**Misi:**  
Buat aplikasi web sederhana (Node.js/Python Flask), dockerize, push ke DockerHub, lalu deploy ke Kubernetes dengan:
- Deployment + Service + Ingress
- ConfigMap untuk konfigurasi app
- Secret untuk API key
- HPA untuk autoscaling
- Liveness & Readiness probe

**Kriteria Berhasil:**
- [ ] Aplikasi berjalan di container lokal dengan Docker
- [ ] Image berhasil di-push ke DockerHub (tag: `<username>/myapp:v1`)
- [ ] Deployment menggunakan image dari DockerHub
- [ ] Semua komponen berjalan di Kubernetes
- [ ] HPA aktif dan terkonfigurasi

**Deliverable:**  
Kumpulkan semua file YAML + Dockerfile + link DockerHub image + screenshot aplikasi berjalan di K8s.

---

---

# Format Laporan

Kumpulkan laporan praktikum dalam format **Markdown atau PDF** dengan struktur:

```
1. Identitas (Nama, NIM, Kelas)
2. Tujuan Praktikum
3. Langkah Pengerjaan (per Mission Card yang dikerjakan)
   - Screenshot terminal
   - Screenshot browser/aplikasi
   - Penjelasan singkat tiap langkah
4. Refleksi & Kesimpulan
5. Kendala & Solusi
```

### Penilaian Mission Card

| Level | Poin per Mission |
|-------|-----------------|
| Pemula | 10 poin |
| Menengah | 20 poin |
| Lanjutan | 30 poin |
| Expert | 40 poin |

**Total maksimum:** 230 poin  
**Nilai minimum lulus:** Selesaikan minimal 3 mission (1 Pemula + 1 Menengah + 1 Lanjutan)

---

---

# Referensi & Cheatsheet

## kubectl Cheatsheet

```bash
# === CLUSTER ===
kubectl cluster-info
kubectl get nodes -o wide
kubectl top nodes

# === POD ===
kubectl get pods                          # semua pod di default namespace
kubectl get pods -A                       # semua pod di semua namespace
kubectl get pods -o wide                  # tampilkan IP & node
kubectl describe pod <pod-name>
kubectl logs <pod-name> -f                # follow log
kubectl logs <pod-name> -c <container>    # log container tertentu
kubectl exec -it <pod-name> -- bash
kubectl port-forward pod/<pod> 8080:80

# === DEPLOYMENT ===
kubectl get deployments
kubectl apply -f deployment.yaml
kubectl scale deployment <name> --replicas=5
kubectl set image deployment/<name> <container>=<image>:<tag>
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>

# === SERVICE ===
kubectl get services
kubectl expose deployment <name> --port=80 --type=NodePort

# === CONFIGMAP & SECRET ===
kubectl create configmap <name> --from-literal=KEY=VALUE
kubectl create secret generic <name> --from-literal=KEY=VALUE
kubectl get configmap
kubectl get secret

# === NAMESPACE ===
kubectl get namespaces
kubectl create namespace <name>
kubectl config set-context --current --namespace=<name>

# === CLEANUP ===
kubectl delete -f file.yaml
kubectl delete pod <name>
kubectl delete all --all -n <namespace>
```

## Referensi Online

- [Kubernetes Official Docs](https://kubernetes.io/docs/home/)
- [Kubernetes Interactive Tutorial](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [Play with Kubernetes](https://labs.play-with-k8s.com/)
- [Helm Hub](https://artifacthub.io/)
- [CNCF Landscape](https://landscape.cncf.io/)

---

> **Selamat belajar! Kubernetes mungkin terlihat kompleks di awal, tapi setelah hands-on, semuanya akan terasa logis dan natural.**
