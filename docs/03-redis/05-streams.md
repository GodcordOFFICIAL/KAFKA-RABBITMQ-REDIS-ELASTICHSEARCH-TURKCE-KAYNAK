# Redis Streams - Event Streaming ile Redis

## 📋 Özet

Redis Streams, Redis 5.0 ile tanıtılan ve event streaming, message queues ve time-series data için optimize edilmiş güçlü bir veri yapısıdır. Kafka benzeri event streaming özelliklerini Redis'in basitliği ve hızı ile birleştirir.

## 🎯 Learning Objectives

Bu bölümü tamamladığında:

- ✅ Redis Streams veri yapısını anlayacaksın
- ✅ Event sourcing pattern'ini uygulayabileceksin
- ✅ Consumer groups ile distributed processing yapabileceksin
- ✅ Time-series data processing geliştirebileceksin
- ✅ Stream-based microservices mimarisi kurabileceğiniz
- ✅ Real-time analytics sistemleri geliştirebileceksin

## 📋 Prerequisites

- Redis temelleri bilgisi
- Event-driven architecture kavramları
- Message queue sistemleri anlayışı
- Python/Node.js streaming concepts

## 🌊 Redis Streams Temelleri

### Stream Veri Yapısı

Redis Stream, time-ordered sequence of entries şeklinde organize edilmiş bir data structure'dır:

```
Stream: user_events
├── 1634567890123-0: {user_id: "123", action: "login", timestamp: "2021-10-18T10:11:30Z"}
├── 1634567891456-0: {user_id: "456", action: "purchase", product: "laptop", amount: 999}
├── 1634567892789-0: {user_id: "123", action: "logout", duration: 3600}
└── 1634567893012-0: {user_id: "789", action: "signup", email: "user@domain.com"}
```

### Stream ID Format

```
<timestamp_ms>-<sequence_number>
1634567890123-0
     ↑        ↑
timestamp   sequence
(ms)        number
```

### Temel Stream Komutları

```bash
# Entry ekleme
XADD stream_name * field1 value1 field2 value2

# Stream okuma (range)
XRANGE stream_name - + COUNT 10

# Real-time okuma
XREAD COUNT 10 STREAMS stream_name $

# Consumer group oluşturma
XGROUP CREATE stream_name group_name $ MKSTREAM

# Consumer group ile okuma
XREADGROUP GROUP group_name consumer_name COUNT 10 STREAMS stream_name >
```

## 💻 Python ile Redis Streams

### Stream Producer

```python
import redis
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any
import uuid

class RedisStreamProducer:
    """
    Redis Streams için event producer
    """

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        Stream producer başlat

        Args:
            host: Redis host
            port: Redis port
            db: Database numarası
            password: Redis password
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

        try:
            self.redis_client.ping()
            print(f"✅ Redis Stream Producer başlatıldı: {host}:{port}")
        except redis.ConnectionError:
            print(f"❌ Redis bağlantı hatası: {host}:{port}")
            raise

    def publish_event(self, stream_name: str, event_data: Dict[str, Any],
                     event_id: str = '*') -> str:
        """
        Stream'e event yayınla

        Args:
            stream_name: Stream adı
            event_data: Event verisi
            event_id: Event ID (* = auto-generate)

        Returns:
            Generated event ID
        """
        try:
            # Event metadata ekle
            enriched_event = {
                **event_data,
                'published_at': datetime.now().isoformat(),
                'producer_id': 'stream_producer_v1'
            }

            # JSON field'ları serialize et
            serialized_event = {}
            for key, value in enriched_event.items():
                if isinstance(value, (dict, list)):
                    serialized_event[key] = json.dumps(value)
                else:
                    serialized_event[key] = str(value)

            # Stream'e ekle
            event_id = self.redis_client.xadd(stream_name, serialized_event, id=event_id)

            print(f"📡 Event published to {stream_name}: {event_id}")
            return event_id

        except Exception as e:
            print(f"❌ Event publish hatası: {e}")
            return None

    def publish_user_event(self, user_id: str, action: str, **kwargs):
        """
        User event yayınla

        Args:
            user_id: Kullanıcı ID
            action: Action type
            **kwargs: Ek event verileri
        """
        event_data = {
            'event_type': 'user_action',
            'user_id': user_id,
            'action': action,
            'session_id': str(uuid.uuid4()),
            **kwargs
        }

        return self.publish_event('user_events', event_data)

    def publish_order_event(self, order_id: str, status: str, **kwargs):
        """
        Order event yayınla

        Args:
            order_id: Sipariş ID
            status: Sipariş durumu
            **kwargs: Ek order verileri
        """
        event_data = {
            'event_type': 'order_update',
            'order_id': order_id,
            'status': status,
            'updated_at': datetime.now().isoformat(),
            **kwargs
        }

        return self.publish_event('order_events', event_data)

    def publish_system_metric(self, metric_name: str, value: float, **tags):
        """
        System metric yayınla

        Args:
            metric_name: Metric adı
            value: Metric değeri
            **tags: Metric tag'leri
        """
        event_data = {
            'event_type': 'system_metric',
            'metric_name': metric_name,
            'value': value,
            'timestamp': int(time.time() * 1000),  # milliseconds
            'tags': tags
        }

        return self.publish_event('system_metrics', event_data)

    def simulate_user_activity(self, duration_seconds=60):
        """
        Kullanıcı aktivitesi simülasyonu

        Args:
            duration_seconds: Simülasyon süresi
        """
        print(f"🎭 User activity simülasyonu başlıyor ({duration_seconds}s)...")

        users = ['user_001', 'user_002', 'user_003', 'user_004', 'user_005']
        actions = [
            ('login', {}),
            ('page_view', {'page': '/home', 'referrer': 'google'}),
            ('page_view', {'page': '/products', 'category': 'electronics'}),
            ('add_to_cart', {'product_id': 'prod_123', 'quantity': 1}),
            ('purchase', {'order_id': 'ord_456', 'amount': 99.99}),
            ('logout', {'session_duration': random.randint(300, 3600)})
        ]

        start_time = time.time()
        event_count = 0

        try:
            while time.time() - start_time < duration_seconds:
                # Random user ve action seç
                user_id = random.choice(users)
                action, extra_data = random.choice(actions)

                # Event yayınla
                self.publish_user_event(user_id, action, **extra_data)
                event_count += 1

                # Random interval
                time.sleep(random.uniform(0.1, 2.0))

            print(f"✅ Simülasyon tamamlandı: {event_count} event yayınlandı")

        except KeyboardInterrupt:
            print(f"\n🛑 Simülasyon durduruldu: {event_count} event yayınlandı")

class RedisStreamConsumer:
    """
    Redis Streams için event consumer
    """

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        Stream consumer başlat
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

        self.consumer_id = f"consumer_{uuid.uuid4().hex[:8]}"
        print(f"✅ Redis Stream Consumer başlatıldı: {self.consumer_id}")

    def create_consumer_group(self, stream_name: str, group_name: str,
                            start_id: str = '$'):
        """
        Consumer group oluştur

        Args:
            stream_name: Stream adı
            group_name: Group adı
            start_id: Başlangıç position ($=latest, 0=beginning)
        """
        try:
            self.redis_client.xgroup_create(
                stream_name,
                group_name,
                id=start_id,
                mkstream=True
            )
            print(f"✅ Consumer group oluşturuldu: {group_name} @ {stream_name}")

        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"ℹ️  Consumer group zaten mevcut: {group_name}")
            else:
                print(f"❌ Consumer group oluşturma hatası: {e}")

    def consume_events(self, stream_name: str, group_name: str = None,
                      count: int = 10, block: int = 1000):
        """
        Event'leri consume et

        Args:
            stream_name: Stream adı
            group_name: Consumer group (None = direct read)
            count: Okunacak event sayısı
            block: Block süresi (ms)
        """
        try:
            if group_name:
                # Consumer group ile okuma
                messages = self.redis_client.xreadgroup(
                    group_name,
                    self.consumer_id,
                    {stream_name: '>'},
                    count=count,
                    block=block
                )
            else:
                # Direct stream okuma
                messages = self.redis_client.xread(
                    {stream_name: '$'},
                    count=count,
                    block=block
                )

            # Messages işle
            for stream, events in messages:
                for event_id, fields in events:
                    self.process_event(stream.decode() if isinstance(stream, bytes) else stream,
                                     event_id, fields)

                    # Consumer group kullanıyorsa ACK gönder
                    if group_name:
                        self.redis_client.xack(stream_name, group_name, event_id)

            return len(messages)

        except Exception as e:
            print(f"❌ Event consume hatası: {e}")
            return 0

    def process_event(self, stream_name: str, event_id: str, fields: Dict):
        """
        Event'i işle

        Args:
            stream_name: Stream adı
            event_id: Event ID
            fields: Event field'ları
        """
        try:
            # JSON field'ları deserialize et
            processed_fields = {}
            for key, value in fields.items():
                try:
                    # JSON parse dene
                    processed_fields[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Plain string olarak bırak
                    processed_fields[key] = value

            # Event type'a göre işle
            event_type = processed_fields.get('event_type', 'unknown')

            if event_type == 'user_action':
                self._process_user_event(event_id, processed_fields)
            elif event_type == 'order_update':
                self._process_order_event(event_id, processed_fields)
            elif event_type == 'system_metric':
                self._process_metric_event(event_id, processed_fields)
            else:
                print(f"⚠️  Unknown event type: {event_type}")

        except Exception as e:
            print(f"❌ Event processing hatası: {e}")

    def _process_user_event(self, event_id: str, fields: Dict):
        """
        User event'ini işle
        """
        user_id = fields.get('user_id', 'unknown')
        action = fields.get('action', 'unknown')

        print(f"👤 User Event [{event_id[:10]}...]: {user_id} -> {action}")

        # Action'a göre özel işlemler
        if action == 'login':
            print(f"   🔓 User {user_id} logged in")
        elif action == 'purchase':
            amount = fields.get('amount', 0)
            print(f"   💰 User {user_id} made purchase: ${amount}")
        elif action == 'logout':
            duration = fields.get('session_duration', 0)
            print(f"   👋 User {user_id} logged out (session: {duration}s)")

    def _process_order_event(self, event_id: str, fields: Dict):
        """
        Order event'ini işle
        """
        order_id = fields.get('order_id', 'unknown')
        status = fields.get('status', 'unknown')

        print(f"📦 Order Event [{event_id[:10]}...]: {order_id} -> {status}")

    def _process_metric_event(self, event_id: str, fields: Dict):
        """
        System metric event'ini işle
        """
        metric_name = fields.get('metric_name', 'unknown')
        value = fields.get('value', 0)

        print(f"📊 Metric Event [{event_id[:10]}...]: {metric_name} = {value}")

    def start_consuming(self, stream_configs: List[Dict], group_name: str = None):
        """
        Continuous event consuming başlat

        Args:
            stream_configs: [{'stream': 'name', 'group': 'group'}, ...]
            group_name: Default group name
        """
        print(f"🚀 Event consuming başlıyor...")
        print(f"   Consumer ID: {self.consumer_id}")
        print(f"   Streams: {[config['stream'] for config in stream_configs]}")

        # Consumer group'ları oluştur
        for config in stream_configs:
            stream_name = config['stream']
            consumer_group = config.get('group', group_name)

            if consumer_group:
                self.create_consumer_group(stream_name, consumer_group, '0')

        try:
            processed_count = 0

            while True:
                for config in stream_configs:
                    stream_name = config['stream']
                    consumer_group = config.get('group', group_name)

                    events_processed = self.consume_events(
                        stream_name,
                        consumer_group,
                        count=5,
                        block=1000
                    )

                    processed_count += events_processed

                if processed_count % 10 == 0 and processed_count > 0:
                    print(f"📈 Processed {processed_count} events so far...")

        except KeyboardInterrupt:
            print(f"\n🛑 Consumer durduruldu: {processed_count} event işlendi")

class StreamAnalytics:
    """
    Stream analytics ve monitoring
    """

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        Stream analytics başlat
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

    def get_stream_info(self, stream_name: str) -> Dict:
        """
        Stream bilgilerini al
        """
        try:
            info = self.redis_client.xinfo_stream(stream_name)

            return {
                'name': stream_name,
                'length': info['length'],
                'first_entry_id': info['first-entry'][0] if info['first-entry'] else None,
                'last_entry_id': info['last-entry'][0] if info['last-entry'] else None,
                'groups': info['groups']
            }

        except Exception as e:
            print(f"❌ Stream info hatası: {e}")
            return {}

    def get_consumer_group_info(self, stream_name: str, group_name: str) -> Dict:
        """
        Consumer group bilgilerini al
        """
        try:
            groups = self.redis_client.xinfo_groups(stream_name)

            for group in groups:
                if group['name'] == group_name:
                    # Group consumers
                    consumers = self.redis_client.xinfo_consumers(stream_name, group_name)

                    return {
                        'name': group_name,
                        'pending': group['pending'],
                        'last_delivered_id': group['last-delivered-id'],
                        'consumers': [
                            {
                                'name': consumer['name'],
                                'pending': consumer['pending'],
                                'idle': consumer['idle']
                            }
                            for consumer in consumers
                        ]
                    }

            return {}

        except Exception as e:
            print(f"❌ Consumer group info hatası: {e}")
            return {}

    def print_stream_dashboard(self, stream_names: List[str]):
        """
        Stream dashboard göster
        """
        print("📊 Redis Streams Dashboard")
        print("=" * 60)

        for stream_name in stream_names:
            info = self.get_stream_info(stream_name)

            if not info:
                print(f"❌ {stream_name}: Stream bulunamadı")
                continue

            print(f"\n🌊 Stream: {stream_name}")
            print(f"   📏 Length: {info['length']} events")
            print(f"   🆔 First ID: {info['first_entry_id']}")
            print(f"   🆔 Last ID: {info['last_entry_id']}")
            print(f"   👥 Groups: {info['groups']}")

            # Consumer groups detayı
            try:
                groups = self.redis_client.xinfo_groups(stream_name)

                for group in groups:
                    group_info = self.get_consumer_group_info(stream_name, group['name'])

                    print(f"\n   📋 Group: {group['name']}")
                    print(f"      ⏳ Pending: {group_info['pending']}")
                    print(f"      🎯 Last delivered: {group_info['last_delivered_id']}")

                    for consumer in group_info['consumers']:
                        idle_minutes = consumer['idle'] // 60000  # ms to minutes
                        print(f"      👤 {consumer['name']}: {consumer['pending']} pending, idle {idle_minutes}m")

            except Exception as e:
                print(f"      ⚠️  Group info alınamadı: {e}")

    def analyze_event_patterns(self, stream_name: str, limit: int = 100):
        """
        Event pattern analizi
        """
        try:
            # Son event'leri al
            events = self.redis_client.xrevrange(stream_name, count=limit)

            if not events:
                print(f"📊 {stream_name}: Henüz event yok")
                return

            # Pattern analizi
            event_types = {}
            user_actions = {}
            hourly_distribution = {}

            for event_id, fields in events:
                # Event type counting
                event_type = fields.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1

                # User action counting
                if event_type == 'user_action':
                    action = fields.get('action', 'unknown')
                    user_actions[action] = user_actions.get(action, 0) + 1

                # Hourly distribution
                timestamp_ms = int(event_id.split('-')[0])
                hour = datetime.fromtimestamp(timestamp_ms / 1000).hour
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1

            # Sonuçları göster
            print(f"📊 Event Pattern Analysis: {stream_name} (son {len(events)} event)")
            print("-" * 50)

            print("📋 Event Types:")
            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(events)) * 100
                print(f"   {event_type}: {count} ({percentage:.1f}%)")

            if user_actions:
                print("\n👤 User Actions:")
                for action, count in sorted(user_actions.items(), key=lambda x: x[1], reverse=True):
                    print(f"   {action}: {count}")

            print("\n🕐 Hourly Distribution:")
            for hour in sorted(hourly_distribution.keys()):
                count = hourly_distribution[hour]
                bar = "█" * (count // max(1, max(hourly_distribution.values()) // 20))
                print(f"   {hour:02d}:00 - {count:3d} {bar}")

        except Exception as e:
            print(f"❌ Pattern analysis hatası: {e}")

def demo_redis_streams():
    """
    Redis Streams comprehensive demo
    """
    print("🌊 Redis Streams Comprehensive Demo")
    print("=" * 50)

    # Producer oluştur
    producer = RedisStreamProducer()

    # Consumer oluştur
    consumer = RedisStreamConsumer()

    # Analytics oluştur
    analytics = StreamAnalytics()

    # 1. Sample events yayınla
    print("\n1️⃣ Sample Events Yayınlanıyor:")

    # User events
    producer.publish_user_event('user_001', 'login', ip='192.168.1.100')
    producer.publish_user_event('user_001', 'page_view', page='/products')
    producer.publish_user_event('user_002', 'signup', email='user2@example.com')
    producer.publish_user_event('user_001', 'purchase', order_id='ord_123', amount=99.99)

    # Order events
    producer.publish_order_event('ord_123', 'confirmed', amount=99.99)
    producer.publish_order_event('ord_123', 'shipped', tracking='TRK123456')

    # System metrics
    producer.publish_system_metric('cpu_usage', 75.5, server='web01', datacenter='us-east')
    producer.publish_system_metric('memory_usage', 82.3, server='web01', datacenter='us-east')

    # 2. Stream info göster
    print("\n2️⃣ Stream Dashboard:")
    analytics.print_stream_dashboard(['user_events', 'order_events', 'system_metrics'])

    # 3. Pattern analysis
    print("\n3️⃣ Event Pattern Analysis:")
    analytics.analyze_event_patterns('user_events')

    # 4. Consumer group demo
    print("\n4️⃣ Consumer Group Demo:")

    # Consumer group'ları oluştur
    stream_configs = [
        {'stream': 'user_events', 'group': 'analytics_team'},
        {'stream': 'order_events', 'group': 'fulfillment_team'},
        {'stream': 'system_metrics', 'group': 'monitoring_team'}
    ]

    # Bir kaç event daha ekle
    print("   📡 Ek event'ler yayınlanıyor...")
    for i in range(5):
        producer.publish_user_event(f'user_{i+10}', 'page_view', page=f'/page_{i}')
        time.sleep(0.1)

    # Consumer başlat (kısa süre için)
    print("   👂 Consumer başlatılıyor (5 saniye)...")

    import threading

    def consume_for_demo():
        """Demo için kısa süreli consuming"""
        end_time = time.time() + 5
        processed = 0

        while time.time() < end_time:
            for config in stream_configs:
                events = consumer.consume_events(
                    config['stream'],
                    config['group'],
                    count=2,
                    block=500
                )
                processed += events

        print(f"   ✅ Demo consumer: {processed} event işlendi")

    # Consumer thread başlat
    consumer_thread = threading.Thread(target=consume_for_demo)
    consumer_thread.start()
    consumer_thread.join()

    # 5. Final dashboard
    print("\n5️⃣ Final Dashboard:")
    analytics.print_stream_dashboard(['user_events', 'order_events', 'system_metrics'])

    print("\n✅ Redis Streams demo tamamlandı!")
    print("💡 Production kullanımı için:")
    print("   - Stream retention policies ayarlayın")
    print("   - Consumer lag monitoring ekleyin")
    print("   - Error handling ve retry logic geliştirin")

if __name__ == "__main__":
    demo_redis_streams()
```

## 🏗️ Stream Architecture Patterns

### 1. Event Sourcing

```python
class EventSourcingExample:
    """
    Event Sourcing pattern Redis Streams ile
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.stream_name = "account_events"

    def create_account(self, account_id: str, initial_balance: float):
        """
        Hesap oluşturma eventi
        """
        event = {
            'event_type': 'AccountCreated',
            'account_id': account_id,
            'initial_balance': initial_balance,
            'timestamp': datetime.now().isoformat()
        }

        return self.redis.xadd(self.stream_name, event)

    def deposit(self, account_id: str, amount: float):
        """
        Para yatırma eventi
        """
        event = {
            'event_type': 'MoneyDeposited',
            'account_id': account_id,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }

        return self.redis.xadd(self.stream_name, event)

    def withdraw(self, account_id: str, amount: float):
        """
        Para çekme eventi
        """
        event = {
            'event_type': 'MoneyWithdrawn',
            'account_id': account_id,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }

        return self.redis.xadd(self.stream_name, event)

    def get_account_balance(self, account_id: str) -> float:
        """
        Event'lerden hesap bakiyesini hesapla
        """
        events = self.redis.xrange(self.stream_name)
        balance = 0.0

        for event_id, fields in events:
            if fields.get('account_id') == account_id:
                event_type = fields.get('event_type')
                amount = float(fields.get('amount', 0))

                if event_type == 'AccountCreated':
                    balance = float(fields.get('initial_balance', 0))
                elif event_type == 'MoneyDeposited':
                    balance += amount
                elif event_type == 'MoneyWithdrawn':
                    balance -= amount

        return balance
```

### 2. CQRS (Command Query Responsibility Segregation)

```python
class CQRSPattern:
    """
    CQRS pattern Redis Streams ile
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.command_stream = "commands"
        self.event_stream = "events"

    def send_command(self, command_type: str, payload: Dict):
        """
        Command gönder
        """
        command = {
            'command_id': str(uuid.uuid4()),
            'command_type': command_type,
            'payload': json.dumps(payload),
            'timestamp': datetime.now().isoformat()
        }

        return self.redis.xadd(self.command_stream, command)

    def process_commands(self):
        """
        Command'ları işle ve event üret
        """
        commands = self.redis.xread({self.command_stream: '$'}, block=1000)

        for stream, events in commands:
            for event_id, fields in events:
                command_type = fields.get('command_type')
                payload = json.loads(fields.get('payload', '{}'))

                # Command'a göre event üret
                if command_type == 'CreateUser':
                    self._handle_create_user(payload)
                elif command_type == 'UpdateUser':
                    self._handle_update_user(payload)

    def _handle_create_user(self, payload: Dict):
        """
        CreateUser command'ını işle
        """
        event = {
            'event_type': 'UserCreated',
            'user_id': payload['user_id'],
            'email': payload['email'],
            'timestamp': datetime.now().isoformat()
        }

        self.redis.xadd(self.event_stream, event)
```

## 🧪 Hands-on Tasks

### Task 1: Real-time Analytics Pipeline

**Hedef**: E-ticaret event'leri için real-time analytics

**Gereksinimler**:

- User behavior tracking
- Real-time metrics calculation
- Dashboard data aggregation
- Alerting for anomalies

### Task 2: Microservices Event Communication

**Hedef**: Microservices arası event-driven communication

**Gereksinimler**:

- Service-to-service messaging
- Event choreography pattern
- Saga pattern implementation
- Dead letter queue handling

### Task 3: Time-series Monitoring System

**Hedef**: System metrics collection ve analysis

**Gereksinimler**:

- Metric collection from multiple sources
- Time-based aggregations
- Retention policies
- Performance dashboards

## ✅ Checklist

Bu bölümü tamamladıktan sonra:

- [ ] Redis Streams veri yapısını anlıyorum
- [ ] Event producer/consumer implementasyonu yapabilirim
- [ ] Consumer groups kullanabiliyorum
- [ ] Event sourcing pattern uygulayabilirim
- [ ] CQRS pattern implementasyonu yapabilirim
- [ ] Stream analytics ve monitoring yapabilirim
- [ ] Production-ready stream architecture tasarlayabilirim
- [ ] Performance tuning ve scaling yapabilirim

## ⚠️ Common Mistakes

### 1. Memory Management

**Problem**: Stream'ler sınırsız büyür
**Çözüm**: MAXLEN ve retention policies

### 2. Consumer Lag

**Problem**: Consumer'lar event'leri yetişemiyor
**Çözüm**: Horizontal scaling, processing optimization

### 3. Poison Messages

**Problem**: Hatalı event'ler processing'i durduruyor
**Çözüm**: Error handling, dead letter streams

## 🔗 İlgili Bölümler

- **Önceki**: [Persistence ve Replication](04-persistence-replication.md)
- **Sonraki**: [Redis Clustering](06-clustering.md)
- **İlgili**: [Kafka Streams](../01-kafka/04-streams.md)

---

**Sonraki Adım**: Redis'in cluster özelliklerini öğrenmek için [Redis Clustering](06-clustering.md) bölümüne geçin! 🚀
