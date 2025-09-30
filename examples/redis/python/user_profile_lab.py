# examples/redis/python/user_profile_lab.py
import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class UserProfileManager:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            password='redis123',
            db=0,
            decode_responses=True
        )
        
        print("🚀 User Profile Manager başlatıldı")
        
    def create_user(self, name: str, email: str, age: int, city: str) -> str:
        """Yeni kullanıcı oluştur"""
        user_id = str(uuid.uuid4())[:8]  # Short UUID
        
        # 1. User hash'i oluştur
        user_key = f"user:{user_id}"
        user_data = {
            "id": user_id,
            "name": name,
            "email": email,
            "age": age,
            "city": city,
            "created_at": datetime.now().isoformat(),
            "last_login": "",
            "login_count": 0,
            "is_active": 1
        }
        
        self.redis.hset(user_key, mapping=user_data)
        
        # 2. Email index oluştur (unique email kontrolü için)
        email_key = f"email:{email}"
        self.redis.set(email_key, user_id)
        
        # 3. City index'e ekle
        city_key = f"city:{city}:users"
        self.redis.sadd(city_key, user_id)
        
        # 4. User counter artır
        total_users = self.redis.incr("stats:total_users")
        
        print(f"✅ User created: {name} (ID: {user_id}) - Total users: {total_users}")
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Kullanıcı bilgilerini al"""
        user_key = f"user:{user_id}"
        user_data = self.redis.hgetall(user_key)
        
        if not user_data:
            return None
            
        # Type conversions
        user_data['age'] = int(user_data['age'])
        user_data['login_count'] = int(user_data['login_count'])
        user_data['is_active'] = bool(int(user_data['is_active']))
        
        return user_data
    
    def update_user(self, user_id: str, **updates) -> bool:
        """Kullanıcı bilgilerini güncelle"""
        user_key = f"user:{user_id}"
        
        # User var mı kontrol et
        if not self.redis.exists(user_key):
            print(f"❌ User not found: {user_id}")
            return False
        
        # Updates uygula
        for field, value in updates.items():
            self.redis.hset(user_key, field, value)
        
        # Last updated zamanını güncelle
        self.redis.hset(user_key, "updated_at", datetime.now().isoformat())
        
        print(f"✅ User updated: {user_id}")
        return True
    
    def user_login(self, email: str) -> Optional[str]:
        """Kullanıcı girişi"""
        # Email ile user_id bul
        email_key = f"email:{email}"
        user_id = self.redis.get(email_key)
        
        if not user_id:
            print(f"❌ User not found with email: {email}")
            return None
        
        user_key = f"user:{user_id}"
        
        # Login count artır
        login_count = self.redis.hincrby(user_key, "login_count", 1)
        
        # Last login güncelle
        self.redis.hset(user_key, "last_login", datetime.now().isoformat())
        
        # Session oluştur
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        session_data = {
            "user_id": user_id,
            "login_time": datetime.now().isoformat(),
            "ip": "127.0.0.1"  # Simulated
        }
        
        # Session 1 saat geçerli
        self.redis.setex(session_key, 3600, json.dumps(session_data))
        
        print(f"✅ User logged in: {email} (Login count: {login_count})")
        return session_id
    
    def add_user_activity(self, user_id: str, activity: str):
        """Kullanıcı aktivitesi ekle"""
        activity_key = f"user:{user_id}:activity"
        timestamp = datetime.now().isoformat()
        activity_data = f"{timestamp}: {activity}"
        
        # Son 100 aktiviteyi tut
        self.redis.lpush(activity_key, activity_data)
        self.redis.ltrim(activity_key, 0, 99)
        
        print(f"📝 Activity added for {user_id}: {activity}")
    
    def get_user_activity(self, user_id: str, limit: int = 10) -> List[str]:
        """Kullanıcı aktivitelerini al"""
        activity_key = f"user:{user_id}:activity"
        activities = self.redis.lrange(activity_key, 0, limit - 1)
        return activities
    
    def add_user_tags(self, user_id: str, *tags):
        """Kullanıcıya tag ekle"""
        tags_key = f"user:{user_id}:tags"
        self.redis.sadd(tags_key, *tags)
        
        # Global tag counter'ları güncelle
        for tag in tags:
            tag_counter_key = f"tag:{tag}:count"
            self.redis.incr(tag_counter_key)
        
        print(f"🏷️ Tags added to {user_id}: {', '.join(tags)}")
    
    def get_users_by_city(self, city: str) -> List[str]:
        """Şehre göre kullanıcıları al"""
        city_key = f"city:{city}:users"
        user_ids = self.redis.smembers(city_key)
        return list(user_ids)
    
    def get_user_score(self, user_id: str) -> int:
        """Kullanıcı skoru al"""
        score_key = "leaderboard:user_score"
        score = self.redis.zscore(score_key, user_id)
        return int(score) if score else 0
    
    def update_user_score(self, user_id: str, points: int):
        """Kullanıcı skorunu güncelle"""
        score_key = "leaderboard:user_score"
        new_score = self.redis.zincrby(score_key, points, user_id)
        
        print(f"🎯 Score updated for {user_id}: +{points} (Total: {int(new_score)})")
        return int(new_score)
    
    def get_leaderboard(self, limit: int = 10) -> List[tuple]:
        """Leaderboard'u al"""
        score_key = "leaderboard:user_score"
        return self.redis.zrevrange(score_key, 0, limit - 1, withscores=True)
    
    def get_stats(self) -> Dict:
        """Sistem istatistikleri"""
        stats = {}
        
        # Total users
        stats['total_users'] = self.redis.get("stats:total_users") or "0"
        
        # Active sessions
        session_keys = self.redis.keys("session:*")
        stats['active_sessions'] = len(session_keys)
        
        # Cities
        city_keys = self.redis.keys("city:*:users")
        stats['cities'] = len(city_keys)
        
        # Memory usage
        info = self.redis.info('memory')
        stats['memory_used'] = info['used_memory_human']
        
        return stats
    
    def run_demo(self):
        """Demo senaryosu çalıştır"""
        print("\n🎬 User Profile Management Demo başlıyor...")
        print("=" * 50)
        
        # 1. Kullanıcılar oluştur
        print("\n👥 Kullanıcılar oluşturuluyor...")
        users = [
            ("Ahmet Yılmaz", "ahmet@example.com", 25, "Istanbul"),
            ("Fatma Kaya", "fatma@example.com", 30, "Ankara"),
            ("Mehmet Demir", "mehmet@example.com", 28, "Izmir"),
            ("Ayşe Şahin", "ayse@example.com", 22, "Istanbul"),
            ("Can Öztürk", "can@example.com", 35, "Bursa")
        ]
        
        user_ids = []
        for name, email, age, city in users:
            user_id = self.create_user(name, email, age, city)
            user_ids.append(user_id)
        
        # 2. Kullanıcı girişleri simüle et
        print("\n🔐 Kullanıcı girişleri...")
        sessions = []
        for name, email, _, _ in users[:3]:  # İlk 3 kullanıcı
            session_id = self.user_login(email)
            sessions.append(session_id)
        
        # 3. Aktiviteler ekle
        print("\n📝 Aktiviteler ekleniyor...")
        activities = [
            "Profile viewed",
            "Settings updated",
            "Friend added",
            "Post created",
            "Comment added"
        ]
        
        for i, user_id in enumerate(user_ids):
            for j, activity in enumerate(activities[:i+2]):
                self.add_user_activity(user_id, activity)
        
        # 4. Tag'lar ekle
        print("\n🏷️ Tag'lar ekleniyor...")
        tag_sets = [
            ["developer", "python", "redis"],
            ["designer", "ui", "ux"], 
            ["manager", "agile", "scrum"],
            ["student", "computer-science"],
            ["entrepreneur", "startup", "tech"]
        ]
        
        for user_id, tags in zip(user_ids, tag_sets):
            self.add_user_tags(user_id, *tags)
        
        # 5. Skorlar ekle
        print("\n🎯 Skorlar ekleniyor...")
        import random
        for user_id in user_ids:
            points = random.randint(100, 1000)
            self.update_user_score(user_id, points)
        
        # 6. Sonuçları göster
        print("\n📊 DEMO SONUÇLARI")
        print("=" * 50)
        
        # İstatistikler
        stats = self.get_stats()
        print("\n📈 Sistem İstatistikleri:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Istanbul kullanıcıları
        istanbul_users = self.get_users_by_city("Istanbul")
        print(f"\n🏙️ Istanbul'daki kullanıcılar: {len(istanbul_users)}")
        for user_id in istanbul_users:
            user = self.get_user(user_id)
            if user:
                print(f"  - {user['name']} (ID: {user_id})")
        
        # Leaderboard
        print("\n🏆 Leaderboard (Top 5):")
        leaderboard = self.get_leaderboard(5)
        for i, (user_id, score) in enumerate(leaderboard, 1):
            user = self.get_user(user_id)
            name = user['name'] if user else 'Unknown'
            print(f"  {i}. {name}: {int(score)} points")
        
        # Bir kullanıcının detayları
        if user_ids:
            sample_user_id = user_ids[0]
            user = self.get_user(sample_user_id)
            print(f"\n👤 Örnek Kullanıcı Detayları ({user['name']}):")
            print(f"  Email: {user['email']}")
            print(f"  Age: {user['age']}")
            print(f"  City: {user['city']}")
            print(f"  Login Count: {user['login_count']}")
            print(f"  Score: {self.get_user_score(sample_user_id)}")
            
            # Son aktiviteler
            activities = self.get_user_activity(sample_user_id, 3)
            print(f"  Recent Activities:")
            for activity in activities:
                print(f"    - {activity}")

if __name__ == "__main__":
    manager = UserProfileManager()
    manager.run_demo()