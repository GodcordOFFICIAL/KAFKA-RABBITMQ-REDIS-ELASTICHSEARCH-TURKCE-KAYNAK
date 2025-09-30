"""
Redis Pub/Sub Temel Örnekleri

Bu dosya Redis Pub/Sub sistemi için temel kullanım örnekleri içerir.
"""

import redis
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Any

class RedisPubSubBasics:
    """
    Redis Pub/Sub temel işlemleri için örnek sınıf
    """
    
    def __init__(self, host='localhost', port=6379, db=0):
        """
        Redis bağlantısını başlat
        
        Args:
            host: Redis sunucu adresi
            port: Redis port numarası
            db: Redis database numarası
        """
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        print(f"✅ Redis'e bağlanıldı: {host}:{port}")
        
    def demo_basic_pubsub(self):
        """
        Temel Pub/Sub işlemlerini göster
        """
        print("\n" + "="*50)
        print("🔄 DEMO: Temel Pub/Sub İşlemleri")
        print("="*50)
        
        # Publisher kısmı
        print("\n📡 Publisher - Mesaj Gönderme:")
        
        messages = [
            ("news", "İlk haber mesajı"),
            ("sports", "Maç sonucu: A takımı kazandı"),
            ("tech", "Yeni AI modeli duyuruldu"),
            ("news", "İkinci haber mesajı")
        ]
        
        for channel, message in messages:
            subscriber_count = self.redis_client.publish(channel, message)
            print(f"   📤 {channel}: '{message}' -> {subscriber_count} subscriber")
            time.sleep(1)
        
        # Channel bilgileri
        print("\n📊 Channel Bilgileri:")
        active_channels = self.redis_client.pubsub_channels()
        print(f"   📡 Aktif channel'lar: {active_channels}")
        
        for channel in ['news', 'sports', 'tech']:
            sub_count = self.redis_client.pubsub_numsub(channel)[1]
            print(f"   👥 {channel}: {sub_count} subscriber")
    
    def demo_pattern_subscription(self):
        """
        Pattern-based subscription örneği
        """
        print("\n" + "="*50)
        print("🔍 DEMO: Pattern Subscription")
        print("="*50)
        
        # Farklı pattern'lere mesaj gönder
        test_channels = [
            "news.tech", "news.sports", "news.politics",
            "alerts.security", "alerts.system",
            "user.login", "user.logout"
        ]
        
        print("\n📡 Test kanallarına mesaj gönderiliyor:")
        for channel in test_channels:
            message = f"Test mesajı - {channel}"
            subscriber_count = self.redis_client.publish(channel, message)
            print(f"   📤 {channel}: {subscriber_count} subscriber")
            
        # Pattern statistics
        pattern_count = self.redis_client.pubsub_numpat()
        print(f"\n📊 Toplam pattern subscription: {pattern_count}")
    
    def demo_json_messaging(self):
        """
        JSON formatında mesajlaşma örneği
        """
        print("\n" + "="*50)
        print("📋 DEMO: JSON Mesajlaşma")
        print("="*50)
        
        # Structured data göndér
        events = [
            {
                "type": "user_login",
                "user_id": "user123",
                "username": "alice",
                "timestamp": datetime.now().isoformat(),
                "ip_address": "192.168.1.100",
                "device": "mobile"
            },
            {
                "type": "order_created", 
                "order_id": "ORD-001",
                "user_id": "user123",
                "amount": 150.50,
                "currency": "TRY",
                "items": ["laptop", "mouse"],
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "payment_completed",
                "order_id": "ORD-001",
                "payment_method": "credit_card",
                "amount": 150.50,
                "timestamp": datetime.now().isoformat(),
                "transaction_id": "TXN-789"
            }
        ]
        
        print("\n📡 Structured event'ler gönderiliyor:")
        for event in events:
            channel = f"events.{event['type']}"
            message = json.dumps(event, ensure_ascii=False, indent=2)
            
            subscriber_count = self.redis_client.publish(channel, message)
            print(f"   📤 {channel}: {subscriber_count} subscriber")
            print(f"       📋 Event: {event['type']}")
            print(f"       🕐 Zaman: {event['timestamp']}")
            print("   " + "-"*40)
            time.sleep(1)

class SimpleSubscriber:
    """
    Basit subscriber implementasyonu
    """
    
    def __init__(self, subscriber_name, host='localhost', port=6379, db=0):
        """
        Subscriber'ı başlat
        
        Args:
            subscriber_name: Subscriber adı
            host: Redis sunucu adresi
            port: Redis port numarası
            db: Redis database numarası
        """
        self.subscriber_name = subscriber_name
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.is_listening = False
        
    def subscribe_to_channels(self, channels: List[str]):
        """
        Belirli kanallara abone ol
        
        Args:
            channels: Abone olunacak kanal listesi
        """
        self.pubsub.subscribe(*channels)
        print(f"👤 {self.subscriber_name} abone oldu:")
        for channel in channels:
            print(f"   📡 {channel}")
        print("-" * 40)
        
    def subscribe_to_patterns(self, patterns: List[str]):
        """
        Pattern'lere abone ol
        
        Args:
            patterns: Pattern listesi
        """
        self.pubsub.psubscribe(*patterns)
        print(f"👤 {self.subscriber_name} pattern abone oldu:")
        for pattern in patterns:
            print(f"   🔍 {pattern}")
        print("-" * 40)
        
    def start_listening(self):
        """
        Mesajları dinlemeye başla
        """
        self.is_listening = True
        print(f"👂 {self.subscriber_name} dinlemeye başladı...")
        
        try:
            for message in self.pubsub.listen():
                if not self.is_listening:
                    break
                    
                self._handle_message(message)
                
        except KeyboardInterrupt:
            print(f"\n🛑 {self.subscriber_name} durduruldu")
        finally:
            self.stop_listening()
    
    def _handle_message(self, message: Dict[str, Any]):
        """
        Gelen mesajı işle
        
        Args:
            message: Redis'ten gelen mesaj
        """
        if message['type'] == 'message':
            print(f"📨 {self.subscriber_name} - Mesaj:")
            print(f"   📡 Kanal: {message['channel']}")
            print(f"   📝 İçerik: {message['data']}")
            print(f"   🕐 Zaman: {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            
        elif message['type'] == 'pmessage':
            print(f"🔍 {self.subscriber_name} - Pattern Mesajı:")
            print(f"   🔍 Pattern: {message['pattern']}")
            print(f"   📡 Kanal: {message['channel']}")
            print(f"   📝 İçerik: {message['data']}")
            print(f"   🕐 Zaman: {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            
        elif message['type'] == 'subscribe':
            print(f"✅ {self.subscriber_name} - {message['channel']} kanalına abone oldu")
            
        elif message['type'] == 'psubscribe':
            print(f"✅ {self.subscriber_name} - {message['pattern']} pattern'ine abone oldu")
    
    def stop_listening(self):
        """
        Dinlemeyi durdur
        """
        self.is_listening = False
        self.pubsub.close()
        print(f"✋ {self.subscriber_name} bağlantısı kapatıldı")

def demo_subscriber_example():
    """
    Subscriber kullanım örneği
    """
    print("👥 Subscriber Demo Başlıyor...")
    print("Bu demo'yu çalıştırdıktan sonra başka bir terminal'de publisher çalıştırın")
    print("Publisher: python -c \"import redis; r=redis.Redis(decode_responses=True); r.publish('test', 'Merhaba!')\"")
    print("-" * 60)
    
    # Subscriber oluştur
    subscriber = SimpleSubscriber("TestSubscriber")
    
    # Kanallara abone ol
    subscriber.subscribe_to_channels(["test", "news", "alerts"])
    
    # Pattern'lere de abone ol
    subscriber.subscribe_to_patterns(["events.*", "user.*"])
    
    try:
        # Dinlemeye başla
        subscriber.start_listening()
    except KeyboardInterrupt:
        print("\n🛑 Demo durduruldu")

def demo_multi_subscriber():
    """
    Çoklu subscriber örneği
    """
    print("👥 Çoklu Subscriber Demo")
    print("-" * 40)
    
    # Farklı subscriber'lar oluştur
    subscribers = [
        ("NewsReader", ["news", "politics"]),
        ("TechEnthusiast", ["tech"]),
        ("AlertMonitor", ["alerts", "system"])
    ]
    
    threads = []
    subscriber_objects = []
    
    # Her subscriber için thread oluştur
    for name, channels in subscribers:
        subscriber = SimpleSubscriber(name)
        subscriber.subscribe_to_channels(channels)
        subscriber_objects.append(subscriber)
        
        # Thread'i başlat
        thread = threading.Thread(target=subscriber.start_listening)
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    print("\n🚀 Tüm subscriber'lar hazır!")
    print("Test mesajları göndermek için başka terminal'de şu komutları çalıştırın:")
    print("redis-cli PUBLISH news 'Son dakika haberi'")
    print("redis-cli PUBLISH tech 'Yeni teknoloji duyurusu'")
    print("redis-cli PUBLISH alerts 'Sistem uyarısı'")
    print("\nÇıkmak için Ctrl+C")
    
    try:
        # Ana thread'i canlı tut
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Tüm subscriber'lar durduruluyor...")
        for subscriber in subscriber_objects:
            subscriber.stop_listening()

if __name__ == "__main__":
    # Temel Redis Pub/Sub örnekleri
    pubsub_demo = RedisPubSubBasics()
    
    print("Redis Pub/Sub Temel Örnekleri")
    print("=" * 50)
    
    # Demo seçenekleri
    demos = {
        "1": ("Temel Pub/Sub", pubsub_demo.demo_basic_pubsub),
        "2": ("Pattern Subscription", pubsub_demo.demo_pattern_subscription),
        "3": ("JSON Mesajlaşma", pubsub_demo.demo_json_messaging),
        "4": ("Subscriber Örneği", demo_subscriber_example),
        "5": ("Çoklu Subscriber", demo_multi_subscriber)
    }
    
    print("\nDemo seçenekleri:")
    for key, (name, _) in demos.items():
        print(f"  {key}: {name}")
    
    choice = input("\nHangi demo'yu çalıştırmak istiyorsunuz? (1-5): ").strip()
    
    if choice in demos:
        print(f"\n🚀 {demos[choice][0]} demo'su başlıyor...\n")
        demos[choice][1]()
    else:
        print("❌ Geçersiz seçim!")