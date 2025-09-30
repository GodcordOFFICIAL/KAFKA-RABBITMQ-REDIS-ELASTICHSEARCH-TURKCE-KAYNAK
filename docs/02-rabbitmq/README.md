# RabbitMQ Rehberi ve Dökümanlar

Bu bölüm RabbitMQ message broker'ı için kapsamlı bir öğrenme rehberi sunmaktadır.

## 📖 Bölümler

### 1. [RabbitMQ Temelleri](01-temeller.md)

- **Ne öğreneceksiniz:**

  - AMQP protokolü ve temel kavramlar
  - RabbitMQ kurulum ve konfigürasyon
  - Producer, Consumer, Queue yapıları
  - Management UI kullanımı
  - İlk mesajlaşma uygulaması

- **Seviye:** Başlangıç
- **Süre:** 2-3 saat
- **Önkoşul:** Docker temel bilgisi

### 2. [Exchange Patterns](02-exchange-patterns.md)

- **Ne öğreneceksiniz:**

  - 4 farklı exchange türü (Direct, Topic, Fanout, Headers)
  - Routing stratejileri ve kullanım senaryoları
  - Binding kavramları ve pattern matching
  - Gerçek dünya örnekleri
  - Multi-exchange architectures

- **Seviye:** Orta
- **Süre:** 4-5 saat
- **Önkoşul:** RabbitMQ Temelleri

### 3. [İleri Düzey Özellikler](03-advanced-features.md)

- **Ne öğreneceksiniz:**

  - Dead Letter Queues (DLQ) ile error handling
  - Message TTL (Time To Live) stratejileri
  - Priority Queues ile öncelikli işlem
  - Publisher Confirms güvenlik katmanı
  - Transactions ve flow control
  - Quorum queues ve persistence

- **Seviye:** İleri
- **Süre:** 4-5 saat
- **Önkoşul:** Exchange Patterns

### 4. Clustering ve High Availability _(Yakında)_

- RabbitMQ Cluster kurulumu
- Queue mirroring
- Load balancing
- Failover strategies

## 🎯 Öğrenme Yolu

### Yeni Başlayanlar İçin

```
1. RabbitMQ Temelleri →
2. Basit Producer/Consumer →
3. Exchange Patterns →
4. Gerçek Proje Uygulaması
```

### Deneyimli Geliştiriciler İçin

```
1. Exchange Patterns →
2. Advanced Features →
3. Clustering →
4. Production Deployment
```

## 🛠️ Pratik Uygulamalar

Her bölüm için detaylı örnekler ve hands-on laboratorlar:

- **Log Processing System** (Direct Exchange)
- **News Distribution** (Topic Exchange)
- **Notification Broadcast** (Fanout Exchange)
- **Order Processing** (Headers Exchange)
- **Chat Application** (Multi-pattern)

## 📁 Örnek Kodlar

Tüm örnekler `../../examples/rabbitmq/` dizininde:

```
examples/rabbitmq/
├── python/           # Python örnekleri
│   ├── simple_*.py      # Temel örnekler
│   ├── chat_*.py        # Chat uygulaması
│   ├── *_exchange_*.py  # Exchange pattern örnekleri
│   └── requirements.txt
├── java/             # Java örnekleri
├── scripts/          # Yardımcı scriptler
└── README.md         # Detaylı kullanım rehberi
```

## 🚀 Hızlı Başlat

```bash
# 1. RabbitMQ başlat
make start-rabbitmq

# 2. Python dependencies kur
cd examples/rabbitmq/python
pip install -r requirements.txt

# 3. İlk testi çalıştır
python simple_producer.py "Merhaba!"
python simple_consumer.py
```

## 📊 İlerleme Takibi

- ✅ **RabbitMQ Temelleri** - Tamamlandı
- ✅ **Exchange Patterns** - Tamamlandı
- ✅ **Advanced Features** - Tamamlandı
- ⏳ **Clustering** - Geliştiriliyor
- 📋 **Production Guide** - Planlandı

## 🎓 Sertifika Hedefleri

Bu dökümanlar aşağıdaki sertifikalara hazırlık amacıyla kullanılabilir:

- RabbitMQ Certified Professional
- VMware Certified Professional
- Cloud Message Broker Certifications

## 💡 Katkı

Bu dökümanları geliştirmek için:

1. İssue açın
2. Pull request gönderin
3. Feedback verin

---

**Başarılı öğrenmeler! 🐰📨**
