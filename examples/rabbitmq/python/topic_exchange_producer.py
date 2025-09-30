#!/usr/bin/env python3
"""
RabbitMQ Topic Exchange Producer
Topic exchange ile pattern-based news routing örneği.
"""

import pika
import json
import sys
import random
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsProducer:
    def __init__(self, host='localhost', port=5672, username='admin', password='admin123'):
        """News Producer initialization"""
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
            
            # Topic exchange declare
            self.channel.exchange_declare(
                exchange='news_exchange',
                exchange_type='topic',
                durable=True
            )
            
            logger.info("✅ Connected to RabbitMQ")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def publish_news(self, category, subcategory, urgency, title, content):
        """Haber yayınla"""
        if not self.channel:
            self.connect()
            
        # Routing key format: category.subcategory.urgency
        routing_key = f"{category}.{subcategory}.{urgency}"
        
        news_data = {
            'category': category,
            'subcategory': subcategory,
            'urgency': urgency,
            'title': title,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'routing_key': routing_key,
            'author': 'News System',
            'views': 0
        }
        
        self.channel.basic_publish(
            exchange='news_exchange',
            routing_key=routing_key,
            body=json.dumps(news_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        urgency_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }.get(urgency, '📰')
        
        print(f"{urgency_emoji} Published: {routing_key} - {title}")
    
    def publish_batch_news(self, news_list):
        """Batch haber yayını"""
        if not self.channel:
            self.connect()
            
        for news in news_list:
            self.publish_news(
                news['category'],
                news['subcategory'], 
                news['urgency'],
                news['title'],
                news['content']
            )
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔒 Connection closed")

def generate_sample_news():
    """Sample haberler oluştur"""
    return [
        {
            'category': 'tech',
            'subcategory': 'ai',
            'urgency': 'high',
            'title': 'New AI Breakthrough in Healthcare',
            'content': 'Revolutionary AI model can diagnose diseases with 99% accuracy...'
        },
        {
            'category': 'tech',
            'subcategory': 'mobile',
            'urgency': 'medium',
            'title': 'New Smartphone Released',
            'content': 'Latest smartphone features advanced camera and longer battery life...'
        },
        {
            'category': 'finance',
            'subcategory': 'crypto',
            'urgency': 'high',
            'title': 'Bitcoin Reaches New High',
            'content': 'Bitcoin price surges to new all-time high amid institutional adoption...'
        },
        {
            'category': 'finance',
            'subcategory': 'stock',
            'urgency': 'medium',
            'title': 'Market Updates',
            'content': 'Stock market shows positive trends in technology sector...'
        },
        {
            'category': 'sports',
            'subcategory': 'football',
            'urgency': 'low',
            'title': 'Championship Match Results',
            'content': 'Yesterday championship match ended with exciting overtime...'
        },
        {
            'category': 'weather',
            'subcategory': 'storm',
            'urgency': 'critical',
            'title': 'Severe Storm Warning',
            'content': 'Severe storm approaching coastal areas, evacuation recommended...'
        },
        {
            'category': 'health',
            'subcategory': 'pandemic',
            'urgency': 'high',
            'title': 'New Vaccine Development',
            'content': 'New vaccine shows promising results in clinical trials...'
        },
        {
            'category': 'tech',
            'subcategory': 'cybersecurity',
            'urgency': 'critical',
            'title': 'Major Security Breach',
            'content': 'Large corporation reports significant data breach affecting millions...'
        }
    ]

def main():
    producer = NewsProducer()
    
    try:
        producer.connect()
        
        if len(sys.argv) > 3:
            # Command line: category subcategory urgency title
            category = sys.argv[1]
            subcategory = sys.argv[2] 
            urgency = sys.argv[3]
            title = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else 'Custom News'
            content = f"Custom news content for {title}"
            
            producer.publish_news(category, subcategory, urgency, title, content)
        else:
            # Demo news
            print("📰 Publishing sample news...")
            sample_news = generate_sample_news()
            producer.publish_batch_news(sample_news)
            
            print(f"\n✅ Published {len(sample_news)} news items")
            print("\n📋 Routing key patterns used:")
            for news in sample_news:
                routing_key = f"{news['category']}.{news['subcategory']}.{news['urgency']}"
                print(f"   {routing_key}")
            
    except Exception as e:
        logger.error(f"❌ Producer error: {e}")
    finally:
        producer.close()

if __name__ == '__main__':
    main()