# Kafka, RabbitMQ, Redis ve Elasticsearch - Kapsamlı Eğitim Dokümantasyonu

Bu repository, **Kafka**, **RabbitMQ**, **Redis** ve **Elasticsearch** teknolojileri için temelden ileri seviyeye kadar ilerleyen kapsamlı bir eğitim dokümantasyonudur.

## 📋 İçerik Yapısı

```
├── docs/                           # Eğitim dokümantasyonu
│   ├── 00-roadmap.md              # Öğrenme yol haritası
│   ├── 01-kafka/                  # Kafka bölümü
│   ├── 02-rabbitmq/               # RabbitMQ bölümü
│   ├── 03-redis/                  # Redis bölümü
│   ├── 04-elasticsearch/          # Elasticsearch bölümü
│   └── 99-appendices/             # Ekler (glossary, cheatsheets, troubleshooting)
├── examples/                      # Kod örnekleri
│   ├── kafka/                     # Kafka kod örnekleri
│   ├── rabbitmq/                  # RabbitMQ kod örnekleri
│   ├── redis/                     # Redis kod örnekleri
│   └── elasticsearch/             # Elasticsearch kod örnekleri
├── deployment/                    # Deployment yapılandırmaları
│   ├── docker-compose/            # Docker Compose dosyaları
│   └── kubernetes/                # Kubernetes manifests
└── README.md                      # Bu dosya
```

## 🎯 Hedef Kitle

- **Başlangıç Seviyesi**: Temel programlama bilgisine sahip geliştiriciler
- **Orta Seviye**: Distributed systems kavramlarını öğrenmek isteyenler
- **İleri Seviye**: Production-ready çözümler geliştirmek isteyenler

## 🚀 Hızlı Başlangıç

### 1. Repository Setup

```bash
git clone <repository-url>
cd KAFKA-RABBITMQ-REDIS-ELASTICHSEARCH
```

### 2. Otomatik Kurulum

```bash
# Tüm servisleri başlat
chmod +x setup.sh
./setup.sh setup

# Veya Makefile kullan
make setup
```

### 3. Servisleri Başlatma

```bash
# Tüm servisleri başlat
make start-all

# Sadece belirli bir servis
make start-kafka      # Kafka cluster
make start-rabbitmq   # RabbitMQ
make start-redis      # Redis
make start-elasticsearch # Elasticsearch
```

### 4. Servis Durumunu Kontrol Et

```bash
make status
# veya
./setup.sh status
```

### 5. Öğrenme Yol Haritası

1. [Roadmap](docs/00-roadmap.md) dosyasını okuyarak öğrenme planınızı oluşturun

2. İlgilendiğiniz teknoloji bölümünden başlayın:
   - [Kafka](docs/01-kafka/01-temeller.md) - Event Streaming Platform
   - [RabbitMQ](docs/02-rabbitmq/01-temeller.md) - Message Broker
   - [Redis](docs/03-redis/01-temeller.md) - In-Memory Data Store
   - [Elasticsearch](docs/04-elasticsearch/01-temeller.md) - Search & Analytics Engine

### 6. Hızlı Test

```bash
# Kafka test
make test-kafka

# RabbitMQ chat uygulaması test
cd examples/rabbitmq/python
python chat_producer.py alice &
python chat_consumer.py bob general

# RabbitMQ performance test
./scripts/rabbitmq_manager.sh performance 1000 3

# Tüm servislerin durumunu kontrol et
make health
```

### 7. Management UI'lar

Servisler başladıktan sonra bu adreslere erişebilirsiniz:

- **Kafka UI**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (admin/admin123)
- **Redis Commander**: http://localhost:8081
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

## � Progress Durumu

### ✅ Tamamlanan Bölümler

- [x] **Project Structure** - Proje iskelet yapısı
- [x] **Kafka Fundamentals** - Temel kavramlar ve kurulum
- [x] **Kafka Producer/Consumer** - API kullanımı ve örnekler
- [x] **Kafka Topic Management** - İleri seviye yönetim
- [x] **RabbitMQ Fundamentals** - Temel kavramlar ve kurulum
- [x] **RabbitMQ Chat Application** - Gerçek dünya örneği
- [x] **Setup & Management Scripts** - Otomatik kurulum ve yönetim

### 🚧 Devam Eden Bölümler

- [ ] **RabbitMQ Exchange Patterns** - Direct, Topic, Fanout, Headers
- [ ] **RabbitMQ Advanced Features** - Dead Letter Queues, TTL, Clustering
- [ ] **Redis Fundamentals** - Data structures ve temel operasyonlar
- [ ] **Redis Advanced** - Pub/Sub, Clustering, Persistence
- [ ] **Elasticsearch Fundamentals** - Indexing ve Search
- [ ] **Elasticsearch Advanced** - Aggregations, Analytics

### 📈 Toplam İlerleme: ~25%

**Estimasyon:**

- Kafka: %80 tamamlandı
- RabbitMQ: %30 tamamlandı
- Redis: %0 başlanmadı
- Elasticsearch: %0 başlanmadı

## �🛠️ Gereksinimler

- Docker ve Docker Compose
- Node.js 16+ (JavaScript örnekleri için)
- Java 11+ (Kafka ve Elasticsearch için)
- Python 3.8+ (Python örnekleri için)

## 📚 Dokümantasyon Özellikleri

- ✅ **Türkçe açıklamalar** ve yorumlar
- ✅ **Çalıştırılabilir kod örnekleri**
- ✅ **Mimari diagramları** (Mermaid.js + ASCII)
- ✅ **Adım adım işlem kılavuzları**
- ✅ **Best practices** ve common pitfalls
- ✅ **Hands-on laboratuvar görevleri**
- ✅ **Production deployment** kılavuzları

## 🎓 Öğrenme Yaklaşımı

Her bölüm şu yapıda organize edilmiştir:

1. **Özet** - Bölümün 3-5 cümlelik özeti
2. **Learning Objectives** - Öğrenme hedefleri
3. **Prerequisites** - Ön gereksinimler
4. **Teorik Açıklama** - Kavramlar ve mimari
5. **Pratik Örnekler** - Kod örnekleri ve açıklamalar
6. **Hands-on Tasks** - Uygulamalı görevler
7. **Checklist** - Kontrol listesi
8. **Common Mistakes** - Yaygın hatalar ve çözümleri

## 📖 Başlangıç Noktaları

- **Mesajlaşma sistemleri yeniyim**: [RabbitMQ Temellerine](docs/02-rabbitmq/01-temeller.md) başlayın
- **Event streaming öğrenmek istiyorum**: [Kafka Temellerine](docs/01-kafka/01-temeller.md) başlayın
- **Cache ve in-memory database**: [Redis Temellerine](docs/03-redis/01-temeller.md) başlayın
- **Arama ve analitik**: [Elasticsearch Temellerine](docs/04-elasticsearch/01-temeller.md) başlayın

## 🤝 Katkıda Bulunma

Bu dokümantasyonu geliştirmek için katkılarınızı bekliyoruz! Lütfen:

1. Issue açarak geri bildirimde bulunun
2. Pull request gönderin
3. Dokümantasyon hatalarını bildirin
4. Yeni örnekler önerin

## 📞 İletişim

Sorularınız için issue açabilir veya dokümantasyondaki ilgili bölümde belirtilen kaynakları inceleyebilirsiniz.

---

**Happy Learning! 🎉**
