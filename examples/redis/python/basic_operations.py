# examples/redis/python/basic_operations.py
import redis
import json
import time
from datetime import datetime, timedelta

class RedisBasics:
    def __init__(self):
        # Redis bağlantısı
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            password='redis123',
            db=0,  # Database 0 kullan
            decode_responses=True  # String response'ları otomatik decode et
        )
        
        # Bağlantı testi
        try:
            self.redis_client.ping()
            print("✅ Redis bağlantısı başarılı!")
        except redis.ConnectionError:
            print("❌ Redis bağlantısı başarısız!")
            raise

    def demo_string_operations(self):
        """String operasyonları demo"""
        print("\n🔤 STRING OPERATIONS DEMO")
        print("=" * 40)
        
        # 1. Basit SET/GET
        key = "user:1001:name"
        value = "Ahmet Yılmaz"
        
        self.redis_client.set(key, value)
        retrieved = self.redis_client.get(key)
        print(f"SET/GET: {key} = {retrieved}")
        
        # 2. TTL (Time To Live) ile SET
        temp_key = "temp:session:abc123"
        self.redis_client.setex(temp_key, 30, "temporary_data")  # 30 saniye TTL
        ttl = self.redis_client.ttl(temp_key)
        print(f"TTL Example: {temp_key} expires in {ttl} seconds")
        
        # 3. Counter operations
        counter_key = "page:views:homepage"
        
        # Counter'ı artır
        views = self.redis_client.incr(counter_key)
        print(f"Page views: {views}")
        
        # Belirli miktarda artır
        views = self.redis_client.incrby(counter_key, 5)
        print(f"Page views after +5: {views}")
        
        # 4. Multiple operations
        user_data = {
            "user:1001:email": "ahmet@example.com",
            "user:1001:age": "25",
            "user:1001:city": "Istanbul"
        }
        
        # Multiple SET
        self.redis_client.mset(user_data)
        
        # Multiple GET
        keys = list(user_data.keys())
        values = self.redis_client.mget(keys)
        
        print("Multiple GET:")
        for key, value in zip(keys, values):
            print(f"  {key}: {value}")

    def demo_hash_operations(self):
        """Hash operasyonları demo"""
        print("\n🗃️ HASH OPERATIONS DEMO")
        print("=" * 40)
        
        hash_key = "user:1001"
        
        # 1. Hash field'ları set et
        user_hash = {
            "name": "Ahmet Yılmaz",
            "email": "ahmet@example.com",
            "age": "25",
            "city": "Istanbul",
            "joined": datetime.now().isoformat()
        }
        
        self.redis_client.hset(hash_key, mapping=user_hash)
        print(f"Hash oluşturuldu: {hash_key}")
        
        # 2. Tek field al
        name = self.redis_client.hget(hash_key, "name")
        print(f"Name: {name}")
        
        # 3. Tüm hash'i al
        all_data = self.redis_client.hgetall(hash_key)
        print("Tüm user data:")
        for field, value in all_data.items():
            print(f"  {field}: {value}")
        
        # 4. Field'ların varlığını kontrol et
        exists = self.redis_client.hexists(hash_key, "email")
        print(f"Email field exists: {exists}")
        
        # 5. Field sayısını al
        field_count = self.redis_client.hlen(hash_key)
        print(f"Field count: {field_count}")
        
        # 6. Sadece field'ları al
        fields = self.redis_client.hkeys(hash_key)
        print(f"Fields: {fields}")
        
        # 7. Numeric field operations
        self.redis_client.hincrby(hash_key, "login_count", 1)
        login_count = self.redis_client.hget(hash_key, "login_count")
        print(f"Login count: {login_count}")

    def demo_list_operations(self):
        """List operasyonları demo"""
        print("\n📝 LIST OPERATIONS DEMO")
        print("=" * 40)
        
        list_key = "user:1001:activity"
        
        # 1. Liste başına ekle (LPUSH)
        activities = [
            "Logged in",
            "Viewed profile", 
            "Updated settings",
            "Logged out"
        ]
        
        for activity in activities:
            timestamp = datetime.now().isoformat()
            activity_data = f"{timestamp}: {activity}"
            self.redis_client.lpush(list_key, activity_data)
        
        print(f"Activities added to list: {list_key}")
        
        # 2. Liste uzunluğu
        length = self.redis_client.llen(list_key)
        print(f"List length: {length}")
        
        # 3. Liste elemanlarını al (son 5)
        recent_activities = self.redis_client.lrange(list_key, 0, 4)
        print("Recent activities:")
        for i, activity in enumerate(recent_activities, 1):
            print(f"  {i}. {activity}")
        
        # 4. Liste sonundan eleman çıkar (RPOP)
        oldest = self.redis_client.rpop(list_key)
        print(f"Removed oldest activity: {oldest}")
        
        # 5. Queue simulation (LPUSH + RPOP)
        queue_key = "task:queue"
        
        # Task'ları queue'ya ekle
        tasks = ["send_email", "process_payment", "generate_report"]
        for task in tasks:
            self.redis_client.lpush(queue_key, task)
        
        # Task'ları işle
        print("Processing tasks from queue:")
        while True:
            task = self.redis_client.rpop(queue_key)
            if not task:
                break
            print(f"  Processing: {task}")

    def demo_set_operations(self):
        """Set operasyonları demo"""
        print("\n🎯 SET OPERATIONS DEMO")
        print("=" * 40)
        
        # 1. User tags
        user_tags_key = "user:1001:tags"
        tags = ["developer", "golang", "redis", "docker", "microservices"]
        
        # Set'e elemanları ekle
        self.redis_client.sadd(user_tags_key, *tags)
        print(f"Tags added to set: {user_tags_key}")
        
        # 2. Set elemanlarını al
        all_tags = self.redis_client.smembers(user_tags_key)
        print(f"All tags: {all_tags}")
        
        # 3. Set boyutu
        tag_count = self.redis_client.scard(user_tags_key)
        print(f"Tag count: {tag_count}")
        
        # 4. Eleman varlığını kontrol et
        has_golang = self.redis_client.sismember(user_tags_key, "golang")
        has_python = self.redis_client.sismember(user_tags_key, "python")
        print(f"Has golang: {has_golang}, Has python: {has_python}")
        
        # 5. Random eleman al
        random_tag = self.redis_client.srandmember(user_tags_key)
        print(f"Random tag: {random_tag}")
        
        # 6. Set operations (union, intersection, difference)
        user2_tags_key = "user:1002:tags"
        user2_tags = ["python", "redis", "mongodb", "kubernetes"]
        self.redis_client.sadd(user2_tags_key, *user2_tags)
        
        # Intersection (ortak taglar)
        common_tags = self.redis_client.sinter(user_tags_key, user2_tags_key)
        print(f"Common tags: {common_tags}")
        
        # Union (tüm taglar)
        all_unique_tags = self.redis_client.sunion(user_tags_key, user2_tags_key)
        print(f"All unique tags: {all_unique_tags}")
        
        # Difference (farklı taglar)
        unique_to_user1 = self.redis_client.sdiff(user_tags_key, user2_tags_key)
        print(f"Tags unique to user1: {unique_to_user1}")

    def demo_sorted_set_operations(self):
        """Sorted Set operasyonları demo"""
        print("\n📈 SORTED SET OPERATIONS DEMO")
        print("=" * 40)
        
        leaderboard_key = "game:leaderboard"
        
        # 1. Skorları ekle
        players = {
            "player1": 1500,
            "player2": 1200,
            "player3": 1800,
            "player4": 1100,
            "player5": 1600
        }
        
        for player, score in players.items():
            self.redis_client.zadd(leaderboard_key, {player: score})
        
        print("Leaderboard created with players and scores")
        
        # 2. En yüksek skorları al (descending order)
        top_players = self.redis_client.zrevrange(leaderboard_key, 0, 2, withscores=True)
        print("Top 3 players:")
        for i, (player, score) in enumerate(top_players, 1):
            print(f"  {i}. {player}: {int(score)} points")
        
        # 3. Player'ın sırasını bul
        rank = self.redis_client.zrevrank(leaderboard_key, "player1")
        score = self.redis_client.zscore(leaderboard_key, "player1")
        print(f"player1 rank: {rank + 1}, score: {int(score)}")
        
        # 4. Skor aralığında oyuncular
        mid_range_players = self.redis_client.zrangebyscore(
            leaderboard_key, 1200, 1600, withscores=True
        )
        print("Players with scores between 1200-1600:")
        for player, score in mid_range_players:
            print(f"  {player}: {int(score)}")
        
        # 5. Skor artırma
        new_score = self.redis_client.zincrby(leaderboard_key, 100, "player4")
        print(f"player4 new score after +100: {int(new_score)}")
        
        # 6. Sorted set boyutu
        total_players = self.redis_client.zcard(leaderboard_key)
        print(f"Total players in leaderboard: {total_players}")

    def demo_expiration_and_ttl(self):
        """Expiration ve TTL demo"""
        print("\n⏰ EXPIRATION & TTL DEMO")
        print("=" * 40)
        
        # 1. TTL ile key oluştur
        session_key = "session:user1001:abc123"
        session_data = json.dumps({
            "user_id": 1001,
            "login_time": datetime.now().isoformat(),
            "ip": "192.168.1.100"
        })
        
        # 60 saniye TTL
        self.redis_client.setex(session_key, 60, session_data)
        print(f"Session created with 60s TTL: {session_key}")
        
        # 2. TTL kontrolü
        ttl = self.redis_client.ttl(session_key)
        print(f"Session TTL: {ttl} seconds")
        
        # 3. TTL uzatma
        self.redis_client.expire(session_key, 120)  # 120 saniyeye uzat
        new_ttl = self.redis_client.ttl(session_key)
        print(f"Session TTL extended to: {new_ttl} seconds")
        
        # 4. Cache pattern example
        cache_key = "cache:user:1001:profile"
        
        # Cache'de var mı kontrol et
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            print("Data found in cache")
            profile = json.loads(cached_data)
        else:
            print("Data not in cache, simulating database fetch...")
            # Simulated database fetch
            time.sleep(0.1)  # Simulate DB delay
            
            profile = {
                "user_id": 1001,
                "name": "Ahmet Yılmaz",
                "email": "ahmet@example.com",
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache'e kaydet (5 dakika TTL)
            self.redis_client.setex(
                cache_key,
                300,  # 5 minutes
                json.dumps(profile)
            )
            print("Data cached for 5 minutes")
        
        print(f"Profile data: {profile}")

    def cleanup_demo_data(self):
        """Demo verilerini temizle"""
        print("\n🧹 CLEANUP DEMO DATA")
        print("=" * 40)
        
        # Demo'da kullanılan key pattern'leri
        patterns = [
            "user:*",
            "temp:*", 
            "page:*",
            "game:*",
            "task:*",
            "session:*",
            "cache:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                total_deleted += deleted
                print(f"Deleted {deleted} keys matching pattern: {pattern}")
        
        print(f"Total keys deleted: {total_deleted}")

    def run_all_demos(self):
        """Tüm demo'ları çalıştır"""
        print("🚀 Redis Basics Demo başlıyor...\n")
        
        try:
            self.demo_string_operations()
            self.demo_hash_operations()
            self.demo_list_operations()
            self.demo_set_operations()
            self.demo_sorted_set_operations()
            self.demo_expiration_and_ttl()
            
            print("\n✅ Tüm demo'lar başarıyla tamamlandı!")
            
            # Cleanup seçeneği
            cleanup = input("\n🧹 Demo verilerini temizlemek ister misiniz? (y/N): ")
            if cleanup.lower() == 'y':
                self.cleanup_demo_data()
                
        except Exception as e:
            print(f"❌ Demo sırasında hata: {str(e)}")
            raise

if __name__ == "__main__":
    redis_demo = RedisBasics()
    redis_demo.run_all_demos()