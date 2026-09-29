# Discord AI Chatbot dengan GitHub Copilot

Bot ini dibuat untuk dua mode pemakaian:

1. **Channel AI khusus**: semua pesan di channel yang Anda daftarkan akan dianggap obrolan ke AI.
2. **Channel lain**: bot hanya merespons jika di-mention atau jika pesan merupakan reply ke balasan bot.

## Rekomendasi model

Default konfigurasi proyek ini memakai:

- `claude-haiku-4.5`

Alasannya:

- ringan dan cepat untuk percakapan Discord
- umumnya lebih hemat dibanding model besar
- kualitas jawabannya sudah cukup bagus untuk chatbot komunitas

Kalau nanti Anda ingin sedikit lebih "rapi" untuk instruksi panjang, Anda bisa coba `gpt-5-mini`, tetapi untuk starting point saya sarankan tetap `claude-haiku-4.5`.

## Setup

1. Install dependency:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy env:

   ```bash
   cp .env.example .env
   ```

3. Isi `.env`:

   - `DISCORD_BOT_TOKEN`: token bot Discord
   - `GITHUB_COPILOT_TOKEN`: token Copilot yang akan Anda pakai
   - `COPILOT_MODEL`: model Copilot, default `claude-haiku-4.5`
   - `COPILOT_BASE_URL`: default `https://api.githubcopilot.com`
   - `AI_CHANNEL_IDS`: daftar channel ID Discord yang akan menjadi channel AI

4. Jalankan:

   ```bash
   python main.py
   ```

## Perilaku bot

- Di channel AI, semua pesan user akan diteruskan ke model.
- Di channel biasa, mention bot atau reply ke pesan bot untuk melanjutkan percakapan.
- Riwayat percakapan disimpan di memori:
  - per-channel untuk channel AI
  - per-user per-channel untuk channel biasa

## Catatan penting

- Implementasi ini disusun untuk memakai endpoint chat completion yang kompatibel dengan konfigurasi Copilot Anda.
- Jika akun atau endpoint Copilot Anda memakai format autentikasi yang berbeda, sesuaikan `GITHUB_COPILOT_TOKEN` atau `COPILOT_BASE_URL`.
