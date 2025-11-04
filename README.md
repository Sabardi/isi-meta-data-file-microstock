## Metadata Applier

Script untuk mengisi metadata (Title, Keywords) ke file media berdasarkan CSV menggunakan exiftool.

### Isi repository
- `metadata_applier.py` — skrip utama
- `run_metadata_applier.bat` — cara cepat di Windows (prompt folder path, auto-detect CSV)
- `requirements.txt` — tidak ada dependensi Python eksternal

### Persyaratan
- **Python** 3.8+
- **ExifTool** terpasang (di PATH) atau sediakan `exiftool.exe`

Install ExifTool (pilih salah satu):
- Winget:
  - `winget install --id=PhilHarvey.ExifTool -e --accept-package-agreements --accept-source-agreements`
- Chocolatey:
  - `choco install exiftool -y`
- Manual:
  - Unduh dari situs Phil Harvey, simpan sebagai `exiftool.exe` dan taruh di folder yang sama dengan `.bat`/skrip atau tambahkan ke PATH

### Format CSV
Kolom wajib: `Filename, Title, Keywords`

Contoh:
```
Filename,Title,Keywords
video1.mp4,Judul Satu,"tag1, tag2"
foto_a.jpg,Judul Dua,"wisata; pantai"
```

Catatan: pemisah default koma, titik-koma juga didukung untuk Keywords.

### Cara pakai (Windows)
1. Klik dua kali `run_metadata_applier.bat` atau jalankan dari PowerShell
2. Masukkan path folder yang berisi file media dan CSV Anda
3. Pilih DRY-RUN untuk uji coba terlebih dahulu (disarankan)

Batch akan menjalankan:
- `metadata_applier.py --dir <folder>`
- Skrip akan otomatis mendeteksi `.csv` di folder tersebut. Prioritas: `metadata.csv`, `meta.csv`, `tags.csv`, lalu `.csv` pertama yang ditemukan.
- Anda juga bisa menaruh `exiftool.exe` di folder yang sama agar otomatis dipakai.

### Cara pakai (PowerShell manual)
```
python metadata_applier.py --dir "C:\path\to\folder"
```
Atau tentukan CSV:
```
python metadata_applier.py --dir "C:\path\to\folder" --csv "metadata.csv"
```

Mode simulasi (tidak menulis metadata):
```
python metadata_applier.py --dir "C:\path\to\folder" --dry-run
```

### Publikasi ke GitHub
Commit semua file ini:
- `metadata_applier.py`
- `run_metadata_applier.bat`
- `README.md`
- `requirements.txt`

Tambahkan instruksi singkat pada repo: instal Python 3.8+, instal ExifTool (winget/choco/manual), lalu jalankan `.bat`.


