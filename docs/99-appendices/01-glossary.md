# 📖 Glossary - Terimler Sözlüğü

Bu bölümde Kafka, RabbitMQ, Redis ve Elasticsearch ile ilgili tüm temel kavramları alfabetik sırayla bulacaksınız.

## 🅰️ A

### Acknowledgment (ACK)

**Türkçe**: Onay, Alındı Bildirimi
**Açıklama**: Consumer'ın mesajı başarıyla işlediğini broker'a bildirmesi
**Teknoloji**: RabbitMQ, Kafka
**Örnek**: `channel.basic_ack(delivery_tag)` (RabbitMQ)

### Aggregation

**Türkçe**: Toplama, Kümeleme
**Açıklama**: Elasticsearch'te veri analizi için kullanılan gruplandırma işlemi
**Teknoloji**: Elasticsearch
**Örnek**: Terms aggregation, Date histogram

### Analyzer

**Türkçe**: Çözümleyici
**Açıklama**: Elasticsearch'te text'i işlemek için kullanılan component
**Teknoloji**: Elasticsearch
**Örnek**: Standard analyzer, Keyword analyzer

### AOF (Append Only File)

**Türkçe**: Sadece Ekleme Dosyası
**Açıklama**: Redis'te persistence için kullanılan log formatı
**Teknoloji**: Redis
**Örnek**: `appendonly yes` config

## 🅱️ B

### Binding

**Türkçe**: Bağlama
**Açıklama**: RabbitMQ'da exchange ile queue arasındaki bağlantı
**Teknoloji**: RabbitMQ
**Örnek**: `queue.bind(exchange, routing_key="user.created")`

### Broker

**Türkçe**: Aracı
**Açıklama**: Mesaj alıp dağıtan sunucu komponenti
**Teknoloji**: Kafka, RabbitMQ
**Örnek**: Kafka broker, RabbitMQ broker

### Bulk Operation

**Türkçe**: Toplu İşlem
**Açıklama**: Elasticsearch'te birden çok document'i aynı anda işleme
**Teknoloji**: Elasticsearch
**Örnek**: `_bulk` API endpoint

## 🅲 C

### Channel

**Türkçe**: Kanal
**Açıklama**: RabbitMQ'da connection içindeki virtual bağlantı
**Teknoloji**: RabbitMQ
**Örnek**: `connection.channel()`

### Cluster

**Türkçe**: Küme
**Açıklama**: Birden çok node'un birlikte çalışması
**Teknoloji**: Tümü
**Örnek**: Kafka cluster, Redis cluster

### Consumer

**Türkçe**: Tüketici
**Açıklama**: Mesaj/event'leri alan ve işleyen component
**Teknoloji**: Kafka, RabbitMQ
**Örnek**: `@KafkaListener` (Spring)

### Consumer Group

**Türkçe**: Tüketici Grubu
**Açıklama**: Kafka'da load balancing için consumer'ları gruplandırma
**Teknoloji**: Kafka
**Örnek**: `group.id=payment-service`

### CQRS (Command Query Responsibility Segregation)

**Türkçe**: Komut Sorgu Sorumluluğu Ayrımı
**Açıklama**: Read ve write operasyonlarını ayıran pattern
**Teknoloji**: Architecture pattern
**Örnek**: Write → Kafka, Read → Elasticsearch

## 🅳 D

### Dead Letter Queue (DLQ)

**Türkçe**: Ölü Mektup Kuyruğu
**Açıklama**: İşlenemayan mesajların toplandığı queue
**Teknoloji**: RabbitMQ, (Kafka'da DLT)
**Örnek**: Failed payment messages → DLQ

### Document

**Türkçe**: Belge
**Açıklama**: Elasticsearch'te basic data unit
**Teknoloji**: Elasticsearch
**Örnek**: JSON format'ta user document

### Durability

**Türkçe**: Dayanıklılık
**Açıklama**: Verilerin disk'e yazılarak kalıcı hale getirilmesi
**Teknoloji**: Tümü
**Örnek**: Durable queue (RabbitMQ)

## 🅴 E

### Event

**Türkçe**: Olay
**Açıklama**: Sistemde gerçekleşen bir durum değişikliği
**Teknoloji**: Event-driven architecture
**Örnek**: `UserRegistered`, `OrderCreated`

### Event Sourcing

**Türkçe**: Olay Kaynağı
**Açıklama**: Durumu events'lerden türeten pattern
**Teknoloji**: Architecture pattern
**Örnek**: Account balance = sum of transactions

### Exchange

**Türkçe**: Değişim
**Açıklama**: RabbitMQ'da mesajları queue'lara yönlendiren component
**Teknoloji**: RabbitMQ
**Örnek**: Direct exchange, Topic exchange

### Expiration (TTL)

**Türkçe**: Süre Sonu
**Açıklama**: Data'nın otomatik silinme süresi
**Teknoloji**: Redis, RabbitMQ
**Örnek**: `EXPIRE key 3600` (Redis)

## 🅵 F

### Fanout Exchange

**Türkçe**: Dağıtım Exchange'i
**Açıklama**: Mesajı tüm bağlı queue'lara gönderen exchange
**Teknoloji**: RabbitMQ
**Örnek**: Broadcast notifications

### Field

**Türkçe**: Alan
**Açıklama**: Document içindeki data element
**Teknoloji**: Elasticsearch
**Örnek**: `name`, `age`, `email` fields

## 🅶 G

### Group Coordinator

**Türkçe**: Grup Koordinatörü
**Açıklama**: Kafka'da consumer group'ları yöneten component
**Teknoloji**: Kafka
**Örnek**: Consumer group membership management

## 🅷 H

### Hash

**Türkçe**: Hash
**Açıklama**: Redis'te key-value pairs'i tutan data structure
**Teknoloji**: Redis
**Örnek**: `HSET user:123 name "John" age 30`

### High Availability (HA)

**Türkçe**: Yüksek Erişilebilirlik
**Açıklama**: Sistem kesintisinin minimize edilmesi
**Teknoloji**: Tümü
**Örnek**: Master-slave replication

## 🅸 I

### Index

**Türkçe**: İndeks
**Açıklama**: Elasticsearch'te document'ların toplandığı container
**Teknoloji**: Elasticsearch
**Örnek**: `users` index, `orders` index

### Idempotency

**Türkçe**: Eşgüçlülük
**Açıklama**: Aynı işlemin tekrar edilmesinde aynı sonucu alma
**Teknoloji**: Kafka, REST API
**Örnek**: Duplicate message handling

### Inverted Index

**Türkçe**: Ters İndeks
**Açıklama**: Elasticsearch'te search için kullanılan data structure
**Teknoloji**: Elasticsearch
**Örnek**: Word → Document mapping

## 🅹 J

### JSON

**Türkçe**: JSON (JavaScript Object Notation)
**Açıklama**: Data exchange için kullanılan format
**Teknoloji**: Tümü
**Örnek**: `{"name": "John", "age": 30}`

## 🅺 K

### Key-Value Store

**Türkçe**: Anahtar-Değer Deposu
**Açıklama**: Basit data storage model
**Teknoloji**: Redis
**Örnek**: `SET user:123 "John Doe"`

## 🅻 L

### Leader

**Türkçe**: Lider
**Açıklama**: Kafka partition'ında write işlemlerini yöneten replica
**Teknoloji**: Kafka
**Örnek**: Partition leader election

### List

**Türkçe**: Liste
**Açıklama**: Redis'te ordered collection data type
**Teknoloji**: Redis
**Örnek**: `LPUSH mylist "item1" "item2"`

### Log Compaction

**Türkçe**: Log Sıkıştırma
**Açıklama**: Kafka'da aynı key'li mesajların latest'ini tutma
**Teknoloji**: Kafka
**Örnek**: User state snapshots

## 🅼 M

### Mapping

**Türkçe**: Haritalama
**Açıklama**: Elasticsearch'te field types tanımlama
**Teknoloji**: Elasticsearch
**Örnek**: `{"properties": {"name": {"type": "text"}}}`

### Message

**Türkçe**: Mesaj
**Açıklama**: Sistemler arası iletilen data unit
**Teknoloji**: RabbitMQ, Kafka
**Örnek**: Order confirmation message

### Multi-tenancy

**Türkçe**: Çok Kiracılık
**Açıklama**: Aynı sistem'i birden çok client'ın kullanması
**Teknoloji**: Architecture pattern
**Örnek**: SaaS applications

## 🅽 N

### Node

**Türkçe**: Düğüm
**Açıklama**: Cluster'daki tek server instance
**Teknoloji**: Elasticsearch, Redis
**Örnek**: Master node, Data node

### Negative Acknowledgment (NACK)

**Türkçe**: Olumsuz Onay
**Açıklama**: Consumer'ın mesajı işleyemediğini bildirmesi
**Teknoloji**: RabbitMQ
**Örnek**: `channel.basic_nack()`

## 🅾️ O

### Offset

**Türkçe**: Offset
**Açıklama**: Kafka partition'ında mesaj pozisyonu
**Teknoloji**: Kafka
**Örnek**: `offset=12345`

### Optimistic Locking

**Türkçe**: İyimser Kilitleme
**Açıklama**: Conflict detection ile concurrent access control
**Teknoloji**: Redis, Elasticsearch
**Örnek**: `WATCH` command (Redis)

## 🅿️ P

### Partition

**Türkçe**: Bölüm
**Açıklama**: Kafka topic'inin paralel işlenen parçası
**Teknoloji**: Kafka
**Örnek**: `orders-topic` → 3 partitions

### Producer

**Türkçe**: Üretici
**Açıklama**: Mesaj/event gönderen component
**Teknoloji**: Kafka, RabbitMQ
**Örnek**: Order service → Kafka producer

### Pub/Sub (Publish/Subscribe)

**Türkçe**: Yayınla/Abone ol
**Açıklama**: Asynchronous messaging pattern
**Teknoloji**: Redis, RabbitMQ, Kafka
**Örnek**: `PUBLISH channel message` (Redis)

## 🇶 Q

### Query

**Türkçe**: Sorgu
**Açıklama**: Data arama/filtreleme işlemi
**Teknoloji**: Elasticsearch
**Örnek**: `{"match": {"title": "kafka"}}`

### Queue

**Türkçe**: Kuyruk
**Açıklama**: Mesajların sırayla bekletildiği yapı
**Teknoloji**: RabbitMQ
**Örnek**: `payment-queue`

### QoS (Quality of Service)

**Türkçe**: Hizmet Kalitesi
**Açıklama**: Message delivery garantilerini tanımlama
**Teknoloji**: RabbitMQ
**Örnek**: `channel.basic_qos(prefetch_count=1)`

## 🇷 R

### Replica

**Türkçe**: Kopya
**Açıklama**: Data'nın backup kopyası
**Teknoloji**: Kafka, Elasticsearch
**Örnek**: Replication factor = 3

### Routing Key

**Türkçe**: Yönlendirme Anahtarı
**Açıklama**: RabbitMQ'da mesajların queue'lara yönlendirilmesi
**Teknoloji**: RabbitMQ
**Örnek**: `user.created.premium`

### RDB (Redis Database)

**Türkçe**: Redis Veritabanı
**Açıklama**: Redis'te snapshot persistence formatı
**Teknoloji**: Redis
**Örnek**: `SAVE` command

## 🇸 S

### Shard

**Türkçe**: Parça
**Açıklama**: Index'in fiziksel bölümü
**Teknoloji**: Elasticsearch
**Örnek**: Index = 5 primary shards

### Stream

**Türkçe**: Akış
**Açıklama**: Continuous data flow
**Teknoloji**: Redis, Kafka
**Örnek**: `XADD mystream * field value` (Redis)

### Serialization

**Türkçe**: Serileştirme
**Açıklama**: Object'i byte array'e çevirme
**Teknoloji**: Kafka
**Örnek**: JSON, Avro, Protobuf

## 🇹 T

### Topic

**Türkçe**: Konu
**Açıklama**: Mesajların kategorize edildiği channel
**Teknoloji**: Kafka, RabbitMQ
**Örnek**: `user-events`, `order-events`

### Transaction

**Türkçe**: İşlem
**Açıklama**: Atomic operation group
**Teknoloji**: Redis, Kafka
**Örnek**: `MULTI ... EXEC` (Redis)

### Tokenizer

**Türkçe**: Belirteç Ayırıcı
**Açıklama**: Text'i token'lara ayıran component
**Teknoloji**: Elasticsearch
**Örnek**: Standard tokenizer

## 🇺 U

### UUID (Universally Unique Identifier)

**Türkçe**: Evrensel Benzersiz Tanımlayıcı
**Açıklama**: Unique identifier generation
**Teknoloji**: Tümü
**Örnek**: `550e8400-e29b-41d4-a716-446655440000`

## 🇻 V

### Virtual Host (vhost)

**Türkçe**: Sanal Sunucu
**Açıklama**: RabbitMQ'da namespace separation
**Teknoloji**: RabbitMQ
**Örnek**: `/production`, `/staging`

## 🇼 W

### WAL (Write-Ahead Log)

**Türkçe**: Önceden Yazma Logu
**Açıklama**: Durability için kullanılan log mechanism
**Teknoloji**: Database systems
**Örnek**: PostgreSQL WAL

### Work Queue

**Türkçe**: İş Kuyruğu
**Açıklama**: Task distribution pattern
**Teknoloji**: RabbitMQ
**Örnek**: Image processing tasks

## 🇽 X

### XADD

**Türkçe**: X Ekle
**Açıklama**: Redis Streams'e entry ekleme komutu
**Teknoloji**: Redis
**Örnek**: `XADD events * type "order" id "123"`

## 🇾 Y

### YAML

**Türkçe**: YAML (YAML Ain't Markup Language)
**Açıklama**: Configuration file format
**Teknoloji**: Configuration
**Örnek**: Docker Compose files

## 🇿 Z

### ZooKeeper

**Türkçe**: ZooKeeper
**Açıklama**: Kafka'da coordination service (legacy)
**Teknoloji**: Kafka (eski versiyonlar)
**Örnek**: Kafka cluster coordination

---

## 🔤 Türkçe-İngilizce Hızlı Çeviri

| Türkçe   | İngilizce | Teknoloji       |
| -------- | --------- | --------------- |
| Aracı    | Broker    | Kafka, RabbitMQ |
| Bölüm    | Partition | Kafka           |
| Değişim  | Exchange  | RabbitMQ        |
| Indeks   | Index     | Elasticsearch   |
| Kuyruk   | Queue     | RabbitMQ        |
| Mesaj    | Message   | RabbitMQ, Kafka |
| Olay     | Event     | Event-driven    |
| Tüketici | Consumer  | Kafka, RabbitMQ |
| Üretici  | Producer  | Kafka, RabbitMQ |
| Yayınla  | Publish   | Pub/Sub         |

---

**💡 İpucu**: Bu glossary'yi bookmark yaparak sürekli referans olarak kullanabilirsiniz!
