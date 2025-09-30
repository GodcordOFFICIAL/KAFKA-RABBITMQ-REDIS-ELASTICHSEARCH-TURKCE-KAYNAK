#!/usr/bin/env python3
"""
RabbitMQ Headers Exchange Producer
Headers exchange ile metadata-based order routing örneği.
"""

import pika
import json
import sys
import random
import time
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrderProducer:
    def __init__(self, host='localhost', port=5672, username='admin', password='admin123'):
        """Order Producer initialization"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        
    def connect(self):
        """RabbitMQ bağlantısı oluştur"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Headers exchange declare
            self.channel.exchange_declare(
                exchange='order_processing',
                exchange_type='headers',
                durable=True
            )
            
            logger.info("✅ Connected to RabbitMQ")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def send_order(self, order_data, headers):
        """Sipariş gönder"""
        if not self.channel:
            self.connect()
            
        order = {
            'order_id': order_data['order_id'],
            'customer_id': order_data['customer_id'],
            'items': order_data['items'],
            'total_amount': order_data['total_amount'],
            'timestamp': datetime.now().isoformat(),
            'order_source': order_data.get('order_source', 'web')
        }
        
        # Headers exchange - routing key önemli değil
        self.channel.basic_publish(
            exchange='order_processing',
            routing_key='',  # Headers exchange'te kullanılmaz
            body=json.dumps(order),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                headers=headers  # Routing header'ları
            )
        )
        
        # Header'ları görsel olarak göster
        header_display = self._format_headers_display(headers)
        
        print(f"🛍️ Order sent: {order_data['order_id']} - ${order_data['total_amount']:.2f}")
        print(f"🏷️ Headers: {header_display}")
    
    def _format_headers_display(self, headers):
        """Header'ları görsel formatında göster"""
        emoji_map = {
            'customer_type': {'premium': '💎', 'vip': '⭐', 'standard': '👤'},
            'shipping_type': {'express': '⚡', 'same_day': '🚀', 'standard': '📦'},
            'payment_method': {'credit_card': '💳', 'paypal': '📱', 'bank_transfer': '🏦'},
            'amount_range': {'high': '💰', 'medium': '💵', 'low': '💲'},
            'region': {'domestic': '🏠', 'international': '🌍'},
            'source': {'web': '🌐', 'mobile': '📱', 'api': '⚙️'}
        }
        
        display_parts = []
        for key, value in headers.items():
            emoji = emoji_map.get(key, {}).get(value, '')
            display_parts.append(f"{emoji}{key}:{value}")
        
        return ' | '.join(display_parts)
    
    def send_batch_orders(self, orders):
        """Batch sipariş gönderme"""
        if not self.channel:
            self.connect()
            
        for order_data, headers in orders:
            self.send_order(order_data, headers)
            time.sleep(0.1)  # Small delay between orders
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔒 Connection closed")

def generate_sample_orders():
    """Sample siparişler oluştur"""
    return [
        # Premium müşteri, express kargo, yurt içi
        ({
            'order_id': 'ORD-001',
            'customer_id': 'CUST-PREMIUM-123',
            'items': ['Laptop Pro 16"', 'Wireless Mouse', 'USB-C Hub'],
            'total_amount': 2499.99,
            'order_source': 'web'
        }, {
            'customer_type': 'premium',
            'shipping_type': 'express',
            'payment_method': 'credit_card',
            'amount_range': 'high',
            'region': 'domestic',
            'source': 'web'
        }),
        
        # Standard müşteri, normal kargo, düşük tutar
        ({
            'order_id': 'ORD-002', 
            'customer_id': 'CUST-STD-456',
            'items': ['Programming Book'],
            'total_amount': 29.99,
            'order_source': 'mobile'
        }, {
            'customer_type': 'standard',
            'shipping_type': 'standard',
            'payment_method': 'paypal',
            'amount_range': 'low',
            'region': 'domestic',
            'source': 'mobile'
        }),
        
        # VIP müşteri, same-day delivery, uluslararası
        ({
            'order_id': 'ORD-003',
            'customer_id': 'CUST-VIP-789',
            'items': ['iPhone 15 Pro', 'AirPods Pro', 'MagSafe Charger'],
            'total_amount': 1399.97,
            'order_source': 'api'
        }, {
            'customer_type': 'vip',
            'shipping_type': 'same_day',
            'payment_method': 'credit_card',
            'amount_range': 'high',
            'region': 'international',
            'source': 'api'
        }),
        
        # Premium müşteri, standart kargo, orta tutar
        ({
            'order_id': 'ORD-004',
            'customer_id': 'CUST-PREMIUM-456',
            'items': ['Gaming Keyboard', 'Gaming Mouse', 'Mousepad'],
            'total_amount': 299.99,
            'order_source': 'web'
        }, {
            'customer_type': 'premium',
            'shipping_type': 'standard',
            'payment_method': 'bank_transfer',
            'amount_range': 'medium',
            'region': 'domestic',
            'source': 'web'
        }),
        
        # Standard müşteri, express kargo, yurt dışı
        ({
            'order_id': 'ORD-005',
            'customer_id': 'CUST-STD-789',
            'items': ['T-Shirt', 'Jeans', 'Sneakers'],
            'total_amount': 159.99,
            'order_source': 'mobile'
        }, {
            'customer_type': 'standard',
            'shipping_type': 'express',
            'payment_method': 'credit_card',
            'amount_range': 'medium',
            'region': 'international',
            'source': 'mobile'
        }),
        
        # VIP müşteri, standart kargo, yüksek tutar
        ({
            'order_id': 'ORD-006',
            'customer_id': 'CUST-VIP-012',
            'items': ['4K Monitor', 'Mechanical Keyboard', 'Ergonomic Chair'],
            'total_amount': 1899.99,
            'order_source': 'web'
        }, {
            'customer_type': 'vip',
            'shipping_type': 'standard',
            'payment_method': 'paypal',
            'amount_range': 'high',
            'region': 'domestic',
            'source': 'web'
        })
    ]

def main():
    producer = OrderProducer()
    
    try:
        producer.connect()
        
        if len(sys.argv) > 1 and sys.argv[1] == 'custom':
            # Özel sipariş oluşturma modu
            print("📝 Custom order mode - Enter order details:")
            
            order_id = input("Order ID: ") or f"ORD-{random.randint(1000, 9999)}"
            customer_id = input("Customer ID: ") or f"CUST-{random.randint(100, 999)}"
            total_amount = float(input("Total Amount: ") or "100.00")
            
            print("\nSelect customer type: 1) standard 2) premium 3) vip")
            customer_type = ['standard', 'premium', 'vip'][int(input("Choice (1-3): ") or "1") - 1]
            
            print("\nSelect shipping: 1) standard 2) express 3) same_day")
            shipping_type = ['standard', 'express', 'same_day'][int(input("Choice (1-3): ") or "1") - 1]
            
            print("\nSelect payment: 1) credit_card 2) paypal 3) bank_transfer")
            payment_method = ['credit_card', 'paypal', 'bank_transfer'][int(input("Choice (1-3): ") or "1") - 1]
            
            # Amount range otomatik belirleme
            if total_amount < 100:
                amount_range = 'low'
            elif total_amount < 500:
                amount_range = 'medium'
            else:
                amount_range = 'high'
            
            order_data = {
                'order_id': order_id,
                'customer_id': customer_id,
                'items': ['Custom Item'],
                'total_amount': total_amount,
                'order_source': 'manual'
            }
            
            headers = {
                'customer_type': customer_type,
                'shipping_type': shipping_type,
                'payment_method': payment_method,
                'amount_range': amount_range,
                'region': 'domestic',
                'source': 'manual'
            }
            
            producer.send_order(order_data, headers)
            
        else:
            # Demo orders
            print("🛍️ Sending sample orders with various header combinations...")
            sample_orders = generate_sample_orders()
            producer.send_batch_orders(sample_orders)
            
            print(f"\n✅ Sent {len(sample_orders)} orders")
            print("\n📋 Header combinations used:")
            for i, (order_data, headers) in enumerate(sample_orders, 1):
                print(f"   {i}. {order_data['order_id']}: {headers}")
            
    except Exception as e:
        logger.error(f"❌ Producer error: {e}")
    finally:
        producer.close()

if __name__ == '__main__':
    main()