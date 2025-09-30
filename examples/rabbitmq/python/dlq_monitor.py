"""
RabbitMQ DLQ Monitor
===================

Bu script Dead Letter Queue'ları izler ve başarısız mesajları analiz eder.

Özellikler:
- DLQ mesaj monitoring
- Failure analysis
- Recovery operations
- Statistics tracking

Kullanım:
    python dlq_monitor.py
    python dlq_monitor.py --auto-recover
"""

import pika
import json
import time
import argparse
import signal
import sys
from datetime import datetime
from collections import defaultdict


class DLQMonitor:
    def __init__(self, auto_recover=False):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.auto_recover = auto_recover
        
        # Statistics
        self.stats = {
            'dlq_processed': 0,
            'recovered': 0,
            'archived': 0,
            'failure_types': defaultdict(int),
            'start_time': datetime.now()
        }
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        
        # Recovery queue setup
        self.setup_recovery_system()
    
    def signal_handler(self, sig, frame):
        """Graceful shutdown handler"""
        print(f"\n🛑 Shutdown signal alındı")
        self.running = False
        self.channel.stop_consuming()
    
    def setup_recovery_system(self):
        """Recovery sistemini kurar"""
        # Recovery exchange
        self.channel.exchange_declare(
            exchange='order_recovery',
            exchange_type='direct',
            durable=True
        )
        
        # Recovery queue
        self.channel.queue_declare(
            queue='recovery_orders',
            durable=True
        )
        
        # Archive queue
        self.channel.queue_declare(
            queue='archived_orders',
            durable=True
        )
        
        # Bindings
        self.channel.queue_bind(
            exchange='order_recovery',
            queue='recovery_orders',
            routing_key='recover'
        )
        
        self.channel.queue_bind(
            exchange='order_recovery',
            queue='archived_orders',
            routing_key='archive'
        )
    
    def analyze_failure(self, order, headers):
        """Failure analizini yapar"""
        failure_info = {
            'order_id': order.get('id', 'Unknown')[:8],
            'product': order.get('product', 'Unknown'),
            'customer': order.get('customer', 'Unknown'),
            'total_retries': headers.get('total_retries', 0),
            'final_failure_reason': headers.get('final_failure_reason', 'Unknown'),
            'final_failure_time': headers.get('final_failure_time', 'Unknown'),
            'original_timestamp': headers.get('original_timestamp', 'Unknown'),
            'is_recoverable': False,
            'recovery_action': 'archive'
        }
        
        # Recovery logic
        reason = failure_info['final_failure_reason'].lower()
        
        if 'random' in reason:
            failure_info['is_recoverable'] = True
            failure_info['recovery_action'] = 'retry'
        elif 'timeout' in reason:
            failure_info['is_recoverable'] = True
            failure_info['recovery_action'] = 'retry_with_delay'
        elif 'invalid quantity' in reason or 'invalid price' in reason:
            failure_info['is_recoverable'] = False
            failure_info['recovery_action'] = 'manual_review'
        elif 'simulated' in reason:
            failure_info['is_recoverable'] = True
            failure_info['recovery_action'] = 'retry'
        else:
            failure_info['is_recoverable'] = False
            failure_info['recovery_action'] = 'archive'
        
        # Statistics
        self.stats['failure_types'][failure_info['final_failure_reason']] += 1
        
        return failure_info
    
    def process_dlq_message(self, channel, method, properties, body):
        """DLQ mesajını işler"""
        try:
            order = json.loads(body)
            headers = properties.headers or {}
            
            # Failure analysis
            failure_info = self.analyze_failure(order, headers)
            
            self.stats['dlq_processed'] += 1
            
            print(f"\n💀 DLQ Mesajı Analizi:")
            print(f"   🆔 Order ID: {failure_info['order_id']}")
            print(f"   👤 Customer: {failure_info['customer']}")
            print(f"   🛍️ Product: {failure_info['product']}")
            print(f"   🔄 Total Retries: {failure_info['total_retries']}")
            print(f"   ❌ Failure Reason: {failure_info['final_failure_reason']}")
            print(f"   ⏰ Failed At: {failure_info['final_failure_time']}")
            print(f"   📅 Original Time: {failure_info['original_timestamp']}")
            
            # Recovery decision
            if failure_info['is_recoverable']:
                print(f"   ✅ Recoverable: YES")
                print(f"   🔧 Action: {failure_info['recovery_action']}")
                
                if self.auto_recover:
                    self.recover_message(order, headers, failure_info)
                else:
                    print(f"   💡 Manual recovery gerekli (--auto-recover kullanın)")
            else:
                print(f"   ❌ Recoverable: NO")
                print(f"   📦 Action: {failure_info['recovery_action']}")
                
                if self.auto_recover:
                    self.archive_message(order, headers, failure_info)
                else:
                    print(f"   💡 Manual archive gerekli")
            
            # Acknowledge DLQ message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            print(f"❌ DLQ JSON parse hatası")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"💥 DLQ işleme hatası: {str(e)}")
            channel.basic_ack(delivery_tag=method.delivery_tag)
    
    def recover_message(self, order, headers, failure_info):
        """Mesajı recovery için gönderir"""
        try:
            # Clean headers for recovery
            recovery_headers = {
                'recovery_reason': failure_info['recovery_action'],
                'recovery_timestamp': datetime.now().isoformat(),
                'original_failure': failure_info['final_failure_reason'],
                'dlq_processed_at': datetime.now().isoformat(),
                'retry_count': 0  # Reset retry count
            }
            
            # Clean order data
            clean_order = order.copy()
            clean_order.pop('simulate_failure', None)  # Remove simulation flag
            
            properties = pika.BasicProperties(
                delivery_mode=2,
                headers=recovery_headers,
                message_id=order.get('id')
            )
            
            # Send to recovery queue for manual processing
            self.channel.basic_publish(
                exchange='order_recovery',
                routing_key='recover',
                body=json.dumps(clean_order, indent=2),
                properties=properties
            )
            
            self.stats['recovered'] += 1
            print(f"   🔄 Recovery queue'ya gönderildi")
            
        except Exception as e:
            print(f"   ❌ Recovery error: {str(e)}")
    
    def archive_message(self, order, headers, failure_info):
        """Mesajı arşivler"""
        try:
            archive_data = {
                'original_order': order,
                'failure_analysis': failure_info,
                'archived_at': datetime.now().isoformat(),
                'archive_reason': 'non_recoverable_failure'
            }
            
            properties = pika.BasicProperties(
                delivery_mode=2,
                headers={
                    'archive_reason': failure_info['recovery_action'],
                    'archived_at': datetime.now().isoformat(),
                    'original_failure': failure_info['final_failure_reason']
                }
            )
            
            self.channel.basic_publish(
                exchange='order_recovery',
                routing_key='archive',
                body=json.dumps(archive_data, indent=2),
                properties=properties
            )
            
            self.stats['archived'] += 1
            print(f"   📦 Archive queue'ya gönderildi")
            
        except Exception as e:
            print(f"   ❌ Archive error: {str(e)}")
    
    def check_queue_status(self):
        """Queue durumlarını kontrol eder"""
        try:
            queues = [
                ('orders', 'Ana sipariş queue'),
                ('failed_orders', 'Dead Letter Queue'),
                ('recovery_orders', 'Recovery queue'),
                ('archived_orders', 'Archive queue')
            ]
            
            print(f"\n📊 Queue Durumu ({datetime.now().strftime('%H:%M:%S')}):")
            print("-" * 50)
            
            for queue_name, description in queues:
                try:
                    result = self.channel.queue_declare(queue=queue_name, passive=True)
                    count = result.method.message_count
                    
                    if count > 0:
                        emoji = "🔴" if queue_name == 'failed_orders' and count > 10 else "🟡" if count > 0 else "🟢"
                        print(f"   {emoji} {description}: {count} mesaj")
                    else:
                        print(f"   🟢 {description}: {count} mesaj")
                        
                except Exception as e:
                    print(f"   ❌ {description}: Error - {str(e)}")
            
        except Exception as e:
            print(f"❌ Queue status check error: {str(e)}")
    
    def print_statistics(self):
        """İstatistikleri yazdırır"""
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            elapsed_seconds = elapsed.total_seconds()
            
            print(f"\n📈 DLQ Monitor İstatistikleri:")
            print("-" * 40)
            print(f"   ⏱️ Çalışma süresi: {elapsed_seconds:.1f}s")
            print(f"   💀 DLQ işlenen: {self.stats['dlq_processed']}")
            print(f"   🔄 Recovered: {self.stats['recovered']}")
            print(f"   📦 Archived: {self.stats['archived']}")
            
            if self.stats['failure_types']:
                print(f"\n📊 Failure Types:")
                for failure_type, count in self.stats['failure_types'].items():
                    print(f"   • {failure_type}: {count}")
    
    def start_monitoring(self):
        """DLQ monitoring'i başlatır"""
        print("👁️ DLQ Monitor başlatılıyor...")
        print(f"🔄 Auto-recover: {'Enabled' if self.auto_recover else 'Disabled'}")
        print("🛑 Çıkış için Ctrl+C")
        print("=" * 50)
        
        # Initial queue status
        self.check_queue_status()
        
        # QoS settings
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming DLQ
        self.channel.basic_consume(
            queue='failed_orders',
            on_message_callback=self.process_dlq_message
        )
        
        try:
            last_status_check = time.time()
            
            while self.running:
                # Process data events
                self.connection.process_data_events(time_limit=1)
                
                # Periodic status check (every 30 seconds)
                if time.time() - last_status_check > 30:
                    self.check_queue_status()
                    last_status_check = time.time()
                    
        except KeyboardInterrupt:
            print(f"\n🛑 KeyboardInterrupt")
        finally:
            print(f"\n🏁 Monitor durduruluyor...")
            self.print_statistics()
            self.check_queue_status()
            self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ DLQ Monitor')
    parser.add_argument('--auto-recover', action='store_true',
                       help='Otomatik recovery işlemlerini aktifleştir')
    parser.add_argument('--status-only', action='store_true',
                       help='Sadece queue durumunu göster ve çık')
    
    args = parser.parse_args()
    
    monitor = DLQMonitor(auto_recover=args.auto_recover)
    
    if args.status_only:
        monitor.check_queue_status()
        monitor.connection.close()
    else:
        monitor.start_monitoring()


if __name__ == "__main__":
    main()