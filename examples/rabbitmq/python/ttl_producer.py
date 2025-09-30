"""
RabbitMQ TTL (Time To Live) Producer
===================================

Bu script farklı TTL stratejilerini demonstre eder.

TTL Türleri:
- Message-level TTL: Her mesaj için ayrı TTL
- Queue-level TTL: Queue'daki tüm mesajlar için TTL  
- Queue TTL: Queue'un kendisi için TTL

Kullanım:
    python ttl_producer.py
    python ttl_producer.py demo
    python ttl_producer.py custom "Test message" 30
"""

import pika
import json
import time
import argparse
from datetime import datetime, timedelta


class TTLProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        
        # Publisher confirms
        self.channel.confirm_delivery()
        
        self.setup_ttl_system()
        self.sent_count = 0
        self.confirmed_count = 0
    
    def setup_ttl_system(self):
        """TTL sistemini kurar"""
        print("🔧 TTL sistemi kuruluyor...")
        
        # Main exchange
        self.channel.exchange_declare(
            exchange='ttl_demo',
            exchange_type='direct',
            durable=True
        )
        
        # DLX for expired messages
        self.channel.exchange_declare(
            exchange='ttl_demo_dlx',
            exchange_type='direct',
            durable=True
        )
        
        # Queue with TTL (30 seconds) - tüm mesajlar 30 saniyede expire olur
        self.channel.queue_declare(
            queue='short_lived_messages',
            durable=True,
            arguments={
                'x-message-ttl': 30000,  # 30 saniye
                'x-dead-letter-exchange': 'ttl_demo_dlx',
                'x-dead-letter-routing-key': 'expired'
            }
        )
        
        # Queue without TTL - sadece message-level TTL
        self.channel.queue_declare(
            queue='normal_messages',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'ttl_demo_dlx',
                'x-dead-letter-routing-key': 'expired'
            }
        )
        
        # Queue with long TTL (5 minutes)
        self.channel.queue_declare(
            queue='long_lived_messages',
            durable=True,
            arguments={
                'x-message-ttl': 300000,  # 5 dakika
                'x-dead-letter-exchange': 'ttl_demo_dlx',
                'x-dead-letter-routing-key': 'expired'
            }
        )
        
        # Expired messages queue
        self.channel.queue_declare(
            queue='expired_messages',
            durable=True
        )
        
        # Temporary queue (queue kendisi 60 saniyede silinir)
        self.channel.queue_declare(
            queue='temp_queue',
            durable=False,
            arguments={
                'x-expires': 60000,  # Queue 60 saniyede silinir
                'x-message-ttl': 20000,  # Mesajlar 20 saniyede expire
                'x-dead-letter-exchange': 'ttl_demo_dlx',
                'x-dead-letter-routing-key': 'expired'
            }
        )
        
        # Bindings
        bindings = [
            ('ttl_demo', 'short_lived_messages', 'short'),
            ('ttl_demo', 'normal_messages', 'normal'),
            ('ttl_demo', 'long_lived_messages', 'long'),
            ('ttl_demo', 'temp_queue', 'temp'),
            ('ttl_demo_dlx', 'expired_messages', 'expired')
        ]
        
        for exchange, queue, routing_key in bindings:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue,
                routing_key=routing_key
            )
        
        print("✅ TTL sistemi hazır!")
    
    def send_message_with_ttl(self, message, ttl_seconds=None, routing_key='normal', priority=0):
        """TTL'li mesaj gönderir"""
        message_data = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'ttl_seconds': ttl_seconds,
            'routing_key': routing_key,
            'priority': priority
        }
        
        # Calculate expiration time
        if ttl_seconds:
            expiration_time = datetime.now() + timedelta(seconds=ttl_seconds)
            message_data['expires_at'] = expiration_time.isoformat()
        
        properties = pika.BasicProperties(
            delivery_mode=2,
            timestamp=int(datetime.now().timestamp()),
            priority=priority,
            headers={
                'sent_at': datetime.now().isoformat(),
                'ttl_type': 'message-level' if ttl_seconds else 'queue-level'
            }
        )
        
        # Message-level TTL
        if ttl_seconds:
            properties.expiration = str(ttl_seconds * 1000)  # Milliseconds
        
        try:
            result = self.channel.basic_publish(
                exchange='ttl_demo',
                routing_key=routing_key,
                body=json.dumps(message_data, indent=2),
                properties=properties,
                mandatory=True
            )
            
            self.sent_count += 1
            
            if result:
                self.confirmed_count += 1
                
                # TTL info
                if ttl_seconds:
                    ttl_info = f"TTL: {ttl_seconds}s (expires at {message_data.get('expires_at', 'unknown')[:19]})"
                else:
                    ttl_info = "Queue TTL"
                
                # Routing info
                route_emoji = {
                    'short': '⏰',
                    'normal': '📝',
                    'long': '⏳',
                    'temp': '🔥'
                }
                
                emoji = route_emoji.get(routing_key, '📨')
                print(f"{emoji} Sent → {routing_key}: {message[:40]}... ({ttl_info})")
                return True
            else:
                print(f"❌ Not confirmed: {message[:40]}...")
                return False
                
        except Exception as e:
            print(f"💥 Send error: {str(e)}")
            return False
    
    def demo_ttl_scenarios(self):
        """TTL senaryolarını gösterir"""
        print("\n🕐 TTL Demo Senaryoları başlıyor...")
        print("=" * 60)
        
        scenarios = [
            # (message, ttl_seconds, routing_key, description)
            ("Bu mesaj queue TTL ile 30 saniye yaşayacak", None, 'short', "Queue TTL (30s)"),
            ("Bu mesaj 5 saniye yaşayacak", 5, 'normal', "Message TTL (5s)"),
            ("Bu mesaj 15 saniye yaşayacak", 15, 'normal', "Message TTL (15s)"),
            ("Bu mesaj 45 saniye yaşayacak", 45, 'normal', "Message TTL (45s)"),
            ("Bu mesaj queue TTL ile 5 dakika yaşayacak", None, 'long', "Queue TTL (5min)"),
            ("Bu mesaj 10 saniye yaşayacak (long queue)", 10, 'long', "Message TTL wins (10s vs 5min)"),
            ("Bu mesaj sonsuz yaşayacak", None, 'normal', "No TTL"),
            ("Temporary queue mesajı (20s TTL)", None, 'temp', "Temp queue (20s TTL, queue expires in 60s)"),
        ]
        
        for i, (message, ttl, routing_key, description) in enumerate(scenarios, 1):
            print(f"\n📨 Scenario {i}: {description}")
            self.send_message_with_ttl(message, ttl, routing_key)
            
            # Small delay between messages
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print(f"📊 Gönderim tamamlandı:")
        print(f"   📤 Total Sent: {self.sent_count}")
        print(f"   ✅ Confirmed: {self.confirmed_count}")
        print(f"   📈 Success Rate: {(self.confirmed_count / self.sent_count) * 100:.1f}%")
        
        print(f"\n⏰ TTL Timeline:")
        print(f"   5s → Message TTL (5s) expires")
        print(f"   10s → Message TTL (10s) expires")  
        print(f"   15s → Message TTL (15s) expires")
        print(f"   20s → Temp queue messages expire")
        print(f"   30s → Short queue messages expire")
        print(f"   45s → Message TTL (45s) expires")
        print(f"   60s → Temp queue itself expires")
        print(f"   5min → Long queue messages expire")
    
    def send_batch_with_staggered_ttl(self):
        """Kademeli TTL'li batch gönderir"""
        print("\n📦 Kademeli TTL Batch gönderimi...")
        
        base_message = "Kademeli TTL mesajı"
        ttl_values = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        
        for i, ttl in enumerate(ttl_values, 1):
            message = f"{base_message} #{i}"
            self.send_message_with_ttl(message, ttl, 'normal', priority=i)
            time.sleep(0.2)
        
        print(f"\n📊 {len(ttl_values)} kademeli TTL mesajı gönderildi")
        print("⏰ Mesajlar 5 saniye arayla expire olacak")
    
    def send_priority_ttl_mix(self):
        """Priority ve TTL karışımı"""
        print("\n🎯 Priority + TTL Mix...")
        
        messages = [
            ("Critical alert - 60s TTL", 60, 10),
            ("High priority - 30s TTL", 30, 8),
            ("Normal task - 45s TTL", 45, 5),
            ("Low priority - 15s TTL", 15, 2),
            ("Background job - 90s TTL", 90, 1)
        ]
        
        for message, ttl, priority in messages:
            self.send_message_with_ttl(
                message, 
                ttl, 
                'normal', 
                priority=priority
            )
            time.sleep(0.3)
        
        print(f"🎯 Priority-TTL mix gönderildi")
    
    def monitor_queues(self):
        """Queue durumlarını gösterir"""
        try:
            queues = [
                ('short_lived_messages', 'Short TTL (30s)'),
                ('normal_messages', 'Normal (No queue TTL)'),
                ('long_lived_messages', 'Long TTL (5min)'),
                ('temp_queue', 'Temporary (20s TTL, 60s queue expire)'),
                ('expired_messages', 'Expired Messages')
            ]
            
            print(f"\n📊 Queue Durumu ({datetime.now().strftime('%H:%M:%S')}):")
            print("-" * 50)
            
            for queue_name, description in queues:
                try:
                    result = self.channel.queue_declare(queue=queue_name, passive=True)
                    count = result.method.message_count
                    
                    if queue_name == 'expired_messages' and count > 0:
                        emoji = "⚰️"
                    elif count > 0:
                        emoji = "📦"
                    else:
                        emoji = "📭"
                    
                    print(f"   {emoji} {description}: {count} mesaj")
                    
                except pika.exceptions.ChannelClosedByBroker as e:
                    if "NOT_FOUND" in str(e):
                        print(f"   💨 {description}: Queue expired/deleted")
                    else:
                        print(f"   ❌ {description}: Error - {str(e)}")
                    # Reopen channel
                    self.channel = self.connection.channel()
                except Exception as e:
                    print(f"   ❌ {description}: Error - {str(e)}")
            
        except Exception as e:
            print(f"❌ Queue monitoring error: {str(e)}")
    
    def close(self):
        self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ TTL Producer')
    parser.add_argument('mode', nargs='?', default='demo',
                       choices=['demo', 'custom', 'batch', 'priority', 'monitor'],
                       help='Çalışma modu')
    parser.add_argument('message', nargs='?', default='Custom TTL message',
                       help='Custom mesaj')
    parser.add_argument('ttl', nargs='?', type=int, default=30,
                       help='TTL saniye')
    parser.add_argument('--routing-key', default='normal',
                       choices=['short', 'normal', 'long', 'temp'],
                       help='Routing key')
    
    args = parser.parse_args()
    
    producer = TTLProducer()
    
    try:
        if args.mode == 'demo':
            producer.demo_ttl_scenarios()
        elif args.mode == 'custom':
            producer.send_message_with_ttl(
                args.message, 
                args.ttl, 
                args.routing_key
            )
        elif args.mode == 'batch':
            producer.send_batch_with_staggered_ttl()
        elif args.mode == 'priority':
            producer.send_priority_ttl_mix()
        elif args.mode == 'monitor':
            producer.monitor_queues()
        
        # Her durumda queue durumunu göster
        if args.mode != 'monitor':
            time.sleep(1)  # Queue update için bekle
            producer.monitor_queues()
            
    finally:
        producer.close()


if __name__ == "__main__":
    main()