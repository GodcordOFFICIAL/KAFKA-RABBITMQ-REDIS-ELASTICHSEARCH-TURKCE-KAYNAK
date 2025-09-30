# RabbitMQ İleri Düzey Özellikler

Bu bölüm RabbitMQ'nun production ortamlarında kullanılan ileri düzey özelliklerini kapsamaktadır.

## 📋 İçindekiler

1. [Dead Letter Queues (DLQ)](#dead-letter-queues-dlq)
2. [Message TTL (Time To Live)](#message-ttl-time-to-live)
3. [Queue Priority](#queue-priority)
4. [Publisher Confirms](#publisher-confirms)
5. [Transactions](#transactions)
6. [Message Persistence](#message-persistence)
7. [Flow Control](#flow-control)
8. [Quorum Queues](#quorum-queues)

---

## Dead Letter Queues (DLQ)

Dead Letter Queues, işlenemeyen mesajların gönderildiği özel queue'lardır.

### 🎯 Kullanım Senaryoları

- **Message Processing Failures**: İşleme sırasında hata alan mesajlar
- **TTL Expiration**: Süresi dolan mesajlar
- **Queue Overflow**: Queue kapasitesi aşan mesajlar
- **Reject/Nack**: Consumer tarafından reddedilen mesajlar

### 🔧 DLQ Konfigürasyonu

```python
import pika
import json
from datetime import datetime

def setup_dlq_system():
    """DLQ sistemi kurar"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    # Main exchange
    channel.exchange_declare(
        exchange='order_processing',
        exchange_type='direct',
        durable=True
    )

    # Dead Letter Exchange
    channel.exchange_declare(
        exchange='order_processing_dlx',
        exchange_type='direct',
        durable=True
    )

    # Main queue with DLQ configuration
    channel.queue_declare(
        queue='orders',
        durable=True,
        arguments={
            'x-dead-letter-exchange': 'order_processing_dlx',
            'x-dead-letter-routing-key': 'failed_orders',
            'x-message-ttl': 300000,  # 5 dakika TTL
            'x-max-retries': 3
        }
    )

    # Dead Letter Queue
    channel.queue_declare(
        queue='failed_orders',
        durable=True
    )

    # Bindings
    channel.queue_bind(
        exchange='order_processing',
        queue='orders',
        routing_key='new_order'
    )

    channel.queue_bind(
        exchange='order_processing_dlx',
        queue='failed_orders',
        routing_key='failed_orders'
    )

    connection.close()
    print("✅ DLQ sistemi kuruldu")

if __name__ == "__main__":
    setup_dlq_system()
```

### 📤 DLQ Producer

```python
import pika
import json
import uuid
from datetime import datetime

class DLQProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()

    def send_order(self, order_data, simulate_failure=False):
        """Sipariş gönderir"""
        order = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'simulate_failure': simulate_failure,
            **order_data
        }

        # Message properties
        properties = pika.BasicProperties(
            message_id=order['id'],
            timestamp=int(datetime.now().timestamp()),
            headers={
                'retry_count': 0,
                'original_timestamp': order['timestamp']
            },
            delivery_mode=2  # Persistent
        )

        self.channel.basic_publish(
            exchange='order_processing',
            routing_key='new_order',
            body=json.dumps(order, indent=2),
            properties=properties
        )

        status = "❌ FAIL SIM" if simulate_failure else "✅ SENT"
        print(f"{status} Order gönderildi: {order['id'][:8]}")

    def send_batch_orders(self):
        """Batch sipariş gönderir"""
        orders = [
            {'product': 'Laptop', 'quantity': 1, 'price': 1500.00},
            {'product': 'Mouse', 'quantity': 2, 'price': 25.50},
            {'product': 'Keyboard', 'quantity': 1, 'price': 75.00, 'invalid_field': True},  # Bu fail olacak
            {'product': 'Monitor', 'quantity': 1, 'price': 300.00}
        ]

        for i, order in enumerate(orders):
            simulate_failure = 'invalid_field' in order
            self.send_order(order, simulate_failure)

        print(f"\n📦 {len(orders)} sipariş gönderildi")

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    producer = DLQProducer()

    try:
        print("🚀 DLQ Producer başlatılıyor...")
        producer.send_batch_orders()
    finally:
        producer.close()
```

### 📥 DLQ Consumer

```python
import pika
import json
import time
import random
from datetime import datetime

class DLQConsumer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.processed_count = 0
        self.failed_count = 0

    def process_order(self, channel, method, properties, body):
        """Sipariş işler"""
        try:
            order = json.loads(body)
            order_id = order.get('id', 'Unknown')[:8]

            # Retry count kontrolü
            retry_count = properties.headers.get('retry_count', 0) if properties.headers else 0

            print(f"\n📦 Sipariş işleniyor: {order_id} (retry: {retry_count})")
            print(f"   Product: {order.get('product')}")
            print(f"   Quantity: {order.get('quantity')}")
            print(f"   Price: ${order.get('price')}")

            # Simulated processing time
            time.sleep(random.uniform(0.5, 2.0))

            # Failure simulation
            if order.get('simulate_failure') or 'invalid_field' in order:
                raise ValueError("Simulated processing failure")

            # Random failure (10% chance)
            if random.random() < 0.1:
                raise Exception("Random processing error")

            # Success
            self.processed_count += 1
            print(f"✅ Sipariş başarıyla işlendi: {order_id}")

            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            self.failed_count += 1
            print(f"❌ Sipariş işleme hatası: {order_id} - {str(e)}")

            # Retry logic
            if retry_count < 3:
                # Update retry count and reject for retry
                new_headers = properties.headers.copy() if properties.headers else {}
                new_headers['retry_count'] = retry_count + 1
                new_headers['last_error'] = str(e)
                new_headers['failed_at'] = datetime.now().isoformat()

                # Requeue with updated headers
                channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                print(f"🔄 Mesaj requeue edildi (retry {retry_count + 1}/3)")
            else:
                # Send to DLQ
                channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                print(f"💀 Mesaj DLQ'ya gönderildi (max retry aşıldı)")

    def start_consuming(self):
        """Consumer'ı başlatır"""
        print("🎧 Order Consumer başlatılıyor...")
        print("📋 Çıkış için Ctrl+C")

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='orders',
            on_message_callback=self.process_order
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print(f"\n🛑 Consumer durduruluyor...")
            print(f"📊 İstatistikler:")
            print(f"   Başarılı: {self.processed_count}")
            print(f"   Başarısız: {self.failed_count}")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    consumer = DLQConsumer()
    consumer.start_consuming()
```

### 🩺 DLQ Monitor

```python
import pika
import json
from datetime import datetime

class DLQMonitor:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()

    def process_failed_message(self, channel, method, properties, body):
        """Failed mesajları işler"""
        try:
            order = json.loads(body)
            order_id = order.get('id', 'Unknown')[:8]

            headers = properties.headers or {}
            retry_count = headers.get('retry_count', 0)
            last_error = headers.get('last_error', 'Unknown error')
            failed_at = headers.get('failed_at', 'Unknown time')

            print(f"\n💀 DLQ Mesajı:")
            print(f"   Order ID: {order_id}")
            print(f"   Product: {order.get('product')}")
            print(f"   Retry Count: {retry_count}")
            print(f"   Last Error: {last_error}")
            print(f"   Failed At: {failed_at}")
            print(f"   Original Time: {headers.get('original_timestamp', 'Unknown')}")

            # Manual recovery options
            print(f"\n🔧 Recovery Options:")
            print(f"   1. Manual fix and reprocess")
            print(f"   2. Log and archive")
            print(f"   3. Send to human review")

            # For demo, we'll just acknowledge
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"❌ DLQ işleme hatası: {str(e)}")
            channel.basic_ack(delivery_tag=method.delivery_tag)

    def start_monitoring(self):
        """DLQ monitoring başlatır"""
        print("👁️ DLQ Monitor başlatılıyor...")
        print("📋 Failed mesajları izleniyor...")

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='failed_orders',
            on_message_callback=self.process_failed_message
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print(f"\n🛑 DLQ Monitor durduruluyor...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    monitor = DLQMonitor()
    monitor.start_monitoring()
```

---

## Message TTL (Time To Live)

Message TTL, mesajların ne kadar süre yaşayacağını belirler.

### ⏰ TTL Türleri

1. **Message-level TTL**: Her mesaj için ayrı TTL
2. **Queue-level TTL**: Queue'daki tüm mesajlar için TTL
3. **Queue TTL**: Queue'un kendisi için TTL

### 🔧 TTL Konfigürasyonu

```python
import pika
import json
from datetime import datetime, timedelta

class TTLProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.setup_ttl_system()

    def setup_ttl_system(self):
        """TTL sistemini kurar"""
        # Exchange
        self.channel.exchange_declare(
            exchange='ttl_demo',
            exchange_type='direct',
            durable=True
        )

        # Queue with TTL (30 seconds)
        self.channel.queue_declare(
            queue='short_lived_messages',
            durable=True,
            arguments={
                'x-message-ttl': 30000,  # 30 saniye
                'x-dead-letter-exchange': 'ttl_demo_dlx'
            }
        )

        # Queue without TTL
        self.channel.queue_declare(
            queue='normal_messages',
            durable=True
        )

        # DLX for expired messages
        self.channel.exchange_declare(
            exchange='ttl_demo_dlx',
            exchange_type='direct',
            durable=True
        )

        self.channel.queue_declare(
            queue='expired_messages',
            durable=True
        )

        # Bindings
        self.channel.queue_bind(
            exchange='ttl_demo',
            queue='short_lived_messages',
            routing_key='short'
        )

        self.channel.queue_bind(
            exchange='ttl_demo',
            queue='normal_messages',
            routing_key='normal'
        )

        self.channel.queue_bind(
            exchange='ttl_demo_dlx',
            queue='expired_messages',
            routing_key='short'
        )

    def send_message_with_ttl(self, message, ttl_seconds=None, routing_key='normal'):
        """TTL'li mesaj gönderir"""
        message_data = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'ttl_seconds': ttl_seconds
        }

        properties = pika.BasicProperties(
            delivery_mode=2,
            timestamp=int(datetime.now().timestamp())
        )

        # Message-level TTL
        if ttl_seconds:
            properties.expiration = str(ttl_seconds * 1000)  # Milliseconds

        self.channel.basic_publish(
            exchange='ttl_demo',
            routing_key=routing_key,
            body=json.dumps(message_data, indent=2),
            properties=properties
        )

        ttl_info = f"TTL: {ttl_seconds}s" if ttl_seconds else "Queue TTL"
        print(f"📤 Mesaj gönderildi: {message[:30]}... ({ttl_info})")

    def demo_ttl_scenarios(self):
        """TTL senaryolarını gösterir"""
        print("🕐 TTL Demo Senaryoları:")

        # 1. Queue TTL (30 seconds)
        self.send_message_with_ttl(
            "Bu mesaj queue TTL ile 30 saniye yaşayacak",
            routing_key='short'
        )

        # 2. Message TTL (10 seconds)
        self.send_message_with_ttl(
            "Bu mesaj 10 saniye yaşayacak",
            ttl_seconds=10,
            routing_key='normal'
        )

        # 3. Message TTL (60 seconds)
        self.send_message_with_ttl(
            "Bu mesaj 60 saniye yaşayacak",
            ttl_seconds=60,
            routing_key='normal'
        )

        # 4. No TTL
        self.send_message_with_ttl(
            "Bu mesaj sonsuz yaşayacak",
            routing_key='normal'
        )

        print("\n⏰ Mesajlar gönderildi. TTL süreleri işleniyor...")

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    producer = TTLProducer()

    try:
        producer.demo_ttl_scenarios()
    finally:
        producer.close()
```

---

## Queue Priority

Mesajların öncelik sırasına göre işlenmesini sağlar.

### 🔝 Priority Queue Konfigürasyonu

```python
import pika
import json
from datetime import datetime

class PriorityProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.setup_priority_system()

    def setup_priority_system(self):
        """Priority sistemini kurar"""
        self.channel.exchange_declare(
            exchange='priority_tasks',
            exchange_type='direct',
            durable=True
        )

        # Priority queue (0-10 priority levels)
        self.channel.queue_declare(
            queue='task_queue',
            durable=True,
            arguments={
                'x-max-priority': 10  # 0-10 arası priority
            }
        )

        self.channel.queue_bind(
            exchange='priority_tasks',
            queue='task_queue',
            routing_key='task'
        )

    def send_task(self, task_name, priority=0, task_data=None):
        """Öncelikli task gönderir"""
        task = {
            'name': task_name,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'data': task_data or {}
        }

        properties = pika.BasicProperties(
            priority=priority,
            delivery_mode=2,
            headers={'task_type': task_name}
        )

        self.channel.basic_publish(
            exchange='priority_tasks',
            routing_key='task',
            body=json.dumps(task, indent=2),
            properties=properties
        )

        priority_emoji = "🔴" if priority >= 8 else "🟡" if priority >= 5 else "🟢"
        print(f"{priority_emoji} Task gönderildi: {task_name} (Priority: {priority})")

    def demo_priority_tasks(self):
        """Priority demo gösterir"""
        print("🎯 Priority Task Demo:")

        tasks = [
            ("Normal Email Send", 2),
            ("Critical System Alert", 10),
            ("User Registration", 3),
            ("Emergency Backup", 9),
            ("Daily Report", 1),
            ("Security Incident", 10),
            ("Newsletter", 1),
            ("Payment Processing", 8),
            ("Log Cleanup", 0),
            ("Database Maintenance", 6)
        ]

        # Tasks'ları karışık sırada gönder
        import random
        random.shuffle(tasks)

        for task_name, priority in tasks:
            self.send_task(task_name, priority)

        print(f"\n📊 {len(tasks)} task gönderildi (karışık sırada)")
        print("🎯 Consumer priority sırasına göre işleyecek")

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    producer = PriorityProducer()

    try:
        producer.demo_priority_tasks()
    finally:
        producer.close()
```

### 📥 Priority Consumer

```python
import pika
import json
import time
from datetime import datetime

class PriorityConsumer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.processed_tasks = []

    def process_task(self, channel, method, properties, body):
        """Task'ı işler"""
        try:
            task = json.loads(body)
            task_name = task.get('name')
            priority = task.get('priority', 0)

            priority_emoji = "🔴" if priority >= 8 else "🟡" if priority >= 5 else "🟢"

            print(f"\n{priority_emoji} Task işleniyor:")
            print(f"   Name: {task_name}")
            print(f"   Priority: {priority}")
            print(f"   Timestamp: {task.get('timestamp')}")

            # Process time based on priority
            process_time = max(0.5, 3.0 - (priority * 0.2))
            time.sleep(process_time)

            self.processed_tasks.append({
                'name': task_name,
                'priority': priority,
                'processed_at': datetime.now().isoformat()
            })

            print(f"✅ Task tamamlandı: {task_name}")

            # Show processing order
            if len(self.processed_tasks) <= 3:
                print(f"📊 İşleme sırası: {[t['name'] for t in self.processed_tasks]}")

            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"❌ Task işleme hatası: {str(e)}")
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """Consumer'ı başlatır"""
        print("🎯 Priority Task Consumer başlatılıyor...")
        print("📋 Yüksek öncelikli task'lar önce işlenecek")

        # QoS ayarları
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='task_queue',
            on_message_callback=self.process_task
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print(f"\n🛑 Consumer durduruluyor...")
            print(f"\n📊 İşlenen Task'lar (sırasıyla):")
            for i, task in enumerate(self.processed_tasks, 1):
                priority_emoji = "🔴" if task['priority'] >= 8 else "🟡" if task['priority'] >= 5 else "🟢"
                print(f"   {i:2d}. {priority_emoji} {task['name']} (P:{task['priority']})")

            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    consumer = PriorityConsumer()
    consumer.start_consuming()
```

---

## Publisher Confirms

Mesajların broker tarafından başarıyla alındığını doğrular.

### ✅ Publisher Confirms Implementasyonu

```python
import pika
import json
import time
from datetime import datetime

class ConfirmProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()

        # Publisher confirms'ı aktifleştir
        self.channel.confirm_delivery()

        self.setup_system()
        self.confirmed_count = 0
        self.failed_count = 0

    def setup_system(self):
        """Sistem kurulumu"""
        self.channel.exchange_declare(
            exchange='confirmed_messages',
            exchange_type='direct',
            durable=True
        )

        self.channel.queue_declare(
            queue='important_messages',
            durable=True
        )

        self.channel.queue_bind(
            exchange='confirmed_messages',
            queue='important_messages',
            routing_key='important'
        )

    def send_message_with_confirm(self, message, routing_key='important'):
        """Confirm'lı mesaj gönderir"""
        message_data = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'message_id': f"msg_{int(time.time() * 1000)}"
        }

        properties = pika.BasicProperties(
            delivery_mode=2,  # Persistent
            message_id=message_data['message_id']
        )

        try:
            # Mesajı gönder ve confirm bekle
            result = self.channel.basic_publish(
                exchange='confirmed_messages',
                routing_key=routing_key,
                body=json.dumps(message_data, indent=2),
                properties=properties,
                mandatory=True  # Routing başarısızlığını yakala
            )

            if result:
                self.confirmed_count += 1
                print(f"✅ CONFIRMED: {message[:50]}...")
                return True
            else:
                self.failed_count += 1
                print(f"❌ NOT CONFIRMED: {message[:50]}...")
                return False

        except pika.exceptions.UnroutableError:
            self.failed_count += 1
            print(f"🚫 UNROUTABLE: {message[:50]}...")
            return False
        except Exception as e:
            self.failed_count += 1
            print(f"💥 ERROR: {message[:50]}... - {str(e)}")
            return False

    def send_batch_with_confirms(self):
        """Batch mesaj gönderir"""
        messages = [
            "Critical system alert - Server down",
            "Payment processing completed",
            "User authentication failed",
            "Database backup completed",
            "Security breach detected",
            "Daily report generated",
            "Cache cleared successfully",
            "Email notification sent"
        ]

        print("📤 Publisher Confirms ile batch gönderim:")
        print("=" * 50)

        start_time = time.time()

        for i, message in enumerate(messages, 1):
            print(f"\n📨 {i}/{len(messages)} - ", end="")
            self.send_message_with_confirm(message)

            # Small delay to see individual confirms
            time.sleep(0.1)

        end_time = time.time()

        print("\n" + "=" * 50)
        print(f"📊 Batch Sonuçları:")
        print(f"   ✅ Confirmed: {self.confirmed_count}")
        print(f"   ❌ Failed: {self.failed_count}")
        print(f"   ⏱️ Total Time: {end_time - start_time:.2f}s")
        print(f"   📈 Success Rate: {(self.confirmed_count / len(messages)) * 100:.1f}%")

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    producer = ConfirmProducer()

    try:
        producer.send_batch_with_confirms()
    finally:
        producer.close()
```

---

## Hands-on Lab: Advanced Features

Şimdi tüm advanced features'ları birleştiren bir lab oluşturalım:

### 🧪 Advanced Features Lab

```python
import pika
import json
import time
import threading
from datetime import datetime
from enum import Enum

class MessageType(Enum):
    NORMAL = 1
    PRIORITY = 2
    TTL_SHORT = 3
    TTL_LONG = 4
    DLQ_TEST = 5

class AdvancedFeaturesLab:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.setup_complete_system()

        # Statistics
        self.stats = {
            'sent': 0,
            'confirmed': 0,
            'processed': 0,
            'failed': 0,
            'dlq': 0
        }

    def setup_complete_system(self):
        """Tüm sistemi kurar"""
        print("🔧 Advanced Features Lab kurulumu...")

        # Main exchange
        self.channel.exchange_declare(
            exchange='advanced_lab',
            exchange_type='topic',
            durable=True
        )

        # DLX
        self.channel.exchange_declare(
            exchange='advanced_lab_dlx',
            exchange_type='direct',
            durable=True
        )

        # Normal queue
        self.channel.queue_declare(
            queue='normal_queue',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'advanced_lab_dlx',
                'x-dead-letter-routing-key': 'failed'
            }
        )

        # Priority queue
        self.channel.queue_declare(
            queue='priority_queue',
            durable=True,
            arguments={
                'x-max-priority': 10,
                'x-dead-letter-exchange': 'advanced_lab_dlx',
                'x-dead-letter-routing-key': 'failed'
            }
        )

        # TTL queue
        self.channel.queue_declare(
            queue='ttl_queue',
            durable=True,
            arguments={
                'x-message-ttl': 30000,  # 30 seconds
                'x-dead-letter-exchange': 'advanced_lab_dlx',
                'x-dead-letter-routing-key': 'expired'
            }
        )

        # DLQ
        self.channel.queue_declare(
            queue='failed_messages',
            durable=True
        )

        self.channel.queue_declare(
            queue='expired_messages',
            durable=True
        )

        # Bindings
        bindings = [
            ('advanced_lab', 'normal_queue', 'normal.*'),
            ('advanced_lab', 'priority_queue', 'priority.*'),
            ('advanced_lab', 'ttl_queue', 'ttl.*'),
            ('advanced_lab_dlx', 'failed_messages', 'failed'),
            ('advanced_lab_dlx', 'expired_messages', 'expired')
        ]

        for exchange, queue, routing_key in bindings:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue,
                routing_key=routing_key
            )

        # Publisher confirms
        self.channel.confirm_delivery()

        print("✅ Advanced Features Lab hazır!")

    def send_message(self, msg_type: MessageType, content: str, priority: int = 0, ttl: int = None):
        """Mesaj gönderir"""
        message_data = {
            'type': msg_type.name,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'priority': priority,
            'ttl': ttl
        }

        # Routing key belirleme
        routing_key_map = {
            MessageType.NORMAL: 'normal.message',
            MessageType.PRIORITY: 'priority.message',
            MessageType.TTL_SHORT: 'ttl.short',
            MessageType.TTL_LONG: 'ttl.long',
            MessageType.DLQ_TEST: 'normal.dlq_test'
        }

        routing_key = routing_key_map[msg_type]

        # Properties
        properties = pika.BasicProperties(
            delivery_mode=2,
            priority=priority if msg_type == MessageType.PRIORITY else 0
        )

        if ttl:
            properties.expiration = str(ttl * 1000)

        # Test için failure simulation
        if msg_type == MessageType.DLQ_TEST:
            properties.headers = {'simulate_failure': True}

        try:
            result = self.channel.basic_publish(
                exchange='advanced_lab',
                routing_key=routing_key,
                body=json.dumps(message_data, indent=2),
                properties=properties,
                mandatory=True
            )

            if result:
                self.stats['sent'] += 1
                self.stats['confirmed'] += 1
                msg_type_emoji = {
                    MessageType.NORMAL: "📝",
                    MessageType.PRIORITY: "🔴",
                    MessageType.TTL_SHORT: "⏰",
                    MessageType.TTL_LONG: "⏳",
                    MessageType.DLQ_TEST: "💀"
                }

                emoji = msg_type_emoji.get(msg_type, "📨")
                print(f"{emoji} {msg_type.name}: {content[:40]}...")
                return True
            else:
                self.stats['sent'] += 1
                print(f"❌ Failed to confirm: {content[:40]}...")
                return False

        except Exception as e:
            print(f"💥 Send error: {str(e)}")
            return False

    def demo_all_features(self):
        """Tüm features'ları demo eder"""
        print("\n🚀 Advanced Features Demo başlıyor...")
        print("=" * 60)

        # 1. Normal messages
        print("\n📝 Normal Messages:")
        for i in range(3):
            self.send_message(MessageType.NORMAL, f"Normal message {i+1}")

        # 2. Priority messages
        print("\n🔴 Priority Messages:")
        priorities = [10, 5, 1, 8, 3]
        for i, priority in enumerate(priorities):
            self.send_message(
                MessageType.PRIORITY,
                f"Priority message {i+1}",
                priority=priority
            )

        # 3. TTL messages
        print("\n⏰ TTL Messages:")
        self.send_message(MessageType.TTL_SHORT, "Short TTL message", ttl=10)
        self.send_message(MessageType.TTL_LONG, "Long TTL message", ttl=60)

        # 4. DLQ test messages
        print("\n💀 DLQ Test Messages:")
        for i in range(2):
            self.send_message(MessageType.DLQ_TEST, f"DLQ test message {i+1}")

        print("\n📊 Demo tamamlandı!")
        self.print_statistics()

    def print_statistics(self):
        """İstatistikleri yazdırır"""
        print("\n📈 Lab İstatistikleri:")
        print("-" * 30)
        for key, value in self.stats.items():
            print(f"   {key.title()}: {value}")

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    lab = AdvancedFeaturesLab()

    try:
        lab.demo_all_features()
        print("\n🎓 Advanced Features Lab tamamlandı!")
        print("💡 Şimdi consumer'ları çalıştırarak mesajları işleyebilirsiniz")
    finally:
        lab.close()
```

---

## 📋 Özet ve Best Practices

### 🎯 Dead Letter Queues

- **Ne zaman kullan:** Error handling, poison messages, retry logic
- **Best Practice:** Her critical queue için DLQ konfigüre et
- **Monitoring:** DLQ message count'unu izle

### ⏰ Message TTL

- **Ne zaman kullan:** Time-sensitive mesajlar, cache-like behavior
- **Best Practice:** Business logic'e uygun TTL değerleri seç
- **Dikkat:** TTL expired mesajlar DLQ'ya gider

### 🔝 Queue Priority

- **Ne zaman kullan:** Farklı öncelik seviyeli işlemler
- **Best Practice:** Az sayıda priority level kullan (0-10)
- **Dikkat:** Yüksek priorityli mesajlar düşük prioritylileri bloke edebilir

### ✅ Publisher Confirms

- **Ne zaman kullan:** Critical mesajlar için güvenlik
- **Best Practice:** Async confirms ile performance artır
- **Trade-off:** Güvenlik vs Performance

### 💡 Genel Best Practices

1. **Monitoring:** Tüm advanced features'ları izle
2. **Testing:** Production'a geçmeden önce load test yap
3. **Documentation:** Tüm konfigürasyonları dokümante et
4. **Backup:** DLQ mesajlarını backup al

---

**Sonraki Bölüm:** [RabbitMQ Clustering ve High Availability](04-clustering.md) 🚀
