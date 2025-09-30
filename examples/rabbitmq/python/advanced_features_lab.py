"""
RabbitMQ Advanced Features Lab
=============================

Bu script tüm advanced features'ları birleştirerek kapsamlı bir lab ortamı sunar.

Features:
- Dead Letter Queues (DLQ)
- Message TTL
- Priority Queues
- Publisher Confirms
- Mixed scenarios

Kullanım:
    python advanced_features_lab.py setup
    python advanced_features_lab.py demo
    python advanced_features_lab.py cleanup
"""

import pika
import json
import time
import random
import threading
import argparse
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class MessageType(Enum):
    NORMAL = 1
    PRIORITY = 2
    TTL_SHORT = 3
    TTL_LONG = 4
    DLQ_TEST = 5
    MIXED = 6


class AdvancedFeaturesLab:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        
        # Publisher confirms
        self.channel.confirm_delivery()
        
        # Statistics
        self.stats = {
            'sent': 0,
            'confirmed': 0,
            'processed': 0,
            'failed': 0,
            'dlq': 0,
            'expired': 0,
            'priority_distribution': defaultdict(int),
            'feature_usage': defaultdict(int)
        }
        
        self.setup_complete_system()
    
    def setup_complete_system(self):
        """Tüm sistemi kurar"""
        print("🔧 Advanced Features Lab kurulumu başlıyor...")
        
        # Main exchanges
        exchanges = [
            ('advanced_lab', 'topic'),
            ('advanced_lab_dlx', 'direct'),
            ('ttl_demo', 'direct'),
            ('priority_tasks', 'direct')
        ]
        
        for exchange_name, exchange_type in exchanges:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True
            )
        
        # Queue definitions with different feature combinations
        queue_configs = [
            # Normal queue with DLQ
            {
                'name': 'normal_queue',
                'args': {
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'failed'
                }
            },
            
            # Priority queue with DLQ and TTL
            {
                'name': 'priority_queue',
                'args': {
                    'x-max-priority': 10,
                    'x-message-ttl': 300000,  # 5 minutes
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'failed_priority'
                }
            },
            
            # Short TTL queue
            {
                'name': 'ttl_short_queue',
                'args': {
                    'x-message-ttl': 30000,  # 30 seconds
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'expired'
                }
            },
            
            # Long TTL queue with priority
            {
                'name': 'ttl_long_queue',
                'args': {
                    'x-message-ttl': 180000,  # 3 minutes
                    'x-max-priority': 5,
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'expired'
                }
            },
            
            # DLQ test queue (high failure rate simulation)
            {
                'name': 'dlq_test_queue',
                'args': {
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'dlq_test',
                    'x-max-retries': 2
                }
            },
            
            # Mixed features queue
            {
                'name': 'mixed_features_queue',
                'args': {
                    'x-max-priority': 10,
                    'x-message-ttl': 120000,  # 2 minutes
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'mixed_failed'
                }
            },
            
            # Temporary queue (self-deleting)
            {
                'name': 'temp_queue',
                'args': {
                    'x-expires': 90000,  # Queue expires in 90 seconds
                    'x-message-ttl': 45000,  # Messages expire in 45 seconds
                    'x-dead-letter-exchange': 'advanced_lab_dlx',
                    'x-dead-letter-routing-key': 'temp_expired'
                }
            }
        ]
        
        # Create queues
        for config in queue_configs:
            self.channel.queue_declare(
                queue=config['name'],
                durable=True,
                arguments=config['args']
            )
        
        # DLQ and expired message queues
        dlq_queues = [
            'failed_messages',
            'failed_priority_messages', 
            'expired_messages',
            'dlq_test_messages',
            'mixed_failed_messages',
            'temp_expired_messages'
        ]
        
        for queue_name in dlq_queues:
            self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Recovery and archive queues
        self.channel.queue_declare(queue='recovery_queue', durable=True)
        self.channel.queue_declare(queue='archive_queue', durable=True)
        
        # Bindings
        bindings = [
            # Main routing
            ('advanced_lab', 'normal_queue', 'normal.*'),
            ('advanced_lab', 'priority_queue', 'priority.*'),
            ('advanced_lab', 'ttl_short_queue', 'ttl.short.*'),
            ('advanced_lab', 'ttl_long_queue', 'ttl.long.*'),
            ('advanced_lab', 'dlq_test_queue', 'dlq.*'),
            ('advanced_lab', 'mixed_features_queue', 'mixed.*'),
            ('advanced_lab', 'temp_queue', 'temp.*'),
            
            # DLX routing
            ('advanced_lab_dlx', 'failed_messages', 'failed'),
            ('advanced_lab_dlx', 'failed_priority_messages', 'failed_priority'),
            ('advanced_lab_dlx', 'expired_messages', 'expired'),
            ('advanced_lab_dlx', 'dlq_test_messages', 'dlq_test'),
            ('advanced_lab_dlx', 'mixed_failed_messages', 'mixed_failed'),
            ('advanced_lab_dlx', 'temp_expired_messages', 'temp_expired')
        ]
        
        for exchange, queue, routing_key in bindings:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue,
                routing_key=routing_key
            )
        
        print("✅ Advanced Features Lab hazır!")
        self.print_system_overview()
    
    def print_system_overview(self):
        """Sistem özetini yazdırır"""
        print(f"\n📋 System Overview:")
        print("-" * 50)
        print("🔀 Exchanges:")
        print("   • advanced_lab (topic)")
        print("   • advanced_lab_dlx (direct)")
        print("   • ttl_demo (direct)")
        print("   • priority_tasks (direct)")
        
        print("\n📦 Queues & Features:")
        queue_features = [
            ("normal_queue", "DLQ"),
            ("priority_queue", "Priority(0-10) + DLQ + TTL(5min)"),
            ("ttl_short_queue", "TTL(30s) + DLQ"),
            ("ttl_long_queue", "TTL(3min) + Priority(0-5) + DLQ"),
            ("dlq_test_queue", "DLQ + Max Retries(2)"),
            ("mixed_features_queue", "Priority(0-10) + TTL(2min) + DLQ"),
            ("temp_queue", "Self-delete(90s) + TTL(45s) + DLQ")
        ]
        
        for queue, features in queue_features:
            print(f"   📋 {queue}: {features}")
    
    def send_message(self, msg_type: MessageType, content: str, routing_key: str, 
                    priority: int = 0, ttl: int = None, simulate_failure: bool = False):
        """Advanced mesaj gönderir"""
        message_data = {
            'id': f"msg_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            'type': msg_type.name,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'priority': priority,
            'ttl': ttl,
            'simulate_failure': simulate_failure,
            'routing_key': routing_key
        }
        
        # Calculate expiration if TTL set
        if ttl:
            expiration_time = datetime.now() + timedelta(seconds=ttl)
            message_data['expires_at'] = expiration_time.isoformat()
        
        # Properties
        properties = pika.BasicProperties(
            delivery_mode=2,
            message_id=message_data['id'],
            timestamp=int(datetime.now().timestamp()),
            priority=priority,
            headers={
                'message_type': msg_type.name,
                'sent_at': datetime.now().isoformat(),
                'lab_test': True,
                'simulate_failure': simulate_failure,
                'features_used': self.get_features_used(routing_key, priority, ttl)
            }
        )
        
        # Message-level TTL
        if ttl:
            properties.expiration = str(ttl * 1000)
        
        try:
            result = self.channel.basic_publish(
                exchange='advanced_lab',
                routing_key=routing_key,
                body=json.dumps(message_data, indent=2),
                properties=properties,
                mandatory=True
            )
            
            self.stats['sent'] += 1
            if result:
                self.stats['confirmed'] += 1
                
            # Update statistics
            self.stats['priority_distribution'][priority] += 1
            for feature in properties.headers['features_used']:
                self.stats['feature_usage'][feature] += 1
            
            # Display info
            features_str = ', '.join(properties.headers['features_used'])
            emoji = self.get_message_emoji(msg_type, priority)
            
            print(f"{emoji} {msg_type.name}: {content[:40]}... ({features_str})")
            return True
            
        except Exception as e:
            print(f"💥 Send error: {str(e)}")
            return False
    
    def get_features_used(self, routing_key, priority, ttl):
        """Kullanılan features'ları döndürür"""
        features = []
        
        if 'priority' in routing_key or priority > 0:
            features.append('Priority')
        
        if 'ttl' in routing_key or ttl:
            features.append('TTL')
            
        if 'dlq' in routing_key:
            features.append('DLQ')
            
        if 'mixed' in routing_key:
            features.extend(['Priority', 'TTL', 'DLQ'])
            
        if 'temp' in routing_key:
            features.extend(['Self-Delete', 'TTL'])
        
        if not features:
            features.append('Basic')
            
        return features
    
    def get_message_emoji(self, msg_type, priority):
        """Mesaj emoji'sini döndürür"""
        if msg_type == MessageType.PRIORITY:
            if priority >= 8:
                return "🔴"
            elif priority >= 5:
                return "🟡"
            else:
                return "🟢"
        elif msg_type == MessageType.TTL_SHORT:
            return "⏰"
        elif msg_type == MessageType.TTL_LONG:
            return "⏳"
        elif msg_type == MessageType.DLQ_TEST:
            return "💀"
        elif msg_type == MessageType.MIXED:
            return "🎯"
        else:
            return "📝"
    
    def demo_all_features(self):
        """Tüm features'ları demo eder"""
        print(f"\n🚀 Advanced Features Demo başlıyor...")
        print("=" * 60)
        
        # 1. Normal messages
        print(f"\n📝 1. Normal Messages (DLQ only):")
        for i in range(3):
            self.send_message(
                MessageType.NORMAL, 
                f"Normal message {i+1}",
                'normal.message'
            )
        
        # 2. Priority messages
        print(f"\n🎯 2. Priority Messages:")
        priorities = [10, 7, 5, 2, 0]
        for i, priority in enumerate(priorities):
            self.send_message(
                MessageType.PRIORITY,
                f"Priority task {i+1} (P{priority})",
                'priority.task',
                priority=priority
            )
        
        # 3. TTL Short messages
        print(f"\n⏰ 3. Short TTL Messages (30s queue TTL):")
        for i in range(2):
            self.send_message(
                MessageType.TTL_SHORT,
                f"Short-lived message {i+1}",
                'ttl.short.message'
            )
        
        # 4. TTL Long messages with custom TTL
        print(f"\n⏳ 4. Long TTL Messages with custom TTL:")
        custom_ttls = [60, 90]
        for i, ttl in enumerate(custom_ttls):
            self.send_message(
                MessageType.TTL_LONG,
                f"Custom TTL message {i+1} ({ttl}s)",
                'ttl.long.message',
                ttl=ttl,
                priority=3
            )
        
        # 5. DLQ test messages
        print(f"\n💀 5. DLQ Test Messages (high failure rate):")
        for i in range(3):
            self.send_message(
                MessageType.DLQ_TEST,
                f"DLQ test message {i+1}",
                'dlq.test',
                simulate_failure=True
            )
        
        # 6. Mixed features
        print(f"\n🎯 6. Mixed Features Messages:")
        mixed_scenarios = [
            ("High priority urgent task", 9, 45),
            ("Medium priority with TTL", 5, 90),
            ("Low priority background", 1, None)
        ]
        
        for i, (content, priority, ttl) in enumerate(mixed_scenarios):
            self.send_message(
                MessageType.MIXED,
                content,
                'mixed.scenario',
                priority=priority,
                ttl=ttl
            )
        
        # 7. Temporary queue messages
        print(f"\n🔥 7. Temporary Queue Messages:")
        for i in range(2):
            self.send_message(
                MessageType.NORMAL,
                f"Temporary message {i+1}",
                'temp.message'
            )
        
        print(f"\n" + "=" * 60)
        self.print_demo_statistics()
    
    def stress_test(self, duration_seconds=60, messages_per_second=10):
        """Stress test yapar"""
        print(f"\n🔥 Stress Test başlıyor...")
        print(f"   ⏱️ Duration: {duration_seconds}s")
        print(f"   📊 Rate: {messages_per_second} msg/s")
        print(f"   📦 Total: ~{duration_seconds * messages_per_second} messages")
        
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Random message type and features
            msg_types = list(MessageType)
            msg_type = random.choice(msg_types)
            
            priority = random.randint(0, 10) if msg_type in [MessageType.PRIORITY, MessageType.MIXED] else 0
            ttl = random.choice([None, 30, 60, 120]) if msg_type in [MessageType.TTL_SHORT, MessageType.TTL_LONG, MessageType.MIXED] else None
            
            routing_keys = {
                MessageType.NORMAL: 'normal.stress',
                MessageType.PRIORITY: 'priority.stress',
                MessageType.TTL_SHORT: 'ttl.short.stress',
                MessageType.TTL_LONG: 'ttl.long.stress',
                MessageType.DLQ_TEST: 'dlq.stress',
                MessageType.MIXED: 'mixed.stress'
            }
            
            routing_key = routing_keys[msg_type]
            simulate_failure = msg_type == MessageType.DLQ_TEST and random.random() < 0.3
            
            self.send_message(
                msg_type,
                f"Stress test message {message_count + 1}",
                routing_key,
                priority=priority,
                ttl=ttl,
                simulate_failure=simulate_failure
            )
            
            message_count += 1
            
            # Rate limiting
            time.sleep(1.0 / messages_per_second)
            
            # Progress update
            if message_count % (messages_per_second * 10) == 0:
                elapsed = time.time() - start_time
                print(f"   📊 {message_count} messages sent in {elapsed:.1f}s")
        
        elapsed = time.time() - start_time
        actual_rate = message_count / elapsed
        
        print(f"\n🏁 Stress Test tamamlandı:")
        print(f"   📦 Messages sent: {message_count}")
        print(f"   ⏱️ Actual duration: {elapsed:.1f}s")
        print(f"   📈 Actual rate: {actual_rate:.1f} msg/s")
        print(f"   ✅ Confirmed: {self.stats['confirmed']}")
        print(f"   📊 Success rate: {(self.stats['confirmed'] / self.stats['sent']) * 100:.1f}%")
    
    def print_demo_statistics(self):
        """Demo istatistiklerini yazdırır"""
        print(f"📊 Demo İstatistikleri:")
        print(f"   📤 Sent: {self.stats['sent']}")
        print(f"   ✅ Confirmed: {self.stats['confirmed']}")
        print(f"   📈 Success Rate: {(self.stats['confirmed'] / self.stats['sent']) * 100:.1f}%")
        
        if self.stats['priority_distribution']:
            print(f"\n🎯 Priority Distribution:")
            for priority in range(10, -1, -1):
                count = self.stats['priority_distribution'][priority]
                if count > 0:
                    print(f"   P{priority}: {count} messages")
        
        if self.stats['feature_usage']:
            print(f"\n🔧 Feature Usage:")
            for feature, count in sorted(self.stats['feature_usage'].items()):
                print(f"   {feature}: {count} messages")
    
    def monitor_queues(self):
        """Queue durumlarını izler"""
        try:
            queues = [
                'normal_queue',
                'priority_queue', 
                'ttl_short_queue',
                'ttl_long_queue',
                'dlq_test_queue',
                'mixed_features_queue',
                'temp_queue',
                'failed_messages',
                'expired_messages'
            ]
            
            print(f"\n📊 Queue Status ({datetime.now().strftime('%H:%M:%S')}):")
            print("-" * 50)
            
            for queue_name in queues:
                try:
                    result = self.channel.queue_declare(queue=queue_name, passive=True)
                    count = result.method.message_count
                    
                    # Queue type emoji
                    if 'failed' in queue_name or 'expired' in queue_name:
                        emoji = "⚰️" if count > 0 else "📭"
                    elif 'priority' in queue_name:
                        emoji = "🎯"
                    elif 'ttl' in queue_name:
                        emoji = "⏰"
                    elif 'dlq' in queue_name:
                        emoji = "💀"
                    elif 'mixed' in queue_name:
                        emoji = "🎨"
                    elif 'temp' in queue_name:
                        emoji = "🔥"
                    else:
                        emoji = "📦"
                    
                    status = f"{count} messages"
                    if count > 100:
                        status += " ⚠️"
                    elif count > 50:
                        status += " 📈"
                    
                    print(f"   {emoji} {queue_name}: {status}")
                    
                except pika.exceptions.ChannelClosedByBroker:
                    print(f"   💨 {queue_name}: Queue expired/deleted")
                    # Reopen channel
                    self.channel = self.connection.channel()
                except Exception as e:
                    print(f"   ❌ {queue_name}: Error - {str(e)}")
            
        except Exception as e:
            print(f"❌ Queue monitoring error: {str(e)}")
    
    def cleanup_lab(self):
        """Lab'ı temizler"""
        print(f"\n🧹 Lab cleanup başlıyor...")
        
        try:
            # Delete all test queues
            queues = [
                'normal_queue', 'priority_queue', 'ttl_short_queue',
                'ttl_long_queue', 'dlq_test_queue', 'mixed_features_queue',
                'temp_queue', 'failed_messages', 'failed_priority_messages',
                'expired_messages', 'dlq_test_messages', 'mixed_failed_messages',
                'temp_expired_messages', 'recovery_queue', 'archive_queue'
            ]
            
            for queue_name in queues:
                try:
                    self.channel.queue_delete(queue=queue_name)
                    print(f"   🗑️ Deleted queue: {queue_name}")
                except Exception as e:
                    print(f"   ⚠️ Could not delete {queue_name}: {str(e)}")
            
            # Delete exchanges
            exchanges = ['advanced_lab', 'advanced_lab_dlx', 'ttl_demo', 'priority_tasks']
            for exchange_name in exchanges:
                try:
                    self.channel.exchange_delete(exchange=exchange_name)
                    print(f"   🗑️ Deleted exchange: {exchange_name}")
                except Exception as e:
                    print(f"   ⚠️ Could not delete {exchange_name}: {str(e)}")
            
            print(f"✅ Lab cleanup tamamlandı")
            
        except Exception as e:
            print(f"❌ Cleanup error: {str(e)}")
    
    def close(self):
        self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ Advanced Features Lab')
    parser.add_argument('action', 
                       choices=['setup', 'demo', 'stress', 'monitor', 'cleanup'],
                       help='Lab action')
    parser.add_argument('--duration', type=int, default=60,
                       help='Stress test duration (seconds)')
    parser.add_argument('--rate', type=int, default=10,
                       help='Stress test rate (messages/second)')
    
    args = parser.parse_args()
    
    lab = AdvancedFeaturesLab()
    
    try:
        if args.action == 'setup':
            print("✅ Lab setup tamamlandı!")
            lab.monitor_queues()
            
        elif args.action == 'demo':
            lab.demo_all_features()
            print(f"\n💡 Şimdi consumer'ları çalıştırarak mesajları işleyebilirsiniz")
            
        elif args.action == 'stress':
            lab.stress_test(args.duration, args.rate)
            
        elif args.action == 'monitor':
            lab.monitor_queues()
            
        elif args.action == 'cleanup':
            lab.cleanup_lab()
            
    finally:
        lab.close()


if __name__ == "__main__":
    main()