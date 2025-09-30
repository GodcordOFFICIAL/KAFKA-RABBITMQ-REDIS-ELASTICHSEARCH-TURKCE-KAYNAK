#!/bin/bash

# RabbitMQ Management and Testing Script
# Bu script RabbitMQ yönetimi ve test işlemleri için kullanılır

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print functions
print_header() {
    echo -e "${PURPLE}============================================${NC}"
    echo -e "${PURPLE}🐰 $1${NC}"
    echo -e "${PURPLE}============================================${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# RabbitMQ health check
check_rabbitmq() {
    print_info "RabbitMQ sağlık kontrolü..."
    
    if docker exec rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        print_success "RabbitMQ sağlıklı ve çalışıyor"
        
        # Connection bilgileri
        echo ""
        print_info "Bağlantı bilgileri:"
        echo "  AMQP Port: 5672"
        echo "  Management UI: http://localhost:15672"
        echo "  Username: admin"
        echo "  Password: admin123"
        
        return 0
    else
        print_error "RabbitMQ çalışmıyor veya erişilemiyor"
        return 1
    fi
}

# Show RabbitMQ status
show_status() {
    print_header "RabbitMQ Cluster Status"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    echo ""
    print_info "Cluster bilgileri:"
    docker exec rabbitmq rabbitmqctl cluster_status
    
    echo ""
    print_info "Node durumu:"
    docker exec rabbitmq rabbitmqctl node_health_check
    
    echo ""
    print_info "Memory kullanımı:"
    docker exec rabbitmq rabbitmqctl status | grep -A 5 "Memory"
    
    echo ""
    print_info "Aktif bağlantılar:"
    docker exec rabbitmq rabbitmqctl list_connections name peer_host peer_port state
    
    echo ""
    print_info "Queue'lar:"
    docker exec rabbitmq rabbitmqctl list_queues name messages consumers
    
    echo ""
    print_info "Exchange'ler:"
    docker exec rabbitmq rabbitmqctl list_exchanges name type
}

# Create sample queues and exchanges
setup_samples() {
    print_header "Sample Setup"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_info "Sample exchange'ler ve queue'lar oluşturuluyor..."
    
    # Python ile setup yap
    python3 << 'EOF'
import pika
import sys

try:
    # Bağlantı oluştur
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials('admin', 'admin123')
        )
    )
    channel = connection.channel()
    
    # Sample exchanges
    print("📢 Exchange'ler oluşturuluyor...")
    
    # Direct exchange
    channel.exchange_declare(exchange='direct_logs', exchange_type='direct', durable=True)
    print("  ✅ direct_logs (direct)")
    
    # Topic exchange  
    channel.exchange_declare(exchange='topic_logs', exchange_type='topic', durable=True)
    print("  ✅ topic_logs (topic)")
    
    # Fanout exchange
    channel.exchange_declare(exchange='broadcast', exchange_type='fanout', durable=True)
    print("  ✅ broadcast (fanout)")
    
    # Chat exchanges
    channel.exchange_declare(exchange='chat_broadcast', exchange_type='fanout', durable=True)
    channel.exchange_declare(exchange='chat_rooms', exchange_type='topic', durable=True)
    print("  ✅ chat exchanges")
    
    # Sample queues
    print("\n📦 Queue'lar oluşturuluyor...")
    
    # Basic queues
    channel.queue_declare(queue='hello', durable=True)
    print("  ✅ hello")
    
    channel.queue_declare(queue='task_queue', durable=True, arguments={'x-max-priority': 10})
    print("  ✅ task_queue (with priority)")
    
    # Log queues
    channel.queue_declare(queue='error_logs', durable=True)
    channel.queue_declare(queue='warn_logs', durable=True)
    channel.queue_declare(queue='info_logs', durable=True)
    
    # Bindings
    channel.queue_bind(exchange='direct_logs', queue='error_logs', routing_key='error')
    channel.queue_bind(exchange='direct_logs', queue='warn_logs', routing_key='warning')
    channel.queue_bind(exchange='direct_logs', queue='info_logs', routing_key='info')
    
    print("  ✅ log queues with bindings")
    
    connection.close()
    print("\n✅ Sample setup tamamlandı!")
    
except Exception as e:
    print(f"❌ Setup hatası: {e}")
    sys.exit(1)
EOF
}

# Send test messages
send_test_messages() {
    print_header "Test Messages"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_info "Test mesajları gönderiliyor..."
    
    # Python ile test mesajları gönder
    python3 << 'EOF'
import pika
import json
import time
from datetime import datetime

try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials('admin', 'admin123')
        )
    )
    channel = connection.channel()
    
    # Test mesajları
    test_messages = [
        {"queue": "hello", "message": "Test mesajı 1", "type": "simple"},
        {"queue": "hello", "message": "Test mesajı 2", "type": "simple"},
        {"queue": "task_queue", "message": "İşlem 1", "type": "task", "priority": 5},
        {"queue": "task_queue", "message": "Yüksek öncelik işlem", "type": "task", "priority": 9},
    ]
    
    for msg_data in test_messages:
        message_body = json.dumps({
            "content": msg_data["message"],
            "timestamp": datetime.now().isoformat(),
            "sender": "test_script",
            "type": msg_data["type"]
        })
        
        properties = pika.BasicProperties(
            delivery_mode=2,
            priority=msg_data.get("priority", 0)
        )
        
        channel.basic_publish(
            exchange='',
            routing_key=msg_data["queue"],
            body=message_body,
            properties=properties
        )
        
        print(f"  📤 {msg_data['queue']}: {msg_data['message']}")
    
    # Log mesajları (exchange'e)
    log_messages = [
        {"level": "info", "message": "Uygulama başlatıldı"},
        {"level": "warning", "message": "Yüksek memory kullanımı"},
        {"level": "error", "message": "Database bağlantı hatası"}
    ]
    
    for log in log_messages:
        log_body = json.dumps({
            "level": log["level"],
            "message": log["message"],
            "timestamp": datetime.now().isoformat(),
            "source": "test_app"
        })
        
        channel.basic_publish(
            exchange='direct_logs',
            routing_key=log["level"],
            body=log_body
        )
        
        print(f"  📝 {log['level']}: {log['message']}")
    
    connection.close()
    print("\n✅ Test mesajları gönderildi!")
    
except Exception as e:
    print(f"❌ Test mesaj hatası: {e}")
EOF
}

# Monitor queues
monitor_queues() {
    print_header "Queue Monitor"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_info "Queue'lar izleniyor... (CTRL+C ile durdurun)"
    
    while true; do
        clear
        echo -e "${CYAN}📊 RabbitMQ Queue Monitor - $(date)${NC}"
        echo "======================================================"
        
        echo ""
        echo -e "${BLUE}Queue Durumu:${NC}"
        docker exec rabbitmq rabbitmqctl list_queues name messages consumers memory | column -t
        
        echo ""
        echo -e "${BLUE}Exchange Durumu:${NC}"
        docker exec rabbitmq rabbitmqctl list_exchanges name type | column -t
        
        echo ""
        echo -e "${BLUE}Aktif Bağlantılar:${NC}"
        docker exec rabbitmq rabbitmqctl list_connections name state | column -t
        
        echo ""
        echo -e "${YELLOW}Sonraki güncellemede 5 saniye...${NC}"
        
        sleep 5
    done
}

# Performance test
performance_test() {
    print_header "Performance Test"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    local message_count=${1:-1000}
    local concurrent_producers=${2:-3}
    
    print_info "Performance test başlatılıyor..."
    print_info "Mesaj sayısı: $message_count"
    print_info "Concurrent producer: $concurrent_producers"
    
    # RabbitMQ performance testing tool kullan
    if ! command -v rabbitmq-perf-test &> /dev/null; then
        print_warning "rabbitmq-perf-test yüklü değil, basit test yapılıyor..."
        
        # Python ile basit performance test
        python3 << EOF
import pika
import json
import time
import threading
from datetime import datetime

def producer_worker(worker_id, message_count):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('admin', 'admin123')
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='perf_test', durable=True)
        
        start_time = time.time()
        
        for i in range(message_count):
            message = json.dumps({
                "worker_id": worker_id,
                "message_id": i,
                "timestamp": datetime.now().isoformat(),
                "data": f"Performance test message {i}"
            })
            
            channel.basic_publish(
                exchange='',
                routing_key='perf_test',
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        
        end_time = time.time()
        duration = end_time - start_time
        rate = message_count / duration
        
        print(f"Worker {worker_id}: {message_count} mesaj, {duration:.2f}s, {rate:.2f} msg/s")
        
        connection.close()
        
    except Exception as e:
        print(f"Worker {worker_id} hatası: {e}")

# Performance test
print("🚀 Performance test başlıyor...")
start_time = time.time()

threads = []
messages_per_worker = $message_count // $concurrent_producers

for i in range($concurrent_producers):
    t = threading.Thread(target=producer_worker, args=(i, messages_per_worker))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

total_time = time.time() - start_time
total_messages = $message_count
total_rate = total_messages / total_time

print(f"\n📊 Toplam Sonuç:")
print(f"   Toplam mesaj: {total_messages}")
print(f"   Toplam süre: {total_time:.2f}s")
print(f"   Toplam rate: {total_rate:.2f} msg/s")
print(f"   Producer sayısı: $concurrent_producers")
EOF
    
    else
        # RabbitMQ perf test tool
        print_info "RabbitMQ performance test tool kullanılıyor..."
        
        rabbitmq-perf-test \
            --uri amqp://admin:admin123@localhost:5672 \
            --producers $concurrent_producers \
            --consumers 0 \
            --message-count $message_count \
            --queue perf_test
    fi
    
    print_success "Performance test tamamlandı!"
}

# Purge all queues
purge_queues() {
    print_header "Queue Purge"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_warning "Tüm queue'lar temizlenecek!"
    read -p "Devam etmek istiyor musunuz? (y/N): " confirm
    
    if [[ $confirm == [yY] ]]; then
        print_info "Queue'lar temizleniyor..."
        
        # Tüm queue'ları listele ve temizle
        queues=$(docker exec rabbitmq rabbitmqctl list_queues name -q)
        
        while IFS= read -r queue; do
            if [[ -n "$queue" ]]; then
                docker exec rabbitmq rabbitmqctl purge_queue "$queue" > /dev/null 2>&1 || true
                print_info "  Queue temizlendi: $queue"
            fi
        done <<< "$queues"
        
        print_success "Tüm queue'lar temizlendi!"
    else
        print_info "İşlem iptal edildi"
    fi
}

# Chat application demo
chat_demo() {
    print_header "Chat Application Demo"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    cd "$(dirname "$0")/../examples/rabbitmq/python"
    
    # Python requirements check
    if ! python3 -c "import pika" 2>/dev/null; then
        print_info "Python requirements yükleniyor..."
        pip3 install pika > /dev/null 2>&1
    fi
    
    print_info "Chat uygulaması demo'su"
    echo ""
    echo "🎭 Demo senaryosu:"
    echo "   1. İki kullanıcı: Alice ve Bob"
    echo "   2. Room'lar: general, tech"
    echo "   3. Alice tüm room'ları dinler"
    echo "   4. Bob sadece general'ı dinler"
    echo ""
    
    # Setup exchanges
    setup_samples > /dev/null 2>&1
    
    echo "📋 Çalıştırılacak komutlar:"
    echo ""
    echo "Terminal 1 (Alice Consumer):"
    echo "  python3 chat_consumer.py alice general tech"
    echo ""
    echo "Terminal 2 (Bob Consumer):"
    echo "  python3 chat_consumer.py bob general"
    echo ""
    echo "Terminal 3 (Alice Producer):"
    echo "  python3 chat_producer.py alice"
    echo ""
    echo "Terminal 4 (Bob Producer):"
    echo "  python3 chat_producer.py bob"
    echo ""
    
    read -p "Demo'yu başlatmak için ENTER'a basın..."
    
    print_info "Demo başlatılıyor..."
    
    # Alice consumer'ı background'da başlat
    echo "🔵 Alice consumer başlatılıyor..."
    python3 chat_consumer.py alice general tech &
    ALICE_PID=$!
    
    sleep 2
    
    # Bob consumer'ı başlat
    echo "🟢 Bob consumer başlatılıyor..."
    python3 chat_consumer.py bob general &
    BOB_PID=$!
    
    sleep 2
    
    # Demo mesajları gönder
    echo "📤 Demo mesajları gönderiliyor..."
    
    # Alice mesajları
    echo "general Alice burda!" | python3 chat_producer.py alice &
    sleep 1
    echo "tech Python öğreniyorum" | python3 chat_producer.py alice &
    sleep 1
    
    # Bob mesajları  
    echo "general Bob da geldi!" | python3 chat_producer.py bob &
    sleep 1
    echo "general Nasılsınız?" | python3 chat_producer.py bob &
    sleep 2
    
    print_info "Demo mesajları gönderildi!"
    print_info "Consumer'ları durdurmak için 10 saniye bekleniyor..."
    
    sleep 10
    
    # Background process'leri durdur
    kill $ALICE_PID $BOB_PID 2>/dev/null || true
    
    print_success "Chat demo tamamlandı!"
}

# Help function
show_help() {
    print_header "RabbitMQ Management Script"
    echo ""
    echo "Kullanım: $0 <komut>"
    echo ""
    echo "Komutlar:"
    echo "  status                 RabbitMQ durumunu göster"
    echo "  health                 Sağlık kontrolü yap"
    echo "  setup-samples          Sample queue/exchange oluştur"
    echo "  test-messages          Test mesajları gönder"
    echo "  monitor               Queue'ları izle"
    echo "  performance [count] [producers]  Performance test"
    echo "  purge                 Tüm queue'ları temizle"
    echo "  chat-demo             Chat uygulaması demo"
    echo "  help                  Bu yardım mesajı"
    echo ""
    echo "Örnekler:"
    echo "  $0 status             # RabbitMQ durumu"
    echo "  $0 performance 5000 5 # 5000 mesaj, 5 producer"
    echo "  $0 monitor            # Canlı izleme"
    echo ""
}

# Main script
main() {
    case "${1:-help}" in
        status)
            show_status
            ;;
        health)
            check_rabbitmq
            ;;
        setup-samples)
            setup_samples
            ;;
        test-messages)
            send_test_messages
            ;;
        monitor)
            monitor_queues
            ;;
        performance)
            performance_test "${2:-1000}" "${3:-3}"
            ;;
        purge)
            purge_queues
            ;;
        chat-demo)
            chat_demo
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Bilinmeyen komut: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Script çalıştır
main "$@"