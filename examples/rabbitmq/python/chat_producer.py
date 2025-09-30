#!/usr/bin/env python3
"""
RabbitMQ Chat Producer
Real-time chat uygulaması için mesaj gönderen component.
"""

import pika
import json
import sys
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatProducer:
    def __init__(self, username, host='localhost', port=5672, user='admin', password='admin123'):
        """Chat Producer initialization"""
        self.username = username
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None
        
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
            
            self.setup_exchanges()
            
            logger.info("✅ RabbitMQ'ya bağlandı")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Bağlantı hatası: {e}")
            raise
    
    def setup_exchanges(self):
        """Exchange'leri oluştur"""
        # Fanout exchange - tüm kullanıcılara broadcast
        self.channel.exchange_declare(
            exchange='chat_broadcast',
            exchange_type='fanout',
            durable=True
        )
        
        # Topic exchange - room'lara göre routing
        self.channel.exchange_declare(
            exchange='chat_rooms',
            exchange_type='topic',
            durable=True
        )
    
    def send_message(self, room, message):
        """Chat mesajı gönder"""
        if not self.channel:
            self.connect()
            
        message_data = {
            'type': 'chat_message',
            'username': self.username,
            'room': room,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Room'a göre routing
        routing_key = f"room.{room}"
        
        self.channel.basic_publish(
            exchange='chat_rooms',
            routing_key=routing_key,
            body=json.dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        print(f"📤 [{room}] {self.username}: {message}")
    
    def send_notification(self, action):
        """Kullanıcı bildirimi gönder (join/leave)"""
        if not self.channel:
            self.connect()
            
        notification_data = {
            'type': 'user_notification',
            'username': self.username,
            'action': action,  # 'joined' or 'left'
            'timestamp': datetime.now().isoformat()
        }
        
        self.channel.basic_publish(
            exchange='chat_broadcast',
            routing_key='',
            body=json.dumps(notification_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        print(f"🔔 {self.username} {action} the chat")
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔒 Bağlantı kapatıldı")

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python chat_producer.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    producer = ChatProducer(username)
    
    try:
        producer.connect()
        
        # Giriş bildirimi
        producer.send_notification('joined')
        
        print(f"💬 Chat'e hoş geldin {username}!")
        print("📝 Mesaj formatı: <room> <mesaj>")
        print("   Örnek: general Merhaba dünya!")
        print("📌 Çıkmak için 'quit' yaz")
        
        while True:
            user_input = input(f"{username}> ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if ' ' in user_input:
                room, message = user_input.split(' ', 1)
                producer.send_message(room, message)
            else:
                print("❌ Format: <room> <mesaj>")
    
    except KeyboardInterrupt:
        pass
    
    finally:
        # Çıkış bildirimi
        producer.send_notification('left')
        producer.close()

if __name__ == '__main__':
    main()