"""
Redis Pub/Sub Tabanlı Real-time Chat Uygulaması

Kullanım:
    python chat_application.py <room_name> <username>
    
Örnek:
    python chat_application.py general alice
    python chat_application.py general bob
"""

import redis
import json
import threading
import uuid
import sys
from datetime import datetime
from typing import Optional

class ChatRoom:
    """
    Redis Pub/Sub tabanlı chat odası implementasyonu
    """
    
    def __init__(self, room_name: str, host='localhost', port=6379, db=0):
        """
        Chat odası oluştur
        
        Args:
            room_name: Chat odası adı
            host: Redis sunucu adresi
            port: Redis port numarası
            db: Redis database numarası
        """
        self.room_name = room_name
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.channel = f"chat.{room_name}"
        self.private_channel = None
        self.user_id = str(uuid.uuid4())[:8]
        self.username = None
        self.is_active = False
        
        # Chat komutları
        self.commands = {
            '/help': self._show_help,
            '/users': self._list_users,
            '/private': self._send_private_message,
            '/rooms': self._list_rooms,
            '/clear': self._clear_screen,
            '/quit': self._quit_chat,
            '/exit': self._quit_chat
        }
        
    def join_room(self, username: str):
        """
        Chat odasına katıl
        
        Args:
            username: Kullanıcı adı
        """
        self.username = username
        self.private_channel = f"chat.private.{username}"
        
        # Ana channel ve özel mesaj channel'ına abone ol
        self.pubsub.subscribe(self.channel, self.private_channel)
        
        # Kullanıcı listesini güncelle (Redis Hash kullanarak)
        user_key = f"chat.users.{self.room_name}"
        self.redis_client.hset(user_key, self.username, json.dumps({
            'user_id': self.user_id,
            'joined_at': datetime.now().isoformat(),
            'status': 'online'
        }))
        
        # Katılım mesajı gönder
        join_message = {
            'type': 'join',
            'user_id': self.user_id,
            'username': username,
            'room': self.room_name,
            'timestamp': datetime.now().isoformat(),
            'content': f"{username} '{self.room_name}' odasına katıldı"
        }
        
        self.redis_client.publish(self.channel, json.dumps(join_message, ensure_ascii=False))
        
        # Kullanıcıya hoş geldin mesajı göster
        self._print_welcome_message()
        
    def _print_welcome_message(self):
        """
        Hoş geldin mesajını göster
        """
        print(f"\n🎉 Hoş geldin {self.username}!")
        print(f"📍 Oda: {self.room_name}")
        print(f"🆔 Kullanıcı ID: {self.user_id}")
        print("─" * 50)
        print("💡 Komutlar:")
        print("   /help     - Yardım")
        print("   /users    - Çevrimiçi kullanıcılar")
        print("   /private @kullanıcı mesaj - Özel mesaj")
        print("   /clear    - Ekranı temizle")
        print("   /quit     - Çıkış")
        print("─" * 50)
        
    def send_message(self, content: str):
        """
        Normal chat mesajı gönder
        
        Args:
            content: Mesaj içeriği
        """
        message = {
            'type': 'message',
            'user_id': self.user_id,
            'username': self.username,
            'room': self.room_name,
            'timestamp': datetime.now().isoformat(),
            'content': content
        }
        
        subscriber_count = self.redis_client.publish(self.channel, json.dumps(message, ensure_ascii=False))
        
        # Kendi mesajımızı echo et
        time_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] 💬 Sen: {content}")
        
        return subscriber_count
    
    def _send_private_message(self, args: str):
        """
        Özel mesaj gönder
        
        Args:
            args: "/private @kullanıcı mesaj" formatındaki string
        """
        parts = args.strip().split(' ', 2)
        if len(parts) < 3:
            print("💡 Kullanım: /private @kullanıcı mesaj")
            return
            
        target_user = parts[1].lstrip('@')
        content = parts[2]
        
        # Hedef kullanıcının online olup olmadığını kontrol et
        user_key = f"chat.users.{self.room_name}"
        user_data = self.redis_client.hget(user_key, target_user)
        
        if not user_data:
            print(f"❌ Kullanıcı '{target_user}' bu odada bulunamadı")
            return
            
        # Özel mesaj kanalına gönder
        private_channel = f"chat.private.{target_user}"
        
        message = {
            'type': 'private',
            'user_id': self.user_id,
            'username': self.username,
            'target': target_user,
            'room': self.room_name,
            'timestamp': datetime.now().isoformat(),
            'content': content
        }
        
        subscriber_count = self.redis_client.publish(private_channel, json.dumps(message, ensure_ascii=False))
        
        if subscriber_count > 0:
            time_str = datetime.now().strftime("%H:%M:%S")
            print(f"[{time_str}] 📨 @{target_user} kullanıcısına özel: {content}")
        else:
            print(f"⚠️  '{target_user}' kullanıcısı şu anda çevrimdışı")
    
    def _list_users(self, args: str = ""):
        """
        Çevrimiçi kullanıcıları listele
        """
        user_key = f"chat.users.{self.room_name}"
        users = self.redis_client.hgetall(user_key)
        
        if not users:
            print("👥 Henüz kimse yok")
            return
            
        print(f"👥 '{self.room_name}' odasındaki kullanıcılar:")
        for username, user_data_str in users.items():
            try:
                user_data = json.loads(user_data_str)
                joined_time = datetime.fromisoformat(user_data['joined_at']).strftime("%H:%M")
                status_icon = "🟢" if user_data['status'] == 'online' else "🔴"
                
                if username == self.username:
                    print(f"   {status_icon} {username} (sen) - Katıldı: {joined_time}")
                else:
                    print(f"   {status_icon} {username} - Katıldı: {joined_time}")
            except:
                print(f"   ❓ {username}")
    
    def _list_rooms(self, args: str = ""):
        """
        Aktif chat odalarını listele
        """
        pattern = "chat.users.*"
        room_keys = []
        
        for key in self.redis_client.scan_iter(match=pattern):
            room_name = key.replace("chat.users.", "")
            user_count = self.redis_client.hlen(key)
            if user_count > 0:
                room_keys.append((room_name, user_count))
        
        if not room_keys:
            print("🏠 Aktif oda yok")
            return
            
        print("🏠 Aktif chat odaları:")
        for room_name, user_count in sorted(room_keys):
            current_icon = "📍" if room_name == self.room_name else "🏠"
            print(f"   {current_icon} {room_name} ({user_count} kullanıcı)")
    
    def _show_help(self, args: str = ""):
        """
        Yardım mesajını göster
        """
        print("\n📖 Chat Komutları:")
        print("   /help           - Bu yardım mesajını göster")
        print("   /users          - Çevrimiçi kullanıcıları listele")
        print("   /rooms          - Aktif odaları listele")
        print("   /private @user  - Özel mesaj gönder")
        print("   /clear          - Ekranı temizle")
        print("   /quit, /exit    - Chat'ten çık")
        print("\n💡 İpuçları:")
        print("   • Normal mesaj göndermek için komut kullanmadan yazın")
        print("   • Özel mesaj: /private @alice Merhaba!")
        print("   • '@kullanıcı' ile birini bahsedebilirsiniz")
        print()
    
    def _clear_screen(self, args: str = ""):
        """
        Ekranı temizle
        """
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self._print_welcome_message()
    
    def _quit_chat(self, args: str = ""):
        """
        Chat'ten çık
        """
        self.leave_room()
        print("👋 Chat'ten çıkılıyor...")
        sys.exit(0)
    
    def handle_message(self, message: dict):
        """
        Gelen mesajı işle ve göster
        
        Args:
            message: Redis'ten gelen mesaj
        """
        if message['type'] == 'message':
            try:
                msg_data = json.loads(message['data'])
                msg_type = msg_data.get('type', 'message')
                username = msg_data.get('username', 'Unknown')
                content = msg_data.get('content', '')
                timestamp = msg_data.get('timestamp', '')
                
                # Kendi mesajlarımızı tekrar gösterme
                if msg_data.get('user_id') == self.user_id:
                    return
                
                time_str = datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
                
                if msg_type == 'join':
                    print(f"[{time_str}] 🚪 {content}")
                elif msg_type == 'leave':
                    print(f"[{time_str}] 👋 {content}")
                elif msg_type == 'message':
                    # Mention detection
                    if f"@{self.username}" in content:
                        print(f"[{time_str}] 🔔 {username}: {content}")
                    else:
                        print(f"[{time_str}] 💬 {username}: {content}")
                elif msg_type == 'private':
                    print(f"[{time_str}] 📨 Özel mesaj - {username}: {content}")
                    
            except json.JSONDecodeError:
                print("❌ Mesaj format hatası")
            except Exception as e:
                print(f"❌ Mesaj işleme hatası: {e}")
    
    def listen_messages(self):
        """
        Mesajları dinle (ayrı thread'te çalışır)
        """
        self.is_active = True
        
        try:
            for message in self.pubsub.listen():
                if not self.is_active:
                    break
                self.handle_message(message)
                
        except Exception as e:
            print(f"❌ Dinleme hatası: {e}")
        finally:
            self.is_active = False
    
    def process_input(self, user_input: str):
        """
        Kullanıcı girişini işle
        
        Args:
            user_input: Kullanıcının yazdığı metin
        """
        user_input = user_input.strip()
        
        if not user_input:
            return
            
        # Komut kontrolü
        if user_input.startswith('/'):
            command_parts = user_input.split(' ', 1)
            command = command_parts[0]
            args = command_parts[1] if len(command_parts) > 1 else ""
            
            if command in self.commands:
                self.commands[command](args)
            else:
                print(f"❌ Bilinmeyen komut: {command}")
                print("💡 /help yazarak komutları görebilirsiniz")
        else:
            # Normal mesaj gönder
            self.send_message(user_input)
    
    def leave_room(self):
        """
        Chat odasından ayrıl
        """
        if self.username:
            # Kullanıcı listesinden çıkar
            user_key = f"chat.users.{self.room_name}"
            self.redis_client.hdel(user_key, self.username)
            
            # Ayrılma mesajı gönder
            leave_message = {
                'type': 'leave',
                'user_id': self.user_id,
                'username': self.username,
                'room': self.room_name,
                'timestamp': datetime.now().isoformat(),
                'content': f"{self.username} '{self.room_name}' odasından ayrıldı"
            }
            
            self.redis_client.publish(self.channel, json.dumps(leave_message, ensure_ascii=False))
        
        self.is_active = False
        self.pubsub.close()
    
    def start_chat(self, username: str):
        """
        Chat'i başlat (ana metod)
        
        Args:
            username: Kullanıcı adı
        """
        try:
            # Odaya katıl
            self.join_room(username)
            
            # Mesaj dinleyici thread'i başlat
            listen_thread = threading.Thread(target=self.listen_messages)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Ana thread'te kullanıcı input'unu işle
            while self.is_active:
                try:
                    user_input = input()
                    self.process_input(user_input)
                except EOFError:
                    # Ctrl+D ile çıkış
                    break
                except KeyboardInterrupt:
                    # Ctrl+C ile çıkış
                    break
                    
        except Exception as e:
            print(f"❌ Chat hatası: {e}")
        finally:
            self.leave_room()

def main():
    """
    Ana fonksiyon - CLI arguments'ları işle
    """
    if len(sys.argv) < 3:
        print("🎯 Redis Chat Uygulaması")
        print("\nKullanım:")
        print("   python chat_application.py <oda_adı> <kullanıcı_adı>")
        print("\nÖrnekler:")
        print("   python chat_application.py general alice")
        print("   python chat_application.py tech bob")
        print("   python chat_application.py random charlie")
        print("\n💡 İpucu: Farklı terminallerde farklı kullanıcılarla bağlanın!")
        sys.exit(1)
    
    room_name = sys.argv[1]
    username = sys.argv[2]
    
    # Redis bağlantısını test et
    try:
        test_redis = redis.Redis(host='localhost', port=6379, db=0)
        test_redis.ping()
    except redis.ConnectionError:
        print("❌ Redis'e bağlanılamıyor!")
        print("💡 Redis'in çalıştığından emin olun: docker run -d -p 6379:6379 redis")
        sys.exit(1)
    
    # Chat'i başlat
    print(f"🚀 '{room_name}' odasına '{username}' olarak katılıyorsunuz...")
    print("💡 Çıkmak için /quit yazın veya Ctrl+C basın")
    
    chat = ChatRoom(room_name)
    chat.start_chat(username)

if __name__ == "__main__":
    main()