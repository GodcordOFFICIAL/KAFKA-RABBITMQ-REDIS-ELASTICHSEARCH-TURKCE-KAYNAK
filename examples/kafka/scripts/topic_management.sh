#!/bin/bash

# Kafka Topic Management Helper Script
# Bu script Kafka topic'lerinin yönetimini kolaylaştırır

KAFKA_CONTAINER="kafka1"
BOOTSTRAP_SERVERS="localhost:9092"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
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

print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Check if Kafka is running
check_kafka() {
    print_step "Checking Kafka connectivity..."
    
    if docker exec $KAFKA_CONTAINER kafka-broker-api-versions.sh --bootstrap-server $BOOTSTRAP_SERVERS &>/dev/null; then
        print_success "Kafka cluster is accessible"
        return 0
    else
        print_error "Cannot connect to Kafka cluster"
        print_info "Please ensure Kafka is running: docker-compose up -d kafka-cluster"
        return 1
    fi
}

# Create topic with best practices
create_topic() {
    local topic_name=$1
    local partitions=${2:-6}
    local replication_factor=${3:-1}
    local retention_days=${4:-7}
    
    if [ -z "$topic_name" ]; then
        print_error "Topic name is required"
        echo "Usage: $0 create <topic-name> [partitions] [replication-factor] [retention-days]"
        return 1
    fi
    
    print_header "Creating Kafka Topic"
    print_info "Topic Name: $topic_name"
    print_info "Partitions: $partitions"
    print_info "Replication Factor: $replication_factor"
    print_info "Retention: $retention_days days"
    
    local retention_ms=$((retention_days * 24 * 60 * 60 * 1000))
    
    print_step "Creating topic with optimized settings..."
    
    docker exec -it $KAFKA_CONTAINER kafka-topics.sh \
        --create \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --topic $topic_name \
        --partitions $partitions \
        --replication-factor $replication_factor \
        --config retention.ms=$retention_ms \
        --config segment.ms=86400000 \
        --config compression.type=gzip \
        --config cleanup.policy=delete \
        --config min.insync.replicas=1
    
    if [ $? -eq 0 ]; then
        print_success "Topic '$topic_name' created successfully"
        describe_topic $topic_name
    else
        print_error "Failed to create topic '$topic_name'"
        return 1
    fi
}

# Delete topic with confirmation
delete_topic() {
    local topic_name=$1
    
    if [ -z "$topic_name" ]; then
        print_error "Topic name is required"
        echo "Usage: $0 delete <topic-name>"
        return 1
    fi
    
    print_header "Deleting Kafka Topic"
    print_warning "This action will permanently delete topic: $topic_name"
    print_warning "All data in this topic will be lost!"
    
    echo ""
    read -p "Are you absolutely sure? Type 'DELETE' to confirm: " confirm
    
    if [[ $confirm == "DELETE" ]]; then
        print_step "Deleting topic..."
        
        docker exec -it $KAFKA_CONTAINER kafka-topics.sh \
            --delete \
            --bootstrap-server $BOOTSTRAP_SERVERS \
            --topic $topic_name
        
        if [ $? -eq 0 ]; then
            print_success "Topic '$topic_name' deleted successfully"
        else
            print_error "Failed to delete topic '$topic_name'"
            return 1
        fi
    else
        print_info "Topic deletion cancelled"
    fi
}

# Scale topic partitions
scale_topic() {
    local topic_name=$1
    local new_partition_count=$2
    
    if [ -z "$topic_name" ] || [ -z "$new_partition_count" ]; then
        print_error "Topic name and partition count are required"
        echo "Usage: $0 scale <topic-name> <new-partition-count>"
        return 1
    fi
    
    print_header "Scaling Kafka Topic"
    print_info "Topic: $topic_name"
    print_info "New Partition Count: $new_partition_count"
    print_warning "Note: Partition count can only be increased, not decreased"
    
    print_step "Scaling topic partitions..."
    
    docker exec -it $KAFKA_CONTAINER kafka-topics.sh \
        --alter \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --topic $topic_name \
        --partitions $new_partition_count
    
    if [ $? -eq 0 ]; then
        print_success "Topic '$topic_name' scaled to $new_partition_count partitions"
        describe_topic $topic_name
    else
        print_error "Failed to scale topic '$topic_name'"
        return 1
    fi
}

# Show topic details
describe_topic() {
    local topic_name=$1
    
    if [ -z "$topic_name" ]; then
        print_error "Topic name is required"
        echo "Usage: $0 describe <topic-name>"
        return 1
    fi
    
    print_header "Topic Details: $topic_name"
    
    print_step "Topic Structure:"
    docker exec -it $KAFKA_CONTAINER kafka-topics.sh \
        --describe \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --topic $topic_name
    
    echo ""
    print_step "Topic Configurations:"
    docker exec -it $KAFKA_CONTAINER kafka-configs.sh \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --entity-type topics \
        --entity-name $topic_name \
        --describe
}

# List all topics with details
list_topics() {
    print_header "Kafka Topics Overview"
    
    print_step "Getting topic list..."
    
    local topics=$(docker exec $KAFKA_CONTAINER kafka-topics.sh \
        --list \
        --bootstrap-server $BOOTSTRAP_SERVERS 2>/dev/null | grep -v '^$')
    
    if [ -z "$topics" ]; then
        print_warning "No topics found"
        return 0
    fi
    
    echo ""
    printf "%-30s %-10s %-12s %-15s\n" "TOPIC NAME" "PARTITIONS" "REPLICATION" "RETENTION"
    printf "%-30s %-10s %-12s %-15s\n" "----------" "----------" "-----------" "---------"
    
    while IFS= read -r topic; do
        if [[ $topic == _* ]]; then
            continue  # Skip internal topics
        fi
        
        local details=$(docker exec $KAFKA_CONTAINER kafka-topics.sh \
            --describe \
            --bootstrap-server $BOOTSTRAP_SERVERS \
            --topic $topic 2>/dev/null | head -1)
        
        local partition_count=$(echo "$details" | grep -o 'PartitionCount: [0-9]*' | cut -d' ' -f2)
        local replication_factor=$(echo "$details" | grep -o 'ReplicationFactor: [0-9]*' | cut -d' ' -f2)
        
        local retention=$(docker exec $KAFKA_CONTAINER kafka-configs.sh \
            --bootstrap-server $BOOTSTRAP_SERVERS \
            --entity-type topics \
            --entity-name $topic \
            --describe 2>/dev/null | grep 'retention.ms' | cut -d'=' -f2)
        
        if [ -n "$retention" ]; then
            local retention_days=$((retention / 86400000))
            retention="${retention_days}d"
        else
            retention="7d (default)"
        fi
        
        printf "%-30s %-10s %-12s %-15s\n" "$topic" "$partition_count" "$replication_factor" "$retention"
    done <<< "$topics"
}

# Optimize topic for high throughput
optimize_for_throughput() {
    local topic_name=$1
    
    if [ -z "$topic_name" ]; then
        print_error "Topic name is required"
        echo "Usage: $0 optimize-throughput <topic-name>"
        return 1
    fi
    
    print_header "Optimizing Topic for High Throughput"
    print_info "Topic: $topic_name"
    
    print_step "Applying throughput optimizations..."
    print_info "- Large segment size (128MB)"
    print_info "- LZ4 compression"
    print_info "- Longer segment time (1 hour)"
    
    docker exec -it $KAFKA_CONTAINER kafka-configs.sh \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --entity-type topics \
        --entity-name $topic_name \
        --alter \
        --add-config segment.ms=3600000,segment.bytes=134217728,compression.type=lz4,batch.size=65536
    
    if [ $? -eq 0 ]; then
        print_success "Topic '$topic_name' optimized for throughput"
        print_info "Settings applied:"
        print_info "  - Segment time: 1 hour"
        print_info "  - Segment size: 128MB"
        print_info "  - Compression: LZ4"
        print_info "  - Batch size: 64KB"
    else
        print_error "Failed to optimize topic '$topic_name'"
        return 1
    fi
}

# Optimize topic for low latency
optimize_for_latency() {
    local topic_name=$1
    
    if [ -z "$topic_name" ]; then
        print_error "Topic name is required"
        echo "Usage: $0 optimize-latency <topic-name>"
        return 1
    fi
    
    print_header "Optimizing Topic for Low Latency"
    print_info "Topic: $topic_name"
    
    print_step "Applying latency optimizations..."
    print_info "- Small segment time (10 minutes)"
    print_info "- No compression"
    print_info "- Frequent flushes"
    
    docker exec -it $KAFKA_CONTAINER kafka-configs.sh \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --entity-type topics \
        --entity-name $topic_name \
        --alter \
        --add-config segment.ms=600000,compression.type=uncompressed,flush.ms=100
    
    if [ $? -eq 0 ]; then
        print_success "Topic '$topic_name' optimized for latency"
        print_info "Settings applied:"
        print_info "  - Segment time: 10 minutes"
        print_info "  - Compression: None"
        print_info "  - Flush interval: 100ms"
    else
        print_error "Failed to optimize topic '$topic_name'"
        return 1
    fi
}

# Setup topic for log compaction
setup_compaction() {
    local topic_name=$1
    
    if [ -z "$topic_name" ]; then
        print_error "Topic name is required"
        echo "Usage: $0 setup-compaction <topic-name>"
        return 1
    fi
    
    print_header "Setting up Log Compaction"
    print_info "Topic: $topic_name"
    
    print_step "Applying compaction settings..."
    print_info "- Cleanup policy: compact"
    print_info "- Min cleanable dirty ratio: 0.1"
    print_info "- Delete retention: 24 hours"
    
    docker exec -it $KAFKA_CONTAINER kafka-configs.sh \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --entity-type topics \
        --entity-name $topic_name \
        --alter \
        --add-config cleanup.policy=compact,min.cleanable.dirty.ratio=0.1,delete.retention.ms=86400000
    
    if [ $? -eq 0 ]; then
        print_success "Log compaction configured for topic '$topic_name'"
        print_info "Settings applied:"
        print_info "  - Cleanup policy: compact"
        print_info "  - Min cleanable ratio: 10%"
        print_info "  - Delete retention: 24 hours"
    else
        print_error "Failed to setup compaction for topic '$topic_name'"
        return 1
    fi
}

# Show topic health status
health_check() {
    local topic_name=$1
    
    if [ -z "$topic_name" ]; then
        # Check all topics
        print_header "Kafka Cluster Health Check"
        
        local topics=$(docker exec $KAFKA_CONTAINER kafka-topics.sh \
            --list \
            --bootstrap-server $BOOTSTRAP_SERVERS 2>/dev/null | grep -v '^$' | grep -v '^_')
        
        local total_topics=0
        local healthy_topics=0
        
        while IFS= read -r topic; do
            if [ -n "$topic" ]; then
                total_topics=$((total_topics + 1))
                if check_topic_health "$topic"; then
                    healthy_topics=$((healthy_topics + 1))
                fi
            fi
        done <<< "$topics"
        
        echo ""
        print_info "Health Summary:"
        print_info "  Total Topics: $total_topics"
        print_success "  Healthy Topics: $healthy_topics"
        
        if [ $healthy_topics -eq $total_topics ]; then
            print_success "All topics are healthy! ✨"
        else
            local unhealthy=$((total_topics - healthy_topics))
            print_warning "Unhealthy Topics: $unhealthy"
        fi
    else
        # Check specific topic
        print_header "Topic Health Check: $topic_name"
        check_topic_health "$topic_name"
    fi
}

# Check health of a specific topic
check_topic_health() {
    local topic_name=$1
    local healthy=true
    
    print_step "Checking topic: $topic_name"
    
    # Check if topic exists
    if ! docker exec $KAFKA_CONTAINER kafka-topics.sh \
        --describe \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --topic $topic_name &>/dev/null; then
        print_error "  Topic does not exist"
        return 1
    fi
    
    # Get topic details
    local details=$(docker exec $KAFKA_CONTAINER kafka-topics.sh \
        --describe \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --topic $topic_name 2>/dev/null)
    
    # Check replication factor
    local replication_factor=$(echo "$details" | head -1 | grep -o 'ReplicationFactor: [0-9]*' | cut -d' ' -f2)
    if [ "$replication_factor" -lt 3 ]; then
        print_warning "  Low replication factor: $replication_factor (recommended: 3+)"
        healthy=false
    fi
    
    # Check for under-replicated partitions
    local under_replicated=$(echo "$details" | grep -c "Isr:")
    local total_partitions=$(echo "$details" | head -1 | grep -o 'PartitionCount: [0-9]*' | cut -d' ' -f2)
    
    # Check partition distribution
    if echo "$details" | grep -q "Leader: none"; then
        print_error "  No leader for some partitions"
        healthy=false
    fi
    
    # Check ISR
    if echo "$details" | grep -q "Isr:.*,$"; then
        print_warning "  Some partitions have under-replicated ISR"
        healthy=false
    fi
    
    # Check retention settings
    local configs=$(docker exec $KAFKA_CONTAINER kafka-configs.sh \
        --bootstrap-server $BOOTSTRAP_SERVERS \
        --entity-type topics \
        --entity-name $topic_name \
        --describe 2>/dev/null)
    
    local retention_ms=$(echo "$configs" | grep 'retention.ms' | cut -d'=' -f2)
    if [ -n "$retention_ms" ]; then
        local retention_days=$((retention_ms / 86400000))
        if [ "$retention_days" -gt 30 ]; then
            print_warning "  Long retention period: ${retention_days} days"
        fi
    fi
    
    if $healthy; then
        print_success "  Topic is healthy"
        return 0
    else
        return 1
    fi
}

# Show usage information
show_usage() {
    print_header "Kafka Topic Management Tool"
    echo ""
    echo "Usage: $0 <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  create <topic> [partitions] [replication] [retention-days]"
    echo "                          Create a new topic with best practices"
    echo "  delete <topic>          Delete a topic (with confirmation)"
    echo "  scale <topic> <count>   Increase partition count"
    echo "  describe <topic>        Show detailed topic information"
    echo "  list                    List all topics with summary"
    echo "  optimize-throughput <topic>  Optimize topic for high throughput"
    echo "  optimize-latency <topic>     Optimize topic for low latency"
    echo "  setup-compaction <topic>     Configure log compaction"
    echo "  health [topic]          Check topic health status"
    echo ""
    echo "Examples:"
    echo "  $0 create user-events 12 1 7"
    echo "  $0 delete temp-topic"
    echo "  $0 scale user-events 24"
    echo "  $0 describe user-events"
    echo "  $0 list"
    echo "  $0 optimize-throughput user-events"
    echo "  $0 optimize-latency notifications"
    echo "  $0 setup-compaction user-profiles"
    echo "  $0 health user-events"
    echo "  $0 health"
}

# Main script logic
main() {
    # Check if Kafka is accessible first
    if ! check_kafka; then
        exit 1
    fi
    
    case "$1" in
        create)
            create_topic "$2" "$3" "$4" "$5"
            ;;
        delete)
            delete_topic "$2"
            ;;
        scale)
            scale_topic "$2" "$3"
            ;;
        describe)
            describe_topic "$2"
            ;;
        list)
            list_topics
            ;;
        optimize-throughput)
            optimize_for_throughput "$2"
            ;;
        optimize-latency)
            optimize_for_latency "$2"
            ;;
        setup-compaction)
            setup_compaction "$2"
            ;;
        health)
            health_check "$2"
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"