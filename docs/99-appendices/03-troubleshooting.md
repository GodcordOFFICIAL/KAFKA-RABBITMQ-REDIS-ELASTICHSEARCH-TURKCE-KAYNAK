# 🚨 Troubleshooting - Sorun Giderme Kılavuzu

Bu bölümde Kafka, RabbitMQ, Redis ve Elasticsearch ile çalışırken karşılaşabileceğiniz yaygın problemleri ve çözümlerini bulacaksınız.

## 🌊 Kafka Troubleshooting

### 🔥 Yaygın Hatalar

#### 1. Connection Refused / Can't Connect to Broker

**Hata Mesajı**:

```
org.apache.kafka.common.errors.TimeoutException: Failed to update metadata after 60000 ms.
Connection to node -1 could not be established. Broker may not be available.
```

**Çözüm**:

```bash
# 1. Kafka servisinin çalışıp çalışmadığını kontrol et
docker ps | grep kafka

# 2. Kafka loglarını kontrol et
docker logs kafka1

# 3. Port'un açık olup olmadığını kontrol et
netstat -tuln | grep 9092
# veya
telnet localhost 9092

# 4. Firewall ayarlarını kontrol et
sudo ufw status

# 5. Doğru bootstrap server adresini kullan
# Yanlış: kafka1:9092 (container name)
# Doğru: localhost:9092 (local development)
```

#### 2. Topic Already Exists

**Hata Mesajı**:

```
org.apache.kafka.common.errors.TopicExistsException: Topic 'orders' already exists.
```

**Çözüm**:

```bash
# Topic'in var olup olmadığını kontrol et
kafka-topics.sh --list --bootstrap-server localhost:9092

# Topic detaylarını gör
kafka-topics.sh --describe --topic orders --bootstrap-server localhost:9092

# Topic'i sil (dikkatli ol!)
kafka-topics.sh --delete --topic orders --bootstrap-server localhost:9092

# Var olan topic'e yeni partition ekle
kafka-topics.sh --alter --topic orders --partitions 6 --bootstrap-server localhost:9092
```

#### 3. Consumer Lag Issues

**Problem**: Consumer'lar mesajları yavaş işliyor

**Diagnosis**:

```bash
# Consumer lag'i kontrol et
kafka-consumer-groups.sh --describe --group my-group --bootstrap-server localhost:9092

# Output:
# TOPIC     PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG     CONSUMER-ID     HOST            CLIENT-ID
# orders    0          100             1500            1400    consumer-1      /192.168.1.10   my-app
```

**Çözümler**:

```bash
# 1. Consumer sayısını artır (partition sayısına kadar)
# 2. Batch processing kullan
# 3. Consumer performance'ını optimize et

# Consumer group'u reset et (development only!)
kafka-consumer-groups.sh --reset-offsets --group my-group --topic orders --to-earliest --execute --bootstrap-server localhost:9092
```

#### 4. Disk Space Issues

**Hata Mesajı**:

```
ERROR Error while flushing log for topicName-0 in dir /kafka-logs with offset 1234567
(kafka.log.LogManager)
```

**Çözüm**:

```bash
# Disk kullanımını kontrol et
df -h

# Log retention ayarlarını değiştir
kafka-configs.sh --alter --entity-type topics --entity-name orders \
  --add-config retention.ms=604800000 --bootstrap-server localhost:9092

# Log compaction aktifleştir
kafka-configs.sh --alter --entity-type topics --entity-name orders \
  --add-config cleanup.policy=compact --bootstrap-server localhost:9092

# Eski segment'leri manuel temizle
kafka-log-dirs.sh --bootstrap-server localhost:9092 --describe
```

#### 5. OutOfMemory Errors

**Hata Mesajı**:

```
java.lang.OutOfMemoryError: Java heap space
```

**Çözüm**:

```bash
# Heap size'ı artır
export KAFKA_HEAP_OPTS="-Xmx2G -Xms2G"

# Docker Compose ile
environment:
  KAFKA_HEAP_OPTS: "-Xmx4G -Xms4G"

# Producer batch size'ı optimize et
batch.size=32768
linger.ms=5
buffer.memory=67108864

# Consumer fetch size'ı optimize et
fetch.max.bytes=52428800
max.partition.fetch.bytes=1048576
```

---

## 🐰 RabbitMQ Troubleshooting

### 🔥 Yaygın Hatalar

#### 1. Connection Refused

**Hata Mesajı**:

```
pika.exceptions.AMQPConnectionError: Connection to localhost:5672 failed: [Errno 61] Connection refused
```

**Çözüm**:

```bash
# 1. RabbitMQ servisinin durumunu kontrol et
docker ps | grep rabbitmq
systemctl status rabbitmq-server  # Linux

# 2. RabbitMQ management plugin'ini aktifleştir
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_management

# 3. Port'ları kontrol et
netstat -tuln | grep -E ":5672|:15672"

# 4. Credentials'ı kontrol et
docker exec rabbitmq rabbitmqctl list_users

# 5. Firewall'u kontrol et
sudo ufw allow 5672
sudo ufw allow 15672
```

#### 2. Authentication Failed

**Hata Mesajı**:

```
pika.exceptions.ProbableAuthenticationError: ConnectionClosedByBroker: (403) 'ACCESS_REFUSED'
```

**Çözüm**:

```bash
# Default user credentials kontrol et
echo "Username: admin, Password: admin123"

# Yeni user oluştur
docker exec rabbitmq rabbitmqctl add_user myuser mypassword
docker exec rabbitmq rabbitmqctl set_user_tags myuser administrator
docker exec rabbitmq rabbitmqctl set_permissions -p / myuser ".*" ".*" ".*"

# User listesini gör
docker exec rabbitmq rabbitmqctl list_users

# Permission'ları kontrol et
docker exec rabbitmq rabbitmqctl list_permissions
```

#### 3. Queue Memory Issues

**Problem**: Queue'larda çok fazla mesaj birikmiş

**Diagnosis**:

```bash
# Queue durumunu kontrol et
docker exec rabbitmq rabbitmqctl list_queues name messages consumers memory

# Memory usage
docker exec rabbitmq rabbitmqctl status | grep memory
```

**Çözümler**:

```bash
# 1. Queue'yu purge et (tüm mesajları sil)
docker exec rabbitmq rabbitmqctl purge_queue payment_queue

# 2. Memory threshold ayarla
docker exec rabbitmq rabbitmqctl set_vm_memory_high_watermark 0.6

# 3. Max queue length ayarla
# Python code:
channel.queue_declare(
    queue='payment_queue',
    arguments={'x-max-length': 1000}
)

# 4. Dead letter queue kullan
channel.queue_declare(
    queue='payment_queue',
    arguments={
        'x-message-ttl': 60000,
        'x-dead-letter-exchange': 'dlx'
    }
)
```

#### 4. Consumer Acknowledgment Issues

**Problem**: Mesajlar tekrar tekrar işleniyor

**Çözüm**:

```python
# Doğru ACK kullanımı
def callback(ch, method, properties, body):
    try:
        # Mesajı işle
        process_message(body)

        # Başarılı ise ACK gönder
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")

        # Hata durumunda NACK gönder (requeue=False)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# QoS ayarla
channel.basic_qos(prefetch_count=1)
```

#### 5. Cluster Split-Brain

**Problem**: Cluster node'ları arasında iletişim problemi

**Diagnosis**:

```bash
# Cluster durumunu kontrol et
docker exec rabbitmq rabbitmqctl cluster_status

# Node health
docker exec rabbitmq rabbitmqctl node_health_check
```

**Çözüm**:

```bash
# Node'u cluster'a tekrar join et
docker exec rabbitmq rabbitmqctl stop_app
docker exec rabbitmq rabbitmqctl join_cluster rabbit@rabbitmq1
docker exec rabbitmq rabbitmqctl start_app

# Cluster'ı reset et (son çare)
docker exec rabbitmq rabbitmqctl stop_app
docker exec rabbitmq rabbitmqctl reset
docker exec rabbitmq rabbitmqctl start_app
```

---

## 🔴 Redis Troubleshooting

### 🔥 Yaygın Hatalar

#### 1. Connection Refused

**Hata Mesajı**:

```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

**Çözüm**:

```bash
# 1. Redis servisinin durumunu kontrol et
docker ps | grep redis
systemctl status redis  # Linux

# 2. Redis loglarını kontrol et
docker logs redis

# 3. Port'u kontrol et
netstat -tuln | grep 6379

# 4. Redis configuration kontrol et
docker exec redis redis-cli config get "*"

# 5. Protected mode'u disable et (development only)
docker exec redis redis-cli config set protected-mode no
```

#### 2. Memory Issues

**Hata Mesajı**:

```
OOM command not allowed when used memory > 'maxmemory'
```

**Çözüm**:

```bash
# Memory kullanımını kontrol et
docker exec redis redis-cli info memory

# Memory policy'yi değiştir
docker exec redis redis-cli config set maxmemory-policy allkeys-lru

# Maxmemory limitini artır
docker exec redis redis-cli config set maxmemory 2gb

# Memory'yi temizle
docker exec redis redis-cli flushdb
```

#### 3. Slow Query Issues

**Problem**: Redis komutları yavaş çalışıyor

**Diagnosis**:

```bash
# Slow log'u kontrol et
docker exec redis redis-cli slowlog get 10

# Current operations
docker exec redis redis-cli monitor
```

**Çözümler**:

```bash
# 1. KEYS command yerine SCAN kullan
# Yanlış:
redis-cli KEYS user:*

# Doğru:
redis-cli --scan --pattern "user:*"

# 2. Big data structures'ı böl
# Büyük list yerine birden çok küçük list
# Büyük hash yerine hash of hashes

# 3. Pipeline kullan
redis-cli --pipe < commands.txt
```

#### 4. Persistence Issues

**Problem**: Data kayboluyor

**Çözüm**:

```bash
# RDB snapshot ayarları
docker exec redis redis-cli config get save
docker exec redis redis-cli config set save "300 10"  # 300 saniyede 10 değişiklik

# AOF enable et
docker exec redis redis-cli config set appendonly yes
docker exec redis redis-cli config set appendfsync everysec

# Manuel backup al
docker exec redis redis-cli bgsave

# AOF rewrite
docker exec redis redis-cli bgrewriteaof
```

#### 5. Replication Issues

**Problem**: Master-slave senkronizasyon problemi

**Diagnosis**:

```bash
# Replication info
docker exec redis-master redis-cli info replication
docker exec redis-slave redis-cli info replication

# Replication offset kontrol et
docker exec redis-master redis-cli info replication | grep offset
```

**Çözüm**:

```bash
# Slave'i tekrar sync et
docker exec redis-slave redis-cli slaveof no one
docker exec redis-slave redis-cli slaveof redis-master 6379

# Full resync zorla
docker exec redis-slave redis-cli debug restart
```

---

## 🔍 Elasticsearch Troubleshooting

### 🔥 Yaygın Hatalar

#### 1. Cluster RED/YELLOW Status

**Problem**: Cluster sağlık durumu kötü

**Diagnosis**:

```bash
# Cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Index status
curl -X GET "localhost:9200/_cat/indices?v"

# Shard allocation
curl -X GET "localhost:9200/_cluster/allocation/explain?pretty"
```

**Çözümler**:

```bash
# 1. Unassigned shard'ları reroute et
curl -X POST "localhost:9200/_cluster/reroute?pretty" -H 'Content-Type: application/json' -d'
{
  "commands": [{
    "allocate_empty_primary": {
      "index": "my-index",
      "shard": 0,
      "node": "node-1",
      "accept_data_loss": true
    }
  }]
}'

# 2. Replica sayısını azalt
curl -X PUT "localhost:9200/my-index/_settings?pretty" -H 'Content-Type: application/json' -d'
{
  "number_of_replicas": 0
}'

# 3. Index'i tekrar aç
curl -X POST "localhost:9200/my-index/_open?pretty"
```

#### 2. Memory/Heap Issues

**Hata Mesajı**:

```
java.lang.OutOfMemoryError: Java heap space
```

**Çözüm**:

```bash
# JVM heap ayarları
export ES_JAVA_OPTS="-Xms2g -Xmx2g"

# Docker Compose ile
environment:
  - "ES_JAVA_OPTS=-Xms4g -Xmx4g"

# Memory lock ayarları
ulimit -l unlimited
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
sysctl -p

# Node stats kontrol et
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty"
```

#### 3. Mapping Conflicts

**Hata Mesajı**:

```
mapper_parsing_exception: failed to parse field [price] of type [text] in document
```

**Çözüm**:

```bash
# Current mapping'i kontrol et
curl -X GET "localhost:9200/products/_mapping?pretty"

# Mapping conflict'i düzelt - yeni index oluştur
curl -X PUT "localhost:9200/products_v2?pretty" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "price": {"type": "double"},
      "title": {"type": "text"}
    }
  }
}'

# Reindex data
curl -X POST "localhost:9200/_reindex?pretty" -H 'Content-Type: application/json' -d'
{
  "source": {"index": "products"},
  "dest": {"index": "products_v2"}
}'

# Alias kullan
curl -X POST "localhost:9200/_aliases?pretty" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {"remove": {"index": "products", "alias": "products_alias"}},
    {"add": {"index": "products_v2", "alias": "products_alias"}}
  ]
}'
```

#### 4. Search Performance Issues

**Problem**: Search query'leri yavaş

**Diagnosis**:

```bash
# Search profiling
curl -X GET "localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "profile": true,
  "query": {"match": {"title": "iphone"}}
}'

# Index stats
curl -X GET "localhost:9200/products/_stats?pretty"

# Hot threads
curl -X GET "localhost:9200/_nodes/hot_threads?pretty"
```

**Çözümler**:

```bash
# 1. Index ayarlarını optimize et
curl -X PUT "localhost:9200/products/_settings?pretty" -H 'Content-Type: application/json' -d'
{
  "refresh_interval": "30s",
  "number_of_replicas": 1
}'

# 2. Force merge (segment'leri birleştir)
curl -X POST "localhost:9200/products/_forcemerge?max_num_segments=1&pretty"

# 3. Index'i warm up et
curl -X POST "localhost:9200/products/_warmer/warmer_1?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}}
}'
```

#### 5. Disk Space Issues

**Problem**: Disk dolmuş, write işlemleri blocked

**Diagnosis**:

```bash
# Disk usage
curl -X GET "localhost:9200/_nodes/stats/fs?pretty"

# Allocation settings
curl -X GET "localhost:9200/_cluster/settings?pretty"
```

**Çözüm**:

```bash
# Read-only restriction'ı kaldır
curl -X PUT "localhost:9200/_cluster/settings?pretty" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.disk.threshold_enabled": false
  }
}'

curl -X PUT "localhost:9200/*/_settings?pretty" -H 'Content-Type: application/json' -d'
{
  "index.blocks.read_only_allow_delete": null
}'

# Eski index'leri sil
curl -X DELETE "localhost:9200/old-logs-2023*?pretty"

# Index lifecycle management kullan
curl -X PUT "localhost:9200/_ilm/policy/delete_after_30d?pretty" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'
```

---

## 🐳 Docker Troubleshooting

### 🔥 Yaygın Docker Problemleri

#### 1. Container Won't Start

**Diagnosis**:

```bash
# Container status
docker ps -a

# Container logs
docker logs container_name

# Resource usage
docker stats
```

**Çözümler**:

```bash
# 1. Port conflict
netstat -tuln | grep 9092
# Farklı port kullan veya çakışan process'i durdur

# 2. Memory issues
docker system prune
docker volume prune

# 3. Permission issues
sudo chown -R 1000:1000 ./data/
```

#### 2. Network Issues

**Problem**: Container'lar birbirine bağlanamıyor

**Çözüm**:

```bash
# Network listesi
docker network ls

# Network inspect
docker network inspect bridge

# Custom network oluştur
docker network create my-network

# Container'ı network'e bağla
docker run --network my-network kafka
```

#### 3. Volume Issues

**Problem**: Data persist etmiyor

**Çözüm**:

```bash
# Volume listesi
docker volume ls

# Volume inspect
docker volume inspect kafka_data

# Volume'u temizle
docker volume rm kafka_data

# Correct volume mounting
docker run -v kafka_data:/kafka-logs kafka
```

---

## 🔧 Diagnostic Commands Summary

### 🚀 Quick Health Checks

```bash
# Kafka
kafka-broker-api-versions.sh --bootstrap-server localhost:9092 &> /dev/null && echo "✅ Kafka OK" || echo "❌ Kafka FAIL"

# RabbitMQ
curl -s -u admin:admin123 http://localhost:15672/api/healthchecks/node &> /dev/null && echo "✅ RabbitMQ OK" || echo "❌ RabbitMQ FAIL"

# Redis
redis-cli ping &> /dev/null && echo "✅ Redis OK" || echo "❌ Redis FAIL"

# Elasticsearch
curl -s http://localhost:9200/_cluster/health &> /dev/null && echo "✅ Elasticsearch OK" || echo "❌ Elasticsearch FAIL"
```

### 📊 Performance Monitoring

```bash
# System resources
htop
iotop
nethogs

# Docker stats
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Port listening
netstat -tuln | grep -E ":9092|:5672|:6379|:9200"
```

---

## 📞 Getting Help

### 📚 Official Documentation

- **Kafka**: https://kafka.apache.org/documentation/
- **RabbitMQ**: https://www.rabbitmq.com/documentation.html
- **Redis**: https://redis.io/documentation
- **Elasticsearch**: https://www.elastic.co/guide/

### 🔍 Debug Tools

```bash
# Network debugging
tcpdump -i any port 9092
wireshark

# JVM debugging
jstack <pid>
jmap -dump:format=b,file=heap.hprof <pid>

# Log analysis
tail -f /var/log/kafka/server.log | grep ERROR
journalctl -u elasticsearch -f
```

### 🆘 Emergency Commands

```bash
# Kill all related processes
pkill -f kafka
pkill -f rabbitmq
pkill -f redis
pkill -f elasticsearch

# Clean everything (DANGEROUS!)
docker system prune -a --volumes
rm -rf ./data/*

# Quick restart
docker-compose down && docker-compose up -d
```

---

**💡 İpucu**: Problemle karşılaştığınızda önce diagnostic commands'ları çalıştırın, log'ları kontrol edin, sonra çözümleri deneyin!
