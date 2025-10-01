# Kafka, RabbitMQ, Redis ve Elasticsearch - Kapsamlı Eğitim Dokümantasyonu

[![GitHub](https://img.shields.io/badge/GitHub-omerada-blue?logo=github)](https://github.com/omerada)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](deployment/docker-compose/)

Bu repository, **Kafka**, **RabbitMQ**, **Redis** ve **Elasticsearch** teknolojileri için temelden ileri seviyeye kadar ilerleyen kapsamlı bir eğitim dokümantasyonudur.
  
- GitHub: [@omerada](https://github.com/omerada)
- Email: omer.ada@example.com

## 🔧 Özellikler

- ✅ **Kapsamlı Dokümantasyon**: Türkçe dokümantasyon ve rehberler
- ✅ **Pratik Örnekler**: Her teknoloji için çalışan kod örnekleri (Python & Java)
- ✅ **Docker Support**: Kolay kurulum ve test ortamı
- ✅ **Production Ready**: Gerçek proje senaryoları
- ✅ **Integration Examples**: Teknolojilerin birlikte kullanımı
- ✅ **Real-time Monitoring**: Birleşik monitoring dashboard
- ✅ **Performance Optimization**: Otomatik optimizasyon önerileri
- ✅ **Event-driven Architecture**: Mikroservis iletişim patterns
- ✅ **Graceful Degradation**: Servis kesintilerinde graceful handling
- ✅ **Comprehensive Benchmarking**: Performance test suite'i

## 🛠️ Gereksinimler

- Docker ve Docker Compose
- Python 3.8+ (Python örnekleri için)
- Java 11+ (Java örnekleri için)
- Make (Linux/macOS) veya PowerShell (Windows)

## 📋 Proje Yapısı

```
KAFKA-RABBITMQ-REDIS-ELASTICHSEARCH/
├── README.md                          # Ana dokümantasyon
├── Makefile                          # Build ve deployment komutları
├── setup.sh                          # Otomatik kurulum scripti
├── docs/                             # Eğitim dokümantasyonu
│   ├── 00-roadmap.md                # Öğrenme yol haritası
│   ├── 01-kafka/                    # Kafka dokümantasyonu
│   │   ├── 01-temeller.md
│   │   ├── 02-producer-consumer.md
│   │   ├── 03-topic-partition.md
│   │   └── README.md
│   ├── 02-rabbitmq/                 # RabbitMQ dokümantasyonu
│   │   ├── 01-temeller.md
│   │   ├── 02-exchange-patterns.md
│   │   ├── 03-advanced-features.md
│   │   └── README.md
│   ├── 03-redis/                    # Redis dokümantasyonu
│   │   ├── 01-temeller.md
│   │   ├── 02-pubsub.md
│   │   ├── 03-transactions-scripting.md
│   │   ├── 04-persistence-replication.md
│   │   ├── 05-streams.md
│   │   ├── 06-clustering-production.md
│   │   └── README.md
│   ├── 04-elasticsearch/            # Elasticsearch dokümantasyonu
│   │   ├── 01-temeller.md
│   │   ├── 02-crud-index-management.md
│   │   ├── 03-search-aggregations.md
│   │   ├── 04-production-deployment.md
│   │   └── README.md
│   ├── 05-integration/              # Integration dokümantasyonu
│   │   ├── 01-event-driven-architecture.md
│   │   └── 02-performance-optimization.md
│   └── 99-appendices/               # Ekler ve referanslar
│       ├── 01-glossary.md
│       ├── 02-cheatsheets.md
│       ├── 03-troubleshooting.md
│       ├── 04-further-reading.md
│       ├── 05-performance-benchmarks.md
│       └── README.md
├── examples/                        # Kod örnekleri
│   ├── kafka/                      # Kafka örnekleri
│   │   ├── java/                   # Java implementasyonları
│   │   ├── python/                 # Python implementasyonları
│   │   └── scripts/                # Yönetim scriptleri
│   ├── rabbitmq/                   # RabbitMQ örnekleri
│   │   ├── java/                   # Java implementasyonları
│   │   ├── python/                 # Python implementasyonları
│   │   └── scripts/                # Yönetim scriptleri
│   ├── redis/                      # Redis örnekleri
│   │   ├── java/                   # Java implementasyonları
│   │   └── python/                 # Python implementasyonları
│   ├── elasticsearch/              # Elasticsearch örnekleri
│   │   ├── java/                   # Java implementasyonları
│   │   └── python/                 # Python implementasyonları
│   └── integration/                # Integration örnekleri
│       ├── java/                   # Java implementasyonları
│       └── python/                 # Python implementasyonları
├── deployment/                      # Deployment yapılandırmaları
│   └── docker-compose/             # Docker Compose dosyaları
│       ├── kafka-cluster.yml
│       ├── redis.yml
│       ├── redis.conf
│       ├── elasticsearch.yml
│       └── elasticsearch.conf
└── scripts/                        # Yönetim scriptleri
    ├── rabbitmq_manager.sh
    ├── setup_elasticsearch.sh
    └── setup_redis.sh
```

## 🎯 Hedef Kitle

- **Başlangıç Seviyesi**: Temel programlama bilgisine sahip geliştiriciler
- **Orta Seviye**: Distributed systems kavramlarını öğrenmek isteyenler
- **İleri Seviye**: Production-ready çözümler geliştirmek isteyenler

## 🚀 Hızlı Başlangıç

## 🚀 Hızlı Başlangıç

### 1. Repository Setup

```bash
git clone https://github.com/omerada/KAFKA-RABBITMQ-REDIS-ELASTICHSEARCH.git
cd KAFKA-RABBITMQ-REDIS-ELASTICHSEARCH
```

### 2. Otomatik Kurulum

```bash
# Linux/macOS için
chmod +x setup.sh
./setup.sh setup

# Windows PowerShell için
.\setup.sh setup

# Veya Makefile kullan (Linux/macOS)
make setup
```

### 3. Servisleri Başlatma

```bash
# Linux/macOS - Tüm servisleri başlat
make start-all

# Veya belirli servisleri başlat
make start-kafka      # Kafka cluster
make start-rabbitmq   # RabbitMQ
make start-redis      # Redis
make start-elasticsearch # Elasticsearch

# Windows PowerShell için
docker-compose -f deployment/docker-compose/kafka-cluster.yml up -d
docker-compose -f deployment/docker-compose/redis.yml up -d
docker-compose -f deployment/docker-compose/elasticsearch.yml up -d
```

### 4. Servis Durumunu Kontrol Et

```bash
# Linux/macOS
make status
# veya
./setup.sh status

# Windows PowerShell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 5. Örnekleri Çalıştırma

#### Kafka Örnekleri

```bash
# Python Producer/Consumer
cd examples/kafka/python
pip install -r requirements.txt
python simple_producer.py
python simple_consumer.py

# Java örnekleri
cd examples/kafka/java
mvn compile exec:java -Dexec.mainClass="KafkaProducerExample"
```

#### RabbitMQ Örnekleri

```bash
# Chat uygulaması
cd examples/rabbitmq/python
pip install -r requirements.txt
python chat_producer.py alice &
python chat_consumer.py bob general

# Exchange pattern örnekleri
python direct_exchange_producer.py
python direct_exchange_consumer.py
```

#### Redis Örnekleri

```bash
# Temel operasyonlar
cd examples/redis/python
pip install -r requirements.txt
python basic_operations.py

# Pub/Sub sistemi
python pub_sub_publisher.py
python pub_sub_subscriber.py
```

#### Elasticsearch Örnekleri

```bash
# CRUD işlemleri
cd examples/elasticsearch/python
pip install -r requirements.txt
python basic_operations.py
python advanced_crud_operations.py

# Arama ve aggregation
python product_search_lab.py
python advanced_aggregations.py
```

### 6. Integration Örnekleri

```bash
# Event-driven architecture örneği
cd examples/integration/python
python ecommerce_platform.py

# Monitoring dashboard
python monitoring_dashboard.py
```

### 7. Management UI'lar

Servisler başladıktan sonra bu adreslere erişebilirsiniz:

- **Kafka UI**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (admin/admin123)
- **Redis Commander**: http://localhost:8081
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

### 8. Öğrenme Yol Haritası

1. [Roadmap](docs/00-roadmap.md) dosyasını okuyarak öğrenme planınızı oluşturun

2. İlgilendiğiniz teknoloji bölümünden başlayın:

   - [Kafka](docs/01-kafka/01-temeller.md) - Event Streaming Platform
   - [RabbitMQ](docs/02-rabbitmq/01-temeller.md) - Message Broker
   - [Redis](docs/03-redis/01-temeller.md) - In-Memory Data Store
   - [Elasticsearch](docs/04-elasticsearch/01-temeller.md) - Search & Analytics Engine

3. Integration örnekleri ile teknolojileri birlikte kullanımını öğrenin:
   - [Event-driven Architecture](docs/05-integration/01-event-driven-architecture.md)
   - [Performance Optimization](docs/05-integration/02-performance-optimization.md)

## 📊 Progress Durumu

### 🚧 Tamamlanan Tüm Bölümler ✅

#### Kafka (100% Tamamlandı)

- [x] **Kafka Fundamentals** - Temel kavramlar ve kurulum
- [x] **Kafka Producer/Consumer** - API kullanımı ve örnekler
- [x] **Kafka Topic Management** - İleri seviye yönetim

#### RabbitMQ (100% Tamamlandı)

- [x] **RabbitMQ Fundamentals** - Temel kavramlar ve kurulum
- [x] **RabbitMQ Exchange Patterns** - Direct, Topic, Fanout, Headers
- [x] **RabbitMQ Advanced Features** - Dead Letter Queues, TTL, Priority
- [x] **RabbitMQ Chat Application** - Gerçek dünya örneği

#### Redis (100% Tamamlandı)

- [x] **Redis Fundamentals** - Temel kavramlar, data types, kurulum
- [x] **Redis Pub/Sub System** - Real-time messaging, chat uygulaması
- [x] **Redis Transactions** - MULTI/EXEC, Lua scripting, optimistic locking
- [x] **Redis Persistence & Replication** - RDB/AOF, master-slave
- [x] **Redis Streams** - Event streaming, consumer groups
- [x] **Redis Clustering** - Horizontal scaling, production deployment

#### Elasticsearch (100% Tamamlandı)

- [x] **Elasticsearch Fundamentals** - Temel kavramlar, REST API, kurulum
- [x] **Elasticsearch Advanced CRUD** - Document lifecycle, bulk operations
- [x] **Elasticsearch Search Queries** - Complex queries ve aggregations
- [x] **Elasticsearch Production** - Security, monitoring, ILM

#### Integration & Production (100% Tamamlandı)

- [x] **Integration Examples** - Event-driven architecture örnekleri
- [x] **Monitoring Dashboard** - Real-time birleşik monitoring
- [x] **Performance Optimization** - Tuning ve best practices
- [x] **Setup & Management Scripts** - Otomatik kurulum ve yönetim

### 📈 Toplam İlerleme: 100% 🎉

**Final Durumu:**

- Kafka: %100 tamamlandı ✅
- RabbitMQ: %100 tamamlandı ✅
- Redis: %100 tamamlandı ✅
- Elasticsearch: %100 tamamlandı ✅
- Integration: %100 tamamlandı ✅
- Performance: %100 tamamlandı ✅

## Dokümantasyon Özellikleri

- ✅ **Türkçe açıklamalar** ve yorumlar
- ✅ **Çalıştırılabilir kod örnekleri** (Python & Java)
- ✅ **Mimari diagramları** (Mermaid.js + ASCII)
- ✅ **Adım adım işlem kılavuzları**
- ✅ **Best practices** ve common pitfalls
- ✅ **Hands-on laboratuvar görevleri**
- ✅ **Production deployment** kılavuzları
- ✅ **Cross-platform compatibility** (Windows, Linux, macOS)

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

**Kullanım senaryonuza göre başlangıç noktası seçin:**

- 🔄 **Event Streaming & Real-time Processing**: [Kafka Temellerine](docs/01-kafka/01-temeller.md) başlayın
- 📬 **Message Queue & Asynchronous Communication**: [RabbitMQ Temellerine](docs/02-rabbitmq/01-temeller.md) başlayın
- ⚡ **Cache & Session Management**: [Redis Temellerine](docs/03-redis/01-temeller.md) başlayın
- 🔍 **Search & Analytics**: [Elasticsearch Temellerine](docs/04-elasticsearch/01-temeller.md) başlayın
- 🏗️ **Microservices Architecture**: [Integration örneklerine](docs/05-integration/01-event-driven-architecture.md) başlayın

## 🎯 Hedef Kitle

- **Başlangıç Seviyesi**: Temel programlama bilgisine sahip geliştiriciler
- **Orta Seviye**: Distributed systems kavramlarını öğrenmek isteyenler
- **İleri Seviye**: Production-ready çözümler geliştirmek isteyenler
- **DevOps Engineers**: Deployment ve monitoring konularında uzmanlaşmak isteyenler

## 🔗 Faydalı Linkler

- [Kafka Resmi Dokümantasyon](https://kafka.apache.org/documentation/)
- [RabbitMQ Resmi Dokümantasyon](https://www.rabbitmq.com/documentation.html)
- [Redis Resmi Dokümantasyon](https://redis.io/documentation)
- [Elasticsearch Resmi Dokümantasyon](https://www.elastic.co/guide/)

## 🤝 Katkıda Bulunma

Bu dokümantasyonu geliştirmek için katkılarınızı bekliyoruz! Lütfen:

1. **Issue açarak** geri bildirimde bulunun
2. **Pull request** gönderin
3. **Dokümantasyon hatalarını** bildirin
4. **Yeni örnekler** önerin
5. **Performance iyileştirmeleri** paylaşın

### Katkı Kuralları

- Tüm örnekler hem Python hem de Java dillerinde olmalı
- Dokümantasyon Türkçe olarak yazılmalı
- Kod örnekleri test edilmiş ve çalışır durumda olmalı
- Commit mesajları anlamlı ve açıklayıcı olmalı

## 📞 İletişim ve Destek

- **GitHub Issues**: Teknik sorular ve bug raporları için
- **Discussions**: Genel sorular ve tartışmalar için
- **Email**: omer.ada@example.com (Proje sahibi ile iletişim)

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

**Bu proje ile öğrenmeye başladığınız için teşekkürler! 🎉**

_Ömer Ada tarafından ❤️ ile geliştirilmiştir._
