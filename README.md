# Flask Menu User

Aplikasi Flask sederhana dengan fitur:
- Login/logout
- User management
- Group management
- modul Products
- Blueprint-based application structure

## Struktur project
- `app.py` — entry point aplikasi
- `helpers.py` — helper database dan autentikasi
- `modules/` — blueprint modules (`auth`, `settings`, `products`)
- `templates/` — HTML templates
- `static/` — file statis seperti CSS

## Persiapan lokal
1. Clone repository
2. Buat virtual environment:
   - `python -m venv .venv`
3. Aktifkan virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/macOS: `source .venv/bin/activate`
4. Install dependency:
   - `pip install -r requirements.txt`
5. Jalankan aplikasi:
   - `python app.py`

## Variabel lingkungan
File `.env.example` sudah disiapkan. Anda dapat menyalin menjadi `.env` jika ingin memakai environment variables.

## Default user
- Username: `admin`
- Password: `rahasia`

## Catatan GitHub
Project ini sudah dilengkapi dengan:
- `.gitignore`
- `requirements.txt`
- `.env.example`
- README dokumentasi

Dengan file-file dasar ini, project siap diupload ke GitHub dan dikloning ulang di komputer lain.
