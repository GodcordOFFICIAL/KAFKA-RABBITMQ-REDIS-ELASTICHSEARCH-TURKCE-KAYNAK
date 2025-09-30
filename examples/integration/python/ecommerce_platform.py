"""
Complete Event-Driven E-commerce Platform
Kafka + RabbitMQ + Redis + Elasticsearch integration
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging
import threading
import random

# Technology clients
try:
    from kafka import KafkaProducer, KafkaConsumer
except ImportError:
    print("⚠️ kafka-python not installed. Run: pip install kafka-python")
    KafkaProducer = KafkaConsumer = None

try:
    import pika
except ImportError:
    print("⚠️ pika not installed. Run: pip install pika")
    pika = None

try:
    import redis
except ImportError:
    print("⚠️ redis not installed. Run: pip install redis")
    redis = None

try:
    from elasticsearch import Elasticsearch
except ImportError:
    print("⚠️ elasticsearch not installed. Run: pip install elasticsearch")
    Elasticsearch = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

class TechnologyChecker:
    """Check which technologies are available"""
    
    @staticmethod
    def check_kafka() -> bool:
        if KafkaProducer is None:
            return False
        try:
            # Test connection
            producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                request_timeout_ms=5000,
                api_version=(0, 10, 1)
            )
            producer.close()
            return True
        except Exception:
            return False
    
    @staticmethod
    def check_rabbitmq() -> bool:
        if pika is None:
            return False
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost', connection_attempts=3, retry_delay=1)
            )
            connection.close()
            return True
        except Exception:
            return False
    
    @staticmethod
    def check_redis() -> bool:
        if redis is None:
            return False
        try:
            client = redis.Redis(host='localhost', port=6379, socket_timeout=2)
            client.ping()
            return True
        except Exception:
            return False
    
    @staticmethod
    def check_elasticsearch() -> bool:
        if Elasticsearch is None:
            return False
        try:
            es = Elasticsearch(['localhost:9200'], request_timeout=5)
            es.ping()
            return True
        except Exception:
            return False
    
    @classmethod
    def get_available_technologies(cls) -> Dict[str, bool]:
        return {
            'kafka': cls.check_kafka(),
            'rabbitmq': cls.check_rabbitmq(), 
            'redis': cls.check_redis(),
            'elasticsearch': cls.check_elasticsearch()
        }

class MockEventBus:
    """Mock event bus for when services are not available"""
    
    def __init__(self):
        self.events = []
        logger.info("🎭 Mock Event Bus initialized (technologies not available)")
    
    def publish_event(self, event: Event, **kwargs):
        self.events.append(event)
        logger.info(f"📤 Mock: Event published - {event.event_type.value}")
    
    def get_events(self) -> List[Event]:
        return self.events

class EventBus:
    """Central event bus managing all message technologies"""
    
    def __init__(self):
        """Initialize available technology connections"""
        self.available_tech = TechnologyChecker.get_available_technologies()
        
        # Initialize only available technologies
        self.kafka_producer = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.redis_client = None
        self.elasticsearch = None
        
        self._initialize_technologies()
        self._setup_infrastructure()
        
        logger.info(f"✅ Event Bus initialized with: {', '.join([k for k, v in self.available_tech.items() if v])}")
    
    def _initialize_technologies(self):
        """Initialize available technologies"""
        # Kafka
        if self.available_tech['kafka']:
            try:
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=['localhost:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None
                )
                logger.info("✅ Kafka producer initialized")
            except Exception as e:
                logger.warning(f"⚠️ Kafka initialization failed: {e}")
                self.available_tech['kafka'] = False
        
        # RabbitMQ
        if self.available_tech['rabbitmq']:
            try:
                self.rabbitmq_connection = pika.BlockingConnection(
                    pika.ConnectionParameters('localhost')
                )
                self.rabbitmq_channel = self.rabbitmq_connection.channel()
                logger.info("✅ RabbitMQ connection initialized")
            except Exception as e:
                logger.warning(f"⚠️ RabbitMQ initialization failed: {e}")
                self.available_tech['rabbitmq'] = False
        
        # Redis
        if self.available_tech['redis']:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Redis client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Redis initialization failed: {e}")
                self.available_tech['redis'] = False
        
        # Elasticsearch
        if self.available_tech['elasticsearch']:
            try:
                self.elasticsearch = Elasticsearch(['localhost:9200'])
                self.elasticsearch.ping()
                logger.info("✅ Elasticsearch client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Elasticsearch initialization failed: {e}")
                self.available_tech['elasticsearch'] = False
    
    def _setup_infrastructure(self):
        """Setup queues, topics and indices for available technologies"""
        # RabbitMQ setup
        if self.available_tech['rabbitmq'] and self.rabbitmq_channel:
            try:
                self.rabbitmq_channel.exchange_declare(
                    exchange='notifications',
                    exchange_type='topic',
                    durable=True
                )
                
                for queue_name in ['email.queue', 'sms.queue', 'push.queue']:
                    self.rabbitmq_channel.queue_declare(queue=queue_name, durable=True)
                    self.rabbitmq_channel.queue_bind(
                        exchange='notifications',
                        queue=queue_name,
                        routing_key=queue_name.replace('.queue', '.*')
                    )
            except Exception as e:
                logger.warning(f"⚠️ RabbitMQ setup failed: {e}")
        
        # Elasticsearch setup
        if self.available_tech['elasticsearch'] and self.elasticsearch:
            try:
                # Events index
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
                logger.warning(f"⚠️ Elasticsearch setup failed: {e}")
    
    def publish_event(self, event: Event, use_kafka: bool = True, use_rabbitmq: bool = False):
        """Publish event to available message systems"""
        try:
            event_data = event.to_dict()
            
            # Kafka for high-throughput domain events
            if use_kafka and self.available_tech['kafka'] and self.kafka_producer:
                topic = f"events.{event.event_type.value.split('.')[0]}"
                self.kafka_producer.send(
                    topic=topic,
                    key=event.aggregate_id,
                    value=event_data
                )
                logger.info(f"📤 Event published to Kafka: {event.event_type.value}")
            
            # RabbitMQ for reliable notifications
            if use_rabbitmq and self.available_tech['rabbitmq'] and self.rabbitmq_channel:
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
            
            # Elasticsearch for event store
            if self.available_tech['elasticsearch'] and self.elasticsearch:
                self.elasticsearch.index(
                    index='events',
                    id=event.event_id,
                    body=event_data
                )
            
            # Redis for caching and pub/sub
            if self.available_tech['redis'] and self.redis_client:
                # Cache recent events
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

class ECommerceService:
    """Base service class"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.redis_client = event_bus.redis_client
        self.available_tech = event_bus.available_tech

class UserService(ECommerceService):
    """User management service"""
    
    def register_user(self, user_data: Dict) -> str:
        """Register new user and publish event"""
        user_id = str(uuid.uuid4())
        
        user_info = {
            **user_data,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Store in Redis if available, otherwise in memory
        if self.available_tech['redis'] and self.redis_client:
            self.redis_client.hset(f"user:{user_id}", mapping=user_info)
        
        # Publish event
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

class OrderService(ECommerceService):
    """Order management service"""
    
    def create_order(self, user_id: str, items: List[Dict]) -> str:
        """Create new order and publish events"""
        order_id = str(uuid.uuid4())
        
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
        if self.available_tech['redis'] and self.redis_client:
            self.redis_client.hset(
                f"order:{order_id}",
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                        for k, v in order_data.items()}
            )
        
        # Publish event
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

class AnalyticsService(ECommerceService):
    """Real-time analytics service"""
    
    def track_metrics(self, event_type: str, data: Dict):
        """Track metrics in available systems"""
        timestamp = datetime.now()
        
        # Redis counters
        if self.available_tech['redis'] and self.redis_client:
            hour_key = timestamp.strftime('%Y%m%d%H')
            day_key = timestamp.strftime('%Y%m%d')
            
            self.redis_client.incr(f"analytics:events:{event_type}:hourly:{hour_key}")
            self.redis_client.incr(f"analytics:events:{event_type}:daily:{day_key}")
            
            # Set TTL
            self.redis_client.expire(f"analytics:events:{event_type}:hourly:{hour_key}", 24 * 3600)
            self.redis_client.expire(f"analytics:events:{event_type}:daily:{day_key}", 30 * 24 * 3600)
        
        # Elasticsearch analytics
        if self.available_tech['elasticsearch'] and self.event_bus.elasticsearch:
            analytics_doc = {
                'event_type': event_type,
                'timestamp': timestamp.isoformat(),
                'hour': timestamp.strftime('%Y%m%d%H'),
                'date': timestamp.strftime('%Y%m%d'),
                'data': data
            }
            
            try:
                self.event_bus.elasticsearch.index(
                    index='analytics',
                    body=analytics_doc
                )
            except Exception as e:
                logger.error(f"❌ Analytics indexing error: {e}")
    
    def get_metrics_summary(self) -> Dict:
        """Get metrics summary from available systems"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'available_technologies': self.available_tech,
            'metrics': {}
        }
        
        # Redis metrics
        if self.available_tech['redis'] and self.redis_client:
            now = datetime.now()
            current_hour = now.strftime('%Y%m%d%H')
            current_date = now.strftime('%Y%m%d')
            
            for event_type in EventType:
                event_name = event_type.value
                hourly_key = f"analytics:events:{event_name}:hourly:{current_hour}"
                daily_key = f"analytics:events:{event_name}:daily:{current_date}"
                
                summary['metrics'][event_name] = {
                    'hourly_count': int(self.redis_client.get(hourly_key) or 0),
                    'daily_count': int(self.redis_client.get(daily_key) or 0)
                }
        
        return summary

class ECommercePlatform:
    """Complete e-commerce platform orchestrator"""
    
    def __init__(self):
        """Initialize platform with available technologies"""
        # Check available technologies
        available_tech = TechnologyChecker.get_available_technologies()
        
        print("🔍 Technology Availability Check:")
        for tech, available in available_tech.items():
            status = "✅" if available else "❌"
            print(f"   {status} {tech.upper()}: {'Available' if available else 'Not available'}")
        
        if not any(available_tech.values()):
            print("\n⚠️ No technologies available. Using mock services.")
            self.event_bus = MockEventBus()
            self.use_mock = True
        else:
            self.event_bus = EventBus()
            self.use_mock = False
        
        # Initialize services
        if not self.use_mock:
            self.user_service = UserService(self.event_bus)
            self.order_service = OrderService(self.event_bus)
            self.analytics_service = AnalyticsService(self.event_bus)
        
        logger.info("🚀 E-commerce platform initialized")
    
    def simulate_user_journey(self, num_users: int = 5, num_orders: int = 10):
        """Simulate complete user journey"""
        if self.use_mock:
            self._simulate_mock_journey(num_users, num_orders)
            return
        
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
            time.sleep(0.1)
        
        # Create orders
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
            
            # Track analytics
            self.analytics_service.track_metrics('order.created', {'order_id': order_id})
            
            time.sleep(0.2)
        
        logger.info("🎭 User journey simulation completed")
    
    def _simulate_mock_journey(self, num_users: int, num_orders: int):
        """Simulate journey with mock services"""
        logger.info(f"🎭 Mock simulation: {num_users} users, {num_orders} orders")
        
        for i in range(num_users):
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_REGISTERED,
                aggregate_id=str(uuid.uuid4()),
                data={'email': f'user{i+1}@example.com'},
                timestamp=datetime.now().isoformat()
            )
            self.event_bus.publish_event(event)
        
        for i in range(num_orders):
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ORDER_CREATED,
                aggregate_id=str(uuid.uuid4()),
                data={'total_amount': random.uniform(50, 500)},
                timestamp=datetime.now().isoformat()
            )
            self.event_bus.publish_event(event)
        
        logger.info("🎭 Mock simulation completed")
    
    def get_platform_status(self) -> Dict:
        """Get platform status"""
        if self.use_mock:
            return {
                'mode': 'mock',
                'events_count': len(self.event_bus.get_events()),
                'available_technologies': TechnologyChecker.get_available_technologies()
            }
        
        status = {
            'mode': 'live',
            'available_technologies': self.event_bus.available_tech,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add analytics if available
        try:
            metrics = self.analytics_service.get_metrics_summary()
            status['metrics'] = metrics
        except Exception as e:
            logger.error(f"❌ Status check error: {e}")
            status['error'] = str(e)
        
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
    platform.simulate_user_journey(num_users=3, num_orders=5)
    
    # Wait for events to be processed
    print("\n⏳ Processing events...")
    time.sleep(3)
    
    # Get platform status
    print("\n📊 Platform Status Report:")
    status = platform.get_platform_status()
    
    print(f"   📅 Report time: {status.get('timestamp', 'N/A')}")
    print(f"   🎭 Mode: {status.get('mode', 'unknown')}")
    
    # Technology status
    available_tech = status.get('available_technologies', {})
    print(f"\n🔧 Available Technologies:")
    for tech, available in available_tech.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {tech.upper()}")
    
    # Metrics if available
    if 'metrics' in status and status['metrics'].get('metrics'):
        print(f"\n📈 Event Metrics:")
        for event_type, counts in status['metrics']['metrics'].items():
            if counts['hourly_count'] > 0 or counts['daily_count'] > 0:
                print(f"   {event_type}: {counts['hourly_count']} this hour, {counts['daily_count']} today")
    
    if status.get('mode') == 'mock':
        print(f"\n🎭 Mock Events Generated: {status.get('events_count', 0)}")
    
    print("\n✅ Integration platform demo completed!")
    print("\n🎯 This demo showcased:")
    print("   • Event-driven architecture with available technologies")
    print("   • Graceful degradation when services are unavailable") 
    print("   • Microservices communication patterns")
    print("   • Real-time analytics and monitoring")
    
    # Installation suggestions
    missing_tech = [tech for tech, available in available_tech.items() if not available]
    if missing_tech:
        print(f"\n💡 To enable missing technologies:")
        for tech in missing_tech:
            if tech == 'kafka':
                print(f"   📤 Kafka: Start with 'make start-kafka'")
            elif tech == 'rabbitmq':
                print(f"   🐰 RabbitMQ: Start with 'make start-rabbitmq'")
            elif tech == 'redis':
                print(f"   🔴 Redis: Start with 'make start-redis'")
            elif tech == 'elasticsearch':
                print(f"   🔍 Elasticsearch: Start with 'make start-elasticsearch'")

if __name__ == "__main__":
    demo_integration_platform()