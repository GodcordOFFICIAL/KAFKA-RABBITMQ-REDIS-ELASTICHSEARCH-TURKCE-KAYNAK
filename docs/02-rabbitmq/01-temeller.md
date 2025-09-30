# RabbitMQ Temelleri ve Kurulum

## 📋 İçindekiler

1. [RabbitMQ Nedir?](#rabbitmq-nedir)
2. [Temel Kavramlar](#temel-kavramlar)
3. [Kurulum ve Yapılandırma](#kurulum-ve-yapılandırma)
4. [İlk Mesajlaşma Örneği](#ilk-mesajlaşma-örneği)
5. [Management UI](#management-ui)
6. [Hands-on Lab](#hands-on-lab)

## 🐰 RabbitMQ Nedir?

RabbitMQ, **AMQP (Advanced Message Queuing Protocol)** protokolünü kullanan, açık kaynaklı bir **message broker**'dır. Erlang programlama dili ile geliştirilmiş olup, yüksek performans ve güvenilirlik sağlar.

### Kafka vs RabbitMQ - Temel Farklar

| Özellik            | Kafka                 | RabbitMQ          |
| ------------------ | --------------------- | ----------------- |
| **Protokol**       | Kendi protokolü       | AMQP, MQTT, STOMP |
| **Mesaj Modeli**   | Pub/Sub (Log-based)   | Queue + Exchange  |
| **Performans**     | Çok yüksek throughput | Düşük latency     |
| **Kullanım Alanı** | Event Streaming       | Klasik mesajlaşma |
| **Mesaj Sırası**   | Partition bazında     | Queue bazında     |
| **Routing**        | Topic patterns        | Flexible routing  |

### Ne Zaman RabbitMQ Kullanmalı?

✅ **RabbitMQ İdeal Durumlar:**

- Request/Response pattern'leri
- Complex routing gereksinimleri
- Düşük latency önemli
- Reliable delivery gerekli
- Micro-services arası communication

✅ **Kafka İdeal Durumlar:**

- Event sourcing
- Log aggregation
- Real-time analytics
- High throughput stream processing

## 🧩 Temel Kavramlar

### 1. Message Flow

```
Producer → Exchange → Queue → Consumer
```

### 2. Temel Bileşenler

#### **Producer (Üretici)**

Mesaj gönderen uygulama:

```python
# Python Producer Örneği
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Queue declare et
channel.queue_declare(queue='hello')

# Mesaj gönder
channel.basic_publish(exchange='',
                      routing_key='hello',
                      body='Hello World!')

connection.close()
```

#### **Exchange (Değişim)**

Mesajları queue'lara yönlendiren router:

**Exchange Types:**

1. **Direct** - Exact routing key match
2. **Topic** - Pattern-based routing
3. **Fanout** - Tüm queue'lara broadcast
4. **Headers** - Header-based routing

#### **Queue (Kuyruk)**

Mesajların saklandığı buffer:

```bash
# Queue properties
- Durable: Server restart'ta kalıcı
- Exclusive: Sadece bir connection
- Auto-delete: Consumer yokken silinir
```

#### **Consumer (Tüketici)**

Mesaj alan uygulama:

```python
# Python Consumer Örneği
def callback(ch, method, properties, body):
    print(f"Received: {body}")

channel.basic_consume(queue='hello',
                      on_message_callback=callback,
                      auto_ack=True)

channel.start_consuming()
```

### 3. Binding

Exchange ile queue arasındaki bağlantı:

```bash
# Direct binding
queue.bind(exchange="direct_logs", routing_key="error")

# Topic binding
queue.bind(exchange="topic_logs", routing_key="*.error")
```

## 🚀 Kurulum ve Yapılandırma

### Docker ile Kurulum

```bash
# 1. RabbitMQ container'ı başlat
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin123 \
  rabbitmq:3.12-management

# 2. Management UI erişimi
# http://localhost:15672 (admin/admin123)

# 3. Health check
docker exec rabbitmq rabbitmq-diagnostics ping
```

### Docker Compose ile Kurulum

```yaml
# deployment/docker-compose/rabbitmq-cluster.yml
version: "3.8"

services:
  rabbitmq:
    image: rabbitmq:3.12-management
    hostname: rabbitmq
    container_name: rabbitmq
    ports:
      - "5672:5672" # AMQP port
      - "15672:15672" # Management UI
      - "15692:15692" # Prometheus metrics
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin123
      RABBITMQ_DEFAULT_VHOST: /
      RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.6
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
      - ./config/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - rabbitmq-network

volumes:
  rabbitmq-data:

networks:
  rabbitmq-network:
    driver: bridge
```

### Konfigürasyon Dosyası

```bash
# config/rabbitmq.conf
# Memory configuration
vm_memory_high_watermark.relative = 0.6
vm_memory_high_watermark_paging_ratio = 0.5

# Disk space configuration
disk_free_limit.relative = 2.0

# Network configuration
listeners.tcp.default = 5672
management.tcp.port = 15672

# Logging
log.file.level = info
log.console = true

# Clustering
cluster_formation.peer_discovery_backend = classic_config
```

## 📨 İlk Mesajlaşma Örneği

### 1. Basit Queue Örneği

**Producer (Gönderen):**

```python
# examples/rabbitmq/python/simple_producer.py
import pika
import sys
import json
from datetime import datetime

def create_connection():
    """RabbitMQ bağlantısı oluştur"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('admin', 'admin123')
            )
        )
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        print(f"❌ Bağlantı hatası: {e}")
        sys.exit(1)

def send_message(message):
    """Mesaj gönder"""
    connection = create_connection()
    channel = connection.channel()

    # Queue declare et (idempotent)
    channel.queue_declare(queue='hello', durable=True)

    # Mesajı JSON formatında hazırla
    message_body = json.dumps({
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'sender': 'simple_producer'
    })

    # Mesaj gönder
    channel.basic_publish(
        exchange='',
        routing_key='hello',
        body=message_body,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Mesajı persistent yap
        )
    )

    print(f"✅ Mesaj gönderildi: {message}")
    connection.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        message = ' '.join(sys.argv[1:])
    else:
        message = "Merhaba RabbitMQ!"

    send_message(message)
```

**Consumer (Alan):**

```python
# examples/rabbitmq/python/simple_consumer.py
import pika
import json
import time
import signal
import sys

class SimpleConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.should_stop = False

        # Graceful shutdown için signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        print("\n🔴 Consumer durduruluyor...")
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        sys.exit(0)

    def create_connection(self):
        """RabbitMQ bağlantısı oluştur"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='localhost',
                    port=5672,
                    credentials=pika.PlainCredentials('admin', 'admin123')
                )
            )
            self.channel = self.connection.channel()

            # Queue declare et
            self.channel.queue_declare(queue='hello', durable=True)

            # QoS ayarı - aynı anda max 1 mesaj işle
            self.channel.basic_qos(prefetch_count=1)

            print("✅ RabbitMQ'ya bağlandı")

        except pika.exceptions.AMQPConnectionError as e:
            print(f"❌ Bağlantı hatası: {e}")
            sys.exit(1)

    def process_message(self, ch, method, properties, body):
        """Mesaj işleme callback'i"""
        try:
            # JSON parse et
            message_data = json.loads(body)

            print(f"📨 Mesaj alındı:")
            print(f"   Content: {message_data.get('message')}")
            print(f"   Timestamp: {message_data.get('timestamp')}")
            print(f"   Sender: {message_data.get('sender')}")

            # Mesaj işleme simülasyonu
            time.sleep(1)

            # Manual ACK
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("✅ Mesaj işlendi ve ACK gönderildi\n")

        except json.JSONDecodeError:
            print(f"❌ JSON decode hatası: {body}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            print(f"❌ Mesaj işleme hatası: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Mesaj tüketmeye başla"""
        self.create_connection()

        # Consumer setup
        self.channel.basic_consume(
            queue='hello',
            on_message_callback=self.process_message,
            auto_ack=False  # Manual ACK kullan
        )

        print("🔄 Mesaj bekleniyor... (Durdurmak için CTRL+C)")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

if __name__ == '__main__':
    consumer = SimpleConsumer()
    consumer.start_consuming()
```

### 2. Test Scripti

```bash
# examples/rabbitmq/scripts/test_basic.sh
#!/bin/bash

echo "🧪 RabbitMQ Temel Test"
echo "====================="

# RabbitMQ sağlık kontrolü
echo "1. RabbitMQ sağlık kontrolü..."
if docker exec rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
    echo "✅ RabbitMQ sağlıklı"
else
    echo "❌ RabbitMQ çalışmıyor"
    exit 1
fi

# Queue bilgilerini göster
echo -e "\n2. Queue durumu:"
docker exec rabbitmq rabbitmqctl list_queues name messages

# Birkaç test mesajı gönder
echo -e "\n3. Test mesajları gönderiliyor..."
cd examples/rabbitmq/python

python simple_producer.py "Test mesajı 1"
python simple_producer.py "Test mesajı 2"
python simple_producer.py "Test mesajı 3"

echo -e "\n4. Queue durumu (mesaj sonrası):"
docker exec rabbitmq rabbitmqctl list_queues name messages

echo -e "\n✅ Test tamamlandı!"
echo "📌 Consumer çalıştırmak için: python simple_consumer.py"
```

## 🎛️ Management UI

RabbitMQ Management UI, cluster'ınızı görsel olarak yönetmenizi sağlar.

### Erişim

```
URL: http://localhost:15672
Username: admin
Password: admin123
```

### Temel Özellikler

#### 1. Overview (Genel Bakış)

- Cluster durumu
- Connection sayısı
- Queue statistics
- Message rates

#### 2. Connections

- Aktif bağlantılar
- Client bilgileri
- Data transfer rates

#### 3. Channels

- Channel listesi
- Message statistics
- Consumer bilgileri

#### 4. Exchanges

- Exchange listesi
- Binding'ler
- Message rates

#### 5. Queues

- Queue listesi
- Message counts
- Consumer bilgileri
- Mesaj tarama

#### 6. Admin

- User management
- Virtual hosts
- Policies
- Cluster configuration

## 🧪 Hands-on Lab: Chat Uygulaması

Gerçek zamanlı chat uygulaması ile RabbitMQ'yu öğrenelim.

### Lab Senaryosu

**Amaç:** Çoklu kullanıcı chat uygulaması geliştirmek

**Gereksinimler:**

- Kullanıcılar mesaj gönderebilir
- Tüm kullanıcılar mesajları alır
- Room'lara göre mesaj filtreleme
- Kullanıcı giriş/çıkış bildirimleri

### 1. Chat Producer

```python
# examples/rabbitmq/python/chat_producer.py
import pika
import json
import sys
from datetime import datetime

class ChatProducer:
    def __init__(self, username):
        self.username = username
        self.connection = self.create_connection()
        self.channel = self.connection.channel()
        self.setup_exchanges()

    def create_connection(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('admin', 'admin123')
            )
        )

    def setup_exchanges(self):
        """Exchange'leri oluştur"""
        # Fanout exchange - tüm kullanıcılara broadcast
        self.channel.exchange_declare(
            exchange='chat_broadcast',
            exchange_type='fanout',
            durable=True
        )

        # Topic exchange - room'lara göre routing
        self.channel.exchange_declare(
            exchange='chat_rooms',
            exchange_type='topic',
            durable=True
        )

    def send_message(self, room, message):
        """Chat mesajı gönder"""
        message_data = {
            'type': 'chat_message',
            'username': self.username,
            'room': room,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        # Room'a göre routing
        routing_key = f"room.{room}"

        self.channel.basic_publish(
            exchange='chat_rooms',
            routing_key=routing_key,
            body=json.dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        print(f"📤 [{room}] {self.username}: {message}")

    def send_notification(self, action):
        """Kullanıcı bildirimi gönder (join/leave)"""
        notification_data = {
            'type': 'user_notification',
            'username': self.username,
            'action': action,  # 'joined' or 'left'
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_broadcast',
            routing_key='',
            body=json.dumps(notification_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        print(f"🔔 {self.username} {action} the chat")

    def close(self):
        self.connection.close()

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python chat_producer.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    producer = ChatProducer(username)

    # Giriş bildirimi
    producer.send_notification('joined')

    print(f"💬 Chat'e hoş geldin {username}!")
    print("📝 Mesaj formatı: <room> <mesaj>")
    print("   Örnek: general Merhaba dünya!")
    print("📌 Çıkmak için 'quit' yaz")

    try:
        while True:
            user_input = input(f"{username}> ").strip()

            if user_input.lower() in ['quit', 'exit']:
                break

            if ' ' in user_input:
                room, message = user_input.split(' ', 1)
                producer.send_message(room, message)
            else:
                print("❌ Format: <room> <mesaj>")

    except KeyboardInterrupt:
        pass

    finally:
        # Çıkış bildirimi
        producer.send_notification('left')
        producer.close()

if __name__ == '__main__':
    main()
```

### 2. Chat Consumer

```python
# examples/rabbitmq/python/chat_consumer.py
import pika
import json
import threading
import signal
import sys
from datetime import datetime

class ChatConsumer:
    def __init__(self, username, rooms):
        self.username = username
        self.rooms = rooms
        self.connection = self.create_connection()
        self.channel = self.connection.channel()
        self.should_stop = False

        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.setup_queues()

    def create_connection(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('admin', 'admin123')
            )
        )

    def setup_queues(self):
        """Queue'ları ve binding'leri oluştur"""
        # Broadcast queue (notifications için)
        broadcast_queue = f"chat_notifications_{self.username}"
        self.channel.queue_declare(
            queue=broadcast_queue,
            exclusive=True,
            auto_delete=True
        )

        self.channel.queue_bind(
            exchange='chat_broadcast',
            queue=broadcast_queue
        )

        # Room queue'ları
        room_queue = f"chat_rooms_{self.username}"
        self.channel.queue_declare(
            queue=room_queue,
            exclusive=True,
            auto_delete=True
        )

        # Her room için binding
        for room in self.rooms:
            self.channel.queue_bind(
                exchange='chat_rooms',
                queue=room_queue,
                routing_key=f"room.{room}"
            )

        # Consumers setup
        self.channel.basic_consume(
            queue=broadcast_queue,
            on_message_callback=self.handle_notification,
            auto_ack=True
        )

        self.channel.basic_consume(
            queue=room_queue,
            on_message_callback=self.handle_chat_message,
            auto_ack=True
        )

    def handle_notification(self, ch, method, properties, body):
        """Kullanıcı bildirimlerini işle"""
        try:
            data = json.loads(body)

            if data['username'] != self.username:  # Kendi bildirimini gösterme
                action_emoji = "👋" if data['action'] == 'joined' else "👋"
                print(f"\n{action_emoji} {data['username']} {data['action']} the chat")

        except Exception as e:
            print(f"❌ Notification error: {e}")

    def handle_chat_message(self, ch, method, properties, body):
        """Chat mesajlarını işle"""
        try:
            data = json.loads(body)

            if data['username'] != self.username:  # Kendi mesajını gösterme
                timestamp = datetime.fromisoformat(data['timestamp'])
                time_str = timestamp.strftime("%H:%M")

                print(f"\n📨 [{data['room']}] {data['username']} ({time_str}): {data['message']}")

        except Exception as e:
            print(f"❌ Message error: {e}")

    def signal_handler(self, signum, frame):
        print(f"\n👋 {self.username} chat'ten ayrılıyor...")
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        sys.exit(0)

    def start_consuming(self):
        """Mesaj dinlemeye başla"""
        print(f"👂 {self.username}, {', '.join(self.rooms)} room'larını dinliyor...")
        print("🔴 Durdurmak için CTRL+C")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def main():
    if len(sys.argv) < 3:
        print("Kullanım: python chat_consumer.py <username> <room1> [room2] [room3]...")
        print("Örnek: python chat_consumer.py alice general tech random")
        sys.exit(1)

    username = sys.argv[1]
    rooms = sys.argv[2:]

    consumer = ChatConsumer(username, rooms)
    consumer.start_consuming()

if __name__ == '__main__':
    main()
```

### 3. Lab Test Scripti

```bash
# examples/rabbitmq/scripts/test_chat.sh
#!/bin/bash

echo "💬 RabbitMQ Chat Lab"
echo "==================="

# Python requirements check
echo "1. Python kütüphanelerini kontrol et..."
cd examples/rabbitmq/python
pip install pika > /dev/null 2>&1

# RabbitMQ sağlık kontrolü
echo "2. RabbitMQ kontrolü..."
if ! docker exec rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
    echo "❌ RabbitMQ çalışmıyor. Önce başlatın:"
    echo "   docker-compose -f deployment/docker-compose/rabbitmq-cluster.yml up -d"
    exit 1
fi

echo "✅ RabbitMQ hazır"

# Exchange'leri oluştur
echo "3. Exchange'leri hazırla..."
docker exec rabbitmq rabbitmqctl eval "
rabbit_exchange:declare({resource, <<\"/\">>, exchange, <<\"chat_broadcast\">>}, fanout, true, false, false, []).
rabbit_exchange:declare({resource, <<\"/\">>, exchange, <<\"chat_rooms\">>}, topic, true, false, false, []).
" > /dev/null 2>&1

echo "✅ Exchange'ler hazır"

# Test senaryosu
echo -e "\n📋 Test Senaryosu:"
echo "1. Terminal 1: python chat_consumer.py alice general tech"
echo "2. Terminal 2: python chat_consumer.py bob general"
echo "3. Terminal 3: python chat_producer.py alice"
echo "4. Terminal 4: python chat_producer.py bob"
echo ""
echo "🎯 Test adımları:"
echo "   - Producer terminallerinde mesaj gönderin"
echo "   - Format: <room> <mesaj>"
echo "   - Örnek: general Merhaba!"
echo "   - Örnek: tech Python öğreniyorum"
echo ""
echo "🔍 Beklenen sonuç:"
echo "   - alice hem general hem tech mesajlarını alır"
echo "   - bob sadece general mesajlarını alır"
echo "   - Join/leave bildirimleri tüm kullanıcılara gider"

echo -e "\n📊 Management UI: http://localhost:15672"
echo "   Exchanges, Queues ve Bindings'leri görüntüleyebilirsiniz"

echo -e "\n✅ Lab hazır! Yukarıdaki terminalleri açın ve test edin."
```

### Lab Çalıştırma

```bash
# 1. RabbitMQ başlat
make start-rabbitmq

# 2. Test scriptini çalıştır
chmod +x examples/rabbitmq/scripts/test_chat.sh
./examples/rabbitmq/scripts/test_chat.sh

# 3. Farklı terminallerde consumer'ları başlat
python examples/rabbitmq/python/chat_consumer.py alice general tech
python examples/rabbitmq/python/chat_consumer.py bob general

# 4. Farklı terminallerde producer'ları başlat
python examples/rabbitmq/python/chat_producer.py alice
python examples/rabbitmq/python/chat_producer.py bob
```

## ✅ Öğrendiklerimiz

Bu bölümde şunları öğrendik:

1. **RabbitMQ Temelleri**

   - Message broker kavramı
   - AMQP protokolü
   - Kafka ile karşılaştırma

2. **Temel Bileşenler**

   - Producer/Consumer
   - Exchange types (Fanout, Topic)
   - Queue'lar ve Binding'ler

3. **Pratik Uygulama**

   - Docker ile kurulum
   - Python ile mesajlaşma
   - Management UI kullanımı

4. **Gerçek Dünya Örneği**
   - Chat uygulaması
   - Multiple exchange pattern
   - Real-time communication

## 📚 Sonraki Adım

Bir sonraki bölümde **RabbitMQ Exchange Patterns** konusunu işleyeceğiz:

- Direct Exchange
- Topic Exchange
- Fanout Exchange
- Headers Exchange
- Dead Letter Queues

---

**🎯 Pratik Görev:** Chat uygulamasını çalıştırın ve farklı room'larda mesajlaşmayı test edin. Management UI'da queue'ları ve exchange'leri inceleyin.
