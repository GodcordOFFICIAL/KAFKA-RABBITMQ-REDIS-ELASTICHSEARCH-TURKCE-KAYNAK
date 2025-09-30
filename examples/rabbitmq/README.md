# RabbitMQ Örnekleri ve Dökümanlar

Bu dizin RabbitMQ ile ilgili kapsamlı örnekleri ve dökümanları içermektedir.

## 📁 Dizin Yapısı

```
docs/02-rabbitmq/
├── 01-temeller.md           # RabbitMQ temelleri ve kurulum
├── 02-exchange-patterns.md  # Exchange türleri ve routing patterns
└── README.md               # Bu dosya

examples/rabbitmq/
├── python/                 # Python örnekleri
│   ├── simple_producer.py        # Basit producer
│   ├── simple_consumer.py        # Basit consumer
│   ├── chat_producer.py          # Chat uygulaması producer
│   ├── chat_consumer.py          # Chat uygulaması consumer
│   ├── direct_exchange_producer.py   # Direct exchange producer
│   ├── direct_exchange_consumer.py   # Direct exchange consumer
│   ├── topic_exchange_producer.py    # Topic exchange producer
│   ├── topic_exchange_consumer.py    # Topic exchange consumer
│   ├── fanout_exchange_producer.py   # Fanout exchange producer
│   ├── fanout_exchange_consumer.py   # Fanout exchange consumer
│   ├── headers_exchange_producer.py  # Headers exchange producer
│   ├── headers_exchange_consumer.py  # Headers exchange consumer
│   ├── dlq_producer.py              # Dead Letter Queue producer
│   ├── dlq_consumer.py              # Dead Letter Queue consumer
│   ├── dlq_monitor.py               # DLQ monitoring tool
│   ├── ttl_producer.py              # TTL (Time To Live) producer
│   ├── priority_producer.py         # Priority queue producer
│   ├── priority_consumer.py         # Priority queue consumer
│   ├── advanced_features_lab.py     # Complete advanced features lab
│   └── requirements.txt              # Python dependencies
├── java/                   # Java örnekleri
│   ├── src/main/java/
│   │   └── SimpleProducer.java      # Java producer örneği
│   └── pom.xml                      # Maven configuration
└── scripts/                # Yardımcı scriptler
    └── setup_multi_exchange_lab.sh  # Multi-exchange lab kurulumu
```

## 🚀 Hızlı Başlangıç

### 1. RabbitMQ'yu Başlat

```bash
# Docker Compose ile
make start-rabbitmq

# Veya manuel olarak
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin123 \
  rabbitmq:3.12-management
```

### 2. Python Environment Hazırla

```bash
cd examples/rabbitmq/python
pip install -r requirements.txt
```

### 3. Basit Mesajlaşma Testi

```bash
# Terminal 1: Consumer başlat
python simple_consumer.py

# Terminal 2: Producer ile mesaj gönder
python simple_producer.py "Merhaba RabbitMQ!"
```

## 📚 Öğrenme Sırası

### Seviye 1: Temel Kavramlar

1. **[RabbitMQ Temelleri](../../docs/02-rabbitmq/01-temeller.md)**

   - AMQP protokolü
   - Producer/Consumer/Queue kavramları
   - Management UI kullanımı

2. **Basit Mesajlaşma**
   ```bash
   python simple_producer.py "Test mesajı"
   python simple_consumer.py
   ```

### Seviye 2: Exchange Patterns

3. **[Exchange Patterns](../../docs/02-rabbitmq/02-exchange-patterns.md)**

   - Direct, Topic, Fanout, Headers exchange'ler
   - Routing stratejileri
   - Binding kavramları

4. **Exchange Örnekleri**

   ```bash
   # Direct Exchange - Log Sistemi
   python direct_exchange_consumer.py error warning
   python direct_exchange_producer.py

   # Topic Exchange - Haber Sistemi
   python topic_exchange_consumer.py "tech.*.*"
   python topic_exchange_producer.py

   # Fanout Exchange - Bildirimler
   python fanout_exchange_consumer.py mobile_app
   python fanout_exchange_producer.py

   # Headers Exchange - Sipariş İşleme
   python headers_exchange_consumer.py premium
   python headers_exchange_producer.py
   ```

### Seviye 3: İleri Düzey Özellikler

5. **[Advanced Features](../../docs/02-rabbitmq/03-advanced-features.md)**

   - Dead Letter Queues (DLQ)
   - Message TTL stratejileri
   - Priority Queues
   - Publisher Confirms

6. **DLQ (Dead Letter Queue) Sistemi**

   ```bash
   # DLQ producer ile test mesajları gönder
   python dlq_producer.py sample

   # DLQ consumer ile işle (bazıları fail olacak)
   python dlq_consumer.py

   # Failed mesajları monitör et
   python dlq_monitor.py --auto-recover

   # Sadece failure test mesajları
   python dlq_producer.py failure
   ```

7. **TTL (Time To Live) Sistemi**

   ```bash
   # TTL demo senaryoları
   python ttl_producer.py demo

   # Custom TTL mesajı
   python ttl_producer.py custom "Bu mesaj 45 saniye yaşayacak" 45

   # Kademeli TTL batch
   python ttl_producer.py batch

   # Queue durumunu izle
   python ttl_producer.py monitor
   ```

8. **Priority Queue Sistemi**

   ```bash
   # Priority demo (karışık sırada gönderim)
   python priority_producer.py demo

   # Consumer'lar priority sırasına göre işleyecek
   python priority_consumer.py --fast

   # Sadece urgent tasks işle
   python priority_consumer.py --queue urgent_tasks

   # Department based tasks
   python priority_producer.py department
   ```

9. **Complete Advanced Features Lab**

   ```bash
   # Tam sistem kurulumu
   python advanced_features_lab.py setup

   # Tüm features demo
   python advanced_features_lab.py demo

   # Stress test (60s, 10 msg/s)
   python advanced_features_lab.py stress --duration 60 --rate 10

   # Queue monitoring
   python advanced_features_lab.py monitor

   # Cleanup
   python advanced_features_lab.py cleanup
   ```

### Seviye 4: Gerçek Dünya Uygulamaları

10. **Chat Uygulaması**

```bash
# Multiple rooms destekli chat
python chat_consumer.py alice general tech
python chat_producer.py alice
```

11. **Multi-Exchange Lab**

```bash
chmod +x scripts/setup_multi_exchange_lab.sh
./scripts/setup_multi_exchange_lab.sh setup
./scripts/setup_multi_exchange_lab.sh demo
```

## 🔧 Örnek Kullanımlar

### Direct Exchange - Severity-based Log Routing

**Producer:**

```python
# Log gönderme
python direct_exchange_producer.py
# Veya özel log
python direct_exchange_producer.py error "Database connection failed"
```

**Consumer:**

```python
# Sadece error logları dinle
python direct_exchange_consumer.py error

# Error ve warning logları dinle
python direct_exchange_consumer.py error warning
```

### Topic Exchange - Pattern-based News Routing

**Producer:**

```python
# Predefined haberler gönder
python topic_exchange_producer.py

# Özel haber gönder
python topic_exchange_producer.py tech ai high "New AI Breakthrough"
```

**Consumer:**

```python
# Tüm tech haberlerini dinle
python topic_exchange_consumer.py "tech.*.*"

# Sadece yüksek öncelikli haberleri dinle
python topic_exchange_consumer.py "*.*.high"

# Tech ve finance haberlerini dinle
python topic_exchange_consumer.py "tech.#" "finance.#"
```

### Fanout Exchange - Broadcast Notifications

**Producer:**

```python
# Predefined bildirimler gönder
python fanout_exchange_producer.py

# Özel bildirim gönder
python fanout_exchange_producer.py security "Security Alert" "Suspicious activity detected"
```

**Consumer:**

```python
# Tüm bildirimleri dinle
python fanout_exchange_consumer.py mobile_app

# Sadece security ve system bildirimlerini dinle
python fanout_exchange_consumer.py web_app --types security system

# Sadece yüksek öncelikli bildirimleri dinle
python fanout_exchange_consumer.py desktop_app --priority high
```

### Headers Exchange - Metadata-based Order Processing

**Producer:**

```python
# Sample siparişler gönder
python headers_exchange_producer.py

# Interaktif sipariş oluştur
python headers_exchange_producer.py custom
```

**Consumer:**

```python
# Premium müşteri siparişlerini işle
python headers_exchange_consumer.py premium

# Express kargo siparişlerini işle
python headers_exchange_consumer.py express

# VIP + Express kombinasyonunu işle
python headers_exchange_consumer.py vip_express
```

## 🧪 Test Senaryoları

### Senaryo 1: E-ticaret Log Analizi

```bash
# 1. Error log consumer başlat
python direct_exchange_consumer.py error critical

# 2. System monitör başlat
python direct_exchange_consumer.py warning info

# 3. Log üret
python direct_exchange_producer.py
```

### Senaryo 2: Haber Dağıtım Sistemi

```bash
# 1. Tech editörü
python topic_exchange_consumer.py "tech.*.*" --name TechEditor

# 2. Breaking news editörü
python topic_exchange_consumer.py "*.*.critical" --name BreakingNews

# 3. Haberci
python topic_exchange_producer.py
```

### Senaryo 3: Çoklu Bildirim Sistemi

```bash
# 1. Mobile app
python fanout_exchange_consumer.py mobile_app --types alert security

# 2. Web dashboard
python fanout_exchange_consumer.py web_dashboard --priority high

# 3. Admin panel
python fanout_exchange_consumer.py admin_panel

# 4. Bildirim gönder
python fanout_exchange_producer.py
```

### Senaryo 4: Sipariş İşleme Pipeline

```bash
# 1. Premium müşteri işlemci
python headers_exchange_consumer.py premium

# 2. Express kargo işlemci
python headers_exchange_consumer.py express

# 3. Yüksek değerli sipariş işlemci
python headers_exchange_consumer.py high_value

# 4. Sipariş gönder
python headers_exchange_producer.py
```

## 🎛️ Management UI

RabbitMQ Management UI: http://localhost:15672

- Username: `admin`
- Password: `admin123`

### Önemli Sayfalar:

- **Overview**: Cluster genel durumu
- **Connections**: Aktif bağlantılar
- **Channels**: Message kanalları
- **Exchanges**: Exchange'ler ve binding'ler
- **Queues**: Queue'lar ve mesaj sayıları

## 🔍 Debugging ve Monitoring

### RabbitMQ Durumu Kontrol Et

```bash
# Genel durum
./scripts/rabbitmq_manager.sh status

# Exchange'leri listele
docker exec rabbitmq rabbitmqctl list_exchanges

# Queue'ları listele
docker exec rabbitmq rabbitmqctl list_queues

# Binding'leri listele
docker exec rabbitmq rabbitmqctl list_bindings
```

### Performance Monitoring

```bash
# Multi-exchange performance test
./scripts/setup_multi_exchange_lab.sh performance 60 200

# RabbitMQ manager ile monitoring
./scripts/rabbitmq_manager.sh monitor
```

## 🚨 Yaygın Hatalar ve Çözümler

### 1. Connection Refused

```bash
# RabbitMQ çalışıyor mu kontrol et
docker ps | grep rabbitmq

# RabbitMQ loglarını kontrol et
docker logs rabbitmq
```

### 2. Authentication Failed

```bash
# Credentials doğru mu kontrol et
# Default: admin/admin123
```

### 3. Exchange/Queue Not Found

```bash
# Exchange'leri tekrar oluştur
./scripts/setup_multi_exchange_lab.sh setup
```

### 4. Messages Not Routing

```bash
# Binding'leri kontrol et
docker exec rabbitmq rabbitmqctl list_bindings

# Exchange type ve routing key doğru mu?
```

## 📊 Performance Tips

1. **Connection Management**

   - Connection'ları yeniden kullan
   - Connection pooling uygula

2. **Message Durability**

   - Critical mesajlar için durable queue
   - Non-critical için memory-only

3. **Batch Processing**

   - Çok sayıda mesaj için batch send
   - Manual acknowledgment kullan

4. **Monitoring**
   - Message rates izle
   - Queue depth kontrol et
   - Memory usage takip et

## 🔗 Faydalı Linkler

- **RabbitMQ Documentation**: https://www.rabbitmq.com/documentation.html
- **AMQP 0-9-1 Specification**: https://www.rabbitmq.com/amqp-0-9-1-reference.html
- **Python pika Documentation**: https://pika.readthedocs.io/
- **Management Plugin**: https://www.rabbitmq.com/management.html

---

**Happy Messaging! 🐰**
