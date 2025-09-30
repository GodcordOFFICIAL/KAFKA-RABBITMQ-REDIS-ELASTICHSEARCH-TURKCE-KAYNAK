package main.java;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch.core.*;
import co.elastic.clients.elasticsearch.core.search.*;
import co.elastic.clients.elasticsearch.indices.*;
import co.elastic.clients.elasticsearch._types.aggregations.*;
import co.elastic.clients.elasticsearch._types.query_dsl.*;
import co.elastic.clients.elasticsearch._types.mapping.*;
import co.elastic.clients.json.jackson.JacksonJsonpMapper;
import co.elastic.clients.transport.ElasticsearchTransport;
import co.elastic.clients.transport.rest_client.RestClientTransport;
import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.*;

/**
 * Elasticsearch Advanced Search & Aggregations - İleri Düzey Arama ve
 * Agregasyon İşlemleri
 * 
 * Bu örnek Elasticsearch'in güçlü arama ve analiz özelliklerini kapsamlı olarak
 * gösterir:
 * - Kompleks arama sorguları (bool, nested, wildcard)
 * - Agregasyon işlemleri (metrics, bucket, pipeline)
 * - Faceted search ve filtering
 * - Highlight ve suggest özellikleri
 * - Performans optimizasyonu
 * - E-ticaret arama motoru simülasyonu
 * 
 * @author: Senior Software Architect
 * @version: 1.0
 */
public class AdvancedSearchAggregations {

    private ElasticsearchClient esClient;
    private static final String PRODUCTS_INDEX = "ecommerce_products";
    private static final String ANALYTICS_INDEX = "user_analytics";

    /**
     * Product entity - e-ticaret ürün modeli
     */
    public static class Product {
        @JsonProperty("id")
        private String id;

        @JsonProperty("name")
        private String name;

        @JsonProperty("description")
        private String description;

        @JsonProperty("category")
        private String category;

        @JsonProperty("brand")
        private String brand;

        @JsonProperty("price")
        private Double price;

        @JsonProperty("rating")
        private Double rating;

        @JsonProperty("tags")
        private List<String> tags;

        @JsonProperty("inStock")
        private Boolean inStock;

        @JsonProperty("createdAt")
        private String createdAt;

        // Constructors
        public Product() {
        }

        public Product(String id, String name, String description, String category,
                String brand, Double price, Double rating, List<String> tags,
                Boolean inStock) {
            this.id = id;
            this.name = name;
            this.description = description;
            this.category = category;
            this.brand = brand;
            this.price = price;
            this.rating = rating;
            this.tags = tags;
            this.inStock = inStock;
            this.createdAt = LocalDateTime.now().toString();
        }

        // Getters and Setters
        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
        }

        public String getCategory() {
            return category;
        }

        public void setCategory(String category) {
            this.category = category;
        }

        public String getBrand() {
            return brand;
        }

        public void setBrand(String brand) {
            this.brand = brand;
        }

        public Double getPrice() {
            return price;
        }

        public void setPrice(Double price) {
            this.price = price;
        }

        public Double getRating() {
            return rating;
        }

        public void setRating(Double rating) {
            this.rating = rating;
        }

        public List<String> getTags() {
            return tags;
        }

        public void setTags(List<String> tags) {
            this.tags = tags;
        }

        public Boolean getInStock() {
            return inStock;
        }

        public void setInStock(Boolean inStock) {
            this.inStock = inStock;
        }

        public String getCreatedAt() {
            return createdAt;
        }

        public void setCreatedAt(String createdAt) {
            this.createdAt = createdAt;
        }
    }

    /**
     * User Analytics entity - kullanıcı analitik modeli
     */
    public static class UserAnalytics {
        @JsonProperty("userId")
        private String userId;

        @JsonProperty("action")
        private String action; // search, view, purchase, add_to_cart

        @JsonProperty("productId")
        private String productId;

        @JsonProperty("searchQuery")
        private String searchQuery;

        @JsonProperty("timestamp")
        private String timestamp;

        @JsonProperty("sessionId")
        private String sessionId;

        public UserAnalytics() {
        }

        public UserAnalytics(String userId, String action, String productId, String searchQuery, String sessionId) {
            this.userId = userId;
            this.action = action;
            this.productId = productId;
            this.searchQuery = searchQuery;
            this.sessionId = sessionId;
            this.timestamp = LocalDateTime.now().toString();
        }

        // Getters and Setters
        public String getUserId() {
            return userId;
        }

        public void setUserId(String userId) {
            this.userId = userId;
        }

        public String getAction() {
            return action;
        }

        public void setAction(String action) {
            this.action = action;
        }

        public String getProductId() {
            return productId;
        }

        public void setProductId(String productId) {
            this.productId = productId;
        }

        public String getSearchQuery() {
            return searchQuery;
        }

        public void setSearchQuery(String searchQuery) {
            this.searchQuery = searchQuery;
        }

        public String getTimestamp() {
            return timestamp;
        }

        public void setTimestamp(String timestamp) {
            this.timestamp = timestamp;
        }

        public String getSessionId() {
            return sessionId;
        }

        public void setSessionId(String sessionId) {
            this.sessionId = sessionId;
        }
    }

    /**
     * Elasticsearch client'ını başlatır
     */
    public void initializeClient() {
        System.out.println("=== Elasticsearch Advanced Client Başlatılıyor ===");

        try {
            // REST client oluştur
            RestClient restClient = RestClient.builder(
                    new HttpHost("localhost", 9200, "http")).build();

            // Transport layer
            ElasticsearchTransport transport = new RestClientTransport(
                    restClient, new JacksonJsonpMapper());

            // Elasticsearch client
            esClient = new ElasticsearchClient(transport);

            System.out.println("✅ Elasticsearch client başlatıldı!");

        } catch (Exception e) {
            System.err.println("❌ Client başlatma hatası: " + e.getMessage());
        }
    }

    /**
     * Gelişmiş index'leri oluşturur
     */
    public void createAdvancedIndexes() {
        System.out.println("\n=== Gelişmiş Index'ler Oluşturuluyor ===");

        try {
            // Products index mapping
            CreateIndexRequest.Builder productsBuilder = new CreateIndexRequest.Builder()
                    .index(PRODUCTS_INDEX)
                    .mappings(m -> m
                            .properties("id", p -> p.keyword(k -> k))
                            .properties("name", p -> p.text(t -> t
                                    .analyzer("standard")
                                    .fields("keyword", f -> f.keyword(k -> k))))
                            .properties("description", p -> p.text(t -> t.analyzer("standard")))
                            .properties("category", p -> p.keyword(k -> k))
                            .properties("brand", p -> p.keyword(k -> k))
                            .properties("price", p -> p.double_(d -> d))
                            .properties("rating", p -> p.double_(d -> d))
                            .properties("tags", p -> p.keyword(k -> k))
                            .properties("inStock", p -> p.boolean_(b -> b))
                            .properties("createdAt", p -> p.date(d -> d)))
                    .settings(s -> s
                            .numberOfShards("1")
                            .numberOfReplicas("0")
                            .analysis(a -> a
                                    .analyzer("autocomplete", an -> an
                                            .custom(c -> c
                                                    .tokenizer("standard")
                                                    .filter("lowercase", "edge_ngram_filter")))
                                    .filter("edge_ngram_filter", f -> f
                                            .definition(d -> d
                                                    .edgeNGram(e -> e
                                                            .minGram(2)
                                                            .maxGram(10))))));

            // Analytics index mapping
            CreateIndexRequest.Builder analyticsBuilder = new CreateIndexRequest.Builder()
                    .index(ANALYTICS_INDEX)
                    .mappings(m -> m
                            .properties("userId", p -> p.keyword(k -> k))
                            .properties("action", p -> p.keyword(k -> k))
                            .properties("productId", p -> p.keyword(k -> k))
                            .properties("searchQuery", p -> p.text(t -> t.analyzer("standard")))
                            .properties("timestamp", p -> p.date(d -> d))
                            .properties("sessionId", p -> p.keyword(k -> k)));

            // Index'leri oluştur
            esClient.indices().create(productsBuilder.build());
            esClient.indices().create(analyticsBuilder.build());

            System.out.println("✅ İleri düzey index'ler oluşturuldu!");

        } catch (Exception e) {
            System.err.println("❌ Index oluşturma hatası: " + e.getMessage());
        }
    }

    /**
     * Örnek veri setini yükler
     */
    public void loadSampleData() {
        System.out.println("\n=== Örnek Veri Seti Yükleniyor ===");

        try {
            // Örnek ürünler
            List<Product> products = Arrays.asList(
                    new Product("1", "iPhone 14 Pro", "Apple'ın en yeni flagship telefonu",
                            "Electronics", "Apple", 1299.99, 4.5,
                            Arrays.asList("smartphone", "premium", "5G"), true),

                    new Product("2", "Samsung Galaxy S23", "Android'in güçlü temsilcisi",
                            "Electronics", "Samsung", 899.99, 4.3,
                            Arrays.asList("smartphone", "android", "camera"), true),

                    new Product("3", "MacBook Air M2", "Ultra ince ve güçlü laptop",
                            "Computers", "Apple", 1199.99, 4.7,
                            Arrays.asList("laptop", "ultrabook", "M2"), true),

                    new Product("4", "Dell XPS 13", "Premium Windows laptop",
                            "Computers", "Dell", 999.99, 4.4,
                            Arrays.asList("laptop", "windows", "business"), false),

                    new Product("5", "Sony WH-1000XM4", "Noise cancelling kulaklık",
                            "Audio", "Sony", 349.99, 4.6,
                            Arrays.asList("headphones", "wireless", "noise-cancelling"), true),

                    new Product("6", "Nike Air Max", "Rahat spor ayakkabı",
                            "Shoes", "Nike", 129.99, 4.2,
                            Arrays.asList("sneakers", "running", "casual"), true),

                    new Product("7", "Levi's 501 Jeans", "Klasik straight-leg jean",
                            "Clothing", "Levi's", 79.99, 4.1,
                            Arrays.asList("jeans", "classic", "denim"), true),

                    new Product("8", "Instant Pot Duo", "Çok fonksiyonlu pressure cooker",
                            "Kitchen", "Instant Pot", 89.99, 4.8,
                            Arrays.asList("cooking", "pressure-cooker", "kitchen"), true));

            // Bulk insert için request builder
            BulkRequest.Builder bulkBuilder = new BulkRequest.Builder();

            for (Product product : products) {
                bulkBuilder.operations(op -> op
                        .index(idx -> idx
                                .index(PRODUCTS_INDEX)
                                .id(product.getId())
                                .document(product)));
            }

            BulkResponse bulkResponse = esClient.bulk(bulkBuilder.build());

            if (bulkResponse.errors()) {
                System.err.println("⚠️ Bazı belgeler yüklenemedi");
                bulkResponse.items().forEach(item -> {
                    if (item.error() != null) {
                        System.err.println("Hata: " + item.error().reason());
                    }
                });
            } else {
                System.out.println("✅ " + products.size() + " ürün başarıyla yüklendi!");
            }

            // Örnek analytics verisi
            List<UserAnalytics> analytics = Arrays.asList(
                    new UserAnalytics("user1", "search", null, "iphone", "sess1"),
                    new UserAnalytics("user1", "view", "1", null, "sess1"),
                    new UserAnalytics("user1", "add_to_cart", "1", null, "sess1"),
                    new UserAnalytics("user2", "search", null, "laptop", "sess2"),
                    new UserAnalytics("user2", "view", "3", null, "sess2"),
                    new UserAnalytics("user2", "purchase", "3", null, "sess2"),
                    new UserAnalytics("user3", "search", null, "nike shoes", "sess3"),
                    new UserAnalytics("user3", "view", "6", null, "sess3"));

            BulkRequest.Builder analyticsBulkBuilder = new BulkRequest.Builder();

            for (int i = 0; i < analytics.size(); i++) {
                UserAnalytics analytic = analytics.get(i);
                analyticsBulkBuilder.operations(op -> op
                        .index(idx -> idx
                                .index(ANALYTICS_INDEX)
                                .id(String.valueOf(i + 1))
                                .document(analytic)));
            }

            esClient.bulk(analyticsBulkBuilder.build());
            System.out.println("✅ Analytics verisi yüklendi!");

            // Index'in refresh olmasını bekle
            esClient.indices().refresh(r -> r.index(PRODUCTS_INDEX, ANALYTICS_INDEX));

        } catch (Exception e) {
            System.err.println("❌ Veri yükleme hatası: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Kompleks bool query ile arama yapar
     */
    public void performComplexSearch() {
        System.out.println("\n=== Kompleks Boolean Arama ===");

        try {
            // Kompleks arama: Electronics kategorisinde, fiyatı 1000$ altında, stokta olan
            // ürünler
            SearchRequest searchRequest = SearchRequest.of(s -> s
                    .index(PRODUCTS_INDEX)
                    .query(q -> q
                            .bool(b -> b
                                    .must(m -> m
                                            .term(t -> t
                                                    .field("category")
                                                    .value("Electronics")))
                                    .must(m -> m
                                            .range(r -> r
                                                    .field("price")
                                                    .lt(JsonData.of(1000))))
                                    .must(m -> m
                                            .term(t -> t
                                                    .field("inStock")
                                                    .value(true)))
                                    .should(sh -> sh
                                            .match(ma -> ma
                                                    .field("name")
                                                    .query("premium")
                                                    .boost(2.0f)))
                                    .should(sh -> sh
                                            .terms(te -> te
                                                    .field("tags")
                                                    .terms(ter -> ter.value(Arrays.asList(
                                                            FieldValue.of("smartphone"),
                                                            FieldValue.of("premium"))))
                                                    .boost(1.5f)))
                                    .minimumShouldMatch("1")))
                    .highlight(h -> h
                            .fields("name", hf -> hf
                                    .preTags("<em>")
                                    .postTags("</em>"))
                            .fields("description", hf -> hf
                                    .fragmentSize(150)
                                    .numberOfFragments(2)))
                    .sort(so -> so
                            .field(f -> f
                                    .field("rating")
                                    .order(SortOrder.Desc)))
                    .size(10));

            SearchResponse<Product> response = esClient.search(searchRequest, Product.class);

            System.out.println("📊 Arama Sonuçları:");
            System.out.println("   Toplam bulunan: " + response.hits().total().value());
            System.out.println("   Maksimum skor: " + response.hits().maxScore());

            response.hits().hits().forEach(hit -> {
                Product product = hit.source();
                System.out.println("\n   🔍 Ürün: " + product.getName());
                System.out.println("      Skor: " + hit.score());
                System.out.println("      Fiyat: $" + product.getPrice());
                System.out.println("      Rating: " + product.getRating());

                // Highlight sonuçları
                if (hit.highlight() != null) {
                    hit.highlight().forEach((field, highlights) -> {
                        System.out.println("      Highlight (" + field + "): " + highlights.get(0));
                    });
                }
            });

        } catch (Exception e) {
            System.err.println("❌ Kompleks arama hatası: " + e.getMessage());
        }
    }

    /**
     * Aggregation işlemleri gerçekleştirir
     */
    public void performAggregations() {
        System.out.println("\n=== Aggregation İşlemleri ===");

        try {
            SearchRequest aggregationRequest = SearchRequest.of(s -> s
                    .index(PRODUCTS_INDEX)
                    .size(0) // Sadece agregasyon sonuçları istiyoruz
                    .aggregations("categories", a -> a
                            .terms(t -> t
                                    .field("category")
                                    .size(10))
                            .aggregations("avg_price", aa -> aa
                                    .avg(av -> av.field("price")))
                            .aggregations("max_rating", aa -> aa
                                    .max(mx -> mx.field("rating"))))
                    .aggregations("price_ranges", a -> a
                            .range(r -> r
                                    .field("price")
                                    .ranges(ra -> ra.to(100.0))
                                    .ranges(ra -> ra.from(100.0).to(500.0))
                                    .ranges(ra -> ra.from(500.0).to(1000.0))
                                    .ranges(ra -> ra.from(1000.0))))
                    .aggregations("rating_histogram", a -> a
                            .histogram(h -> h
                                    .field("rating")
                                    .interval(0.5)
                                    .minDocCount(1)))
                    .aggregations("brand_stats", a -> a
                            .terms(t -> t
                                    .field("brand")
                                    .size(5))
                            .aggregations("price_stats", aa -> aa
                                    .stats(st -> st.field("price")))));

            SearchResponse<Product> response = esClient.search(aggregationRequest, Product.class);

            System.out.println("📊 Agregasyon Sonuçları:");

            // Kategori agregasyonu
            if (response.aggregations().get("categories") != null) {
                StringTermsAggregate categoriesAgg = response.aggregations()
                        .get("categories").sterms();

                System.out.println("\n   📁 Kategoriler:");
                categoriesAgg.buckets().array().forEach(bucket -> {
                    System.out.println("      " + bucket.key() + ": " + bucket.docCount() + " ürün");

                    // Alt agregasyonlar
                    if (bucket.aggregations().get("avg_price") != null) {
                        double avgPrice = bucket.aggregations().get("avg_price").avg().value();
                        System.out.printf("         Ortalama fiyat: $%.2f\n", avgPrice);
                    }

                    if (bucket.aggregations().get("max_rating") != null) {
                        double maxRating = bucket.aggregations().get("max_rating").max().value();
                        System.out.printf("         En yüksek rating: %.1f\n", maxRating);
                    }
                });
            }

            // Fiyat aralıkları
            if (response.aggregations().get("price_ranges") != null) {
                RangeAggregate priceRangesAgg = response.aggregations()
                        .get("price_ranges").range();

                System.out.println("\n   💰 Fiyat Aralıkları:");
                priceRangesAgg.buckets().array().forEach(bucket -> {
                    String from = bucket.from() != null ? String.format("$%.0f", bucket.from()) : "-";
                    String to = bucket.to() != null ? String.format("$%.0f", bucket.to()) : "+";
                    System.out.println("      " + from + " - " + to + ": " + bucket.docCount() + " ürün");
                });
            }

            // Rating histogram
            if (response.aggregations().get("rating_histogram") != null) {
                HistogramAggregate ratingHistogram = response.aggregations()
                        .get("rating_histogram").histogram();

                System.out.println("\n   ⭐ Rating Dağılımı:");
                ratingHistogram.buckets().array().forEach(bucket -> {
                    System.out.printf("      %.1f+: %d ürün\n", bucket.key(), bucket.docCount());
                });
            }

        } catch (Exception e) {
            System.err.println("❌ Agregasyon hatası: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Faceted search (çok boyutlu arama) gerçekleştirir
     */
    public void performFacetedSearch() {
        System.out.println("\n=== Faceted Search (Çok Boyutlu Arama) ===");

        try {
            String searchTerm = "phone";
            List<String> selectedCategories = Arrays.asList("Electronics");
            double minPrice = 0;
            double maxPrice = 2000;

            SearchRequest facetedRequest = SearchRequest.of(s -> s
                    .index(PRODUCTS_INDEX)
                    .query(q -> q
                            .bool(b -> {
                                // Ana arama terimi
                                if (searchTerm != null && !searchTerm.isEmpty()) {
                                    b.must(m -> m
                                            .multiMatch(mm -> mm
                                                    .query(searchTerm)
                                                    .fields("name^3", "description^1", "tags^2")
                                                    .type(TextQueryType.BestFields)
                                                    .fuzziness("AUTO")));
                                }

                                // Kategori filtresi
                                if (!selectedCategories.isEmpty()) {
                                    b.filter(f -> f
                                            .terms(t -> t
                                                    .field("category")
                                                    .terms(ter -> ter.value(
                                                            selectedCategories.stream()
                                                                    .map(FieldValue::of)
                                                                    .toList()))));
                                }

                                // Fiyat aralığı filtresi
                                b.filter(f -> f
                                        .range(r -> r
                                                .field("price")
                                                .gte(JsonData.of(minPrice))
                                                .lte(JsonData.of(maxPrice))));

                                // Sadece stokta olan ürünler
                                b.filter(f -> f
                                        .term(t -> t
                                                .field("inStock")
                                                .value(true)));

                                return b;
                            }))
                    .aggregations("categories_facet", a -> a
                            .terms(t -> t.field("category").size(20)))
                    .aggregations("brands_facet", a -> a
                            .terms(t -> t.field("brand").size(20)))
                    .aggregations("price_facet", a -> a
                            .range(r -> r
                                    .field("price")
                                    .ranges(ra -> ra.key("0-100").to(100.0))
                                    .ranges(ra -> ra.key("100-500").from(100.0).to(500.0))
                                    .ranges(ra -> ra.key("500-1000").from(500.0).to(1000.0))
                                    .ranges(ra -> ra.key("1000+").from(1000.0))))
                    .aggregations("rating_facet", a -> a
                            .range(r -> r
                                    .field("rating")
                                    .ranges(ra -> ra.key("4.5+").from(4.5))
                                    .ranges(ra -> ra.key("4.0+").from(4.0).to(4.5))
                                    .ranges(ra -> ra.key("3.5+").from(3.5).to(4.0))
                                    .ranges(ra -> ra.key("3.0+").from(3.0).to(3.5))))
                    .size(20));

            SearchResponse<Product> response = esClient.search(facetedRequest, Product.class);

            System.out.println("🔍 Faceted Search Sonuçları:");
            System.out.println("   Arama terimi: '" + searchTerm + "'");
            System.out.println("   Toplam sonuç: " + response.hits().total().value());

            // Ana sonuçlar
            System.out.println("\n   📱 Bulunan Ürünler:");
            response.hits().hits().forEach(hit -> {
                Product product = hit.source();
                System.out.printf("      %s - $%.2f (Rating: %.1f)\n",
                        product.getName(), product.getPrice(), product.getRating());
            });

            // Facet sonuçları
            System.out.println("\n   🎛️ Filtre Seçenekleri:");

            // Kategori facet
            if (response.aggregations().get("categories_facet") != null) {
                System.out.println("      📁 Kategoriler:");
                response.aggregations().get("categories_facet").sterms()
                        .buckets().array().forEach(bucket -> {
                            System.out.println("         " + bucket.key() + " (" + bucket.docCount() + ")");
                        });
            }

            // Marka facet
            if (response.aggregations().get("brands_facet") != null) {
                System.out.println("      🏷️ Markalar:");
                response.aggregations().get("brands_facet").sterms()
                        .buckets().array().forEach(bucket -> {
                            System.out.println("         " + bucket.key() + " (" + bucket.docCount() + ")");
                        });
            }

            // Fiyat facet
            if (response.aggregations().get("price_facet") != null) {
                System.out.println("      💰 Fiyat Aralıkları:");
                response.aggregations().get("price_facet").range()
                        .buckets().array().forEach(bucket -> {
                            System.out.println("         " + bucket.key() + " (" + bucket.docCount() + ")");
                        });
            }

        } catch (Exception e) {
            System.err.println("❌ Faceted search hatası: " + e.getMessage());
        }
    }

    /**
     * Auto-complete ve suggestion özellikleri
     */
    public void demonstrateAutoComplete() {
        System.out.println("\n=== Auto-Complete ve Suggestion ===");

        try {
            String partialQuery = "iph";

            // Prefix-based autocomplete
            SearchRequest autocompleteRequest = SearchRequest.of(s -> s
                    .index(PRODUCTS_INDEX)
                    .query(q -> q
                            .bool(b -> b
                                    .should(sh -> sh
                                            .prefix(p -> p
                                                    .field("name")
                                                    .value(partialQuery)
                                                    .boost(3.0f)))
                                    .should(sh -> sh
                                            .prefix(p -> p
                                                    .field("description")
                                                    .value(partialQuery)
                                                    .boost(1.0f)))
                                    .should(sh -> sh
                                            .wildcard(w -> w
                                                    .field("name")
                                                    .value("*" + partialQuery + "*")
                                                    .boost(2.0f)))))
                    .size(5)
                    .source(src -> src
                            .filter(f -> f.includes("name", "category", "price"))));

            SearchResponse<Product> autocompleteResponse = esClient.search(autocompleteRequest, Product.class);

            System.out.println("🔤 Auto-Complete Sonuçları ('" + partialQuery + "'):");
            autocompleteResponse.hits().hits().forEach(hit -> {
                Product product = hit.source();
                System.out.printf("   📱 %s (%s) - $%.2f\n",
                        product.getName(), product.getCategory(), product.getPrice());
            });

            // Suggestion (typo tolerance)
            String misspelledQuery = "iphon";

            SearchRequest suggestionRequest = SearchRequest.of(s -> s
                    .index(PRODUCTS_INDEX)
                    .query(q -> q
                            .match(m -> m
                                    .field("name")
                                    .query(misspelledQuery)
                                    .fuzziness("AUTO")
                                    .prefixLength(1)
                                    .maxExpansions(10)))
                    .size(3));

            SearchResponse<Product> suggestionResponse = esClient.search(suggestionRequest, Product.class);

            System.out.println("\n🔍 Suggestion Sonuçları ('" + misspelledQuery + "'):");
            suggestionResponse.hits().hits().forEach(hit -> {
                Product product = hit.source();
                System.out.printf("   📱 %s (skor: %.2f)\n",
                        product.getName(), hit.score());
            });

        } catch (Exception e) {
            System.err.println("❌ Auto-complete hatası: " + e.getMessage());
        }
    }

    /**
     * Analytics ve reporting queries
     */
    public void performAnalyticsQueries() {
        System.out.println("\n=== Analytics ve Reporting ===");

        try {
            // En çok aranan terimler
            SearchRequest topSearchesRequest = SearchRequest.of(s -> s
                    .index(ANALYTICS_INDEX)
                    .size(0)
                    .query(q -> q
                            .term(t -> t
                                    .field("action")
                                    .value("search")))
                    .aggregations("top_searches", a -> a
                            .terms(t -> t
                                    .field("searchQuery")
                                    .size(10)
                                    .order(NamedValue.of("_count", SortOrder.Desc)))));

            SearchResponse<UserAnalytics> topSearchesResponse = esClient.search(topSearchesRequest,
                    UserAnalytics.class);

            System.out.println("🔍 En Çok Aranan Terimler:");
            if (topSearchesResponse.aggregations().get("top_searches") != null) {
                topSearchesResponse.aggregations().get("top_searches").sterms()
                        .buckets().array().forEach(bucket -> {
                            System.out.println("   '" + bucket.key() + "': " + bucket.docCount() + " arama");
                        });
            }

            // En çok görüntülenen ürünler
            SearchRequest topViewedRequest = SearchRequest.of(s -> s
                    .index(ANALYTICS_INDEX)
                    .size(0)
                    .query(q -> q
                            .term(t -> t
                                    .field("action")
                                    .value("view")))
                    .aggregations("top_viewed", a -> a
                            .terms(t -> t
                                    .field("productId")
                                    .size(5))));

            SearchResponse<UserAnalytics> topViewedResponse = esClient.search(topViewedRequest, UserAnalytics.class);

            System.out.println("\n👀 En Çok Görüntülenen Ürünler:");
            if (topViewedResponse.aggregations().get("top_viewed") != null) {
                topViewedResponse.aggregations().get("top_viewed").sterms()
                        .buckets().array().forEach(bucket -> {
                            System.out.println(
                                    "   Ürün ID: " + bucket.key() + " (" + bucket.docCount() + " görüntüleme)");
                        });
            }

            // Kullanıcı davranış analizi
            SearchRequest userBehaviorRequest = SearchRequest.of(s -> s
                    .index(ANALYTICS_INDEX)
                    .size(0)
                    .aggregations("actions_distribution", a -> a
                            .terms(t -> t.field("action").size(10)))
                    .aggregations("unique_users", a -> a
                            .cardinality(c -> c.field("userId")))
                    .aggregations("unique_sessions", a -> a
                            .cardinality(c -> c.field("sessionId"))));

            SearchResponse<UserAnalytics> behaviorResponse = esClient.search(userBehaviorRequest, UserAnalytics.class);

            System.out.println("\n📊 Kullanıcı Davranış Analizi:");

            if (behaviorResponse.aggregations().get("actions_distribution") != null) {
                System.out.println("   Eylem Dağılımı:");
                behaviorResponse.aggregations().get("actions_distribution").sterms()
                        .buckets().array().forEach(bucket -> {
                            System.out.println("      " + bucket.key() + ": " + bucket.docCount());
                        });
            }

            if (behaviorResponse.aggregations().get("unique_users") != null) {
                long uniqueUsers = behaviorResponse.aggregations().get("unique_users").cardinality().value();
                System.out.println("   Benzersiz kullanıcı sayısı: " + uniqueUsers);
            }

            if (behaviorResponse.aggregations().get("unique_sessions") != null) {
                long uniqueSessions = behaviorResponse.aggregations().get("unique_sessions").cardinality().value();
                System.out.println("   Benzersiz oturum sayısı: " + uniqueSessions);
            }

        } catch (Exception e) {
            System.err.println("❌ Analytics sorguları hatası: " + e.getMessage());
        }
    }

    /**
     * Index'leri temizler
     */
    public void cleanup() {
        try {
            esClient.indices().delete(d -> d.index(PRODUCTS_INDEX, ANALYTICS_INDEX));
            System.out.println("✅ Index'ler temizlendi");
        } catch (Exception e) {
            System.err.println("❌ Temizlik hatası: " + e.getMessage());
        }
    }

    /**
     * Ana method - tüm gelişmiş arama özelliklerini gösterir
     */
    public static void main(String[] args) {
        AdvancedSearchAggregations demo = new AdvancedSearchAggregations();

        try {
            System.out.println("🚀 Elasticsearch Advanced Search & Aggregations Demo Başlıyor...\n");

            // 1. Client'ı başlat
            demo.initializeClient();

            // 2. Gelişmiş index'leri oluştur
            demo.createAdvancedIndexes();

            // 3. Örnek veri setini yükle
            demo.loadSampleData();

            // 4. Kompleks boolean arama
            demo.performComplexSearch();

            // 5. Aggregation işlemleri
            demo.performAggregations();

            // 6. Faceted search
            demo.performFacetedSearch();

            // 7. Auto-complete ve suggestion
            demo.demonstrateAutoComplete();

            // 8. Analytics ve reporting
            demo.performAnalyticsQueries();

            System.out.println("\n🎉 Elasticsearch Advanced Demo Tamamlandı!");

            // Uncomment to cleanup
            // demo.cleanup();

        } catch (Exception e) {
            System.err.println("❌ Demo çalıştırma hatası: " + e.getMessage());
            e.printStackTrace();
        }
    }
}