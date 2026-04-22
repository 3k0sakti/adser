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

Kita akan men-deploy aplikasi web sederhana berbasis **Nginx** yang menampilkan halaman identitas mahasiswa. Sepanjang lab, aplikasi ini digunakan untuk mempraktikkan konsep inti Kubernetes: deployment, scaling, autoscaling, dan isolasi namespace.

---

## Struktur Lab

```
Bagian 1  →  Setup Cluster (minikube)
Bagian 2  →  Deploy Aplikasi Web Pertama
Bagian 3  →  Scaling & Self-Healing
Bagian 4  →  Namespace & Isolasi
Bagian 5  →  Cleanup
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
minikube addons enable metrics-server

# Tunggu metrics-server siap (~1 menit), lalu verifikasi
kubectl get pods -n kube-system | grep metrics-server
kubectl top nodes
kubectl top pods
```

Buat file `hpa.yaml` untuk mendefinisikan HPA secara deklaratif:

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

# Pantau status HPA (tunggu beberapa saat hingga kolom TARGETS tidak <unknown>)
kubectl get hpa -w
```

> **Catatan:** Nilai `<unknown>` pada kolom `TARGETS` muncul jika:
> - `metrics-server` belum siap — tunggu 1–2 menit setelah diaktifkan
> - Terdapat lebih dari satu HPA yang mengontrol Deployment yang sama (ambiguous selector)
>
> Pastikan hanya ada **satu HPA** untuk Deployment `webapp`. Cek dengan `kubectl get hpa` dan hapus duplikat jika ada: `kubectl delete hpa <nama-duplikat>`

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

# BAGIAN 4 — Namespace & Isolasi

## 4.1 Apa itu Namespace?

Namespace adalah mekanisme Kubernetes untuk **mengisolasi resource** dalam satu cluster. Berguna untuk memisahkan environment (development vs production) atau tim yang berbeda.

```bash
# Lihat namespace yang ada
kubectl get namespaces

# Namespace bawaan Kubernetes:
# default         – digunakan jika namespace tidak disebutkan
# kube-system     – komponen internal Kubernetes
# kube-public     – resource yang bisa diakses publik
# kube-node-lease – heartbeat node
```

## 4.2 Buat Namespace

```bash
# Buat namespace development dan staging
kubectl create namespace development
kubectl create namespace staging

# Verifikasi
kubectl get namespaces
```

Atau via file YAML:

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
```

```bash
kubectl apply -f namespace.yaml
```

## 4.3 Deploy ke Namespace Tertentu

```bash
# Deploy webapp ke namespace development
kubectl apply -f configmap.yaml -f deployment.yaml -f service.yaml \
  -n development

# Lihat pod di namespace development
kubectl get pods -n development

# Lihat semua pod di semua namespace
kubectl get pods -A
```

## 4.4 Set Default Namespace

Agar tidak perlu mengetik `-n development` setiap saat:

```bash
kubectl config set-context --current --namespace=development

# Verifikasi
kubectl config view --minify | grep namespace

# Kembali ke namespace default
kubectl config set-context --current --namespace=default
```

## 4.5 Batasi Resource dengan ResourceQuota

```yaml
# resourcequota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: development-quota
  namespace: development
spec:
  hard:
    pods: "10"
    requests.cpu: "2"
    requests.memory: 2Gi
    limits.cpu: "4"
    limits.memory: 4Gi
```

```bash
kubectl apply -f resourcequota.yaml
kubectl describe resourcequota development-quota -n development
```

## 4.6 Komunikasi Lintas Namespace

Service dari namespace berbeda dapat diakses via DNS lengkap:

```
<service-name>.<namespace>.svc.cluster.local
```

```bash
# Test dari dalam pod di namespace lain
kubectl run test-pod --image=busybox --restart=Never -it --rm \
  -n staging -- wget -qO- http://webapp-svc.development.svc.cluster.local
```

---

---

# BAGIAN 5 — Cleanup

```bash
# Hapus semua resource yang dibuat
kubectl delete -f ~/k8s-lab/app/

# Hapus namespace beserta semua isinya
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

| Mission | Poin |
|---------|------|
| Mission 1 — Hello, Pod! | 50 poin |
| Mission 2 — Scale It Up! | 50 poin |

**Total maksimum:** 100 poin  
**Nilai minimum lulus:** Selesaikan kedua mission

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
