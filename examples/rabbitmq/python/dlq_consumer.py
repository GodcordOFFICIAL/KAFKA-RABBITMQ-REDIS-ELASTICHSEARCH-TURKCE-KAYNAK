"""
RabbitMQ Dead Letter Queue (DLQ) Consumer
========================================

Bu script siparişleri işler ve başarısız olanları DLQ'ya gönderir.

Özellikler:
- Retry logic
- Failure simulation handling
- Graceful error handling
- Statistics tracking

Kullanım:
    python dlq_consumer.py
    python dlq_consumer.py --max-retries 5
"""

import pika
import json
import time
import random
import signal
import sys
import argparse
from datetime import datetime


class DLQConsumer:
    def __init__(self, max_retries=3, process_delay=1.0):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.max_retries = max_retries
        self.process_delay = process_delay
        
        # Statistics
        self.stats = {
            'processed': 0,
            'failed': 0,
            'retried': 0,
            'dlq_sent': 0,
            'start_time': datetime.now()
        }
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
    
    def signal_handler(self, sig, frame):
        """Graceful shutdown handler"""
        print(f"\n🛑 Shutdown signal alındı ({sig})")
        self.running = False
        self.channel.stop_consuming()
    
    def simulate_processing_error(self, order):
        """İşleme hatası simülasyonu"""
        # Failure simulation flag kontrolü
        if order.get('simulate_failure', False):
            return "Simulated processing failure"
        
        # Invalid data kontrolü
        if order.get('quantity', 0) <= 0:
            return "Invalid quantity"
        
        if order.get('price', 0) <= 0:
            return "Invalid price"
        
        if not isinstance(order.get('quantity'), (int, float)):
            return "Quantity must be numeric"
        
        if not isinstance(order.get('price'), (int, float)):
            return "Price must be numeric"
        
        # Random failure (5% chance)
        if random.random() < 0.05:
            return "Random processing error"
        
        # Product-specific failures
        product = order.get('product', '').lower()
        if 'corrupt' in product:
            return "Corrupt product data"
        elif 'timeout' in product:
            return "Processing timeout"
        elif 'validation' in product:
            return "Validation failed"
        elif 'invalid' in product:
            return "Invalid product"
        
        return None  # No error
    
    def process_order(self, channel, method, properties, body):
        """Sipariş işler"""
        try:
            order = json.loads(body)
            order_id = order.get('id', 'Unknown')[:8]
            product = order.get('product', 'Unknown')
            customer = order.get('customer', 'Unknown')
            
            # Header'lardan retry count al
            headers = properties.headers or {}
            retry_count = headers.get('retry_count', 0)
            original_timestamp = headers.get('original_timestamp', 'Unknown')
            
            print(f"\n📦 İşleniyor: {order_id}")
            print(f"   👤 Customer: {customer}")
            print(f"   🛍️ Product: {product}")
            print(f"   📊 Quantity: {order.get('quantity', 0)}")
            print(f"   💰 Price: ${order.get('price', 0):.2f}")
            print(f"   🔄 Retry: {retry_count}/{self.max_retries}")
            print(f"   ⏰ Original: {original_timestamp}")
            
            # Processing simulation
            time.sleep(random.uniform(0.5, self.process_delay))
            
            # Error simulation
            error = self.simulate_processing_error(order)
            
            if error:
                # Processing failed
                self.stats['failed'] += 1
                print(f"❌ İşleme hatası: {error}")
                
                if retry_count < self.max_retries:
                    # Retry
                    self.stats['retried'] += 1
                    
                    # Update headers for retry
                    new_headers = headers.copy()
                    new_headers['retry_count'] = retry_count + 1
                    new_headers['last_error'] = error
                    new_headers['failed_at'] = datetime.now().isoformat()
                    new_headers['retry_timestamp'] = datetime.now().isoformat()
                    
                    # Create new message with updated headers
                    new_properties = pika.BasicProperties(
                        message_id=properties.message_id,
                        timestamp=properties.timestamp,
                        headers=new_headers,
                        delivery_mode=2
                    )
                    
                    # Requeue with updated headers (small delay)
                    time.sleep(0.1)
                    
                    channel.basic_publish(
                        exchange='order_processing',
                        routing_key='new_order',
                        body=body,
                        properties=new_properties
                    )
                    
                    print(f"🔄 Retry edildi ({retry_count + 1}/{self.max_retries})")
                    
                    # Acknowledge original message
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    
                else:
                    # Max retry aşıldı, DLQ'ya gönder
                    self.stats['dlq_sent'] += 1
                    print(f"💀 Max retry aşıldı, DLQ'ya gönderiliyor")
                    
                    # Add final failure info to headers
                    new_headers = headers.copy()
                    new_headers['final_failure_reason'] = error
                    new_headers['final_failure_time'] = datetime.now().isoformat()
                    new_headers['total_retries'] = retry_count
                    
                    # Send to DLQ by rejecting (DLX will handle routing)
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            
            else:
                # Processing successful
                self.stats['processed'] += 1
                print(f"✅ Sipariş başarıyla işlendi!")
                
                # Success processing simulation
                if retry_count > 0:
                    print(f"🎉 {retry_count} retry sonrası başarılı!")
                
                # Process different order types
                if order.get('price', 0) > 500:
                    print(f"💎 Yüksek değerli sipariş - özel işlem")
                
                if order.get('quantity', 0) > 5:
                    print(f"📦 Bulk sipariş - toplu işlem")
                
                # Acknowledge message
                channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            print(f"❌ JSON parse hatası")
            # Bad message format - reject without requeue
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {str(e)}")
            # Unexpected error - reject without requeue to avoid infinite loop
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    
    def print_statistics(self):
        """İstatistikleri yazdırır"""
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            elapsed_seconds = elapsed.total_seconds()
            
            print(f"\n📊 Consumer İstatistikleri:")
            print(f"   ⏱️ Çalışma süresi: {elapsed_seconds:.1f}s")
            print(f"   ✅ İşlenen: {self.stats['processed']}")
            print(f"   ❌ Başarısız: {self.stats['failed']}")
            print(f"   🔄 Retry edilen: {self.stats['retried']}")
            print(f"   💀 DLQ'ya giden: {self.stats['dlq_sent']}")
            
            total_handled = self.stats['processed'] + self.stats['dlq_sent']
            if total_handled > 0:
                success_rate = (self.stats['processed'] / total_handled) * 100
                print(f"   📈 Başarı oranı: {success_rate:.1f}%")
                
                if elapsed_seconds > 0:
                    throughput = total_handled / elapsed_seconds
                    print(f"   🚀 Throughput: {throughput:.2f} orders/sec")
    
    def start_consuming(self):
        """Consumer'ı başlatır"""
        print("🎧 DLQ Order Consumer başlatılıyor...")
        print(f"📋 Max retries: {self.max_retries}")
        print(f"⏱️ Process delay: {self.process_delay}s")
        print("🛑 Çıkış için Ctrl+C")
        print("=" * 50)
        
        # QoS settings
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue='orders',
            on_message_callback=self.process_order
        )
        
        try:
            while self.running:
                self.connection.process_data_events(time_limit=1)
        except KeyboardInterrupt:
            print(f"\n🛑 KeyboardInterrupt")
        finally:
            print(f"\n🏁 Consumer durduruluyor...")
            self.print_statistics()
            self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ DLQ Consumer')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum retry sayısı (default: 3)')
    parser.add_argument('--process-delay', type=float, default=1.0,
                       help='İşleme gecikmesi saniye (default: 1.0)')
    parser.add_argument('--fast', action='store_true',
                       help='Hızlı işleme modu (0.2s delay)')
    
    args = parser.parse_args()
    
    # Fast mode
    if args.fast:
        args.process_delay = 0.2
    
    consumer = DLQConsumer(
        max_retries=args.max_retries,
        process_delay=args.process_delay
    )
    
    consumer.start_consuming()


if __name__ == "__main__":
    main()