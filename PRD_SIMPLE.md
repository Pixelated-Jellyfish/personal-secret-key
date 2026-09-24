# PRD: SecretNotes Simple — Aplikasi Catatan Rahasia Berenkripsi AES (Tanpa Auth)

> Versi sederhana dari PRD asli. Fokus pada fungsionalitas inti: enkripsi/dekripsi catatan dengan AES + visualisasi proses AES. Tidak ada login, PIN, session, atau auto-lock.

## 1. Ringkasan

SecretNotes Simple adalah aplikasi web single-user untuk menyimpan catatan pribadi yang dienkripsi dengan AES sebelum disimpan ke file JSON. Aplikasi ini juga menampilkan visualisasi proses AES (matriks hex blok pertama dan round keys) untuk tujuan pembelajaran kriptografi.

**Konteks:** Proyek akademik (D3 Teknik Informatika). Kode harus sederhana, mudah dibaca, dan mudah dijelaskan.

## 2. Tujuan dan Non-Tujuan

**Tujuan**
- Catatan di database (JSON) hanya berupa ciphertext.
- Menampilkan cara kerja AES secara visual (matriks hex per ronde + round keys).
- Kode sederhana, berkomentar, tanpa abstraksi berlebihan.

**Non-tujuan**
- Multi-user / autentikasi / PIN / session / auto-lock
- Database PostgreSQL/Supabase
- Lampiran file, sinkronisasi, aplikasi mobile

## 3. Tech Stack

| Lapisan | Teknologi |
|---|---|
| Frontend | Vue.js 3 (Composition API), Vite, Vue Router, Pinia |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | File JSON lokal (`data/notes.json`) |
| Kripto | Implementasi AES manual (`aes.py`), PBKDF2 (`hashlib`), pembanding: `pycryptodome` |
| Pengujian | pytest (backend), Vitest (frontend, opsional) |

## 4. Keputusan Desain

| # | Keputusan | Nilai |
|---|---|---|
| D1 | Lokasi enkripsi | Backend Python |
| D2 | Ukuran kunci | AES-128 (10 ronde, 11 round key) |
| D3 | Mode operasi | CBC + IV acak per catatan |
| D4 | Judul catatan | Dienkripsi (agar daftar tetap rahasia) |
| D5 | Pengguna | Single-user, tanpa autentikasi |
| D6 | Kunci AES | Di-generate dari passphrase tetap (hardcoded atau config), atau user input passphrase per sesi (simple) |

> **Catatan:** Karena tidak ada auth, kunci AES bisa di-derive dari passphrase sederhana yang dimasukkan user sekali saat buka aplikasi (disimpan di memori frontend), atau pakai kunci tetap untuk demo. Pilih yang paling simpel.

## 5. Kebutuhan Fungsional

### F1 — Buka Aplikasi (Passphrase Sederhana)
- Saat pertama load, minta user input **passphrase** (minimal 8 karakter).
- Passphrase di-derive jadi kunci AES-128 via PBKDF2 (salt tetap, iterasi 100000).
- Kunci disimpan di memori frontend (Pinia store) selama tab terbuka.
- **Acceptance:** Tanpa passphrase benar, tidak bisa akses daftar catatan.

### F2 — Membuat Catatan
- Input: judul dan isi.
- Judul + isi dienkripsi (CBC, IV acak 16 byte) lalu disimpan ke `notes.json`.
- **Acceptance:** File JSON hanya berisi ciphertext + IV (base64); plaintext tidak ada di file.

### F3 — Daftar Catatan
- Menampilkan daftar catatan dengan judul (didekripsi di frontend) dan `updated_at`.
- Isi catatan tidak ditampilkan di daftar.
- **Acceptance:** Diurutkan dari yang terbaru.

### F4 — Membuka Catatan (Dekripsi)
- Ciphertext diambil, didekripsi dengan kunci di memori, ditampilkan.
- **Acceptance:** Isi yang tampil sama persis dengan yang disimpan.

### F5 — Mengedit Catatan
- Isi baru dienkripsi ulang dengan **IV baru**.
- **Acceptance:** `updated_at` berubah; IV berbeda dari sebelumnya.

### F6 — Menghapus Catatan
- Dengan dialog konfirmasi.
- **Acceptance:** Data terhapus dari JSON dan hilang dari daftar.

### F7 — Log Matriks Hexadecimal (Blok Pertama)
- Menampilkan 16 byte pertama plaintext sebagai matriks 4×4 hex (column-major).
- Menampilkan state setelah tiap tahap per ronde: AddRoundKey awal, SubBytes, ShiftRows, MixColumns, AddRoundKey untuk ronde 1–9, ronde 10 tanpa MixColumns.
- **Acceptance:** Output ronde akhir = 16 byte pertama ciphertext (ECB) dari `pycryptodome` untuk kunci & plaintext sama.

### F8 — Visualisasi Round Keys (Key Expansion)
- Menampilkan 11 round key (masing-masing matriks 4×4 hex).
- Menandai word yang melewati `RotWord`, `SubWord`, `Rcon`.
- **Acceptance:** Untuk kunci FIPS-197 `2b7e151628aed2a6abf7158809cf4f3c`, round key 1 = `a0fafe1788542cb123a339392a6c7605`.

## 6. Kebutuhan Non-Fungsional

| ID | Kebutuhan |
|---|---|
| NF1 | Kunci AES tidak pernah ditulis ke file JSON, log, atau disk. |
| NF2 | Buka/simpan catatan ≤ 10 KB selesai < 1 detik. |
| NF3 | UI responsif (desktop & mobile browser). |
| NF4 | Kode modular, diberi komentar, tanpa abstraksi berlebihan. |

## 7. Rancangan Kriptografi

- **Turunan kunci:** `PBKDF2-HMAC-SHA256(passphrase, salt_tetap, iterasi=100000, panjang=16)` → kunci AES-128.
- **Enkripsi:** AES-128 CBC, IV acak 16 byte per catatan, padding PKCS#7.
- **Penyimpanan:** ciphertext dan IV dalam base64 di JSON.
- **Modul AES manual** mengekspos fungsi:
  - `key_expansion(key) -> list[round_key]`
  - `encrypt_block(block, round_keys, trace=False) -> ciphertext, trace`
  - `decrypt_block(block, round_keys) -> plaintext`
  - `sub_bytes`, `shift_rows`, `mix_columns`, `add_round_key`, kebalikannya
- Pengujian silang dengan `pycryptodome` + test vector FIPS-197 wajib lulus.

## 8. Arsitektur

```
Vue.js (UI, passphrase input, Pinia store)  <->  FastAPI (REST)  <->  data/notes.json (file)
                                  |
                                  +-- aes.py, kdf.py, modes.py
```

### Struktur Folder

```
secretnotes-simple/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI init, CORS
│   │   ├── config.py          # baca .env (opsional, untuk salt)
│   │   ├── crypto/
│   │   │   ├── aes.py         # AES manual + trace
│   │   │   ├── kdf.py         # PBKDF2
│   │   │   └── modes.py       # CBC + padding PKCS#7
│   │   ├── storage.py         # baca/tulis notes.json
│   │   ├── schemas.py         # model Pydantic
│   │   └── routes/
│   │       └── notes.py       # CRUD + aes-log + round-keys
│   ├── tests/
│   │   ├── test_aes.py
│   │   └── test_notes.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── main.js
    │   ├── router/index.js
    │   ├── stores/            # crypto.js (key + passphrase), notes.js
    │   ├── api/client.js      # wrapper fetch
    │   ├── views/             # PassphraseView, NotesView, NoteEditorView, AesLabView
    │   └── components/        # HexMatrix.vue, RoundKeys.vue, NoteList.vue
    └── package.json
```

## 9. Skema Data (notes.json)

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

File dibuat otomatis saat pertama kali menyimpan catatan.

## 10. Spesifikasi API

Tidak ada autentikasi. Semua endpoint terbuka (single-user lokal).

| Method | Endpoint | Body | Respons |
|---|---|---|---|
| GET | `/notes` | - | `[{id, title, updated_at}]` (judul didekripsi backend pakai key dari header) |
| POST | `/notes` | `{title, body}` | `{id}` |
| GET | `/notes/{id}` | - | `{id, title, body, created_at, updated_at}` (didekripsi) |
| PUT | `/notes/{id}` | `{title, body}` | 200 |
| DELETE | `/notes/{id}` | - | 204 |
| GET | `/notes/{id}/aes-log` | - | matriks input blok pertama + trace per ronde (hex) |
| GET | `/notes/{id}/round-keys` | - | `{round_keys: [11 x matriks 4x4 hex]}` + info RotWord/SubWord/Rcon |

**Header wajib:** `X-AES-Key: <base64_32_chars>` (kunci AES 16 byte base64, dikirim frontend dari Pinia store).

Format error: `{"detail": "pesan"}` dengan kode HTTP sesuai.

## 11. Layar Antarmuka

1. **PassphraseView** — input passphrase, tombol "Buka", validasi minimal 8 char.
2. **NotesView** — daftar catatan, tombol "Catatan Baru".
3. **NoteEditorView** — input judul dan isi, tombol simpan/hapus.
4. **AesLabView** — tab "Blok Pertama" (matriks hex per ronde) dan tab "Round Keys" (11 matriks).

## 12. Milestone dan Urutan Pengerjaan

| Tahap | Isi | Selesai bila |
|---|---|---|
| 1 | Modul AES manual + key expansion + trace | `test_aes.py` lulus (FIPS-197 + banding pycryptodome) |
| 2 | KDF, mode CBC + padding | Enkripsi-dekripsi bolak-balik benar |
| 3 | Backend: CRUD notes + JSON storage + aes-log/round-keys endpoints | Semua endpoint F2–F8 berfungsi |
| 4 | Frontend: PassphraseView, daftar, editor, kirim key via header | F1–F6 berjalan end-to-end |
| 5 | Frontend: AesLabView | Visualisasi sesuai backend |
| 6 | Pengujian akhir & dokumentasi | Semua acceptance criteria lulus |

## 13. Kriteria Keberhasilan Keseluruhan

- [ ] Isi `notes.json` tidak bisa dibaca tanpa passphrase (ciphertext only).
- [ ] Hasil AES manual identik dengan `pycryptodome` dan test vector FIPS-197.
- [ ] Matriks hex dan 11 round key tampil benar.
- [ ] Tidak ada kunci, passphrase, atau plaintext catatan di file JSON maupun log.

## 14. Catatan Implementasi

- **Passphrase handling:** Frontend derive key via PBKDF2 (bisa pakai `crypto.subtle` di browser atau minta backend derive via endpoint terpisah). Paling simpel: frontend kirim passphrase ke backend `/crypto/derive`, backend return key base64, frontend simpan di Pinia.
- **Salt:** Bisa hardcoded di `.env` (contoh: `SALT_BASE64=...`) atau generate sekali saat setup pertama.
- **CORS:** Allow localhost:5173 (Vite default).
- **File JSON locking:** Untuk simpel, pakai `filelock` atau `portalocker` di backend saat baca/tulis `notes.json` agar aman concurrent request.

## 15. Instruksi untuk AI Agent

- Kerjakan berurutan sesuai bagian 12; jangan lompat tahap.
- Utamakan kode sederhana dan mudah dibaca, dengan komentar singkat pada langkah-langkah AES.
- Jangan menambah fitur di luar bagian 5.
- Jangan menyimpan passphrase, kunci AES, atau plaintext catatan di file JSON maupun log.