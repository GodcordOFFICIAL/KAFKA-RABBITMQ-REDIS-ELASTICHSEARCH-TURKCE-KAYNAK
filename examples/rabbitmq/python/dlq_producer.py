"""
RabbitMQ Dead Letter Queue (DLQ) Producer
=========================================

Bu script DLQ sistemini kurar ve test mesajları gönderir.

Özellikler:
- Dead Letter Exchange kurulumu
- Retry logic ile message handling
- Failure simulation
- TTL integration

Kullanım:
    python dlq_producer.py
    python dlq_producer.py custom "Custom order data"
"""

import pika
import json
import uuid
import argparse
from datetime import datetime


class DLQProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        
        # Publisher confirms için
        self.channel.confirm_delivery()
        
        self.setup_dlq_system()
        
        self.sent_count = 0
        self.confirmed_count = 0
    
    def setup_dlq_system(self):
        """DLQ sistemini kurar"""
        # Main exchange
        self.channel.exchange_declare(
            exchange='order_processing',
            exchange_type='direct',
            durable=True
        )
        
        # Dead Letter Exchange
        self.channel.exchange_declare(
            exchange='order_processing_dlx',
            exchange_type='direct',
            durable=True
        )
        
        # Main queue with DLQ configuration
        self.channel.queue_declare(
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
        self.channel.queue_declare(
            queue='failed_orders',
            durable=True
        )
        
        # Recovery queue (manual processing için)
        self.channel.queue_declare(
            queue='recovery_orders',
            durable=True
        )
        
        # Bindings
        self.channel.queue_bind(
            exchange='order_processing',
            queue='orders',
            routing_key='new_order'
        )
        
        self.channel.queue_bind(
            exchange='order_processing_dlx',
            queue='failed_orders',
            routing_key='failed_orders'
        )
        
        print("✅ DLQ sistemi kuruldu")
    
    def send_order(self, order_data, simulate_failure=False):
        """Sipariş gönderir"""
        order = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'simulate_failure': simulate_failure,
            'retry_count': 0,
            **order_data
        }
        
        # Message properties
        properties = pika.BasicProperties(
            message_id=order['id'],
            timestamp=int(datetime.now().timestamp()),
            headers={
                'retry_count': 0,
                'original_timestamp': order['timestamp'],
                'order_type': order_data.get('product', 'unknown'),
                'failure_simulation': simulate_failure
            },
            delivery_mode=2  # Persistent
        )
        
        try:
            result = self.channel.basic_publish(
                exchange='order_processing',
                routing_key='new_order',
                body=json.dumps(order, indent=2),
                properties=properties,
                mandatory=True
            )
            
            self.sent_count += 1
            
            if result:
                self.confirmed_count += 1
                status = "❌ FAIL SIM" if simulate_failure else "✅ CONFIRMED"
                print(f"{status} Order: {order['id'][:8]} - {order_data.get('product', 'N/A')}")
                return True
            else:
                print(f"⚠️ NOT CONFIRMED: {order['id'][:8]}")
                return False
                
        except Exception as e:
            print(f"💥 Send error: {str(e)}")
            return False
    
    def send_sample_orders(self):
        """Sample siparişler gönderir"""
        orders = [
            {'product': 'Laptop Dell XPS', 'quantity': 1, 'price': 1500.00, 'customer': 'Alice'},
            {'product': 'Wireless Mouse', 'quantity': 2, 'price': 25.50, 'customer': 'Bob'},
            {'product': 'Mechanical Keyboard', 'quantity': 1, 'price': 75.00, 'customer': 'Charlie'},
            {'product': 'Monitor 4K', 'quantity': 1, 'price': 300.00, 'customer': 'Diana'},
            {'product': 'USB-C Hub', 'quantity': 3, 'price': 45.00, 'customer': 'Eve'},
            # Bu sipariş failure simulation ile gönderilecek
            {'product': 'Invalid Product', 'quantity': -1, 'price': 0.00, 'customer': 'Test'},
            {'product': 'Webcam HD', 'quantity': 1, 'price': 120.00, 'customer': 'Frank'},
            {'product': 'Headphones', 'quantity': 1, 'price': 80.00, 'customer': 'Grace'}
        ]
        
        print("📦 Sample Orders gönderiliyor...")
        print("=" * 50)
        
        for i, order in enumerate(orders):
            # 6. sipariş (Invalid Product) failure simulation ile
            simulate_failure = (i == 5) or ('Invalid' in order.get('product', ''))
            
            self.send_order(order, simulate_failure)
        
        print("=" * 50)
        print(f"📊 Gönderim İstatistikleri:")
        print(f"   📤 Gönderilen: {self.sent_count}")
        print(f"   ✅ Confirmed: {self.confirmed_count}")
        print(f"   📈 Success Rate: {(self.confirmed_count / self.sent_count) * 100:.1f}%")
    
    def send_custom_order(self, product, quantity=1, price=100.0, customer="Custom"):
        """Custom sipariş gönderir"""
        order = {
            'product': product,
            'quantity': quantity,
            'price': price,
            'customer': customer
        }
        
        print(f"📦 Custom Order gönderiliyor: {product}")
        self.send_order(order)
    
    def send_failure_test_orders(self):
        """Sadece failure test siparişleri gönderir"""
        failure_orders = [
            {'product': 'Corrupt Data Product', 'quantity': 0, 'price': -100, 'customer': 'Error1'},
            {'product': 'Timeout Test Product', 'quantity': 999, 'price': 99999, 'customer': 'Error2'},
            {'product': 'Validation Fail Product', 'quantity': 'invalid', 'price': 'invalid', 'customer': 'Error3'}
        ]
        
        print("💀 DLQ Test Orders gönderiliyor...")
        print("=" * 50)
        
        for order in failure_orders:
            self.send_order(order, simulate_failure=True)
        
        print(f"💀 {len(failure_orders)} failure test order gönderildi")
    
    def monitor_queues(self):
        """Queue durumlarını kontrol eder"""
        try:
            # Ana queue
            orders_queue = self.channel.queue_declare(queue='orders', passive=True)
            orders_count = orders_queue.method.message_count
            
            # DLQ
            dlq_queue = self.channel.queue_declare(queue='failed_orders', passive=True)
            dlq_count = dlq_queue.method.message_count
            
            print(f"\n📊 Queue Durumu:")
            print(f"   📦 orders: {orders_count} mesaj")
            print(f"   💀 failed_orders: {dlq_count} mesaj")
            
            return orders_count, dlq_count
            
        except Exception as e:
            print(f"❌ Queue monitoring error: {str(e)}")
            return 0, 0
    
    def close(self):
        self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ DLQ Producer')
    parser.add_argument('mode', nargs='?', default='sample', 
                       choices=['sample', 'custom', 'failure', 'monitor'],
                       help='Çalışma modu')
    parser.add_argument('product', nargs='?', default='Test Product',
                       help='Custom mode için ürün adı')
    parser.add_argument('--quantity', type=int, default=1,
                       help='Ürün miktarı')
    parser.add_argument('--price', type=float, default=100.0,
                       help='Ürün fiyatı')
    parser.add_argument('--customer', default='Test Customer',
                       help='Müşteri adı')
    
    args = parser.parse_args()
    
    producer = DLQProducer()
    
    try:
        if args.mode == 'sample':
            producer.send_sample_orders()
        elif args.mode == 'custom':
            producer.send_custom_order(
                args.product, 
                args.quantity, 
                args.price, 
                args.customer
            )
        elif args.mode == 'failure':
            producer.send_failure_test_orders()
        elif args.mode == 'monitor':
            producer.monitor_queues()
        
        # Her durumda queue durumunu göster
        if args.mode != 'monitor':
            producer.monitor_queues()
            
    finally:
        producer.close()


if __name__ == "__main__":
    main()