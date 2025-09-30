#!/usr/bin/env python3
"""
RabbitMQ Chat Consumer
Real-time chat uygulaması için mesaj alan component.
"""

import pika
import json
import signal
import sys
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatConsumer:
    def __init__(self, username, rooms, host='localhost', port=5672, user='admin', password='admin123'):
        """Chat Consumer initialization"""
        self.username = username
        self.rooms = rooms
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None
        self.should_stop = False
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        print(f"\n👋 {self.username} chat'ten ayrılıyor...")
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        sys.exit(0)
    
    def connect(self):
        """RabbitMQ bağlantısı oluştur"""
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.setup_queues()
            
            logger.info("✅ RabbitMQ'ya bağlandı")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Bağlantı hatası: {e}")
            raise
    
    def setup_queues(self):
        """Queue'ları ve binding'leri oluştur"""
        # Broadcast queue (notifications için)
        broadcast_queue = f"chat_notifications_{self.username}"
        self.channel.queue_declare(
            queue=broadcast_queue,
            exclusive=True,
            auto_delete=True
        )
        
        self.channel.queue_bind(
            exchange='chat_broadcast',
            queue=broadcast_queue
        )
        
        # Room queue'ları
        room_queue = f"chat_rooms_{self.username}"
        self.channel.queue_declare(
            queue=room_queue,
            exclusive=True,
            auto_delete=True
        )
        
        # Her room için binding
        for room in self.rooms:
            self.channel.queue_bind(
                exchange='chat_rooms',
                queue=room_queue,
                routing_key=f"room.{room}"
            )
        
        # Consumers setup
        self.channel.basic_consume(
            queue=broadcast_queue,
            on_message_callback=self.handle_notification,
            auto_ack=True
        )
        
        self.channel.basic_consume(
            queue=room_queue,
            on_message_callback=self.handle_chat_message,
            auto_ack=True
        )
    
    def handle_notification(self, ch, method, properties, body):
        """Kullanıcı bildirimlerini işle"""
        try:
            data = json.loads(body)
            
            if data['username'] != self.username:  # Kendi bildirimini gösterme
                action_emoji = "👋" if data['action'] == 'joined' else "👋"
                print(f"\n{action_emoji} {data['username']} {data['action']} the chat")
                
        except Exception as e:
            logger.error(f"❌ Notification error: {e}")
    
    def handle_chat_message(self, ch, method, properties, body):
        """Chat mesajlarını işle"""
        try:
            data = json.loads(body)
            
            if data['username'] != self.username:  # Kendi mesajını gösterme
                timestamp = datetime.fromisoformat(data['timestamp'])
                time_str = timestamp.strftime("%H:%M")
                
                print(f"\n📨 [{data['room']}] {data['username']} ({time_str}): {data['message']}")
                
        except Exception as e:
            logger.error(f"❌ Message error: {e}")
    
    def start_consuming(self):
        """Mesaj dinlemeye başla"""
        if not self.channel:
            self.connect()
        
        print(f"👂 {self.username}, {', '.join(self.rooms)} room'larını dinliyor...")
        print("🔴 Durdurmak için CTRL+C")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def main():
    if len(sys.argv) < 3:
        print("Kullanım: python chat_consumer.py <username> <room1> [room2] [room3]...")
        print("Örnek: python chat_consumer.py alice general tech random")
        sys.exit(1)
    
    username = sys.argv[1]
    rooms = sys.argv[2:]
    
    consumer = ChatConsumer(username, rooms)
    consumer.start_consuming()

if __name__ == '__main__':
    main()