#!/bin/bash

# Multi-Exchange RabbitMQ Lab Setup Script
# Bu script çeşitli exchange pattern'lerini test etmek için gerekli ortamı hazırlar

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
    echo -e "${PURPLE}🔀 $1${NC}"
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

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Check RabbitMQ health
check_rabbitmq() {
    if docker exec rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        print_success "RabbitMQ is running and healthy"
        return 0
    else
        print_error "RabbitMQ is not running"
        print_info "Start RabbitMQ with: make start-rabbitmq"
        return 1
    fi
}

# Setup all exchanges
setup_exchanges() {
    print_header "Setting up Multi-Exchange Environment"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_step "Setting up exchanges via Python..."
    
    cd "$(dirname "$0")/../python"
    
    # Check Python requirements
    if ! python3 -c "import pika" 2>/dev/null; then
        print_info "Installing Python requirements..."
        pip3 install pika > /dev/null 2>&1
    fi
    
    # Setup exchanges using Python
    python3 << 'EOF'
import pika
import sys

try:
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials('admin', 'admin123')
        )
    )
    channel = connection.channel()
    
    print("🔀 Setting up exchanges...")
    
    # Direct Exchange for logging
    channel.exchange_declare(exchange='direct_logs', exchange_type='direct', durable=True)
    print("  ✅ direct_logs (direct) - for severity-based log routing")
    
    # Topic Exchange for news
    channel.exchange_declare(exchange='news_exchange', exchange_type='topic', durable=True)
    print("  ✅ news_exchange (topic) - for pattern-based news routing")
    
    # Fanout Exchange for notifications
    channel.exchange_declare(exchange='notifications', exchange_type='fanout', durable=True)
    print("  ✅ notifications (fanout) - for broadcast notifications")
    
    # Headers Exchange for order processing
    channel.exchange_declare(exchange='order_processing', exchange_type='headers', durable=True)
    print("  ✅ order_processing (headers) - for metadata-based order routing")
    
    print("\n📦 Setting up sample queues...")
    
    # Create some persistent queues for demo
    channel.queue_declare(queue='error_logs', durable=True)
    channel.queue_declare(queue='warning_logs', durable=True)
    channel.queue_declare(queue='info_logs', durable=True)
    
    # Bind log queues to direct exchange
    channel.queue_bind(exchange='direct_logs', queue='error_logs', routing_key='error')
    channel.queue_bind(exchange='direct_logs', queue='warning_logs', routing_key='warning')
    channel.queue_bind(exchange='direct_logs', queue='info_logs', routing_key='info')
    
    print("  ✅ Log queues bound to direct exchange")
    
    connection.close()
    print("\n✅ Multi-exchange environment setup complete!")
    
except Exception as e:
    print(f"❌ Setup error: {e}")
    sys.exit(1)
EOF
    
    print_success "Exchange setup completed successfully!"
}

# Show exchange status
show_exchange_status() {
    print_header "Exchange Status Overview"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_step "Checking exchanges..."
    docker exec rabbitmq rabbitmqctl list_exchanges name type durable auto_delete | grep -E "(direct_logs|news_exchange|notifications|order_processing|^Name)"
    
    echo ""
    print_step "Checking queues..."
    docker exec rabbitmq rabbitmqctl list_queues name messages consumers durable | grep -E "(logs|^Name)"
    
    echo ""
    print_step "Checking bindings..."
    docker exec rabbitmq rabbitmqctl list_bindings source_name destination_name destination_type routing_key | grep -E "(direct_logs|news_exchange|notifications|order_processing|^Listing)"
}

# Run demo scenarios
run_demo_scenarios() {
    print_header "Multi-Exchange Demo Scenarios"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    cd "$(dirname "$0")/../python"
    
    print_step "Scenario 1: Direct Exchange - Log System"
    print_info "Sending different severity logs..."
    python3 direct_exchange_producer.py
    echo ""
    
    print_step "Scenario 2: Topic Exchange - News System"
    print_info "Publishing categorized news..."
    python3 topic_exchange_producer.py
    echo ""
    
    print_step "Scenario 3: Fanout Exchange - Notifications"
    print_info "Broadcasting notifications..."
    python3 fanout_exchange_producer.py
    echo ""
    
    print_step "Scenario 4: Headers Exchange - Order Processing"
    print_info "Processing orders with metadata..."
    python3 headers_exchange_producer.py
    echo ""
    
    print_success "All demo scenarios completed!"
    
    print_info "Check message counts:"
    docker exec rabbitmq rabbitmqctl list_queues name messages
}

# Interactive test mode
interactive_test() {
    print_header "Interactive Multi-Exchange Test"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    cd "$(dirname "$0")/../python"
    
    echo ""
    print_info "This will open multiple terminals for testing different exchanges."
    print_info "You can test each exchange type in real-time."
    echo ""
    
    print_step "Terminal commands to run:"
    echo ""
    
    echo -e "${CYAN}Direct Exchange (Log System):${NC}"
    echo "  Consumer: python3 direct_exchange_consumer.py error warning"
    echo "  Producer: python3 direct_exchange_producer.py"
    echo ""
    
    echo -e "${CYAN}Topic Exchange (News System):${NC}"
    echo "  Consumer: python3 topic_exchange_consumer.py 'tech.*.*' --name TechConsumer"
    echo "  Consumer: python3 topic_exchange_consumer.py '*.*.high' --name HighPriorityConsumer"
    echo "  Producer: python3 topic_exchange_producer.py"
    echo ""
    
    echo -e "${CYAN}Fanout Exchange (Notifications):${NC}"
    echo "  Consumer: python3 fanout_exchange_consumer.py mobile_app --types system security"
    echo "  Consumer: python3 fanout_exchange_consumer.py web_app --priority high"
    echo "  Producer: python3 fanout_exchange_producer.py"
    echo ""
    
    echo -e "${CYAN}Headers Exchange (Order Processing):${NC}"
    echo "  Consumer: python3 headers_exchange_consumer.py premium"
    echo "  Consumer: python3 headers_exchange_consumer.py express"
    echo "  Producer: python3 headers_exchange_producer.py"
    echo ""
    
    read -p "Press ENTER to start automatic demo or CTRL+C to run manually..."
    
    # Run automatic demo
    print_step "Starting automatic demo in background..."
    
    # Start consumers in background
    python3 direct_exchange_consumer.py error warning > /dev/null 2>&1 &
    DIRECT_PID=$!
    
    python3 topic_exchange_consumer.py "tech.*.*" --name TechConsumer > /dev/null 2>&1 &
    TOPIC_PID=$!
    
    python3 fanout_exchange_consumer.py mobile_app > /dev/null 2>&1 &
    FANOUT_PID=$!
    
    python3 headers_exchange_consumer.py premium > /dev/null 2>&1 &
    HEADERS_PID=$!
    
    sleep 2
    
    print_info "Consumers started, sending test messages..."
    
    # Send test messages
    python3 direct_exchange_producer.py > /dev/null 2>&1
    python3 topic_exchange_producer.py > /dev/null 2>&1
    python3 fanout_exchange_producer.py > /dev/null 2>&1
    python3 headers_exchange_producer.py > /dev/null 2>&1
    
    sleep 3
    
    # Stop background consumers
    kill $DIRECT_PID $TOPIC_PID $FANOUT_PID $HEADERS_PID 2>/dev/null || true
    
    print_success "Automatic demo completed!"
}

# Performance test
performance_test() {
    print_header "Multi-Exchange Performance Test"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    cd "$(dirname "$0")/../python"
    
    local test_duration=${1:-30}
    local message_rate=${2:-100}
    
    print_info "Running performance test for $test_duration seconds at $message_rate msg/sec"
    
    # Performance test script
    python3 << EOF
import pika
import json
import time
import threading
from datetime import datetime

def performance_producer(exchange, exchange_type, duration, rate):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('admin', 'admin123')
            )
        )
        channel = connection.channel()
        
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < duration:
            message = {
                'test_id': f'{exchange}_{message_count}',
                'timestamp': datetime.now().isoformat(),
                'data': f'Performance test message {message_count}'
            }
            
            if exchange_type == 'direct':
                routing_key = 'info'
            elif exchange_type == 'topic':
                routing_key = 'tech.performance.test'
            else:
                routing_key = ''
            
            headers = {'customer_type': 'standard'} if exchange_type == 'headers' else None
            
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers=headers
                )
            )
            
            message_count += 1
            time.sleep(1.0 / rate)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        actual_rate = message_count / actual_duration
        
        print(f"📊 {exchange} ({exchange_type}): {message_count} messages in {actual_duration:.2f}s = {actual_rate:.2f} msg/s")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error in {exchange}: {e}")

# Test all exchange types
exchanges = [
    ('direct_logs', 'direct'),
    ('news_exchange', 'topic'),
    ('notifications', 'fanout'),
    ('order_processing', 'headers')
]

threads = []
for exchange, exchange_type in exchanges:
    t = threading.Thread(target=performance_producer, args=(exchange, exchange_type, $test_duration, $message_rate))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("✅ Performance test completed!")
EOF
}

# Clean up exchanges and queues
cleanup() {
    print_header "Cleaning Up Multi-Exchange Environment"
    
    if ! check_rabbitmq; then
        return 1
    fi
    
    print_warning "This will delete all exchanges and queues!"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ $confirm == [yY] ]]; then
        print_step "Cleaning up exchanges and queues..."
        
        # Delete exchanges
        docker exec rabbitmq rabbitmqctl delete_exchange direct_logs 2>/dev/null || true
        docker exec rabbitmq rabbitmqctl delete_exchange news_exchange 2>/dev/null || true
        docker exec rabbitmq rabbitmqctl delete_exchange notifications 2>/dev/null || true
        docker exec rabbitmq rabbitmqctl delete_exchange order_processing 2>/dev/null || true
        
        # Delete queues
        docker exec rabbitmq rabbitmqctl delete_queue error_logs 2>/dev/null || true
        docker exec rabbitmq rabbitmqctl delete_queue warning_logs 2>/dev/null || true
        docker exec rabbitmq rabbitmqctl delete_queue info_logs 2>/dev/null || true
        
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled"
    fi
}

# Show help
show_help() {
    print_header "Multi-Exchange Lab Help"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup              Set up all exchanges and sample queues"
    echo "  status             Show exchange and queue status"
    echo "  demo               Run demo scenarios (automated)"
    echo "  interactive        Interactive test mode with manual commands"
    echo "  performance [duration] [rate]  Run performance test"
    echo "  cleanup            Clean up all exchanges and queues"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup           # Setup multi-exchange environment"
    echo "  $0 demo            # Run automated demo"
    echo "  $0 performance 60 200  # 60 second test at 200 msg/sec"
    echo ""
    echo "Exchange Types Covered:"
    echo "  📍 Direct Exchange    - exact routing key matching"
    echo "  🔄 Topic Exchange     - pattern-based routing"
    echo "  📢 Fanout Exchange    - broadcast to all bound queues"
    echo "  🏷️ Headers Exchange   - metadata-based routing"
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            setup_exchanges
            ;;
        status)
            show_exchange_status
            ;;
        demo)
            setup_exchanges
            run_demo_scenarios
            ;;
        interactive)
            setup_exchanges
            interactive_test
            ;;
        performance)
            setup_exchanges
            performance_test "${2:-30}" "${3:-100}"
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"