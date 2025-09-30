#!/usr/bin/env python3
"""
RabbitMQ Headers Exchange Consumer
Headers exchange ile metadata-based order processing örneği.
"""

import pika
import json
import sys
import signal
import time
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrderProcessor:
    def __init__(self, processor_name, header_match, match_headers, host='localhost', port=5672, username='admin', password='admin123'):
        """Order Processor initialization"""
        self.processor_name = processor_name
        self.header_match = header_match  # 'all' or 'any'
        self.match_headers = match_headers
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.queue_name = None
        self.processed_count = 0
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        logger.info(f"\n🔴 [{self.processor_name}] Processor stopping...")
        logger.info(f"📊 Processed {self.processed_count} orders")
        if self.connection and not self.connection.is_closed:
            self.channel.stop_consuming()
            self.connection.close()
        sys.exit(0)
        
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
            
            # Exchange declare
            self.channel.exchange_declare(
                exchange='order_processing',
                exchange_type='headers',
                durable=True
            )
            
            # Exclusive queue
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
            
            # Headers binding arguments
            binding_args = {'x-match': self.header_match}
            binding_args.update(self.match_headers)
            
            # Headers exchange'e bind et
            self.channel.queue_bind(
                exchange='order_processing',
                queue=self.queue_name,
                arguments=binding_args
            )
            
            logger.info(f"✅ [{self.processor_name}] Connected to RabbitMQ")
            logger.info(f"🔗 [{self.processor_name}] Bound with x-match: {self.header_match}")
            logger.info(f"📋 [{self.processor_name}] Match headers: {self.match_headers}")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def callback(self, ch, method, properties, body):
        """Sipariş işle"""
        try:
            order = json.loads(body)
            headers = properties.headers or {}
            
            self.processed_count += 1
            
            # Display order info
            self._display_order(order, headers)
            
            # Process order based on headers
            self._process_order(order, headers)
            
            # Simulate processing time
            processing_time = self._calculate_processing_time(headers)
            if processing_time > 0:
                time.sleep(processing_time)
                print(f"✅ [{self.processor_name}] Order {order['order_id']} processed in {processing_time}s")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
    
    def _display_order(self, order, headers):
        """Sipariş bilgilerini görüntüle"""
        customer_emoji = {
            'standard': '👤',
            'premium': '💎', 
            'vip': '⭐'
        }.get(headers.get('customer_type'), '👤')
        
        shipping_emoji = {
            'standard': '📦',
            'express': '⚡',
            'same_day': '🚀'
        }.get(headers.get('shipping_type'), '📦')
        
        print(f"\n🛍️ [{self.processor_name}] Processing Order: {order['order_id']}")
        print(f"{customer_emoji} Customer: {order['customer_id']} ({headers.get('customer_type', 'unknown')})")
        print(f"🏷️ Headers: {dict(headers)}")
        print(f"💰 Amount: ${order['total_amount']:.2f} ({headers.get('amount_range', 'unknown')})")
        print(f"{shipping_emoji} Shipping: {headers.get('shipping_type', 'unknown')}")
        print(f"📦 Items: {', '.join(order['items'])}")
        print(f"🌐 Source: {headers.get('source', 'unknown')}")
    
    def _process_order(self, order, headers):
        """Sipariş işleme logic'i"""
        customer_type = headers.get('customer_type', 'standard')
        shipping_type = headers.get('shipping_type', 'standard')
        amount_range = headers.get('amount_range', 'low')
        region = headers.get('region', 'domestic')
        
        # Customer type based processing
        if customer_type == 'vip':
            print("⭐ VIP CUSTOMER: Priority processing, dedicated support, complimentary gift wrapping")
            print("📧 Sending VIP welcome email with tracking details")
        elif customer_type == 'premium':
            print("💎 PREMIUM CUSTOMER: Enhanced service, priority queue, extended warranty")
            print("📱 Sending SMS notifications for order updates")
        else:
            print("👤 STANDARD CUSTOMER: Regular processing, standard support")
        
        # Shipping type based processing
        if shipping_type == 'same_day':
            print("🚀 SAME DAY DELIVERY: Immediate warehouse notification, courier dispatch")
            print("📍 Real-time GPS tracking enabled")
        elif shipping_type == 'express':
            print("⚡ EXPRESS SHIPPING: Priority warehouse processing, 1-2 day delivery")
            print("📦 Express packaging with tracking")
        else:
            print("📦 STANDARD SHIPPING: Regular processing, 3-5 day delivery")
        
        # Amount range based processing
        if amount_range == 'high':
            print("💰 HIGH VALUE ORDER: Fraud check required, insurance included")
            print("🔒 Additional security verification")
        elif amount_range == 'medium':
            print("💵 MEDIUM VALUE ORDER: Standard verification, optional insurance")
        else:
            print("💲 LOW VALUE ORDER: Quick processing, basic packaging")
        
        # Region based processing
        if region == 'international':
            print("🌍 INTERNATIONAL ORDER: Customs documentation, duty calculation")
            print("📄 Generating international shipping labels")
        else:
            print("🏠 DOMESTIC ORDER: Standard domestic processing")
        
        # Special processor actions
        self._execute_processor_specific_actions(order, headers)
    
    def _execute_processor_specific_actions(self, order, headers):
        """Processor tipine özel aksiyonlar"""
        if 'premium' in self.processor_name.lower():
            print("🎁 PREMIUM ACTION: Adding loyalty points, preparing premium packaging")
        elif 'express' in self.processor_name.lower():
            print("⏱️ EXPRESS ACTION: Fast-tracking through warehouse, priority labeling")
        elif 'high_value' in self.processor_name.lower():
            print("🔍 HIGH VALUE ACTION: Manager approval, secure packaging, signature required")
        elif 'international' in self.processor_name.lower():
            print("🌍 INTERNATIONAL ACTION: Customs forms, international courier selection")
    
    def _calculate_processing_time(self, headers):
        """Header'lara göre işlem süresini hesapla"""
        base_time = 1.0
        
        # Customer type multiplier
        customer_multiplier = {
            'vip': 0.5,      # VIP gets faster processing
            'premium': 0.7,  # Premium gets faster processing
            'standard': 1.0  # Standard processing
        }.get(headers.get('customer_type'), 1.0)
        
        # Shipping type multiplier
        shipping_multiplier = {
            'same_day': 0.3,  # Very fast processing
            'express': 0.6,   # Fast processing
            'standard': 1.0   # Normal processing
        }.get(headers.get('shipping_type'), 1.0)
        
        # Amount range multiplier
        amount_multiplier = {
            'high': 1.5,    # More verification needed
            'medium': 1.0,  # Standard processing
            'low': 0.8      # Quick processing
        }.get(headers.get('amount_range'), 1.0)
        
        return base_time * customer_multiplier * shipping_multiplier * amount_multiplier
    
    def start_consuming(self):
        """Sipariş dinlemeye başla"""
        if not self.channel:
            self.connect()
            
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=True
        )
        
        print(f"👂 [{self.processor_name}] Listening for orders...")
        print("🔴 Press CTRL+C to exit\n")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

# Predefined processors
def create_premium_processor():
    """Premium/VIP müşteri siparişleri"""
    return OrderProcessor(
        'Premium Processor',
        'any',  # Herhangi biri eşleşsin
        {'customer_type': 'premium', 'customer_type': 'vip'}
    )

def create_express_processor():
    """Express kargo siparişleri"""
    return OrderProcessor(
        'Express Processor',
        'all',  # Hepsi eşleşmeli
        {'shipping_type': 'express'}
    )

def create_same_day_processor():
    """Same day delivery siparişleri"""
    return OrderProcessor(
        'Same Day Processor',
        'all',
        {'shipping_type': 'same_day'}
    )

def create_high_value_processor():
    """Yüksek tutarlı siparişler"""
    return OrderProcessor(
        'High Value Processor',
        'any',
        {'amount_range': 'high', 'amount_range': 'medium'}
    )

def create_international_processor():
    """Uluslararası siparişler"""
    return OrderProcessor(
        'International Processor',
        'all',
        {'region': 'international'}
    )

def create_vip_express_processor():
    """VIP müşteri + Express kargo (strict matching)"""
    return OrderProcessor(
        'VIP Express Processor',
        'all',  # Tüm header'lar eşleşmeli
        {'customer_type': 'vip', 'shipping_type': 'express'}
    )

def create_credit_card_processor():
    """Kredi kartı ödemeli siparişler"""
    return OrderProcessor(
        'Credit Card Processor',
        'all',
        {'payment_method': 'credit_card'}
    )

def show_available_processors():
    """Mevcut processor'ları göster"""
    print("\n📋 Available processors:")
    print("  premium           # Premium/VIP customers (any match)")
    print("  express           # Express shipping orders (all match)")
    print("  same_day          # Same day delivery orders (all match)")
    print("  high_value        # High/Medium value orders (any match)")
    print("  international     # International orders (all match)")
    print("  vip_express       # VIP + Express (strict all match)")
    print("  credit_card       # Credit card payments (all match)")
    print("\n🔑 Match types:")
    print("  all = All specified headers must match")
    print("  any = At least one specified header must match")

def main():
    if len(sys.argv) < 2:
        print("Usage: python headers_exchange_consumer.py <processor_type>")
        show_available_processors()
        sys.exit(1)
    
    processor_type = sys.argv[1].lower()
    
    processors = {
        'premium': create_premium_processor,
        'express': create_express_processor,
        'same_day': create_same_day_processor,
        'high_value': create_high_value_processor,
        'international': create_international_processor,
        'vip_express': create_vip_express_processor,
        'credit_card': create_credit_card_processor
    }
    
    if processor_type not in processors:
        print(f"❌ Unknown processor type: {processor_type}")
        show_available_processors()
        sys.exit(1)
    
    processor = processors[processor_type]()
    processor.start_consuming()

if __name__ == '__main__':
    main()