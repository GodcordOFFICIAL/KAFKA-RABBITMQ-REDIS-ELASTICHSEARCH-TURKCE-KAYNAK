# 📋 Cheatsheets - Hızlı Referans

Bu bölümde tüm teknolojiler için en sık kullanılan komutları, konfigürasyonları ve API'leri hızlı referans olarak bulacaksınız.

## 🌊 Kafka Cheatsheet

### 🔧 Temel Komutlar

```bash
# Topic oluşturma
kafka-topics.sh --create --topic orders --partitions 3 --replication-factor 2 --bootstrap-server localhost:9092

# Topic listeleme
kafka-topics.sh --list --bootstrap-server localhost:9092

# Topic detayları
kafka-topics.sh --describe --topic orders --bootstrap-server localhost:9092

# Consumer group listeleme
kafka-consumer-groups.sh --list --bootstrap-server localhost:9092

# Consumer group detayları
kafka-consumer-groups.sh --describe --group my-group --bootstrap-server localhost:9092

# Consumer lag kontrol
kafka-consumer-groups.sh --describe --group my-group --bootstrap-server localhost:9092 --members --verbose

# Topic silme
kafka-topics.sh --delete --topic orders --bootstrap-server localhost:9092
```

### 🚀 Producer Komutları

```bash
# Console producer
kafka-console-producer.sh --topic orders --bootstrap-server localhost:9092

# Key-value producer
kafka-console-producer.sh --topic orders --bootstrap-server localhost:9092 --property "key.separator=:" --property "parse.key=true"

# Avro producer
kafka-avro-console-producer --topic orders --bootstrap-server localhost:9092 --property schema.registry.url=http://localhost:8081 --property value.schema='{"type":"record","name":"Order","fields":[{"name":"id","type":"string"}]}'
```

### 📨 Consumer Komutları

```bash
# Console consumer
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092 --from-beginning

# Consumer group ile
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092 --group my-group

# Key-value consumer
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092 --property print.key=true --property key.separator=":"

# Latest messages
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092 --max-messages 10
```

### ⚙️ Kafka Configuration

```properties
# Server (broker) konfigürasyonu
broker.id=1
listeners=PLAINTEXT://localhost:9092
log.dirs=/kafka-logs
num.network.threads=8
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
num.partitions=3
default.replication.factor=2
min.insync.replicas=1
unclean.leader.election.enable=false
auto.create.topics.enable=false

# Producer optimizasyonu
acks=all
batch.size=16384
linger.ms=5
buffer.memory=33554432
compression.type=snappy
retries=2147483647
enable.idempotence=true

# Consumer optimizasyonu
fetch.min.bytes=1
fetch.max.wait.ms=500
max.partition.fetch.bytes=1048576
enable.auto.commit=true
auto.commit.interval.ms=5000
session.timeout.ms=30000
heartbeat.interval.ms=3000
```

### 🐍 Python Kafka API

```python
# Producer
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    acks='all',
    retries=3,
    batch_size=16384,
    linger_ms=5,
    compression_type='snappy'
)

# Mesaj gönderme
producer.send('orders', {'order_id': '123', 'amount': 99.99})
producer.flush()

# Consumer
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=['localhost:9092'],
    group_id='my-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    consumer_timeout_ms=1000
)

for message in consumer:
    print(f"Topic: {message.topic}, Partition: {message.partition}, Offset: {message.offset}")
    print(f"Value: {message.value}")
```

---

## 🐰 RabbitMQ Cheatsheet

### 🔧 Management Commands

```bash
# Management plugin aktifleştir
rabbitmq-plugins enable rabbitmq_management

# User oluşturma
rabbitmqctl add_user admin admin123
rabbitmqctl set_user_tags admin administrator
rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

# Virtual host oluşturma
rabbitmqctl add_vhost /production
rabbitmqctl set_permissions -p /production admin ".*" ".*" ".*"

# Queue listeleme
rabbitmqctl list_queues name messages consumers

# Exchange listeleme
rabbitmqctl list_exchanges name type

# Binding listeleme
rabbitmqctl list_bindings

# Connection listeleme
rabbitmqctl list_connections name peer_host peer_port state

# Node status
rabbitmqctl node_health_check
rabbitmqctl status
```

### 🔄 Queue Operations

```bash
# Purge queue
rabbitmqctl purge_queue payment_queue

# Delete queue
rabbitmqctl delete_queue temp_queue

# Queue info
rabbitmqctl list_queue_info payment_queue messages consumers memory
```

### 🐍 Python RabbitMQ API

```python
import pika
import json

# Connection
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        port=5672,
        virtual_host='/',
        credentials=pika.PlainCredentials('admin', 'admin123')
    )
)
channel = connection.channel()

# Direct Exchange Producer
channel.exchange_declare(exchange='direct_logs', exchange_type='direct', durable=True)
channel.queue_declare(queue='payment_queue', durable=True)
channel.queue_bind(exchange='direct_logs', queue='payment_queue', routing_key='payment')

message = json.dumps({'order_id': '123', 'amount': 99.99})
channel.basic_publish(
    exchange='direct_logs',
    routing_key='payment',
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=2,  # make message persistent
        content_type='application/json'
    )
)

# Consumer
def callback(ch, method, properties, body):
    data = json.loads(body)
    print(f"Received: {data}")
    # İşlem başarılı ise
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='payment_queue', on_message_callback=callback)
channel.start_consuming()
```

### 📊 Exchange Types Summary

```bash
# Direct Exchange - Exact routing key match
routing_key="payment.created" → Queue with binding "payment.created"

# Topic Exchange - Pattern matching
routing_key="user.profile.updated" → Queue with binding "user.#" or "user.profile.*"

# Fanout Exchange - Broadcast
routing_key=ignored → All bound queues

# Headers Exchange - Header matching
headers={"type": "payment", "urgent": true} → Queue with matching headers
```

---

## 🔴 Redis Cheatsheet

### 🔧 Temel Komutlar

```bash
# Connection
redis-cli -h localhost -p 6379 -a password

# Database selection
SELECT 1

# Key operations
KEYS pattern      # List keys (avoid in production)
EXISTS key        # Check if key exists
TYPE key          # Get key type
TTL key           # Get time to live
EXPIRE key 3600   # Set expiration
DEL key           # Delete key
FLUSHDB           # Clear current database
FLUSHALL          # Clear all databases

# Server info
INFO              # Server information
CONFIG GET *      # Configuration
CLIENT LIST       # Connected clients
MONITOR           # Monitor commands (debug only)
```

### 📊 Data Types Operations

```bash
# Strings
SET key value
GET key
INCR counter
DECR counter
INCRBY counter 5
APPEND key " additional"
MSET key1 val1 key2 val2
MGET key1 key2

# Hashes
HSET user:123 name "John" age 30
HGET user:123 name
HGETALL user:123
HINCRBY user:123 age 1
HDEL user:123 age

# Lists
LPUSH mylist item1 item2
RPUSH mylist item3
LPOP mylist
RPOP mylist
LRANGE mylist 0 -1
LLEN mylist

# Sets
SADD myset member1 member2
SMEMBERS myset
SISMEMBER myset member1
SCARD myset
SINTER set1 set2
SUNION set1 set2

# Sorted Sets
ZADD leaderboard 100 "player1" 200 "player2"
ZRANGE leaderboard 0 -1 WITHSCORES
ZRANK leaderboard "player1"
ZCOUNT leaderboard 100 200
```

### 📡 Pub/Sub Commands

```bash
# Publisher
PUBLISH channel message

# Subscriber
SUBSCRIBE channel1 channel2
PSUBSCRIBE pattern*
UNSUBSCRIBE channel1
PUNSUBSCRIBE pattern*

# Channel info
PUBSUB CHANNELS
PUBSUB NUMSUB channel
PUBSUB NUMPAT
```

### 🔄 Transactions

```bash
# Basic transaction
MULTI
SET key1 value1
SET key2 value2
EXEC

# With watch (optimistic locking)
WATCH mykey
val = GET mykey
MULTI
SET mykey (val + 1)
EXEC
```

### 🌊 Streams

```bash
# Add to stream
XADD events * type "order" id "123" amount 99.99

# Read from stream
XREAD STREAMS events 0
XREAD COUNT 2 STREAMS events $

# Consumer groups
XGROUP CREATE events mygroup $ MKSTREAM
XREADGROUP GROUP mygroup consumer1 STREAMS events >
XACK events mygroup message_id
```

### 🐍 Python Redis API

```python
import redis
import json

# Connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Basic operations
r.set('user:123', json.dumps({'name': 'John', 'age': 30}))
user = json.loads(r.get('user:123'))

# Hash operations
r.hset('user:124', mapping={'name': 'Jane', 'age': 25})
r.hget('user:124', 'name')

# Pub/Sub
pubsub = r.pubsub()
pubsub.subscribe('notifications')

# Publisher
r.publish('notifications', json.dumps({'type': 'order', 'message': 'Order completed'}))

# Transaction
pipe = r.pipeline()
pipe.multi()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.execute()
```

---

## 🔍 Elasticsearch Cheatsheet

### 🔧 Cluster Management

```bash
# Cluster health
GET /_cluster/health

# Node info
GET /_nodes

# Index list
GET /_cat/indices?v

# Allocation explain
GET /_cluster/allocation/explain

# Settings
GET /_cluster/settings
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}
```

### 📝 Index Operations

```bash
# Create index
PUT /products
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "title": {"type": "text", "analyzer": "standard"},
      "price": {"type": "double"},
      "category": {"type": "keyword"},
      "created_at": {"type": "date"}
    }
  }
}

# Delete index
DELETE /products

# Open/Close index
POST /products/_close
POST /products/_open

# Index settings
GET /products/_settings
PUT /products/_settings
{
  "number_of_replicas": 2
}

# Index mapping
GET /products/_mapping
PUT /products/_mapping
{
  "properties": {
    "description": {"type": "text"}
  }
}
```

### 📄 Document Operations

```bash
# Index document
PUT /products/_doc/1
{
  "title": "iPhone 13",
  "price": 999.99,
  "category": "electronics",
  "created_at": "2024-01-01T10:00:00Z"
}

# Get document
GET /products/_doc/1

# Update document
POST /products/_update/1
{
  "doc": {
    "price": 899.99
  }
}

# Delete document
DELETE /products/_doc/1

# Bulk operations
POST /_bulk
{"index": {"_index": "products", "_id": "1"}}
{"title": "iPhone 13", "price": 999.99}
{"index": {"_index": "products", "_id": "2"}}
{"title": "Samsung Galaxy", "price": 799.99}
```

### 🔍 Search Queries

```bash
# Simple search
GET /products/_search
{
  "query": {
    "match": {
      "title": "iPhone"
    }
  }
}

# Bool query
GET /products/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"title": "iPhone"}},
        {"range": {"price": {"gte": 500, "lte": 1000}}}
      ],
      "filter": [
        {"term": {"category": "electronics"}}
      ]
    }
  }
}

# Aggregations
GET /products/_search
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {
        "field": "category",
        "size": 10
      }
    },
    "avg_price": {
      "avg": {
        "field": "price"
      }
    }
  }
}

# Sorting
GET /products/_search
{
  "query": {"match_all": {}},
  "sort": [
    {"price": {"order": "desc"}},
    {"created_at": {"order": "desc"}}
  ]
}
```

### 🐍 Python Elasticsearch API

```python
from elasticsearch import Elasticsearch
import json

# Connection
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

# Index document
doc = {
    'title': 'iPhone 13',
    'price': 999.99,
    'category': 'electronics',
    'created_at': '2024-01-01T10:00:00Z'
}
es.index(index='products', id=1, body=doc)

# Search
search_body = {
    'query': {
        'bool': {
            'must': [
                {'match': {'title': 'iPhone'}},
                {'range': {'price': {'gte': 500, 'lte': 1000}}}
            ]
        }
    }
}
result = es.search(index='products', body=search_body)

# Bulk operations
from elasticsearch.helpers import bulk

actions = [
    {
        '_index': 'products',
        '_id': i,
        '_source': {
            'title': f'Product {i}',
            'price': i * 10.99,
            'category': 'electronics'
        }
    }
    for i in range(1, 1001)
]

bulk(es, actions)
```

---

## 🐳 Docker Compose Hızlı Başlangıç

### 🚀 Tüm Servisleri Başlatma

```bash
# Tüm servisleri background'da başlat
docker-compose up -d

# Sadece belirli servisleri başlat
docker-compose up -d kafka redis

# Servisleri durdur
docker-compose down

# Volumes ile birlikte durdur (data silinir)
docker-compose down -v

# Logları görüntüle
docker-compose logs -f kafka
```

### 📊 Servis Status

```bash
# Çalışan servisleri görüntüle
docker-compose ps

# Servis resource kullanımı
docker-compose top

# Servis restart
docker-compose restart kafka
```

---

## 🛠️ Common Configuration Patterns

### ⚡ Performance Tuning

```yaml
# Kafka Production Config
kafka:
  environment:
    KAFKA_HEAP_OPTS: "-Xmx2G -Xms2G"
    KAFKA_LOG_RETENTION_HOURS: 168
    KAFKA_LOG_SEGMENT_BYTES: 1073741824
    KAFKA_NUM_PARTITIONS: 3
    KAFKA_DEFAULT_REPLICATION_FACTOR: 3
    KAFKA_MIN_INSYNC_REPLICAS: 2

# Redis Production Config
redis:
  sysctls:
    - net.core.somaxconn=65535
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

# Elasticsearch Production Config
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    - discovery.type=single-node
    - bootstrap.memory_lock=true
  ulimits:
    memlock:
      soft: -1
      hard: -1
```

### 🔐 Security Configuration

```yaml
# RabbitMQ Security
rabbitmq:
  environment:
    RABBITMQ_DEFAULT_USER: admin
    RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    RABBITMQ_SSL_CERTFILE: /etc/rabbitmq/ssl/cert.pem
    RABBITMQ_SSL_KEYFILE: /etc/rabbitmq/ssl/key.pem

# Elasticsearch Security
elasticsearch:
  environment:
    - xpack.security.enabled=true
    - xpack.security.transport.ssl.enabled=true
```

---

## 📈 Monitoring Commands

### 📊 Health Checks

```bash
# Kafka health
kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# RabbitMQ health
curl -u admin:admin123 http://localhost:15672/api/healthchecks/node

# Redis health
redis-cli ping

# Elasticsearch health
curl http://localhost:9200/_cluster/health
```

### 📉 Performance Metrics

```bash
# Kafka JMX metrics
jconsole localhost:9999

# RabbitMQ metrics
curl -u admin:admin123 http://localhost:15672/api/overview

# Redis INFO
redis-cli info stats

# Elasticsearch metrics
curl http://localhost:9200/_nodes/stats
```

---

**💡 İpucu**: Bu cheatsheet'i yazırken terminalde açık tutarak hızlı referans olarak kullanabilirsiniz!
