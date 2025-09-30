"""
Elasticsearch Advanced Aggregations Implementation
Real-time analytics ve data mining için kapsamlı aggregation framework
"""

from elasticsearch import Elasticsearch
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Union
import json
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass
class AggregationResult:
    """Aggregation sonucu wrapper"""
    name: str
    type: str
    value: Any
    buckets: List[Dict] = None
    metadata: Dict = None

class ElasticsearchAggregations:
    """
    Advanced Elasticsearch Aggregations Framework
    Real-time analytics ve business intelligence için optimized
    """
    
    def __init__(self, hosts=['localhost:9200'], **kwargs):
        """
        Elasticsearch aggregations client
        """
        self.es = Elasticsearch(hosts, **kwargs)
        print(f"📊 Elasticsearch Aggregations Framework başlatıldı")
    
    def sales_analytics(self, index: str = "sales", date_range: Dict = None) -> Dict[str, AggregationResult]:
        """
        Comprehensive sales analytics
        
        Args:
            index: Sales index name
            date_range: {"from": "2023-01-01", "to": "2023-12-31"}
        """
        print("💰 Sales Analytics başlatılıyor...")
        
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": []
                }
            },
            "aggs": {
                # Basic metrics
                "total_revenue": {
                    "sum": {
                        "field": "amount"
                    }
                },
                "avg_order_value": {
                    "avg": {
                        "field": "amount"
                    }
                },
                "order_count": {
                    "value_count": {
                        "field": "order_id"
                    }
                },
                "revenue_stats": {
                    "stats": {
                        "field": "amount"
                    }
                },
                
                # Time-series analysis
                "monthly_revenue": {
                    "date_histogram": {
                        "field": "order_date",
                        "calendar_interval": "month",
                        "format": "yyyy-MM",
                        "min_doc_count": 0
                    },
                    "aggs": {
                        "revenue": {
                            "sum": {
                                "field": "amount"
                            }
                        },
                        "order_count": {
                            "value_count": {
                                "field": "order_id"
                            }
                        },
                        "avg_order_value": {
                            "avg": {
                                "field": "amount"
                            }
                        }
                    }
                },
                
                # Product category analysis
                "category_performance": {
                    "terms": {
                        "field": "category",
                        "size": 20,
                        "order": {
                            "revenue": "desc"
                        }
                    },
                    "aggs": {
                        "revenue": {
                            "sum": {
                                "field": "amount"
                            }
                        },
                        "avg_price": {
                            "avg": {
                                "field": "amount"
                            }
                        },
                        "order_count": {
                            "value_count": {
                                "field": "order_id"
                            }
                        }
                    }
                },
                
                # Customer segmentation
                "customer_segments": {
                    "range": {
                        "field": "amount",
                        "ranges": [
                            {"key": "budget", "to": 50},
                            {"key": "standard", "from": 50, "to": 200},
                            {"key": "premium", "from": 200, "to": 500},
                            {"key": "luxury", "from": 500}
                        ]
                    },
                    "aggs": {
                        "customer_count": {
                            "cardinality": {
                                "field": "customer_id"
                            }
                        },
                        "total_revenue": {
                            "sum": {
                                "field": "amount"
                            }
                        }
                    }
                },
                
                # Geographic analysis
                "revenue_by_region": {
                    "terms": {
                        "field": "region",
                        "size": 10
                    },
                    "aggs": {
                        "revenue": {
                            "sum": {
                                "field": "amount"
                            }
                        },
                        "cities": {
                            "terms": {
                                "field": "city",
                                "size": 5
                            },
                            "aggs": {
                                "city_revenue": {
                                    "sum": {
                                        "field": "amount"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Date range filter
        if date_range:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "order_date": {
                        "gte": date_range.get("from"),
                        "lte": date_range.get("to")
                    }
                }
            })
        
        try:
            result = self.es.search(index=index, body=query)
            aggregations = result['aggregations']
            
            # Sonuçları parse et
            analytics_results = {}
            
            # Basic metrics
            analytics_results['total_revenue'] = AggregationResult(
                name="Total Revenue",
                type="metric",
                value=aggregations['total_revenue']['value']
            )
            
            analytics_results['avg_order_value'] = AggregationResult(
                name="Average Order Value",
                type="metric",
                value=aggregations['avg_order_value']['value']
            )
            
            analytics_results['order_count'] = AggregationResult(
                name="Total Orders",
                type="metric",
                value=aggregations['order_count']['value']
            )
            
            # Monthly trends
            monthly_buckets = aggregations['monthly_revenue']['buckets']
            analytics_results['monthly_trends'] = AggregationResult(
                name="Monthly Revenue Trends",
                type="time_series",
                value=None,
                buckets=monthly_buckets
            )
            
            # Category performance
            category_buckets = aggregations['category_performance']['buckets']
            analytics_results['category_performance'] = AggregationResult(
                name="Category Performance",
                type="terms",
                value=None,
                buckets=category_buckets
            )
            
            # Customer segments
            segment_buckets = aggregations['customer_segments']['buckets']
            analytics_results['customer_segments'] = AggregationResult(
                name="Customer Segments",
                type="range",
                value=None,
                buckets=segment_buckets
            )
            
            # Geographic analysis
            region_buckets = aggregations['revenue_by_region']['buckets']
            analytics_results['geographic_performance'] = AggregationResult(
                name="Geographic Performance",
                type="terms",
                value=None,
                buckets=region_buckets
            )
            
            print(f"✅ Sales analytics tamamlandı - {len(analytics_results)} metric hesaplandı")
            return analytics_results
            
        except Exception as e:
            print(f"❌ Sales analytics hatası: {e}")
            return {}
    
    def product_analytics(self, index: str = "products") -> Dict[str, AggregationResult]:
        """
        Product performance analytics
        """
        print("📦 Product Analytics başlatılıyor...")
        
        query = {
            "size": 0,
            "aggs": {
                # Inventory analysis
                "inventory_stats": {
                    "stats": {
                        "field": "stock_quantity"
                    }
                },
                
                # Price analysis
                "price_distribution": {
                    "histogram": {
                        "field": "price",
                        "interval": 50,
                        "min_doc_count": 1
                    }
                },
                
                # Rating analysis
                "rating_distribution": {
                    "range": {
                        "field": "rating",
                        "ranges": [
                            {"key": "poor", "to": 2},
                            {"key": "fair", "from": 2, "to": 3},
                            {"key": "good", "from": 3, "to": 4},
                            {"key": "excellent", "from": 4}
                        ]
                    }
                },
                
                # Top rated products
                "top_rated_categories": {
                    "terms": {
                        "field": "category",
                        "size": 10,
                        "order": {
                            "avg_rating": "desc"
                        }
                    },
                    "aggs": {
                        "avg_rating": {
                            "avg": {
                                "field": "rating"
                            }
                        },
                        "avg_price": {
                            "avg": {
                                "field": "price"
                            }
                        },
                        "total_products": {
                            "value_count": {
                                "field": "product_id"
                            }
                        }
                    }
                },
                
                # Stock alerts
                "low_stock_products": {
                    "filter": {
                        "range": {
                            "stock_quantity": {
                                "lt": 10
                            }
                        }
                    },
                    "aggs": {
                        "categories": {
                            "terms": {
                                "field": "category",
                                "size": 10
                            }
                        }
                    }
                },
                
                # Brand analysis
                "brand_performance": {
                    "terms": {
                        "field": "brand",
                        "size": 15
                    },
                    "aggs": {
                        "avg_price": {
                            "avg": {
                                "field": "price"
                            }
                        },
                        "avg_rating": {
                            "avg": {
                                "field": "rating"
                            }
                        },
                        "product_count": {
                            "value_count": {
                                "field": "product_id"
                            }
                        }
                    }
                }
            }
        }
        
        try:
            result = self.es.search(index=index, body=query)
            aggregations = result['aggregations']
            
            analytics_results = {}
            
            # Inventory stats
            analytics_results['inventory_stats'] = AggregationResult(
                name="Inventory Statistics",
                type="stats",
                value=aggregations['inventory_stats']
            )
            
            # Price distribution
            analytics_results['price_distribution'] = AggregationResult(
                name="Price Distribution",
                type="histogram",
                value=None,
                buckets=aggregations['price_distribution']['buckets']
            )
            
            # Rating distribution
            analytics_results['rating_distribution'] = AggregationResult(
                name="Rating Distribution",
                type="range",
                value=None,
                buckets=aggregations['rating_distribution']['buckets']
            )
            
            # Top rated categories
            analytics_results['top_rated_categories'] = AggregationResult(
                name="Top Rated Categories",
                type="terms",
                value=None,
                buckets=aggregations['top_rated_categories']['buckets']
            )
            
            # Low stock alerts
            low_stock_count = aggregations['low_stock_products']['doc_count']
            analytics_results['low_stock_alert'] = AggregationResult(
                name="Low Stock Alert",
                type="filter",
                value=low_stock_count,
                metadata={"threshold": 10}
            )
            
            # Brand performance
            analytics_results['brand_performance'] = AggregationResult(
                name="Brand Performance",
                type="terms",
                value=None,
                buckets=aggregations['brand_performance']['buckets']
            )
            
            print(f"✅ Product analytics tamamlandı - {len(analytics_results)} metric hesaplandı")
            return analytics_results
            
        except Exception as e:
            print(f"❌ Product analytics hatası: {e}")
            return {}
    
    def customer_analytics(self, index: str = "customers") -> Dict[str, AggregationResult]:
        """
        Customer behavior analytics
        """
        print("👥 Customer Analytics başlatılıyor...")
        
        query = {
            "size": 0,
            "aggs": {
                # Customer lifetime value segments
                "clv_segments": {
                    "percentiles": {
                        "field": "lifetime_value",
                        "percents": [25, 50, 75, 90, 95]
                    }
                },
                
                # Age demographics
                "age_demographics": {
                    "range": {
                        "field": "age",
                        "ranges": [
                            {"key": "18-25", "from": 18, "to": 26},
                            {"key": "26-35", "from": 26, "to": 36},
                            {"key": "36-45", "from": 36, "to": 46},
                            {"key": "46-55", "from": 46, "to": 56},
                            {"key": "55+", "from": 56}
                        ]
                    },
                    "aggs": {
                        "avg_clv": {
                            "avg": {
                                "field": "lifetime_value"
                            }
                        },
                        "avg_order_frequency": {
                            "avg": {
                                "field": "order_frequency"
                            }
                        }
                    }
                },
                
                # Geographic distribution
                "customer_by_city": {
                    "terms": {
                        "field": "city",
                        "size": 20
                    },
                    "aggs": {
                        "avg_clv": {
                            "avg": {
                                "field": "lifetime_value"
                            }
                        }
                    }
                },
                
                # Registration trends
                "monthly_registrations": {
                    "date_histogram": {
                        "field": "registration_date",
                        "calendar_interval": "month",
                        "format": "yyyy-MM"
                    }
                },
                
                # Customer status distribution
                "customer_status": {
                    "terms": {
                        "field": "status",
                        "size": 10
                    }
                },
                
                # Premium customers
                "premium_customers": {
                    "filter": {
                        "range": {
                            "lifetime_value": {
                                "gte": 1000
                            }
                        }
                    },
                    "aggs": {
                        "total_value": {
                            "sum": {
                                "field": "lifetime_value"
                            }
                        },
                        "avg_age": {
                            "avg": {
                                "field": "age"
                            }
                        },
                        "top_cities": {
                            "terms": {
                                "field": "city",
                                "size": 5
                            }
                        }
                    }
                }
            }
        }
        
        try:
            result = self.es.search(index=index, body=query)
            aggregations = result['aggregations']
            
            analytics_results = {}
            
            # CLV segments
            analytics_results['clv_segments'] = AggregationResult(
                name="Customer Lifetime Value Segments",
                type="percentiles",
                value=aggregations['clv_segments']['values']
            )
            
            # Age demographics
            analytics_results['age_demographics'] = AggregationResult(
                name="Age Demographics",
                type="range",
                value=None,
                buckets=aggregations['age_demographics']['buckets']
            )
            
            # Geographic distribution
            analytics_results['geographic_distribution'] = AggregationResult(
                name="Customer Geographic Distribution",
                type="terms",
                value=None,
                buckets=aggregations['customer_by_city']['buckets']
            )
            
            # Registration trends
            analytics_results['registration_trends'] = AggregationResult(
                name="Monthly Registration Trends",
                type="time_series",
                value=None,
                buckets=aggregations['monthly_registrations']['buckets']
            )
            
            # Customer status
            analytics_results['customer_status'] = AggregationResult(
                name="Customer Status Distribution",
                type="terms",
                value=None,
                buckets=aggregations['customer_status']['buckets']
            )
            
            # Premium customers analysis
            premium_data = aggregations['premium_customers']
            analytics_results['premium_customers'] = AggregationResult(
                name="Premium Customers Analysis",
                type="filter",
                value=premium_data['doc_count'],
                metadata={
                    "total_value": premium_data['total_value']['value'],
                    "avg_age": premium_data['avg_age']['value'],
                    "top_cities": premium_data['top_cities']['buckets']
                }
            )
            
            print(f"✅ Customer analytics tamamlandı - {len(analytics_results)} metric hesaplandı")
            return analytics_results
            
        except Exception as e:
            print(f"❌ Customer analytics hatası: {e}")
            return {}
    
    def real_time_dashboard_data(self, indices: List[str]) -> Dict:
        """
        Real-time dashboard için consolidated data
        """
        print("📊 Real-time Dashboard Data toplaniyor...")
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'trends': {},
            'alerts': []
        }
        
        try:
            # Sales metrics
            if 'sales' in indices:
                sales_data = self.sales_analytics('sales')
                dashboard_data['metrics']['sales'] = {
                    'total_revenue': sales_data.get('total_revenue', AggregationResult("", "", 0)).value,
                    'avg_order_value': sales_data.get('avg_order_value', AggregationResult("", "", 0)).value,
                    'order_count': sales_data.get('order_count', AggregationResult("", "", 0)).value
                }
                
                # Monthly trends
                monthly_trends = sales_data.get('monthly_trends')
                if monthly_trends and monthly_trends.buckets:
                    dashboard_data['trends']['monthly_revenue'] = [
                        {
                            'month': bucket['key_as_string'],
                            'revenue': bucket['revenue']['value'],
                            'orders': bucket['order_count']['value']
                        }
                        for bucket in monthly_trends.buckets[-6:]  # Son 6 ay
                    ]
            
            # Product metrics
            if 'products' in indices:
                product_data = self.product_analytics('products')
                
                # Low stock alert
                low_stock = product_data.get('low_stock_alert')
                if low_stock and low_stock.value > 0:
                    dashboard_data['alerts'].append({
                        'type': 'warning',
                        'message': f"{low_stock.value} products have low stock",
                        'priority': 'medium'
                    })
            
            # Customer metrics
            if 'customers' in indices:
                customer_data = self.customer_analytics('customers')
                
                # Premium customers
                premium_customers = customer_data.get('premium_customers')
                if premium_customers:
                    dashboard_data['metrics']['customers'] = {
                        'premium_count': premium_customers.value,
                        'premium_value': premium_customers.metadata.get('total_value', 0),
                        'premium_avg_age': premium_customers.metadata.get('avg_age', 0)
                    }
            
            print(f"✅ Dashboard data hazırlandı - {len(dashboard_data['metrics'])} metric, {len(dashboard_data['alerts'])} alert")
            return dashboard_data
            
        except Exception as e:
            print(f"❌ Dashboard data hatası: {e}")
            return dashboard_data
    
    def generate_analytics_report(self, indices: List[str], output_file: str = None) -> Dict:
        """
        Comprehensive analytics report
        """
        print("📋 Comprehensive Analytics Report oluşturuluyor...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'detailed_analysis': {},
            'recommendations': []
        }
        
        try:
            # Sales analysis
            if 'sales' in indices:
                print("   💰 Sales Analytics...")
                sales_results = self.sales_analytics('sales')
                report['detailed_analysis']['sales'] = sales_results
                
                # Sales summary
                total_revenue = sales_results.get('total_revenue', AggregationResult("", "", 0)).value or 0
                avg_order_value = sales_results.get('avg_order_value', AggregationResult("", "", 0)).value or 0
                order_count = sales_results.get('order_count', AggregationResult("", "", 0)).value or 0
                
                report['summary']['sales'] = {
                    'total_revenue': total_revenue,
                    'avg_order_value': avg_order_value,
                    'order_count': order_count
                }
                
                # Recommendations
                if avg_order_value < 100:
                    report['recommendations'].append({
                        'category': 'sales',
                        'type': 'improvement',
                        'message': 'Average order value is low. Consider upselling strategies.',
                        'priority': 'medium'
                    })
            
            # Product analysis
            if 'products' in indices:
                print("   📦 Product Analytics...")
                product_results = self.product_analytics('products')
                report['detailed_analysis']['products'] = product_results
                
                # Low stock recommendations
                low_stock = product_results.get('low_stock_alert')
                if low_stock and low_stock.value > 10:
                    report['recommendations'].append({
                        'category': 'inventory',
                        'type': 'urgent',
                        'message': f"{low_stock.value} products need immediate restocking.",
                        'priority': 'high'
                    })
            
            # Customer analysis
            if 'customers' in indices:
                print("   👥 Customer Analytics...")
                customer_results = self.customer_analytics('customers')
                report['detailed_analysis']['customers'] = customer_results
                
                # Premium customer insights
                premium_customers = customer_results.get('premium_customers')
                if premium_customers:
                    report['summary']['customers'] = {
                        'premium_count': premium_customers.value,
                        'premium_contribution': premium_customers.metadata.get('total_value', 0)
                    }
            
            # Save report
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                print(f"📄 Report saved to: {output_file}")
            
            print(f"✅ Analytics report tamamlandı - {len(report['detailed_analysis'])} section, {len(report['recommendations'])} recommendation")
            return report
            
        except Exception as e:
            print(f"❌ Report generation hatası: {e}")
            return report

def demo_advanced_aggregations():
    """
    Advanced aggregations demo
    """
    print("📊 Elasticsearch Advanced Aggregations Demo")
    print("=" * 50)
    
    # Aggregations framework
    aggregations = ElasticsearchAggregations()
    
    # Sales analytics
    print("\n💰 Sales Analytics Demo:")
    sales_results = aggregations.sales_analytics()
    
    if sales_results:
        # Revenue metrics
        total_revenue = sales_results.get('total_revenue')
        if total_revenue:
            print(f"   📈 Total Revenue: ${total_revenue.value:,.2f}")
        
        avg_order = sales_results.get('avg_order_value')
        if avg_order:
            print(f"   🛒 Average Order Value: ${avg_order.value:.2f}")
        
        # Category performance
        category_perf = sales_results.get('category_performance')
        if category_perf and category_perf.buckets:
            print(f"   🏆 Top Categories:")
            for i, bucket in enumerate(category_perf.buckets[:3], 1):
                revenue = bucket['revenue']['value']
                count = bucket['doc_count']
                print(f"      {i}. {bucket['key']}: ${revenue:,.2f} ({count} orders)")
    
    # Product analytics
    print("\n📦 Product Analytics Demo:")
    product_results = aggregations.product_analytics()
    
    if product_results:
        # Inventory alerts
        low_stock = product_results.get('low_stock_alert')
        if low_stock:
            print(f"   ⚠️  Low Stock Alert: {low_stock.value} products")
        
        # Rating distribution
        rating_dist = product_results.get('rating_distribution')
        if rating_dist and rating_dist.buckets:
            print(f"   ⭐ Rating Distribution:")
            for bucket in rating_dist.buckets:
                print(f"      {bucket['key']}: {bucket['doc_count']} products")
    
    # Customer analytics
    print("\n👥 Customer Analytics Demo:")
    customer_results = aggregations.customer_analytics()
    
    if customer_results:
        # CLV segments
        clv_segments = customer_results.get('clv_segments')
        if clv_segments:
            print(f"   💎 Customer Value Segments:")
            for percentile, value in clv_segments.value.items():
                print(f"      {percentile}th percentile: ${value:.2f}")
        
        # Premium customers
        premium = customer_results.get('premium_customers')
        if premium:
            print(f"   🏆 Premium Customers: {premium.value}")
            if premium.metadata:
                total_value = premium.metadata.get('total_value', 0)
                print(f"      Total Value: ${total_value:,.2f}")
    
    # Real-time dashboard
    print("\n📊 Real-time Dashboard Demo:")
    dashboard_data = aggregations.real_time_dashboard_data(['sales', 'products', 'customers'])
    
    if dashboard_data.get('metrics'):
        print(f"   📈 Dashboard Metrics:")
        for category, metrics in dashboard_data['metrics'].items():
            print(f"      {category.upper()}:")
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    print(f"        {metric}: {value:,.2f}")
    
    if dashboard_data.get('alerts'):
        print(f"   🚨 Active Alerts: {len(dashboard_data['alerts'])}")
        for alert in dashboard_data['alerts']:
            print(f"      {alert['type'].upper()}: {alert['message']}")
    
    # Generate comprehensive report
    print("\n📋 Generating Comprehensive Report...")
    report = aggregations.generate_analytics_report(['sales', 'products', 'customers'])
    
    if report.get('recommendations'):
        print(f"   💡 Recommendations ({len(report['recommendations'])}):")
        for rec in report['recommendations']:
            priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
            print(f"      {priority_icon} {rec['category'].upper()}: {rec['message']}")
    
    print("\n✅ Advanced aggregations demo tamamlandı!")

if __name__ == "__main__":
    demo_advanced_aggregations()