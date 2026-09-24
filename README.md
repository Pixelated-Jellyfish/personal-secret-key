# SecretNotes Simple

Aplikasi web single-user untuk menyimpan catatan pribadi yang dienkripsi dengan AES-128 sebelum disimpan ke file JSON lokal. Aplikasi juga menyediakan visualisasi proses AES dan key expansion untuk kebutuhan pembelajaran kriptografi.

> **Status keamanan:** proyek ini ditujukan untuk penggunaan lokal dan pembelajaran. Tidak ada autentikasi pengguna, session, auto-lock, atau sinkronisasi. Jangan gunakan untuk menyimpan data sensitif di lingkungan produksi.

## Fitur

- Derive kunci AES-128 dari passphrase menggunakan PBKDF2-HMAC-SHA256.
- CRUD catatan dengan enkripsi AES-CBC dan IV acak untuk setiap catatan.
- Judul dan isi catatan disimpan sebagai ciphertext Base64.
- Visualisasi matriks hex untuk blok pertama dan state setiap ronde AES.
- Visualisasi 11 round key beserta informasi `RotWord`, `SubWord`, dan `Rcon`.
- Penyimpanan lokal berbentuk `backend/data/notes.json` dengan file locking.
- Pengujian AES manual terhadap test vector FIPS-197 dan PyCryptodome.

## Teknologi

- **Frontend:** Vue 3, Vite, Vue Router, Pinia
- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **Kriptografi:** AES-128 manual, CBC, PKCS#7, PBKDF2-HMAC-SHA256
- **Penyimpanan:** JSON lokal
- **Testing:** pytest, Vitest (opsional)

## Prasyarat

- Python 3.11 atau lebih baru
- Node.js 18 atau lebih baru
- npm

## Menjalankan Backend

Dari folder root proyek:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend tersedia di `http://localhost:8000`.

- Health check: `http://localhost:8000/health`
- Dokumentasi Swagger: `http://localhost:8000/docs`

Jika PowerShell tidak mengizinkan aktivasi virtual environment, jalankan:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Menjalankan Frontend

Buka terminal baru:

```powershell
cd frontend
npm install
npm run dev
```

Buka `http://localhost:5173` di browser. Vite meneruskan request `/api` ke backend pada port `8000`.

Untuk membuat build produksi:

```powershell
npm run build
npm run preview
```

## Alur Penggunaan

1. Masukkan passphrase minimal 8 karakter pada halaman awal.
2. Backend menurunkan passphrase menjadi kunci AES-128 melalui endpoint `/api/crypto/derive`.
3. Kunci disimpan di state Pinia dan `sessionStorage` pada tab browser agar tetap tersedia saat reload; kunci hilang saat session browser berakhir atau dihapus.
4. Buat, baca, ubah, atau hapus catatan dari halaman Notes.
5. Buka **AES Lab** untuk melihat trace blok AES dan round keys.

Kunci dikirim ke endpoint catatan melalui header `X-AES-Key` dalam format Base64. Kunci, passphrase, dan plaintext tidak ditulis ke `notes.json`.

## API Utama

Semua endpoint catatan memerlukan header `X-AES-Key`, kecuali endpoint derive key.

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `POST` | `/api/crypto/derive` | Derive kunci dari passphrase |
| `GET` | `/api/notes` | Daftar catatan dengan judul terdekripsi |
| `POST` | `/api/notes` | Membuat catatan |
| `GET` | `/api/notes/{id}` | Mengambil dan mendekripsi catatan |
| `PUT` | `/api/notes/{id}` | Mengubah dan mengenkripsi ulang catatan dengan IV baru |
| `DELETE` | `/api/notes/{id}` | Menghapus catatan |
| `GET` | `/api/notes/{id}/aes-log` | Mengambil trace visualisasi AES |
| `GET` | `/api/notes/{id}/round-keys` | Mengambil 11 round keys |

Contoh derive key:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/crypto/derive `
  -ContentType 'application/json' `
  -Body '{"passphrase":"passphrase-rahasia"}'
```

## Penyimpanan Data

File `backend/data/notes.json` dibuat otomatis saat catatan pertama disimpan. Bentuk datanya hanya berisi metadata, ciphertext, dan IV:

```json
{
  "notes": [
    {
      "id": "uuid-v4-string",
      "title_ciphertext": "base64",
      "title_iv": "base64",
      "body_ciphertext": "base64",
      "body_iv": "base64",
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ]
}
```

Jangan commit file `.env`, kunci, passphrase, atau data catatan pribadi ke repository.

## Menjalankan Test

Backend:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pytest -v
```

Frontend (belum memiliki file test otomatis):

```powershell
cd frontend
npm run build
```

## Struktur Proyek

```text
backend/
├── app/
│   ├── crypto/          # AES, KDF, CBC, dan padding
│   ├── routes/          # Endpoint REST catatan dan visualisasi
│   ├── config.py        # Konfigurasi environment
│   ├── main.py          # Aplikasi FastAPI
│   ├── schemas.py       # Model request dan response
│   └── storage.py       # Penyimpanan JSON terenkripsi
├── data/                # notes.json dibuat saat runtime
└── tests/               # Test AES dan API

frontend/
├── src/
│   ├── api/             # Client API
│   ├── components/      # Komponen visualisasi
│   ├── router/          # Routing Vue
│   ├── stores/          # State kunci dan catatan
│   └── views/           # Halaman aplikasi
└── package.json
```

## Konfigurasi Environment

Salin `backend/.env.example` menjadi `backend/.env`, lalu sesuaikan bila diperlukan:

- `SALT_BASE64`: salt PBKDF2 dalam Base64.
- `CORS_ORIGINS`: daftar origin frontend yang dipisahkan koma.

Salt yang berubah akan membuat passphrase menghasilkan kunci berbeda, sehingga catatan lama tidak dapat didekripsi dengan benar.
