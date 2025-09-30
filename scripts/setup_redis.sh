#!/bin/bash
# scripts/setup_redis.sh

echo "🚀 Redis kurulumu başlıyor..."

# Docker Compose ile Redis başlat
echo "📦 Redis containers başlatılıyor..."
docker-compose -f deployment/docker-compose/redis.yml up -d

# Servislerin başlamasını bekle
echo "⏳ Servislerin başlamasını bekleniyor..."
sleep 10

# Health check
echo "🏥 Health check yapılıyor..."
if docker exec redis-server redis-cli -a redis123 ping > /dev/null 2>&1; then
    echo "✅ Redis server hazır!"
else
    echo "❌ Redis server başlatılamadı!"
    exit 1
fi

# Test bağlantısı
echo "🔗 Test bağlantısı yapılıyor..."
docker exec redis-server redis-cli -a redis123 set test "Hello Redis" > /dev/null
if [ "$(docker exec redis-server redis-cli -a redis123 get test)" = "Hello Redis" ]; then
    echo "✅ Redis test başarılı!"
    docker exec redis-server redis-cli -a redis123 del test > /dev/null
else
    echo "❌ Redis test başarısız!"
    exit 1
fi

echo ""
echo "🎉 Redis kurulumu tamamlandı!"
echo ""
echo "📋 Bağlantı Bilgileri:"
echo "   Redis Server: localhost:6379"
echo "   Password: redis123"
echo "   Redis Commander UI: http://localhost:8081"
echo ""
echo "🔧 Test komutları:"
echo "   docker exec -it redis-server redis-cli -a redis123"
echo "   docker exec redis-server redis-cli -a redis123 info"