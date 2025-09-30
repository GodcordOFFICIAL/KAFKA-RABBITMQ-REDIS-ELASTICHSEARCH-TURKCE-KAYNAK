#!/usr/bin/env python3
"""
RabbitMQ Topic Exchange Consumer
Topic exchange ile pattern-based news consumption örneği.
"""

import pika
import json
import sys
import signal
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsConsumer:
    def __init__(self, routing_patterns, consumer_name='NewsConsumer', host='localhost', port=5672, username='admin', password='admin123'):
        """News Consumer initialization"""
        self.routing_patterns = routing_patterns
        self.consumer_name = consumer_name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.queue_name = None
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        logger.info(f"\n🔴 [{self.consumer_name}] Consumer stopping...")
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
                exchange='news_exchange',
                exchange_type='topic',
                durable=True
            )
            
            # Exclusive queue
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
            
            # Pattern'lere göre binding
            for pattern in self.routing_patterns:
                self.channel.queue_bind(
                    exchange='news_exchange',
                    queue=self.queue_name,
                    routing_key=pattern
                )
                logger.info(f"🔗 [{self.consumer_name}] Bound to pattern: {pattern}")
            
            logger.info(f"✅ [{self.consumer_name}] Connected to RabbitMQ")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def callback(self, ch, method, properties, body):
        """Haber mesajını işle"""
        try:
            news = json.loads(body)
            
            urgency_emoji = {
                'low': '🟢',
                'medium': '🟡', 
                'high': '🟠',
                'critical': '🔴'
            }.get(news['urgency'], '📰')
            
            category_emoji = {
                'tech': '💻',
                'finance': '💰',
                'sports': '⚽',
                'weather': '🌤️',
                'health': '🏥',
                'politics': '🏛️'
            }.get(news['category'], '📰')
            
            print(f"\n{urgency_emoji} {category_emoji} [{self.consumer_name}] {news['routing_key']}")
            print(f"📰 {news['title']}")
            print(f"💬 {news['content']}")
            print(f"⏰ {news['timestamp']}")
            print(f"👤 {news['author']}")
            
            # Urgency-based actions
            if news['urgency'] == 'critical':
                print("🚨 CRITICAL NEWS: Immediate attention required!")
            elif news['urgency'] == 'high':
                print("⚡ HIGH PRIORITY: Important update")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
    
    def start_consuming(self):
        """Haber dinlemeye başla"""
        if not self.channel:
            self.connect()
            
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=True
        )
        
        print(f"👂 [{self.consumer_name}] Listening for patterns: {', '.join(self.routing_patterns)}")
        print("🔴 Press CTRL+C to exit\n")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def show_example_patterns():
    """Örnek pattern'leri göster"""
    print("\n📋 Example routing patterns:")
    print("  tech.*.*              # All tech news")
    print("  *.*.high              # All high priority news")
    print("  finance.#             # All finance news (any subcategory/urgency)")
    print("  tech.ai.*             # All AI tech news")
    print("  *.cybersecurity.*     # All cybersecurity news")
    print("  weather.storm.critical # Only critical storm warnings")
    print("  #.critical            # All critical news")
    print("\n🔑 Wildcard usage:")
    print("  * (asterisk)  = exactly one word")
    print("  # (hash)      = zero or more words")

def main():
    if len(sys.argv) < 2:
        print("Usage: python topic_exchange_consumer.py <pattern1> [pattern2] [pattern3]... [--name consumer_name]")
        show_example_patterns()
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    consumer_name = 'NewsConsumer'
    patterns = []
    
    i = 0
    while i < len(args):
        if args[i] == '--name' and i + 1 < len(args):
            consumer_name = args[i + 1]
            i += 2
        else:
            patterns.append(args[i])
            i += 1
    
    if not patterns:
        print("❌ At least one routing pattern is required")
        show_example_patterns()
        sys.exit(1)
    
    # Validate patterns
    for pattern in patterns:
        if not pattern.replace('*', '').replace('#', '').replace('.', '').replace('_', '').replace('-', '').isalnum():
            if not all(c.isalnum() or c in '*.#_-' for c in pattern):
                print(f"❌ Invalid pattern: {pattern}")
                print("✅ Use only alphanumeric characters, dots (.), asterisks (*), and hashes (#)")
                sys.exit(1)
    
    consumer = NewsConsumer(patterns, consumer_name)
    consumer.start_consuming()

if __name__ == '__main__':
    main()