# StorytellerPi - Tam Kurulum ve Kullanım Kılavuzu

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Donanım Gereksinimleri](#donanım-gereksinimleri)
3. [Kurulum](#kurulum)
4. [Konfigürasyon](#konfigürasyon)
5. [API Anahtarları](#api-anahtarları)
6. [Servis Yönetimi](#servis-yönetimi)
7. [Ses Kurulumu](#ses-kurulumu)
8. [Web Arayüzü](#web-arayüzü)
9. [Türkçe Dil Desteği](#türkçe-dil-desteği)
10. [Sorun Giderme](#sorun-giderme)
11. [Geliştirme](#geliştirme)
12. [Sık Sorulan Sorular](#sık-sorulan-sorular)

---

## Genel Bakış

StorytellerPi, 5 yaşındaki çocuklar için özel olarak tasarlanmış yapay zeka destekli hikaye anlatma sistemidir. Sistem, sesli komutları anlayarak çocuğun istediği konularda güvenli, eğitici ve yaş grubuna uygun hikayeler anlatır.

### Özellikler

- **Türkçe ve İngilizce dil desteği**
- **Yapay zeka destekli hikaye üretimi** (OpenAI GPT-4, Google Gemini)
- **Gerçek zamanlı ses tanıma** (Google Cloud Speech)
- **Doğal ses sentezi** (ElevenLabs, Pyttsx3)
- **Uyandırma kelimesi tespiti** (OpenWakeWord)
- **Web tabanlı yönetim arayüzü**
- **Donanım optimizasyonu** (Pi Zero 2W, Pi 4/5)
- **Çocuk güvenliği** (İçerik filtreleme, yaş uygunluğu)

### Desteklenen Donanım

- **Raspberry Pi Zero 2W** + IQAudio Codec Zero HAT
- **Raspberry Pi 4/5** + Waveshare USB Audio Dongle
- **DietPi** veya **Raspberry Pi OS**

---

## Donanım Gereksinimleri

### Raspberry Pi Zero 2W Kurulumu

**Gerekli Bileşenler:**
- Raspberry Pi Zero 2W
- IQAudio Codec Zero HAT
- 32GB+ microSD kart
- Güç adaptörü (5V 2.5A)
- Hoparlör (3.5mm jack)
- Mikrofon (HAT'te dahil)

**Ses Kartı Bağlantısı:**
```bash
# IQAudio Codec Zero HAT GPIO pinleri
GPIO 2  (SDA) -> HAT SDA
GPIO 3  (SCL) -> HAT SCL
GPIO 18 (PCM CLK) -> HAT BCLK
GPIO 19 (PCM FS) -> HAT LRCLK
GPIO 20 (PCM DIN) -> HAT DIN
GPIO 21 (PCM DOUT) -> HAT DOUT
```

### Raspberry Pi 4/5 Kurulumu

**Gerekli Bileşenler:**
- Raspberry Pi 4/5
- Waveshare USB Audio Dongle
- 32GB+ microSD kart
- Güç adaptörü (5V 3A)
- USB hoparlör/mikrofon

**USB Ses Kartı:**
- Waveshare USB Audio Dongle (önerilen)
- Generic USB ses kartları da desteklenir

---

## Kurulum

### Otomatik Kurulum (Önerilen)

**Master Setup Script kullanarak:**

```bash
# Depoyu klonlayın
git clone https://github.com/storytellerpi/storyteller-remote.git
cd storyteller-remote

# Tam kurulum
chmod +x master_setup.sh
./master_setup.sh install

# Türkçe dil desteği ile kurulum
./master_setup.sh install --language tr --child-name "Zeynep" --child-age 5 --child-gender kız
```

**Python Setup Script kullanarak:**

```bash
# Python kurulum scripti
python3 setup_complete.py install

# Seçeneklerle kurulum
python3 setup_complete.py install --language turkish --child-name "Ayşe" --child-age 5 --child-gender kız
```

### Manuel Kurulum

**1. Sistem Güncellemesi:**
```bash
sudo apt update && sudo apt upgrade -y
```

**2. Gerekli Paketler:**
```bash
sudo apt install -y python3 python3-pip python3-venv git curl wget \
    build-essential pkg-config libffi-dev libssl-dev \
    libasound2-dev portaudio19-dev alsa-utils pulseaudio \
    i2c-tools device-tree-compiler
```

**3. Python Sanal Ortam:**
```bash
python3 -m venv /opt/storytellerpi/venv
source /opt/storytellerpi/venv/bin/activate
pip install --upgrade pip
```

**4. Python Bağımlılıkları:**
```bash
pip install flask flask-socketio pyaudio numpy pygame
pip install openai google-generativeai elevenlabs
pip install google-cloud-speech openwakeword
pip install python-dotenv psutil systemd-python
```

### Kurulum Doğrulaması

**Sistem Tanılaması:**
```bash
# Master script ile
./master_setup.sh diagnostics

# Python script ile
python3 setup_complete.py diagnostics
```

---

## Konfigürasyon

### Environment Dosyası (.env)

Kurulum sonrası `/opt/storytellerpi/.env` dosyasını düzenleyin:

```env
# Sistem Konfigürasyonu
SYSTEM_LANGUAGE=tr-TR
STORY_LANGUAGE=turkish
PI_MODEL=pi_zero_2w
AUDIO_SETUP_TYPE=iqaudio_dietpi

# Çocuk Konfigürasyonu
CHILD_NAME=Küçük Prenses
CHILD_AGE=5
CHILD_GENDER=kız
STORY_TARGET_AUDIENCE=5_year_old_kız

# Ses Konfigürasyonu
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_DEVICE_INDEX=0

# Uyandırma Kelimesi
WAKE_WORD_MODEL=hey_elsa
WAKE_WORD_THRESHOLD=0.7
WAKE_WORD_SENSITIVITY=0.5

# STT Konfigürasyonu
STT_SERVICE=google
STT_LANGUAGE_CODE=tr-TR
STT_TIMEOUT=10.0

# LLM Konfigürasyonu
LLM_SERVICE=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.8
LLM_MAX_TOKENS=800

# TTS Konfigürasyonu
TTS_SERVICE=elevenlabs
TTS_LANGUAGE=tr
TTS_VOICE_GENDER=female
TTS_VOICE_STYLE=storyteller

# Hikaye Konfigürasyonu
STORY_THEMES=prenses,peri,dostluk,macera,hayvanlar
STORY_TONE=gentle_enthusiastic
STORY_INCLUDE_MORAL=true
STORY_AVOID_SCARY=true
STORY_CONTENT_FILTER=very_strict

# Web Arayüz
WEB_HOST=0.0.0.0
WEB_PORT=5000
```

### Donanım Spesifik Konfigürasyon

**Pi Zero 2W + IQAudio Codec:**
```env
PI_MODEL=pi_zero_2w
PI_AUDIO_DEVICE=iqaudio_codec
AUDIO_SETUP_TYPE=iqaudio_dietpi  # veya iqaudio_raspios
```

**Pi 4/5 + Waveshare USB:**
```env
PI_MODEL=pi_5
PI_AUDIO_DEVICE=waveshare_usb
AUDIO_SETUP_TYPE=waveshare_dietpi  # veya waveshare_raspios
```

---

## API Anahtarları

### Gerekli API Anahtarları

**1. OpenAI API Key:**
- https://platform.openai.com/api-keys adresinden alın
- Aylık kullanım limiti: ~$10-20
- GPT-4 erişimi gerekli

**2. ElevenLabs API Key:**
- https://elevenlabs.io/ adresinden alın
- Aylık karakter limiti: 10,000 (ücretsiz)
- Türkçe ses desteği mevcut

**3. Google Cloud Speech API:**
- Google Cloud Console'dan proje oluşturun
- Speech-to-Text API'yi etkinleştirin
- Service account oluşturun ve JSON anahtarını indirin

### API Anahtarlarını Yapılandırma

**1. OpenAI ve ElevenLabs:**
```bash
# .env dosyasını düzenleyin
nano /opt/storytellerpi/.env

# Anahtarları ekleyin
OPENAI_API_KEY=sk-your-actual-openai-key
ELEVENLABS_API_KEY=your-actual-elevenlabs-key
```

**2. Google Cloud Speech:**
```bash
# Credentials dosyasını yükleyin
cp your-google-credentials.json /opt/storytellerpi/credentials/google-credentials.json

# Dosya yolunu ayarlayın
export GOOGLE_APPLICATION_CREDENTIALS=/opt/storytellerpi/credentials/google-credentials.json
```

### API Kullanım Limitleri

**OpenAI:**
- GPT-4: $0.03/1K tokens (giriş), $0.06/1K tokens (çıkış)
- Günlük ortalama: ~100 hikaye ($5-10)

**ElevenLabs:**
- Ücretsiz: 10,000 karakter/ay
- Ücretli: $5/ay (30,000 karakter)

**Google Cloud Speech:**
- İlk 60 dakika ücretsiz/ay
- Sonrası: $0.006/15 saniye

---

## Servis Yönetimi

### Systemd Servisi

**Servis Durumu:**
```bash
sudo systemctl status storytellerpi
```

**Servis Başlatma:**
```bash
sudo systemctl start storytellerpi
sudo systemctl enable storytellerpi  # Otomatik başlatma
```

**Servis Durdurma:**
```bash
sudo systemctl stop storytellerpi
sudo systemctl disable storytellerpi  # Otomatik başlatmayı devre dışı bırak
```

**Servis Yeniden Başlatma:**
```bash
sudo systemctl restart storytellerpi
```

### Log Takibi

**Canlı Log İzleme:**
```bash
sudo journalctl -u storytellerpi -f
```

**Son 50 Log:**
```bash
sudo journalctl -u storytellerpi -n 50
```

**Hata Logları:**
```bash
sudo journalctl -u storytellerpi -p err
```

### Manuel Başlatma

**Ana Uygulama:**
```bash
cd /opt/storytellerpi
source venv/bin/activate
python main/storyteller_main.py
```

**Sadece Web Arayüzü:**
```bash
cd /opt/storytellerpi
source venv/bin/activate
python main/web_interface.py
```

---

## Ses Kurulumu

### IQAudio Codec Zero HAT (Pi Zero 2W)

**Boot Konfigürasyonu:**
```bash
# /boot/config.txt dosyasına ekleyin
dtoverlay=iqaudio-codec
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=spi=on
```

**ALSA Konfigürasyonu:**
```bash
# /etc/asound.conf
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
```

**Ses Testi:**
```bash
# Ses kartlarını listele
aplay -l

# Test sesi çal
speaker-test -t wav -c 2

# Mikrofon testi
arecord -D hw:0,0 -f cd test.wav
aplay test.wav
```

### Waveshare USB Audio (Pi 4/5)

**USB Ses Kartı Tanıma:**
```bash
# USB cihazlarını listele
lsusb

# Ses kartlarını listele
aplay -l
```

**ALSA Konfigürasyonu:**
```bash
# /etc/asound.conf
pcm.!default {
    type hw
    card 1
    device 0
}

ctl.!default {
    type hw
    card 1
}
```

**Ses Seviyesi Ayarı:**
```bash
# Ses seviyesini ayarla
amixer set Master 80%
amixer set Mic 70%
```

### Ses Problemleri Çözümü

**Problem: Ses kartı bulunamadı**
```bash
# Ses kartlarını kontrol et
aplay -l

# Modülleri yeniden yükle
sudo modprobe snd-usb-audio
sudo modprobe snd-soc-iqaudio-codec
```

**Problem: Mikrofon çalışmıyor**
```bash
# Mikrofon seviyesini kontrol et
amixer get Mic

# Mikrofon sesini aç
amixer set Mic cap
amixer set Mic 70%
```

**Problem: Hoparlör sesi yok**
```bash
# Hoparlör seviyesini kontrol et
amixer get Master

# Hoparlör sesini aç
amixer set Master unmute
amixer set Master 80%
```

---

## Web Arayüzü

### Erişim

**Yerel Erişim:**
```
http://localhost:5000
http://192.168.1.100:5000  # Pi'nin IP adresi
```

**Uzaktan Erişim:**
```
# SSH tüneli ile
ssh -L 5000:localhost:5000 pi@192.168.1.100

# Güvenlik duvarı ayarları
sudo ufw allow 5000
```

### Özellikler

**Ana Sayfa:**
- Sistem durumu
- Servis durumları
- Hızlı başlatma butonları

**Hikaye Yönetimi:**
- Yeni hikaye oluşturma
- Hikaye geçmişi
- Tema seçimi

**Ses Kontrolü:**
- Ses seviyesi ayarı
- Mikrofon testi
- Hoparlör testi

**Ayarlar:**
- Çocuk profili
- Dil ayarları
- API konfigürasyonu

### Web Arayüzü Sorunları

**Problem: HTTP 500 Hatası**
```bash
# Servisi yeniden başlat
sudo systemctl restart storytellerpi

# Logları kontrol et
sudo journalctl -u storytellerpi -f
```

**Problem: Bağlantı kurulamadı**
```bash
# Port durumunu kontrol et
sudo netstat -tlnp | grep 5000

# Güvenlik duvarı ayarları
sudo ufw status
sudo ufw allow 5000
```

**Problem: Ses kontrolü çalışmıyor**
```bash
# Ses sistemi durumunu kontrol et
./master_setup.sh diagnostics

# Ses kartı erişim izinlerini kontrol et
sudo usermod -a -G audio $USER
```

---

## Türkçe Dil Desteği

### Dil Konfigürasyonu

**Tam Türkçe Kurulum:**
```bash
# Master script ile
./master_setup.sh install --language tr --child-name "Zeynep" --child-age 5 --child-gender kız

# Python script ile
python3 setup_complete.py install --language turkish --child-name "Ayşe" --child-age 5 --child-gender kız
```

**Manual Dil Ayarı:**
```env
# .env dosyasında
SYSTEM_LANGUAGE=tr-TR
STORY_LANGUAGE=turkish
STT_LANGUAGE_CODE=tr-TR
TTS_LANGUAGE=tr
CHILD_NAME=Küçük Prenses
CHILD_GENDER=kız
STORY_THEMES=prenses,peri,dostluk,macera,hayvanlar
```

### Türkçe Özellikler

**Hikaye Temaları:**
- Prenses hikayeleri
- Peri masalları
- Dostluk hikayeleri
- Macera hikayeleri
- Hayvan hikayeleri
- Doğa hikayeleri

**Uyandırma Kelimeleri:**
- "Hey Elsa"
- "Merhaba Elsa"
- "Hikaye anlat"

**Ses Komutları:**
- "Hikaye anlat"
- "Prenses hikayesi"
- "Peri masalı"
- "Teşekkür ederim"
- "Dur/Durdur"

### Türkçe Ses Ayarları

**ElevenLabs Türkçe Sesler:**
```env
TTS_LANGUAGE=tr
TTS_VOICE_GENDER=female
TTS_VOICE_STYLE=storyteller
ELEVENLABS_VOICE_ID=turkish-storyteller-voice
```

**Google Cloud Speech Türkçe:**
```env
STT_LANGUAGE_CODE=tr-TR
STT_ALTERNATIVE_LANGUAGE=tr
```

---

## Sorun Giderme

### Genel Sorunlar

**Problem: Servis başlamıyor**
```bash
# Servis durumunu kontrol et
sudo systemctl status storytellerpi

# Logları kontrol et
sudo journalctl -u storytellerpi -n 50

# Konfigürasyonu kontrol et
python3 -c "from main.config_validator import ConfigValidator; cv = ConfigValidator(); cv.validate_all_settings()"
```

**Problem: API anahtarları çalışmıyor**
```bash
# API anahtarlarını test et
cd /opt/storytellerpi
source venv/bin/activate
python3 -c "
import os
from main.storyteller_llm import StorytellerLLM
import asyncio

async def test():
    llm = StorytellerLLM()
    result = await llm.initialize()
    print(f'LLM init: {result}')

asyncio.run(test())
"
```

**Problem: Ses tanıma çalışmıyor**
```bash
# Mikrofon testini çalıştır
arecord -D hw:0,0 -f cd -t wav -d 5 test.wav
aplay test.wav

# Google Cloud credentials kontrol et
ls -la /opt/storytellerpi/credentials/
export GOOGLE_APPLICATION_CREDENTIALS=/opt/storytellerpi/credentials/google-credentials.json
```

### Ses Sorunları

**Problem: "No soundcards found"**
```bash
# Ses kartlarını kontrol et
aplay -l

# Ses modüllerini yeniden yükle
sudo modprobe snd-usb-audio
sudo modprobe snd-soc-iqaudio-codec

# Ses servisi yeniden başlat
sudo systemctl restart alsa-state
```

**Problem: Mikrofon çalışmıyor**
```bash
# Mikrofon seviyesini kontrol et
amixer get Mic

# Mikrofon testini çalıştır
arecord -D hw:0,0 -f cd -t wav -d 5 mic_test.wav
aplay mic_test.wav
```

### Ağ Sorunları

**Problem: API'lere erişilemiyor**
```bash
# İnternet bağlantısını kontrol et
ping google.com

# DNS çözümleme kontrol et
nslookup api.openai.com
nslookup api.elevenlabs.io

# Güvenlik duvarı kontrol et
sudo ufw status
```

### Bellek Sorunları

**Problem: Bellek yetersiz**
```bash
# Bellek kullanımını kontrol et
free -h
df -h

# Swap dosyası oluştur
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Tam Sistem Sıfırlama

**Kurulumu tamamen temizle:**
```bash
# Servisi durdur
sudo systemctl stop storytellerpi
sudo systemctl disable storytellerpi

# Dosyaları temizle
sudo rm -rf /opt/storytellerpi
sudo rm -f /etc/systemd/system/storytellerpi.service
sudo systemctl daemon-reload

# Yeniden kurulum
git clone https://github.com/storytellerpi/storyteller-remote.git
cd storyteller-remote
./master_setup.sh install
```

---

## Geliştirme

### Geliştirme Ortamı

**Kaynak Kodunu Klonla:**
```bash
git clone https://github.com/storytellerpi/storyteller-remote.git
cd storyteller-remote
```

**Geliştirme Ortamını Hazırla:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest black flake8
```

### Test Çalıştırma

**Tüm Testler:**
```bash
cd /opt/storytellerpi
source venv/bin/activate
python -m pytest tests/ -v
```

**Spesifik Test:**
```bash
python -m pytest tests/test_storyteller_llm.py -v
python -m pytest tests/test_integration.py -v
```

**Manuel Test:**
```bash
# STT servis testi
python main/stt_service.py

# TTS servis testi
python main/tts_service.py

# LLM servis testi
python main/storyteller_llm.py
```

### Kod Formatı

**Kod Formatlamak:**
```bash
black main/ tests/
flake8 main/ tests/
```

**Tip Kontrolü:**
```bash
mypy main/
```

### Yeni Özellik Ekleme

**1. Yeni Servis Oluşturma:**
```python
# main/new_service.py
class NewService:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        # Servis başlatma
        pass
    
    async def cleanup(self):
        # Temizlik
        pass
```

**2. Servis Manager'a Ekleme:**
```python
# main/service_manager.py
from .new_service import NewService

class ServiceManager:
    def __init__(self):
        self.new_service = NewService()
    
    async def initialize_services(self):
        await self.new_service.initialize()
```

**3. Test Yazma:**
```python
# tests/test_new_service.py
import pytest
from main.new_service import NewService

@pytest.mark.asyncio
async def test_new_service():
    service = NewService()
    result = await service.initialize()
    assert result == True
```

---

## Sık Sorulan Sorular

### Genel Sorular

**S: Hangi Raspberry Pi modellerini destekliyor?**
C: Pi Zero 2W, Pi 4, Pi 5 modellerini destekler. Pi Zero 2W için IQAudio Codec Zero HAT, Pi 4/5 için Waveshare USB Audio Dongle önerilir.

**S: İnternet bağlantısı olmadan çalışır mı?**
C: Hayır, sistem OpenAI, ElevenLabs ve Google Cloud API'lerini kullandığı için internet bağlantısı gerekir.

**S: Hangi yaş grubuna uygun?**
C: 3-8 yaş arası çocuklar için optimize edilmiştir. Özellikle 5 yaş civarı çocuklar için tasarlanmıştır.

**S: Türkçe dışında hangi dilleri destekler?**
C: Şu anda Türkçe ve İngilizce desteklenir. Diğer diller için konfigürasyon dosyalarında değişiklik yapılabilir.

### Teknik Sorular

**S: Ses tanıma ne kadar doğru?**
C: Google Cloud Speech API kullanarak %95+ doğrulukla Türkçe ses tanıma yapar. Çevre gürültüsü doğruluğu etkileyebilir.

**S: API maliyeti ne kadar?**
C: Günlük ortalama 100 hikaye için:
- OpenAI: ~$5-10/ay
- ElevenLabs: ~$5/ay
- Google Cloud: ~$2-5/ay

**S: Offline çalışma modu var mı?**
C: Şu anda yok. Gelecekte yerel AI modelleri desteği eklenebilir.

### Güvenlik Sorular

**S: Çocuk güvenliği nasıl sağlanır?**
C: Sistem çok katmanlı güvenlik sağlar:
- İçerik filtreleme
- Yaş uygunluğu kontrolü
- Korkunç/olumsuz içerik engelleme
- Ebeveyn kontrolü

**S: Ses kayıtları saklanır mı?**
C: Hayır, ses kayıtları sadece anlık işleme için kullanılır ve saklanmaz.

**S: Kişisel veriler güvenli mi?**
C: Evet, tüm API çağrıları şifreli bağlantı ile yapılır. Çocuk bilgileri sadece yerel cihazda saklanır.

### Performans Sorular

**S: Pi Zero 2W yeterli mi?**
C: Evet, sistem remote processing kullandığı için Pi Zero 2W yeterlidir. Sadece ses işleme ve API çağrıları yapılır.

**S: Hikaye üretimi ne kadar sürer?**
C: Ortalama 3-5 saniye içinde hikaye üretilir. İnternet hızı ve API yanıt süresine bağlıdır.

**S: Kaç hikaye saklanır?**
C: Son 10 hikaye otomatik olarak saklanır. Eski hikayelerin üzerine yazılır.

---

## Destek ve Katkıda Bulunma

### Topluluk

**GitHub Repository:**
https://github.com/storytellerpi/storyteller-remote

**Yeni Özellik Talebi:**
GitHub Issues bölümünden yeni özellik talebi açabilirsiniz.

**Hata Bildirimi:**
Detaylı hata raporu için:
1. Sistem tanılaması çalıştırın
2. Log dosyalarını toplayın
3. GitHub Issues'ta rapor açın

### Katkıda Bulunma

**Kod Katkısı:**
1. Repository'yi fork edin
2. Yeni branch oluşturun
3. Değişiklikleri yapın
4. Test edin
5. Pull request gönderin

**Dokümantasyon:**
Dokümantasyon geliştirmeleri her zaman memnuniyetle karşılanır.

**Çeviri:**
Yeni dil desteği eklemek için çeviri katkısı yapabilirsiniz.

---

## Lisans

Bu proje MIT lisansı altında dağıtılmaktadır. Detaylar için `LICENSE` dosyasını inceleyiniz.

---

## Teşekkürler

Bu proje aşağıdaki açık kaynak projelerden yararlanmıştır:
- OpenAI GPT-4
- Google Cloud Speech API
- ElevenLabs TTS
- OpenWakeWord
- Flask Framework
- Raspberry Pi Foundation

---

**Son Güncelleme:** 2024-12-19
**Versiyon:** 1.0.0
**Bakım:** Aktif geliştirme