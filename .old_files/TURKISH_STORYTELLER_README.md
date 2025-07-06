# Turkish StorytellerPi - Türkçe Hikaye Asistanı

## 🎭 Genel Bakış

Turkish StorytellerPi, 5 yaşındaki küçük bir prenses için özel olarak tasarlanmış Türkçe hikaye anlatma asistanıdır. Pi Zero 2W için optimize edilmiş bu sistem, tüm ağır işlemleri uzak API'ler aracılığıyla gerçekleştirerek yerel kaynak kullanımını minimum seviyede tutar.

## 🌟 Özellikler

### 🎯 Çocuk Dostu Özellikler
- **Yaş grubu**: 5 yaşındaki kız çocuğu
- **Güvenli içerik**: Korkunç, üzücü içerikler filtrelenir
- **Eğitici hikayeler**: Her hikayenin sonunda güzel bir mesaj
- **Kısa hikayeler**: 2-3 dakika süren, anlaşılır hikayeler
- **Çocuksu dil**: Yaş grubuna uygun kelimeler ve cümleler

### 📚 Hikaye Türleri
- 👑 **Prenses hikayeleri**: Güzel prenseslerin maceraları
- 🧚‍♀️ **Peri masalları**: Büyülü periler ve sihirli dünyalar
- 💖 **Dostluk hikayeleri**: Arkadaşlık ve paylaşım hikayeleri
- 🌍 **Macera hikayeleri**: Güvenli ve eğlenceli maceralar
- 🐰 **Hayvan hikayeleri**: Sevimli hayvan karakterleri
- 🌈 **Doğa hikayeleri**: Çiçekler, ağaçlar ve doğa

### 🎤 Ses Özellikleri
- **Türkçe konuşma tanıma**: Google Cloud Speech API
- **Yüksek kaliteli Türkçe ses**: ElevenLabs API
- **Uyandırma kelimesi**: "Merhaba Asistan" (Porcupine)
- **Çocuk dostu kadın ses**: Hikaye anlatımı için optimize edilmiş

### 🚀 Teknik Özellikler
- **Pi Zero 2W optimizasyonu**: Minimum kaynak kullanımı
- **Uzak işleme**: Tüm ağır işlemler API'lerde
- **Türkçe web arayüzü**: Kolay yönetim paneli
- **Otomatik servis yönetimi**: Systemd integration
- **Kapsamlı loglama**: Türkçe log mesajları

## 🏗️ Sistem Mimarisi

### 📦 Ana Bileşenler
1. **storyteller_llm_turkish.py**: OpenAI GPT-4 ile Türkçe hikaye üretimi
2. **stt_service_turkish.py**: Google Cloud ile Türkçe konuşma tanıma
3. **tts_service_turkish.py**: ElevenLabs ile Türkçe ses sentezi
4. **wake_word_detector.py**: Porcupine ile uyandırma kelimesi
5. **web_interface.py**: Türkçe web yönetim paneli

### 🔗 API Entegrasyonları
- **OpenAI GPT-4**: Hikaye üretimi
- **ElevenLabs**: Ses sentezi
- **Google Cloud Speech**: Konuşma tanıma
- **Porcupine**: Uyandırma kelimesi (yerel)

## 📋 Kurulum Adımları

### 1. 📦 Sistem Gereksinimları
```bash
# Raspberry Pi Zero 2W veya Pi 5
# DietPi veya Raspberry Pi OS
# Python 3.8+
# Internet bağlantısı (API'ler için)
```

### 2. 🚀 Otomatik Kurulum
```bash
# Türkçe StorytellerPi kurulum scripti
python3 setup_complete_turkish.py

# Kurulum tamamlandıktan sonra
chmod +x start_turkish_storyteller.sh
```

### 3. 🔑 API Anahtarları Konfigürasyonu
```bash
# .env dosyasını düzenleyin
nano .env

# Gerekli API anahtarlarını girin:
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ELEVENLABS_VOICE_ID=your_turkish_voice_id_here
PORCUPINE_ACCESS_KEY=your_porcupine_key_here
```

### 4. 📄 Google Credentials
```bash
# Google Cloud credentials JSON dosyasını yükleyin
cp your-google-credentials.json credentials/google-credentials.json
chmod 600 credentials/google-credentials.json
```

### 5. 🎵 Türkçe Ses Seçimi
1. ElevenLabs Voice Library'ye gidin
2. Türkçe destekli kadın ses seçin
3. Hikaye anlatımı için uygun ses bulun
4. Ses ID'sini .env dosyasına ekleyin

## 🎮 Kullanım Kılavuzu

### 🚀 Sistemi Başlatma
```bash
# Manuel başlatma
./start_turkish_storyteller.sh

# Systemd servisi olarak
sudo systemctl start storytellerpi-turkish
sudo systemctl enable storytellerpi-turkish
```

### 🌐 Web Arayüzü
```
http://pi_ip_address:5000
```

Web arayüzü özellikleri:
- 📊 Sistem durumu izleme
- 🎤 Ses testi araçları
- 🔧 Servis yönetimi
- 📈 Performans izleme
- 🎭 Hikaye tema seçimi

### 🎤 Ses Komutları
1. **Uyandırma**: "Merhaba Asistan"
2. **Hikaye isteği**: "Bana bir prenses hikayesi anlat"
3. **Tema seçimi**: "Peri masalı istiyorum"
4. **Devam**: "Hikayeyi devam ettir"

## 🎯 Hikaye Örnekleri

### 👑 Prenses Hikayesi
```
"Bir zamanlar, çok uzak diyarlarda güzel bir prenses yaşarmış. 
Bu prenses çok iyi kalpli ve sevecendi. Bir gün..."
```

### 🧚‍♀️ Peri Masalı
```
"Büyülü bir ormanda, rengarenk kanatları olan güzel bir peri varmış. 
Bu peri her gün çiçeklere bakarmış ve onlara güzel şarkılar söylermiş..."
```

### 💖 Dostluk Hikayesi
```
"Küçük bir tavşan ile sevimli bir sincap çok iyi arkadaşlarmış. 
Her gün birlikte oynarlarmış ve hiçbir zaman kavga etmezlermiş..."
```

## 🔧 Yapılandırma

### 📝 Ana Konfigürasyon (.env)
```bash
# Çocuk Profili
CHILD_NAME=Küçük Prenses
CHILD_AGE=5
CHILD_GENDER=kız

# Hikaye Ayarları
STORY_THEMES=prenses,peri,dostluk,macera,hayvanlar
STORY_LENGTH=short
STORY_TONE=gentle_enthusiastic
STORY_INCLUDE_MORAL=true
STORY_AVOID_SCARY=true

# Performans (Pi Zero 2W)
OPTIMIZE_FOR_PI_ZERO=true
MEMORY_LIMIT=300
CPU_LIMIT=80
USE_LOCAL_MODELS=false
```

### 🎛️ Ses Ayarları
```bash
# TTS Ayarları
TTS_VOICE_STABILITY=0.8
TTS_VOICE_SIMILARITY_BOOST=0.7
TTS_VOICE_STYLE=storyteller

# STT Ayarları
STT_LANGUAGE_CODE=tr-TR
STT_TIMEOUT=10.0
STT_MAX_AUDIO_LENGTH=30.0
```

## 🏥 Sistem Monitörü

### 📊 Durum Kontrolü
```bash
# Servis durumu
systemctl status storytellerpi-turkish

# Logları izleme
tail -f logs/storyteller_turkish.log

# Sistem kaynaklarını izleme
htop
```

### 🔍 Sorun Giderme
```bash
# API bağlantı testleri
python3 main/storyteller_llm_turkish.py
python3 main/stt_service_turkish.py
python3 main/tts_service_turkish.py

# Ses sistemi testi
python3 tests/test_audio_system.py

# Konfigürasyon doğrulama
python3 main/config_validator.py
```

## 💰 Maliyet Analizi

### 📈 Günlük Kullanım (30 hikaye)
- **OpenAI GPT-4**: ~$1.50
- **ElevenLabs TTS**: ~$0.90
- **Google Speech**: ~$0.50
- **Porcupine**: Ücretsiz
- **Toplam**: ~$2.90/gün

### 📊 Aylık Bütçe
- **Normal kullanım**: ~$87/ay
- **Yoğun kullanım**: ~$130/ay
- **Haftalık kullanım**: ~$20/hafta

## 🔒 Güvenlik ve Gizlilik

### 🛡️ Güvenlik Önlemleri
- API anahtarları şifrelenir
- Çocuk dostu içerik filtresi
- Yerel işleme minimum seviyede
- Güvenli bağlantılar (HTTPS)

### 🕵️ Gizlilik Koruması
- Ses verisi geçici olarak saklanır
- Kişisel bilgiler şifrelenir
- Üçüncü taraf paylaşım yok
- GDPR uyumlu

## 🚨 Sorun Giderme

### ❌ Yaygın Sorunlar

#### 1. API Anahtarı Hatası
```
Hata: Invalid API key
Çözüm: API anahtarını .env dosyasında kontrol edin
```

#### 2. Ses Bulunamadı
```
Hata: No audio devices found
Çözüm: setup_hardware_audio.py scriptini çalıştırın
```

#### 3. Türkçe Karakterler
```
Hata: Encoding error
Çözüm: Sistem locale'ini tr_TR.UTF-8 yapın
```

#### 4. Bellek Yetersizliği
```
Hata: Memory allocation failed
Çözüm: MEMORY_LIMIT değerini düşürün
```

### 🔧 Hızlı Çözümler
```bash
# Servisi yeniden başlat
sudo systemctl restart storytellerpi-turkish

# Konfigürasyonu yeniden yükle
sudo systemctl reload storytellerpi-turkish

# Sistem kaynaklarını temizle
sudo systemctl clean storytellerpi-turkish
```

## 📚 Geliştirme

### 🛠️ Özelleştirme
```python
# Yeni hikaye teması ekleme
STORY_THEMES = "prenses,peri,dostluk,macera,hayvanlar,uzay"

# Çocuk profili değiştirme
CHILD_NAME = "Prenses Elif"
CHILD_AGE = 6
```

### 🎯 Test Etme
```bash
# Birim testleri
python3 -m pytest tests/

# Entegrasyon testleri
python3 tests/test_integration.py

# Performans testleri
python3 tests/test_performance.py
```

## 📞 Destek

### 🆘 Yardım Kaynakları
- **Log dosyaları**: `logs/storyteller_turkish.log`
- **API dokümantasyonu**: Her API provider'ın dokümanları
- **Sistem durumu**: Web arayüzü `/status` endpoint
- **Sağlık kontrolü**: `http://pi_ip:5000/health`

### 📧 İletişim
- Sistem loglarını kontrol edin
- API provider'ların destek sayfalarını ziyaret edin
- Konfigürasyon dosyalarını doğrulayın

## 🎉 Başarılı Kurulum Kontrolü

Kurulum başarılı olduğunda:
1. ✅ Web arayüzü açılır: `http://pi_ip:5000`
2. ✅ "Merhaba Asistan" komutu çalışır
3. ✅ Türkçe hikaye anlatır
4. ✅ Ses kalitesi yüksek
5. ✅ Çocuk dostu içerik filtresi aktif

## 🎭 Sonuç

Turkish StorytellerPi, 5 yaşındaki küçük prensesiniz için özel olarak tasarlanmış, güvenli ve eğlenceli bir hikaye anlatma asistanıdır. Pi Zero 2W'da sorunsuz çalışacak şekilde optimize edilmiş, tüm ağır işlemler uzak API'lerde gerçekleştirilir.

**Artık küçük prensesiniz Türkçe hikayelerle dolu büyülü bir dünyaya adım atabilir!** 👑✨

---

*"Bir zamanlar, çok uzak diyarlarda teknoloji ile masalların buluştuğu güzel bir yer varmış..."* 🎭📚