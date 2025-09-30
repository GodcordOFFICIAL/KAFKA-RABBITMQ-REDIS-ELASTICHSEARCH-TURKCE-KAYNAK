#!/bin/bash
# scripts/setup_elasticsearch.sh

echo "🔍 Elasticsearch kurulumu başlıyor..."

# Docker Compose ile Elasticsearch ve Kibana başlat
echo "📦 Elasticsearch ve Kibana containers başlatılıyor..."
docker-compose -f deployment/docker-compose/elasticsearch.yml up -d

# Servislerin başlamasını bekle
echo "⏳ Elasticsearch'ın başlamasını bekleniyor..."
timeout=120
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
        echo "✅ Elasticsearch hazır!"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo "⏳ Bekleniyor... ($counter/$timeout saniye)"
done

if [ $counter -ge $timeout ]; then
    echo "❌ Elasticsearch başlatılamadı!"
    exit 1
fi

# Kibana'nın başlamasını bekle
echo "⏳ Kibana'nın başlamasını bekleniyor..."
timeout=180
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:5601/api/status > /dev/null 2>&1; then
        echo "✅ Kibana hazır!"
        break
    fi
    sleep 3
    counter=$((counter + 3))
    echo "⏳ Kibana bekleniyor... ($counter/$timeout saniye)"
done

# Test verileri yükle
echo "📊 Test verileri yükleniyor..."

# Test index oluştur
curl -X PUT "http://localhost:9200/test-index" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  }' > /dev/null 2>&1

# Test document ekle
curl -X POST "http://localhost:9200/test-index/_doc/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Document",
    "content": "Bu bir test dokümanıdır",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }' > /dev/null 2>&1

echo ""
echo "🎉 Elasticsearch kurulumu tamamlandı!"
echo ""
echo "📋 Bağlantı Bilgileri:"
echo "   Elasticsearch: http://localhost:9200"
echo "   Kibana: http://localhost:5601"
echo ""
echo "🔧 Test komutları:"
echo "   curl http://localhost:9200"
echo "   curl http://localhost:9200/_cluster/health"
echo "   curl http://localhost:9200/_cat/indices"
echo ""
echo "📊 Kibana Dev Tools:"
echo "   http://localhost:5601/app/dev_tools#/console"