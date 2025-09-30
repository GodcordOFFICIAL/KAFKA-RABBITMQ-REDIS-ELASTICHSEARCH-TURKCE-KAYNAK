package com.example.elasticsearch;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch.core.*;
import co.elastic.clients.elasticsearch.core.bulk.BulkOperation;
import co.elastic.clients.elasticsearch.core.search.Hit;
import co.elastic.clients.elasticsearch.indices.*;
import co.elastic.clients.json.jackson.JacksonJsonpMapper;
import co.elastic.clients.transport.ElasticsearchTransport;
import co.elastic.clients.transport.rest_client.RestClientTransport;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.*;

/**
 * Elasticsearch Basic Operations - Temel CRUD işlemleri
 * 
 * Bu sınıf Elasticsearch'ün temel operasyonlarını gösterir:
 * - Index management (create, delete, exists)
 * - Document CRUD operations
 * - Bulk operations
 * - Basic search queries
 * - Index templates and mappings
 */
public class BasicOperations {

    private static final Logger logger = LoggerFactory.getLogger(BasicOperations.class);

    // Elasticsearch connection parameters
    private static final String ES_HOST = "localhost";
    private static final int ES_PORT = 9200;
    private static final String ES_SCHEME = "http";

    private ElasticsearchClient client;
    private ObjectMapper objectMapper;

    public BasicOperations() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        setupElasticsearchClient();
    }

    /**
     * Elasticsearch client'ını yapılandır
     */
    private void setupElasticsearchClient() {
        try {
            // REST client oluştur
            RestClient restClient = RestClient.builder(
                    new HttpHost(ES_HOST, ES_PORT, ES_SCHEME)).build();

            // Transport layer oluştur
            ElasticsearchTransport transport = new RestClientTransport(
                    restClient,
                    new JacksonJsonpMapper());

            // Elasticsearch client oluştur
            client = new ElasticsearchClient(transport);

            // Cluster health kontrolü
            var healthResponse = client.cluster().health();
            logger.info("✅ Elasticsearch client initialized. Cluster status: {}",
                    healthResponse.status());

        } catch (Exception e) {
            logger.error("❌ Elasticsearch client initialization failed", e);
            throw new RuntimeException("Elasticsearch connection failed", e);
        }
    }

    /**
     * Index oluştur
     */
    public boolean createIndex(String indexName) {
        try {
            // Index zaten var mı kontrol et
            if (indexExists(indexName)) {
                logger.info("ℹ️ Index '{}' already exists", indexName);
                return true;
            }

            // Index settings
            var settings = Map.of(
                    "number_of_shards", 1,
                    "number_of_replicas", 0,
                    "refresh_interval", "1s");

            // Index mappings
            var mappings = Map.of(
                    "properties", Map.of(
                            "title", Map.of("type", "text", "analyzer", "standard"),
                            "content", Map.of("type", "text", "analyzer", "standard"),
                            "author", Map.of("type", "keyword"),
                            "category", Map.of("type", "keyword"),
                            "tags", Map.of("type", "keyword"),
                            "created_at", Map.of("type", "date"),
                            "updated_at", Map.of("type", "date"),
                            "view_count", Map.of("type", "integer"),
                            "is_published", Map.of("type", "boolean"),
                            "metadata", Map.of("type", "object")));

            // Index oluştur
            CreateIndexRequest createRequest = CreateIndexRequest.of(c -> c
                    .index(indexName)
                    .settings(s -> s.otherSettings(settings))
                    .mappings(m -> m.withJson(objectMapper.valueToTree(mappings).toString())));

            CreateIndexResponse createResponse = client.indices().create(createRequest);

            logger.info("✅ Index '{}' created successfully (acknowledged: {})",
                    indexName, createResponse.acknowledged());

            return createResponse.acknowledged();

        } catch (Exception e) {
            logger.error("❌ Failed to create index '{}'", indexName, e);
            return false;
        }
    }

    /**
     * Index var mı kontrol et
     */
    public boolean indexExists(String indexName) {
        try {
            ExistsRequest existsRequest = ExistsRequest.of(e -> e.index(indexName));
            return client.indices().exists(existsRequest).value();
        } catch (Exception e) {
            logger.error("❌ Failed to check index existence", e);
            return false;
        }
    }

    /**
     * Index sil
     */
    public boolean deleteIndex(String indexName) {
        try {
            if (!indexExists(indexName)) {
                logger.info("ℹ️ Index '{}' does not exist", indexName);
                return true;
            }

            DeleteIndexRequest deleteRequest = DeleteIndexRequest.of(d -> d.index(indexName));
            DeleteIndexResponse deleteResponse = client.indices().delete(deleteRequest);

            logger.info("✅ Index '{}' deleted successfully (acknowledged: {})",
                    indexName, deleteResponse.acknowledged());

            return deleteResponse.acknowledged();

        } catch (Exception e) {
            logger.error("❌ Failed to delete index '{}'", indexName, e);
            return false;
        }
    }

    /**
     * Document ekle veya güncelle
     */
    public String indexDocument(String indexName, String documentId, Map<String, Object> document) {
        try {
            // Timestamp'leri ekle
            document.put("created_at", LocalDateTime.now().toString());
            document.put("updated_at", LocalDateTime.now().toString());

            IndexRequest<Map<String, Object>> indexRequest = IndexRequest.of(i -> i
                    .index(indexName)
                    .id(documentId)
                    .document(document));

            IndexResponse indexResponse = client.index(indexRequest);

            logger.info("📝 Document indexed: ID={}, Index={}, Result={}",
                    indexResponse.id(), indexName, indexResponse.result());

            return indexResponse.id();

        } catch (Exception e) {
            logger.error("❌ Failed to index document", e);
            return null;
        }
    }

    /**
     * Document al
     */
    public Map<String, Object> getDocument(String indexName, String documentId) {
        try {
            GetRequest getRequest = GetRequest.of(g -> g
                    .index(indexName)
                    .id(documentId));

            GetResponse<Map> getResponse = client.get(getRequest, Map.class);

            if (getResponse.found()) {
                logger.info("📖 Document retrieved: ID={}, Index={}", documentId, indexName);
                return getResponse.source();
            } else {
                logger.info("ℹ️ Document not found: ID={}, Index={}", documentId, indexName);
                return null;
            }

        } catch (Exception e) {
            logger.error("❌ Failed to get document", e);
            return null;
        }
    }

    /**
     * Document güncelle
     */
    public boolean updateDocument(String indexName, String documentId, Map<String, Object> updates) {
        try {
            // Updated timestamp ekle
            updates.put("updated_at", LocalDateTime.now().toString());

            UpdateRequest<Map, Map> updateRequest = UpdateRequest.of(u -> u
                    .index(indexName)
                    .id(documentId)
                    .doc(updates));

            UpdateResponse<Map> updateResponse = client.update(updateRequest, Map.class);

            logger.info("🔄 Document updated: ID={}, Index={}, Result={}",
                    documentId, indexName, updateResponse.result());

            return updateResponse.result().toString().equals("Updated");

        } catch (Exception e) {
            logger.error("❌ Failed to update document", e);
            return false;
        }
    }

    /**
     * Document sil
     */
    public boolean deleteDocument(String indexName, String documentId) {
        try {
            DeleteRequest deleteRequest = DeleteRequest.of(d -> d
                    .index(indexName)
                    .id(documentId));

            DeleteResponse deleteResponse = client.delete(deleteRequest);

            logger.info("🗑️ Document deleted: ID={}, Index={}, Result={}",
                    documentId, indexName, deleteResponse.result());

            return deleteResponse.result().toString().equals("Deleted");

        } catch (Exception e) {
            logger.error("❌ Failed to delete document", e);
            return false;
        }
    }

    /**
     * Bulk operations
     */
    public void bulkIndexDocuments(String indexName, List<Map<String, Object>> documents) {
        try {
            List<BulkOperation> bulkOperations = new ArrayList<>();

            for (int i = 0; i < documents.size(); i++) {
                Map<String, Object> document = documents.get(i);
                String documentId = "bulk_doc_" + (i + 1);

                // Timestamp'leri ekle
                document.put("created_at", LocalDateTime.now().toString());
                document.put("updated_at", LocalDateTime.now().toString());

                BulkOperation operation = BulkOperation.of(o -> o
                        .index(idx -> idx
                                .index(indexName)
                                .id(documentId)
                                .document(document)));

                bulkOperations.add(operation);
            }

            BulkRequest bulkRequest = BulkRequest.of(b -> b
                    .operations(bulkOperations));

            BulkResponse bulkResponse = client.bulk(bulkRequest);

            int successCount = 0;
            int errorCount = 0;

            for (var item : bulkResponse.items()) {
                if (item.error() != null) {
                    errorCount++;
                    logger.warn("❌ Bulk operation failed: {}", item.error().reason());
                } else {
                    successCount++;
                }
            }

            logger.info("📦 Bulk operation completed: {} successful, {} errors, took {} ms",
                    successCount, errorCount, bulkResponse.took());

        } catch (Exception e) {
            logger.error("❌ Bulk operation failed", e);
        }
    }

    /**
     * Basit search
     */
    public List<Map<String, Object>> searchDocuments(String indexName, String query) {
        try {
            SearchRequest searchRequest = SearchRequest.of(s -> s
                    .index(indexName)
                    .query(q -> q
                            .multiMatch(m -> m
                                    .query(query)
                                    .fields("title", "content", "author")))
                    .size(20));

            SearchResponse<Map> searchResponse = client.search(searchRequest, Map.class);

            List<Map<String, Object>> results = new ArrayList<>();

            for (Hit<Map> hit : searchResponse.hits().hits()) {
                Map<String, Object> result = new HashMap<>(hit.source());
                result.put("_id", hit.id());
                result.put("_score", hit.score());
                results.add(result);
            }

            logger.info("🔍 Search completed: query='{}', found {} documents in {} ms",
                    query, results.size(), searchResponse.took());

            return results;

        } catch (Exception e) {
            logger.error("❌ Search failed", e);
            return Collections.emptyList();
        }
    }

    /**
     * Filtered search
     */
    public List<Map<String, Object>> searchWithFilters(String indexName, String query,
            String category, List<String> tags) {
        try {
            SearchRequest.Builder searchBuilder = new SearchRequest.Builder()
                    .index(indexName)
                    .size(20);

            // Bool query builder
            var boolQueryBuilder = new co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery.Builder();

            // Text search
            if (query != null && !query.trim().isEmpty()) {
                boolQueryBuilder.must(m -> m
                        .multiMatch(mm -> mm
                                .query(query)
                                .fields("title^2", "content", "author")));
            }

            // Category filter
            if (category != null && !category.trim().isEmpty()) {
                boolQueryBuilder.filter(f -> f
                        .term(t -> t
                                .field("category")
                                .value(category)));
            }

            // Tags filter
            if (tags != null && !tags.isEmpty()) {
                boolQueryBuilder.filter(f -> f
                        .terms(t -> t
                                .field("tags")
                                .terms(ts -> ts.value(tags.stream()
                                        .map(tag -> co.elastic.clients.elasticsearch._types.FieldValue.of(tag))
                                        .toList()))));
            }

            // Published filter
            boolQueryBuilder.filter(f -> f
                    .term(t -> t
                            .field("is_published")
                            .value(true)));

            SearchRequest searchRequest = searchBuilder
                    .query(q -> q.bool(boolQueryBuilder.build()))
                    .build();

            SearchResponse<Map> searchResponse = client.search(searchRequest, Map.class);

            List<Map<String, Object>> results = new ArrayList<>();

            for (Hit<Map> hit : searchResponse.hits().hits()) {
                Map<String, Object> result = new HashMap<>(hit.source());
                result.put("_id", hit.id());
                result.put("_score", hit.score());
                results.add(result);
            }

            logger.info("🔍 Filtered search: query='{}', category='{}', tags={}, found {} documents",
                    query, category, tags, results.size());

            return results;

        } catch (Exception e) {
            logger.error("❌ Filtered search failed", e);
            return Collections.emptyList();
        }
    }

    /**
     * Range search (tarih aralığı)
     */
    public List<Map<String, Object>> searchByDateRange(String indexName, String fromDate, String toDate) {
        try {
            SearchRequest searchRequest = SearchRequest.of(s -> s
                    .index(indexName)
                    .query(q -> q
                            .range(r -> r
                                    .field("created_at")
                                    .gte(co.elastic.clients.elasticsearch._types.query_dsl.FieldValue.of(fromDate))
                                    .lte(co.elastic.clients.elasticsearch._types.query_dsl.FieldValue.of(toDate))))
                    .sort(sort -> sort
                            .field(f -> f
                                    .field("created_at")
                                    .order(co.elastic.clients.elasticsearch._types.SortOrder.Desc)))
                    .size(50));

            SearchResponse<Map> searchResponse = client.search(searchRequest, Map.class);

            List<Map<String, Object>> results = new ArrayList<>();

            for (Hit<Map> hit : searchResponse.hits().hits()) {
                Map<String, Object> result = new HashMap<>(hit.source());
                result.put("_id", hit.id());
                result.put("_score", hit.score());
                results.add(result);
            }

            logger.info("📅 Date range search: {} to {}, found {} documents",
                    fromDate, toDate, results.size());

            return results;

        } catch (Exception e) {
            logger.error("❌ Date range search failed", e);
            return Collections.emptyList();
        }
    }

    /**
     * Blog demo
     */
    public void runBlogDemo() {
        logger.info("🚀 Starting Elasticsearch Blog Demo...");

        try {
            String indexName = "blog_posts";

            // Index oluştur
            createIndex(indexName);

            // Sample blog posts
            List<Map<String, Object>> blogPosts = createSampleBlogPosts();

            // Bulk index
            bulkIndexDocuments(indexName, blogPosts);

            // Individual document operations
            demonstrateDocumentOperations(indexName);

            // Search operations
            demonstrateSearchOperations(indexName);

            // Cleanup
            Thread.sleep(2000); // Wait for indexing to complete

        } catch (Exception e) {
            logger.error("❌ Blog demo error", e);
        }
    }

    /**
     * Sample blog posts oluştur
     */
    private List<Map<String, Object>> createSampleBlogPosts() {
        List<Map<String, Object>> posts = new ArrayList<>();

        posts.add(Map.of(
                "title", "Introduction to Elasticsearch",
                "content", "Elasticsearch is a powerful search and analytics engine built on Apache Lucene...",
                "author", "john_doe",
                "category", "technology",
                "tags", List.of("elasticsearch", "search", "lucene"),
                "view_count", 1500,
                "is_published", true,
                "metadata", Map.of("reading_time", 5, "difficulty", "beginner")));

        posts.add(Map.of(
                "title", "Redis Pub/Sub vs Kafka",
                "content", "Comparing Redis Pub/Sub with Apache Kafka for real-time messaging...",
                "author", "jane_smith",
                "category", "technology",
                "tags", List.of("redis", "kafka", "messaging", "pubsub"),
                "view_count", 2800,
                "is_published", true,
                "metadata", Map.of("reading_time", 8, "difficulty", "intermediate")));

        posts.add(Map.of(
                "title", "Building Microservices with Docker",
                "content", "Learn how to containerize your microservices using Docker...",
                "author", "bob_wilson",
                "category", "devops",
                "tags", List.of("docker", "microservices", "containers"),
                "view_count", 3200,
                "is_published", true,
                "metadata", Map.of("reading_time", 12, "difficulty", "advanced")));

        posts.add(Map.of(
                "title", "Java Spring Boot Best Practices",
                "content", "Essential best practices for developing Spring Boot applications...",
                "author", "alice_brown",
                "category", "programming",
                "tags", List.of("java", "spring-boot", "best-practices"),
                "view_count", 4100,
                "is_published", true,
                "metadata", Map.of("reading_time", 15, "difficulty", "intermediate")));

        posts.add(Map.of(
                "title", "NoSQL Database Comparison",
                "content", "Comparing different NoSQL databases: MongoDB, Cassandra, Redis...",
                "author", "charlie_davis",
                "category", "database",
                "tags", List.of("nosql", "mongodb", "cassandra", "redis"),
                "view_count", 2100,
                "is_published", false, // Draft
                "metadata", Map.of("reading_time", 10, "difficulty", "intermediate")));

        return posts;
    }

    /**
     * Document operations demo
     */
    private void demonstrateDocumentOperations(String indexName) {
        logger.info("📝 Demonstrating document operations...");

        // Single document operations
        Map<String, Object> newPost = Map.of(
                "title", "Real-time Analytics with Elasticsearch",
                "content", "Learn how to build real-time analytics dashboards...",
                "author", "data_analyst",
                "category", "analytics",
                "tags", List.of("elasticsearch", "analytics", "real-time"),
                "view_count", 0,
                "is_published", true,
                "metadata", Map.of("reading_time", 7, "difficulty", "intermediate"));

        // Index document
        String docId = indexDocument(indexName, "manual_post_1", newPost);

        // Get document
        Map<String, Object> retrieved = getDocument(indexName, docId);
        if (retrieved != null) {
            logger.info("📖 Retrieved document: {}", retrieved.get("title"));
        }

        // Update document
        Map<String, Object> updates = Map.of(
                "view_count", 150,
                "tags", List.of("elasticsearch", "analytics", "real-time", "dashboard"));
        updateDocument(indexName, docId, updates);

        // Get updated document
        Map<String, Object> updatedDoc = getDocument(indexName, docId);
        if (updatedDoc != null) {
            logger.info("🔄 Updated view count: {}", updatedDoc.get("view_count"));
        }
    }

    /**
     * Search operations demo
     */
    private void demonstrateSearchOperations(String indexName) {
        logger.info("🔍 Demonstrating search operations...");

        try {
            // Wait for indexing to complete
            Thread.sleep(2000);

            // Simple search
            List<Map<String, Object>> searchResults = searchDocuments(indexName, "elasticsearch");
            logger.info("📊 Simple search results: {} documents found", searchResults.size());

            // Filtered search
            List<Map<String, Object>> filteredResults = searchWithFilters(
                    indexName, "microservices", "technology", List.of("docker", "containers"));
            logger.info("📊 Filtered search results: {} documents found", filteredResults.size());

            // Category search
            List<Map<String, Object>> categoryResults = searchWithFilters(
                    indexName, null, "programming", null);
            logger.info("📊 Category search results: {} documents found", categoryResults.size());

            // Tag search
            List<Map<String, Object>> tagResults = searchWithFilters(
                    indexName, null, null, List.of("redis"));
            logger.info("📊 Tag search results: {} documents found", tagResults.size());

            // Print sample results
            if (!searchResults.isEmpty()) {
                Map<String, Object> firstResult = searchResults.get(0);
                logger.info("📄 Sample result: {} (Score: {})",
                        firstResult.get("title"), firstResult.get("_score"));
            }

        } catch (Exception e) {
            logger.error("❌ Search demonstration failed", e);
        }
    }

    /**
     * Performance test
     */
    public void runPerformanceTest() {
        logger.info("🏃 Starting Elasticsearch Performance Test...");

        try {
            String indexName = "performance_test";

            // Create index
            createIndex(indexName);

            // Performance test - indexing
            int documentCount = 1000;
            long startTime = System.currentTimeMillis();

            List<Map<String, Object>> documents = new ArrayList<>();
            for (int i = 1; i <= documentCount; i++) {
                Map<String, Object> doc = Map.of(
                        "title", "Performance Test Document " + i,
                        "content", "This is test content for document number " + i + ". Lorem ipsum dolor sit amet.",
                        "author", "test_user_" + (i % 10),
                        "category", "test",
                        "tags", List.of("performance", "test", "document"),
                        "view_count", i * 10,
                        "is_published", true,
                        "metadata", Map.of("sequence", i, "batch", i / 100));
                documents.add(doc);

                // Batch every 100 documents
                if (i % 100 == 0) {
                    bulkIndexDocuments(indexName, new ArrayList<>(documents));
                    documents.clear();
                    logger.info("📊 Indexed {} documents", i);
                }
            }

            // Index remaining documents
            if (!documents.isEmpty()) {
                bulkIndexDocuments(indexName, documents);
            }

            long indexingTime = System.currentTimeMillis() - startTime;
            double indexingRate = (documentCount * 1000.0) / indexingTime;

            logger.info("✅ Indexing Performance: {} documents in {} ms ({:.2f} docs/sec)",
                    documentCount, indexingTime, indexingRate);

            // Wait for indexing to complete
            Thread.sleep(3000);

            // Performance test - searching
            startTime = System.currentTimeMillis();
            int searchCount = 100;

            for (int i = 1; i <= searchCount; i++) {
                String query = "test document " + (i % 50);
                searchDocuments(indexName, query);

                if (i % 20 == 0) {
                    logger.info("📊 Completed {} searches", i);
                }
            }

            long searchTime = System.currentTimeMillis() - startTime;
            double searchRate = (searchCount * 1000.0) / searchTime;

            logger.info("✅ Search Performance: {} searches in {} ms ({:.2f} searches/sec)",
                    searchCount, searchTime, searchRate);

            // Cleanup
            deleteIndex(indexName);

        } catch (Exception e) {
            logger.error("❌ Performance test failed", e);
        }
    }

    /**
     * Resource cleanup
     */
    public void close() {
        try {
            if (client != null) {
                client._transport().close();
                logger.info("🔒 Elasticsearch client closed");
            }
        } catch (IOException e) {
            logger.error("❌ Error closing Elasticsearch client", e);
        }
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java BasicOperations <mode>");
            System.out.println("Modes:");
            System.out.println("  blog        - Blog demo with CRUD operations");
            System.out.println("  performance - Performance test");
            System.out.println("  simple      - Simple operations demo");
            return;
        }

        String mode = args[0].toLowerCase();
        BasicOperations basicOps = new BasicOperations();

        try {
            switch (mode) {
                case "blog":
                    basicOps.runBlogDemo();
                    break;

                case "performance":
                    basicOps.runPerformanceTest();
                    break;

                case "simple":
                    basicOps.runSimpleDemo();
                    break;

                default:
                    logger.error("❌ Unknown mode: {}", mode);
                    return;
            }

        } catch (Exception e) {
            logger.error("❌ Application error", e);
        } finally {
            basicOps.close();
        }
    }

    /**
     * Simple demo
     */
    private void runSimpleDemo() {
        logger.info("🚀 Starting Simple Elasticsearch Demo...");

        try {
            String indexName = "simple_demo";

            // Create index
            createIndex(indexName);

            // Add a document
            Map<String, Object> doc = Map.of(
                    "title", "Hello Elasticsearch",
                    "content", "This is a simple demo document",
                    "author", "demo_user",
                    "category", "demo",
                    "tags", List.of("demo", "elasticsearch"),
                    "view_count", 1,
                    "is_published", true);

            String docId = indexDocument(indexName, "demo_doc_1", doc);
            logger.info("📝 Document indexed: {}", docId);

            // Wait for indexing
            Thread.sleep(1000);

            // Search
            List<Map<String, Object>> results = searchDocuments(indexName, "elasticsearch");
            logger.info("🔍 Found {} documents", results.size());

            // Clean up
            deleteIndex(indexName);

        } catch (Exception e) {
            logger.error("❌ Simple demo failed", e);
        }
    }
}