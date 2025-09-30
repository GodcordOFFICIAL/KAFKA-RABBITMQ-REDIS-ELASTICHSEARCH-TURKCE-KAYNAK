#!/usr/bin/env python3
"""
RabbitMQ Simple Consumer
Bu dosya temel RabbitMQ consumer işlemlerini gösterir.
"""

import pika
import json
import time
import signal
import sys
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleConsumer:
    def __init__(self, host='localhost', port=5672, username='admin', password='admin123'):
        """RabbitMQ Consumer initialization"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.should_stop = False
        
        # Graceful shutdown için signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        logger.info("\n🔴 Consumer durduruluyor...")
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
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
            
            # Queue declare et
            self.channel.queue_declare(queue='hello', durable=True)
            
            # QoS ayarı - aynı anda max 1 mesaj işle
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info("✅ RabbitMQ'ya bağlandı")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Bağlantı hatası: {e}")
            raise
    
    def process_message(self, ch, method, properties, body):
        """Mesaj işleme callback'i"""
        try:
            # JSON parse et
            message_data = json.loads(body)
            
            logger.info("📨 Mesaj alındı:")
            logger.info(f"   Content: {message_data.get('message')}")
            logger.info(f"   Timestamp: {message_data.get('timestamp')}")
            logger.info(f"   Sender: {message_data.get('sender')}")
            
            # Mesaj işleme simülasyonu
            time.sleep(1)
            
            # Manual ACK
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("✅ Mesaj işlendi ve ACK gönderildi\n")
            
        except json.JSONDecodeError:
            logger.error(f"❌ JSON decode hatası: {body}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Mesaj işleme hatası: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Mesaj tüketmeye başla"""
        if not self.channel:
            self.connect()
        
        # Consumer setup
        self.channel.basic_consume(
            queue='hello',
            on_message_callback=self.process_message,
            auto_ack=False  # Manual ACK kullan
        )
        
        logger.info("🔄 Mesaj bekleniyor... (Durdurmak için CTRL+C)")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def main():
    consumer = SimpleConsumer()
    consumer.start_consuming()

if __name__ == '__main__':
    main()