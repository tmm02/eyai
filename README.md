# Discord AI Chatbot dengan Gemini API

Bot ini dibuat untuk dua mode pemakaian:

1. **Channel AI khusus**: semua pesan di channel yang Anda daftarkan akan dianggap obrolan ke AI.
2. **Channel lain**: bot hanya merespons jika di-mention atau jika pesan merupakan reply ke balasan bot.

## Rekomendasi model

Default konfigurasi proyek ini memakai:

- `gemini-3.8-flash`

Alasannya:

- kualitas gratisnya sangat bagus untuk chatbot komunitas
- latency tetap cepat untuk percakapan Discord
- punya free tier resmi sehingga enak untuk mulai

Kalau model yang Anda pakai tidak tersedia saat itu, coba `gemini-3.8-flash` atau `gemini-3.8-flash-lite`; untuk starting point saya sarankan `gemini-3.8-flash`.

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
   - `GEMINI_API_KEY`: API key Gemini dari Google AI Studio
   - `GEMINI_MODEL`: model Gemini, default `gemini-3.8-flash`
   - `GEMINI_BASE_URL`: default `https://generativelanguage.googleapis.com/v1beta`
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

- Implementasi ini memakai REST API Gemini langsung, jadi cukup isi API key Gemini Anda di `.env`.
- Kalau nanti Anda ingin model yang lebih hemat, ganti `GEMINI_MODEL` menjadi `gemini-3.8-flash-lite` atau model yang tersedia di Google AI Studio Anda.
