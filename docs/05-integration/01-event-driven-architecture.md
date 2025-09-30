# Integration Examples - Event-Driven Architecture

## 📋 Özet

Bu bölümde Kafka, RabbitMQ, Redis ve Elasticsearch'in bir arada kullanıldığı gerçek dünya senaryolarını öğreneceksiniz. Event-driven architecture patterns, microservices communication ve comprehensive monitoring solutions'ları implementasyonlarıyla birlikte ele alacağız.

## 🎯 Learning Objectives

Bu bölümü tamamladığında:

- ✅ Event-driven architecture patterns implementasyonu yapabileceksin
- ✅ Microservices arası communication design edebileceksin
- ✅ Real-time analytics pipeline kurabileceksin
- ✅ E-commerce platform event flow'u tasarlayabileceksin
- ✅ Log aggregation ve monitoring sistemleri kurabileceksin
- ✅ Fault tolerance ve resilience patterns uygulayabileceksin
- ✅ Performance optimization strategies geliştirebileceksin

## 📋 Prerequisites

- Tüm teknolojilerin temel bilgisi
- Docker ve containerization
- Microservices architecture concepts
- Event sourcing ve CQRS patterns
- Basic monitoring ve observability

## 🏗️ Architecture Overview

### Complete Event-Driven E-commerce Platform

```
                           Event-Driven E-commerce Architecture

    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   Web Frontend  │    │  Mobile App     │    │   Admin Panel   │
    │                 │    │                 │    │                 │
    └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
              │                      │                      │
              └──────────────────────┼──────────────────────┘
                                     │
                            ┌────────▼────────┐
                            │   API Gateway   │
                            │  (Load Balance) │
                            └────────┬────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
    ┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
    │ User Service    │    │ Order Service   │    │Product Service  │
    │                 │    │                 │    │                 │
    └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
              │                      │                      │
              └──────────────────────┼──────────────────────┘
                                     │
                            ┌────────▼────────┐
                            │  Message Bus    │
                            │     (Kafka)     │
                            └────────┬────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
    ┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
    │ Payment Service │    │Inventory Service│    │ Email Service   │
    │                 │    │                 │    │   (RabbitMQ)    │
    └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
              │                      │                      │
              └──────────────────────┼──────────────────────┘
                                     │
                      ┌──────────────┼──────────────┐
                      │              │              │
            ┌─────────▼───────┐ ┌────▼────┐ ┌──────▼──────┐
            │     Redis       │ │ PostgreSQL│ │Elasticsearch│
            │ (Cache + Pub/Sub│ │(Persistent│ │(Search +    │
            │  + Sessions)    │ │   Data)   │ │ Analytics)  │
            └─────────────────┘ └─────────┘ └─────────────┘
```

### Event Flow Patterns

1. **Command Events**: User actions → Kafka → Service processing
2. **Domain Events**: Business logic results → Event store
3. **Integration Events**: Service-to-service communication
4. **Notification Events**: RabbitMQ → Email/SMS/Push
5. **Analytics Events**: Real-time metrics → Elasticsearch

## 💻 Complete Integration Implementation

### 1. Event-Driven E-commerce Platform

```python
# integration_platform.py
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

# Technology clients
from kafka import KafkaProducer, KafkaConsumer
import pika
import redis
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    USER_REGISTERED = "user.registered"
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    PAYMENT_PROCESSED = "payment.processed"
    INVENTORY_UPDATED = "inventory.updated"
    EMAIL_SENT = "email.sent"
    PRODUCT_VIEWED = "product.viewed"
    CART_UPDATED = "cart.updated"

@dataclass
class Event:
    """Base event structure"""
    event_id: str
    event_type: EventType
    aggregate_id: str
    data: Dict[str, Any]
    timestamp: str
    version: int = 1
    correlation_id: str = None

    def to_dict(self) -> Dict:
        event_dict = asdict(self)
        event_dict['event_type'] = self.event_type.value
        return event_dict

    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)

class EventBus:
    """
    Central event bus managing all message technologies
    """

    def __init__(self):
        """Initialize all technology connections"""
        # Kafka for high-throughput events
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )

        # RabbitMQ for reliable notifications
        self.rabbitmq_connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.rabbitmq_channel = self.rabbitmq_connection.channel()

        # Redis for caching and pub/sub
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Elasticsearch for search and analytics
        self.elasticsearch = Elasticsearch(['localhost:9200'])

        self._setup_infrastructure()
        logger.info("✅ Event Bus initialized with all technologies")

    def _setup_infrastructure(self):
        """Setup queues, topics and indices"""
        # RabbitMQ exchanges and queues
        self.rabbitmq_channel.exchange_declare(
            exchange='notifications',
            exchange_type='topic',
            durable=True
        )

        # Notification queues
        for queue_name in ['email.queue', 'sms.queue', 'push.queue']:
            self.rabbitmq_channel.queue_declare(queue=queue_name, durable=True)
            self.rabbitmq_channel.queue_bind(
                exchange='notifications',
                queue=queue_name,
                routing_key=queue_name.replace('.queue', '.*')
            )

        # Elasticsearch indices
        try:
            # Events index for event sourcing
            if not self.elasticsearch.indices.exists(index='events'):
                events_mapping = {
                    "mappings": {
                        "properties": {
                            "event_id": {"type": "keyword"},
                            "event_type": {"type": "keyword"},
                            "aggregate_id": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "data": {"type": "object"},
                            "correlation_id": {"type": "keyword"}
                        }
                    }
                }
                self.elasticsearch.indices.create(index='events', body=events_mapping)

            # Analytics index
            if not self.elasticsearch.indices.exists(index='analytics'):
                analytics_mapping = {
                    "mappings": {
                        "properties": {
                            "event_type": {"type": "keyword"},
                            "user_id": {"type": "keyword"},
                            "session_id": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "metrics": {"type": "object"}
                        }
                    }
                }
                self.elasticsearch.indices.create(index='analytics', body=analytics_mapping)

        except Exception as e:
            logger.warning(f"Elasticsearch setup warning: {e}")

    def publish_event(self, event: Event, use_kafka: bool = True, use_rabbitmq: bool = False):
        """
        Publish event to appropriate message bus
        """
        try:
            event_data = event.to_dict()

            # Kafka for high-throughput domain events
            if use_kafka:
                topic = f"events.{event.event_type.value.split('.')[0]}"
                self.kafka_producer.send(
                    topic=topic,
                    key=event.aggregate_id,
                    value=event_data
                )
                logger.info(f"📤 Event published to Kafka: {event.event_type.value}")

            # RabbitMQ for reliable notifications
            if use_rabbitmq:
                routing_key = f"notification.{event.event_type.value}"
                self.rabbitmq_channel.basic_publish(
                    exchange='notifications',
                    routing_key=routing_key,
                    body=json.dumps(event_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                        correlation_id=event.correlation_id
                    )
                )
                logger.info(f"📤 Event published to RabbitMQ: {event.event_type.value}")

            # Always store in event store (Elasticsearch)
            self.elasticsearch.index(
                index='events',
                id=event.event_id,
                body=event_data
            )

            # Cache recent events in Redis
            self.redis_client.lpush(
                f"recent_events:{event.aggregate_id}",
                json.dumps(event_data)
            )
            self.redis_client.expire(f"recent_events:{event.aggregate_id}", 3600)

            # Real-time pub/sub notification
            self.redis_client.publish(
                f"events:{event.event_type.value}",
                json.dumps(event_data)
            )

        except Exception as e:
            logger.error(f"❌ Event publishing failed: {e}")

    def get_events_for_aggregate(self, aggregate_id: str) -> List[Event]:
        """Get all events for an aggregate from event store"""
        try:
            query = {
                "query": {
                    "term": {
                        "aggregate_id": aggregate_id
                    }
                },
                "sort": [
                    {"timestamp": {"order": "asc"}}
                ]
            }

            result = self.elasticsearch.search(index='events', body=query, size=1000)

            events = []
            for hit in result['hits']['hits']:
                event_data = hit['_source']
                events.append(Event.from_dict(event_data))

            return events

        except Exception as e:
            logger.error(f"❌ Event retrieval failed: {e}")
            return []

class UserService:
    """User management service"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.redis_client = event_bus.redis_client

    def register_user(self, user_data: Dict) -> str:
        """Register new user and publish event"""
        user_id = str(uuid.uuid4())

        # Store user data in cache
        user_info = {
            **user_data,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }

        self.redis_client.hset(
            f"user:{user_id}",
            mapping=user_info
        )

        # Publish user registered event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_REGISTERED,
            aggregate_id=user_id,
            data=user_info,
            timestamp=datetime.now().isoformat(),
            correlation_id=str(uuid.uuid4())
        )

        self.event_bus.publish_event(event, use_kafka=True, use_rabbitmq=True)

        logger.info(f"👤 User registered: {user_id}")
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user from cache"""
        user_data = self.redis_client.hgetall(f"user:{user_id}")
        return user_data if user_data else None

class OrderService:
    """Order management service"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.redis_client = event_bus.redis_client

    def create_order(self, user_id: str, items: List[Dict]) -> str:
        """Create new order and publish events"""
        order_id = str(uuid.uuid4())

        # Calculate order total
        total_amount = sum(item['price'] * item['quantity'] for item in items)

        order_data = {
            'order_id': order_id,
            'user_id': user_id,
            'items': items,
            'total_amount': total_amount,
            'status': 'created',
            'created_at': datetime.now().isoformat()
        }

        # Store order
        self.redis_client.hset(
            f"order:{order_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in order_data.items()}
        )

        # Publish order created event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ORDER_CREATED,
            aggregate_id=order_id,
            data=order_data,
            timestamp=datetime.now().isoformat(),
            correlation_id=str(uuid.uuid4())
        )

        self.event_bus.publish_event(event, use_kafka=True)

        logger.info(f"🛒 Order created: {order_id} for user {user_id}")
        return order_id

    def confirm_order(self, order_id: str) -> bool:
        """Confirm order and trigger payment"""
        order_data = self.redis_client.hgetall(f"order:{order_id}")

        if not order_data:
            return False

        # Update order status
        self.redis_client.hset(f"order:{order_id}", "status", "confirmed")

        # Publish order confirmed event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ORDER_CONFIRMED,
            aggregate_id=order_id,
            data={
                'order_id': order_id,
                'user_id': order_data.get('user_id'),
                'total_amount': float(order_data.get('total_amount', 0)),
                'confirmed_at': datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )

        self.event_bus.publish_event(event, use_kafka=True, use_rabbitmq=True)

        logger.info(f"✅ Order confirmed: {order_id}")
        return True

class PaymentService:
    """Payment processing service"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        # Subscribe to order confirmed events
        self.setup_event_listener()

    def setup_event_listener(self):
        """Setup Kafka consumer for order events"""
        def consume_order_events():
            consumer = KafkaConsumer(
                'events.order',
                bootstrap_servers=['localhost:9092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='payment-service'
            )

            for message in consumer:
                try:
                    event_data = message.value
                    if event_data.get('event_type') == EventType.ORDER_CONFIRMED.value:
                        self.process_payment(event_data)
                except Exception as e:
                    logger.error(f"❌ Payment processing error: {e}")

        # Start consumer in background thread
        import threading
        consumer_thread = threading.Thread(target=consume_order_events, daemon=True)
        consumer_thread.start()

    def process_payment(self, order_event: Dict) -> bool:
        """Process payment for confirmed order"""
        order_id = order_event['data']['order_id']
        amount = order_event['data']['total_amount']

        # Simulate payment processing
        time.sleep(1)  # Simulate API call

        # Assume payment successful (90% success rate)
        import random
        payment_successful = random.random() > 0.1

        payment_data = {
            'order_id': order_id,
            'amount': amount,
            'status': 'success' if payment_successful else 'failed',
            'payment_id': str(uuid.uuid4()),
            'processed_at': datetime.now().isoformat()
        }

        # Publish payment processed event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.PAYMENT_PROCESSED,
            aggregate_id=order_id,
            data=payment_data,
            timestamp=datetime.now().isoformat()
        )

        self.event_bus.publish_event(event, use_kafka=True, use_rabbitmq=True)

        status_emoji = "💳" if payment_successful else "❌"
        logger.info(f"{status_emoji} Payment processed: {order_id} - {payment_data['status']}")

        return payment_successful

class AnalyticsService:
    """Real-time analytics service"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.elasticsearch = event_bus.elasticsearch
        self.redis_client = event_bus.redis_client

        # Setup real-time analytics
        self.setup_real_time_analytics()

    def setup_real_time_analytics(self):
        """Setup Redis pub/sub for real-time analytics"""
        def process_analytics():
            pubsub = self.redis_client.pubsub()
            pubsub.psubscribe('events:*')

            for message in pubsub.listen():
                if message['type'] == 'pmessage':
                    try:
                        event_data = json.loads(message['data'])
                        self.process_analytics_event(event_data)
                    except Exception as e:
                        logger.error(f"❌ Analytics processing error: {e}")

        import threading
        analytics_thread = threading.Thread(target=process_analytics, daemon=True)
        analytics_thread.start()

    def process_analytics_event(self, event_data: Dict):
        """Process event for analytics"""
        event_type = event_data.get('event_type')
        timestamp = datetime.now()

        analytics_doc = {
            'event_type': event_type,
            'timestamp': timestamp.isoformat(),
            'hour': timestamp.strftime('%Y%m%d%H'),
            'date': timestamp.strftime('%Y%m%d'),
            'data': event_data.get('data', {})
        }

        # Store in Elasticsearch for search and aggregation
        try:
            self.elasticsearch.index(
                index='analytics',
                body=analytics_doc
            )
        except Exception as e:
            logger.error(f"❌ Analytics indexing error: {e}")

        # Update real-time counters in Redis
        hour_key = timestamp.strftime('%Y%m%d%H')
        self.redis_client.incr(f"analytics:events:{event_type}:hourly:{hour_key}")
        self.redis_client.incr(f"analytics:events:{event_type}:daily:{timestamp.strftime('%Y%m%d')}")

        # Set TTL for counters
        self.redis_client.expire(f"analytics:events:{event_type}:hourly:{hour_key}", 24 * 3600)
        self.redis_client.expire(f"analytics:events:{event_type}:daily:{timestamp.strftime('%Y%m%d')}", 30 * 24 * 3600)

    def get_real_time_metrics(self) -> Dict:
        """Get real-time metrics from Redis"""
        now = datetime.now()
        current_hour = now.strftime('%Y%m%d%H')
        current_date = now.strftime('%Y%m%d')

        metrics = {}

        for event_type in EventType:
            event_name = event_type.value

            hourly_key = f"analytics:events:{event_name}:hourly:{current_hour}"
            daily_key = f"analytics:events:{event_name}:daily:{current_date}"

            metrics[event_name] = {
                'hourly_count': int(self.redis_client.get(hourly_key) or 0),
                'daily_count': int(self.redis_client.get(daily_key) or 0)
            }

        return metrics

    def get_historical_analytics(self, days: int = 7) -> Dict:
        """Get historical analytics from Elasticsearch"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            query = {
                "size": 0,
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": start_date.isoformat(),
                            "lte": end_date.isoformat()
                        }
                    }
                },
                "aggs": {
                    "events_by_type": {
                        "terms": {
                            "field": "event_type",
                            "size": 20
                        }
                    },
                    "events_by_day": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "day"
                        },
                        "aggs": {
                            "event_types": {
                                "terms": {
                                    "field": "event_type",
                                    "size": 10
                                }
                            }
                        }
                    }
                }
            }

            result = self.elasticsearch.search(index='analytics', body=query)

            analytics = {
                'total_events': result['hits']['total']['value'],
                'events_by_type': {
                    bucket['key']: bucket['doc_count']
                    for bucket in result['aggregations']['events_by_type']['buckets']
                },
                'daily_breakdown': [
                    {
                        'date': bucket['key_as_string'][:10],
                        'total_events': bucket['doc_count'],
                        'event_types': {
                            sub_bucket['key']: sub_bucket['doc_count']
                            for sub_bucket in bucket['event_types']['buckets']
                        }
                    }
                    for bucket in result['aggregations']['events_by_day']['buckets']
                ]
            }

            return analytics

        except Exception as e:
            logger.error(f"❌ Historical analytics error: {e}")
            return {}

class ECommercePlatform:
    """Complete e-commerce platform orchestrator"""

    def __init__(self):
        """Initialize all services"""
        self.event_bus = EventBus()
        self.user_service = UserService(self.event_bus)
        self.order_service = OrderService(self.event_bus)
        self.payment_service = PaymentService(self.event_bus)
        self.analytics_service = AnalyticsService(self.event_bus)

        logger.info("🚀 E-commerce platform initialized")

    def simulate_user_journey(self, num_users: int = 10, num_orders: int = 20):
        """Simulate complete user journey"""
        logger.info(f"🎭 Simulating {num_users} users with {num_orders} orders")

        user_ids = []

        # Create users
        for i in range(num_users):
            user_data = {
                'email': f'user{i+1}@example.com',
                'name': f'User {i+1}',
                'phone': f'+1234567{i:04d}'
            }
            user_id = self.user_service.register_user(user_data)
            user_ids.append(user_id)
            time.sleep(0.1)  # Simulate realistic timing

        # Create orders
        import random
        products = [
            {'name': 'Laptop', 'price': 999.99},
            {'name': 'Phone', 'price': 699.99},
            {'name': 'Tablet', 'price': 299.99},
            {'name': 'Headphones', 'price': 199.99},
            {'name': 'Monitor', 'price': 399.99}
        ]

        for i in range(num_orders):
            user_id = random.choice(user_ids)

            # Random order items
            num_items = random.randint(1, 3)
            items = []
            for _ in range(num_items):
                product = random.choice(products)
                items.append({
                    **product,
                    'quantity': random.randint(1, 2)
                })

            order_id = self.order_service.create_order(user_id, items)

            # Simulate order confirmation (80% of orders get confirmed)
            if random.random() > 0.2:
                time.sleep(random.uniform(1, 3))  # Simulate user think time
                self.order_service.confirm_order(order_id)

            time.sleep(0.2)  # Simulate realistic timing

        logger.info("🎭 User journey simulation completed")

    def get_platform_status(self) -> Dict:
        """Get complete platform status"""
        # Real-time metrics
        real_time_metrics = self.analytics_service.get_real_time_metrics()

        # Historical analytics
        historical_analytics = self.analytics_service.get_historical_analytics(days=1)

        # Redis statistics
        redis_info = self.event_bus.redis_client.info()

        status = {
            'timestamp': datetime.now().isoformat(),
            'real_time_metrics': real_time_metrics,
            'historical_analytics': historical_analytics,
            'infrastructure': {
                'redis_connected_clients': redis_info.get('connected_clients', 0),
                'redis_total_commands_processed': redis_info.get('total_commands_processed', 0),
                'redis_used_memory_human': redis_info.get('used_memory_human', 'unknown')
            }
        }

        return status

def demo_integration_platform():
    """
    Complete integration platform demo
    """
    print("🚀 Event-Driven E-commerce Platform Demo")
    print("=" * 60)

    # Initialize platform
    platform = ECommercePlatform()

    # Wait for services to initialize
    time.sleep(2)

    # Simulate user journey
    print("\n🎭 Starting user journey simulation...")
    platform.simulate_user_journey(num_users=5, num_orders=10)

    # Wait for all events to be processed
    print("\n⏳ Processing events...")
    time.sleep(5)

    # Get platform status
    print("\n📊 Platform Status Report:")
    status = platform.get_platform_status()

    print(f"   📅 Report time: {status['timestamp']}")

    # Real-time metrics
    print(f"\n📈 Real-time Metrics (current hour):")
    for event_type, metrics in status['real_time_metrics'].items():
        if metrics['hourly_count'] > 0:
            print(f"   {event_type}: {metrics['hourly_count']} events")

    # Historical overview
    if status['historical_analytics'].get('total_events', 0) > 0:
        print(f"\n📊 Today's Summary:")
        print(f"   Total events: {status['historical_analytics']['total_events']}")

        events_by_type = status['historical_analytics'].get('events_by_type', {})
        for event_type, count in events_by_type.items():
            print(f"   {event_type}: {count}")

    # Infrastructure status
    print(f"\n🏗️  Infrastructure Status:")
    infra = status['infrastructure']
    print(f"   Redis connected clients: {infra['redis_connected_clients']}")
    print(f"   Redis commands processed: {infra['redis_total_commands_processed']}")
    print(f"   Redis memory usage: {infra['redis_used_memory_human']}")

    print("\n✅ Integration platform demo completed!")
    print("\n🎯 This demo showcased:")
    print("   • Event-driven architecture with all 4 technologies")
    print("   • Real-time event processing and analytics")
    print("   • Microservices communication patterns")
    print("   • Comprehensive monitoring and observability")

if __name__ == "__main__":
    demo_integration_platform()
```

## 🔧 Technology-Specific Integrations

### Kafka + Redis Integration

```python
# kafka_redis_integration.py
import json
from kafka import KafkaProducer, KafkaConsumer
import redis
from typing import Dict, Any

class KafkaRedisIntegration:
    """
    Kafka ve Redis entegrasyonu
    Real-time stream processing + caching
    """

    def __init__(self):
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def stream_with_cache(self, topic: str, data: Dict[str, Any], cache_key: str, ttl: int = 3600):
        """
        Kafka'ya stream et ve Redis'te cache'le
        """
        # Kafka'ya gönder
        self.kafka_producer.send(topic, data)

        # Redis'te cache'le
        self.redis_client.setex(cache_key, ttl, json.dumps(data))

        print(f"📤 Data streamed to Kafka topic '{topic}' and cached in Redis with key '{cache_key}'")
```

### RabbitMQ + Elasticsearch Integration

```python
# rabbitmq_elasticsearch_integration.py
import pika
import json
from elasticsearch import Elasticsearch

class RabbitMQElasticsearchIntegration:
    """
    RabbitMQ ve Elasticsearch entegrasyonu
    Reliable messaging + search/analytics
    """

    def __init__(self):
        # RabbitMQ setup
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Elasticsearch setup
        self.es = Elasticsearch(['localhost:9200'])

        self.setup_infrastructure()

    def setup_infrastructure(self):
        """Setup queues and indices"""
        # RabbitMQ queue
        self.channel.queue_declare(queue='log_processing', durable=True)

        # Elasticsearch index
        if not self.es.indices.exists(index='logs'):
            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "message": {"type": "text"},
                        "service": {"type": "keyword"},
                        "metadata": {"type": "object"}
                    }
                }
            }
            self.es.indices.create(index='logs', body=mapping)

    def process_logs(self):
        """
        RabbitMQ'dan log'ları al ve Elasticsearch'e index'le
        """
        def callback(ch, method, properties, body):
            try:
                log_data = json.loads(body)

                # Elasticsearch'e index'le
                self.es.index(index='logs', body=log_data)

                print(f"📋 Log indexed: {log_data.get('level', 'INFO')} - {log_data.get('message', '')[:50]}...")

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print(f"❌ Log processing error: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(queue='log_processing', on_message_callback=callback)
        print("🔄 Log processing started. Waiting for messages...")
        self.channel.start_consuming()
```

## 📊 Complete Monitoring Dashboard

```python
# monitoring_dashboard.py
import time
from datetime import datetime, timedelta
from typing import Dict, List
import json

class MonitoringDashboard:
    """
    Tüm teknolojiler için unified monitoring dashboard
    """

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.redis_client = event_bus.redis_client
        self.elasticsearch = event_bus.elasticsearch

    def get_system_health(self) -> Dict:
        """Sistem health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'services': {}
        }

        # Kafka health
        try:
            # Kafka producer test
            self.event_bus.kafka_producer.send('health_check', {'test': True})
            health_status['services']['kafka'] = {
                'status': 'healthy',
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            health_status['services']['kafka'] = {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
            health_status['overall_status'] = 'degraded'

        # RabbitMQ health
        try:
            # RabbitMQ connection test
            channel = self.event_bus.rabbitmq_connection.channel()
            channel.queue_declare(queue='health_check', passive=True)
            health_status['services']['rabbitmq'] = {
                'status': 'healthy',
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            health_status['services']['rabbitmq'] = {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
            health_status['overall_status'] = 'degraded'

        # Redis health
        try:
            self.redis_client.ping()
            redis_info = self.redis_client.info()
            health_status['services']['redis'] = {
                'status': 'healthy',
                'memory_used': redis_info.get('used_memory_human'),
                'connected_clients': redis_info.get('connected_clients'),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            health_status['services']['redis'] = {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
            health_status['overall_status'] = 'degraded'

        # Elasticsearch health
        try:
            es_health = self.elasticsearch.cluster.health()
            health_status['services']['elasticsearch'] = {
                'status': es_health['status'],
                'active_shards': es_health['active_shards'],
                'number_of_nodes': es_health['number_of_nodes'],
                'last_check': datetime.now().isoformat()
            }

            if es_health['status'] in ['yellow', 'red']:
                health_status['overall_status'] = 'degraded'

        except Exception as e:
            health_status['services']['elasticsearch'] = {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
            health_status['overall_status'] = 'degraded'

        return health_status

    def get_performance_metrics(self) -> Dict:
        """Performance metrics from all systems"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        metrics = {
            'timestamp': now.isoformat(),
            'time_range': '1_hour',
            'kafka_metrics': self._get_kafka_metrics(),
            'redis_metrics': self._get_redis_metrics(),
            'elasticsearch_metrics': self._get_elasticsearch_metrics()
        }

        return metrics

    def _get_kafka_metrics(self) -> Dict:
        """Kafka performance metrics"""
        # Bu gerçek ortamda JMX metrics'lerden alınır
        return {
            'messages_per_second': 150,
            'average_latency_ms': 5.2,
            'error_rate_percent': 0.1
        }

    def _get_redis_metrics(self) -> Dict:
        """Redis performance metrics"""
        try:
            info = self.redis_client.info()
            return {
                'commands_per_second': info.get('instantaneous_ops_per_sec', 0),
                'memory_usage_mb': info.get('used_memory', 0) / 1024 / 1024,
                'hit_rate_percent': self._calculate_redis_hit_rate(info),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception:
            return {}

    def _get_elasticsearch_metrics(self) -> Dict:
        """Elasticsearch performance metrics"""
        try:
            stats = self.elasticsearch.cluster.stats()
            return {
                'search_queries_per_second': 45,  # Bu gerçek ortamda API'den alınır
                'indexing_rate_per_second': 120,
                'storage_size_gb': stats['indices']['store']['size_in_bytes'] / 1024 / 1024 / 1024
            }
        except Exception:
            return {}

    def _calculate_redis_hit_rate(self, info: Dict) -> float:
        """Calculate Redis cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses

        if total == 0:
            return 0.0

        return (hits / total) * 100

    def display_dashboard(self):
        """Display comprehensive monitoring dashboard"""
        print("📊 System Monitoring Dashboard")
        print("=" * 60)

        # Health status
        health = self.get_system_health()
        status_emoji = "🟢" if health['overall_status'] == 'healthy' else "🟡"
        print(f"\n{status_emoji} Overall Status: {health['overall_status'].upper()}")
        print(f"   📅 Last check: {health['timestamp']}")

        print(f"\n🔧 Service Status:")
        for service, status in health['services'].items():
            service_emoji = "✅" if status['status'] == 'healthy' else "❌"
            print(f"   {service_emoji} {service.upper()}: {status['status']}")

            if 'error' in status:
                print(f"      Error: {status['error']}")

            # Service-specific metrics
            if service == 'redis' and 'memory_used' in status:
                print(f"      Memory: {status['memory_used']}, Clients: {status['connected_clients']}")
            elif service == 'elasticsearch' and 'active_shards' in status:
                print(f"      Shards: {status['active_shards']}, Nodes: {status['number_of_nodes']}")

        # Performance metrics
        print(f"\n⚡ Performance Metrics (Last Hour):")
        metrics = self.get_performance_metrics()

        if 'kafka_metrics' in metrics:
            kafka_metrics = metrics['kafka_metrics']
            print(f"   📤 Kafka: {kafka_metrics['messages_per_second']} msg/s, "
                  f"{kafka_metrics['average_latency_ms']}ms latency")

        if 'redis_metrics' in metrics:
            redis_metrics = metrics['redis_metrics']
            print(f"   🔴 Redis: {redis_metrics['commands_per_second']} cmd/s, "
                  f"{redis_metrics['memory_usage_mb']:.1f}MB, "
                  f"{redis_metrics['hit_rate_percent']:.1f}% hit rate")

        if 'elasticsearch_metrics' in metrics:
            es_metrics = metrics['elasticsearch_metrics']
            print(f"   🔍 Elasticsearch: {es_metrics['search_queries_per_second']} queries/s, "
                  f"{es_metrics['indexing_rate_per_second']} docs/s")

def demo_monitoring():
    """Monitoring dashboard demo"""
    from integration_platform import ECommercePlatform

    print("📊 Integrated Monitoring Dashboard Demo")
    print("=" * 50)

    # Initialize platform
    platform = ECommercePlatform()

    # Initialize monitoring
    dashboard = MonitoringDashboard(platform.event_bus)

    # Display dashboard
    dashboard.display_dashboard()

    print("\n✅ Monitoring dashboard demo completed!")

if __name__ == "__main__":
    demo_monitoring()
```

## ✅ Checklist

Bu integration bölümünü tamamladıktan sonra:

- [ ] Event-driven architecture patterns implementasyonu yapabiliyorum
- [ ] Microservices communication design edebiliyorum
- [ ] Real-time analytics pipeline kurabiliyorum
- [ ] Complete monitoring ve observability setup edebiliyorum
- [ ] Fault tolerance patterns uygulayabiliyorum
- [ ] Performance optimization strategies geliştirebiliyorum
- [ ] Production-ready integration solutions geliştirebiliyorum

## 🎯 Use Cases Covered

1. **E-commerce Platform** - Complete event-driven architecture
2. **Real-time Analytics** - Stream processing + search
3. **Notification System** - Reliable messaging patterns
4. **Caching Strategy** - Multi-layer caching
5. **Event Sourcing** - Complete audit trail
6. **Monitoring & Observability** - Full system visibility

## 🚀 Next Steps

Bu comprehensive integration guide ile artık tüm 4 teknoloji için production-ready solutions geliştirebilirsiniz:

1. **Start with a specific use case** - E-commerce, analytics, etc.
2. **Choose appropriate technology mix** - Event types → Technology mapping
3. **Implement step by step** - Service by service approach
4. **Add monitoring early** - Observability-first design
5. **Scale incrementally** - Add complexity as needed

---

**🎉 Tebrikler!** Event-driven architecture ile modern, scalable systems geliştirme journey'inizi tamamladınız! 🚀
