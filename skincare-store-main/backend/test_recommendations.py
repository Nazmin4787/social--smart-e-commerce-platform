"""
Test script for AI Recommendation System
Run: python manage.py shell < test_recommendations.py
"""

print("=" * 60)
print("Testing AI Recommendation System")
print("=" * 60)

# Test 1: Get system statistics
print("\n1. Testing system statistics...")
from api.recommender import get_recommendation_stats

stats = get_recommendation_stats()
print(f"   Total Users: {stats['total_users']}")
print(f"   Total Products: {stats['total_products']}")
print(f"   Total Likes: {stats['total_likes']}")
print(f"   Total Purchases: {stats['total_purchases']}")
print(f"   Total Reviews: {stats['total_reviews']}")
print(f"   Total Follows: {stats['total_follows']}")
print(f"   Avg Interactions/User: {stats['avg_interactions_per_user']:.2f}")

# Test 2: Build feature vectors
print("\n2. Building product feature vectors...")
from api.recommender import ProductFeatureVector

vectorizer, feature_matrix, product_ids = ProductFeatureVector.build_feature_vectors()
if feature_matrix is not None:
    print(f"   ✓ Built feature vectors for {len(product_ids)} products")
    print(f"   Feature matrix shape: {feature_matrix.shape}")
else:
    print("   ✗ No products found")

# Test 3: Test similar products
print("\n3. Testing content-based filtering (similar products)...")
from api.recommender import ContentBasedRecommender
from api.models import Product

products = Product.objects.all()[:5]
if products:
    for product in products:
        similar = ContentBasedRecommender.get_similar_products(product.id, top_n=3)
        print(f"   Product: {product.title} (ID: {product.id})")
        print(f"   Similar products found: {len(similar)}")
        for sim in similar[:2]:
            print(f"     - Product ID {sim['product_id']} (similarity: {sim['similarity_score']:.3f})")
else:
    print("   No products available")

# Test 4: Test user recommendations
print("\n4. Testing hybrid recommendations for users...")
from api.recommender import HybridRecommender, DataExporter
from api.models import AppUser

users_with_history = []
for user in AppUser.objects.all()[:10]:
    history = DataExporter.get_user_history(user.id)
    if history['all']:
        users_with_history.append((user, len(history['all'])))

if users_with_history:
    # Test with user who has most interactions
    test_user, interaction_count = max(users_with_history, key=lambda x: x[1])
    print(f"   Testing with user: {test_user.name} (ID: {test_user.id})")
    print(f"   User has {interaction_count} interactions")
    
    recommendations = HybridRecommender.get_personalized_recommendations(test_user.id, top_n=5)
    print(f"   Generated {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"     {i}. {rec['product']['title']}")
        print(f"        Score: {rec['recommendation_score']:.3f}")
        print(f"        Sources: {', '.join(rec['sources'])}")
else:
    print("   No users with interaction history found")

# Test 5: Test cold start recommendations
print("\n5. Testing cold start recommendations...")
cold_start = HybridRecommender.get_cold_start_recommendations(top_n=5)
print(f"   Generated {len(cold_start)} cold start recommendations")
for i, rec in enumerate(cold_start[:3], 1):
    print(f"     {i}. {rec['product']['title']} (Sources: {', '.join(rec['sources'])})")

# Test 6: Test social recommendations
print("\n6. Testing social recommendations...")
from api.recommender import SocialRecommender

users_with_friends = []
for user in AppUser.objects.all()[:10]:
    friends = DataExporter.get_user_friends(user.id)
    if friends:
        users_with_friends.append((user, len(friends)))

if users_with_friends:
    test_user, friend_count = users_with_friends[0]
    print(f"   Testing with user: {test_user.name} (has {friend_count} friends)")
    
    friends_recs = SocialRecommender.get_friends_recommendations(test_user.id, top_n=5)
    print(f"   Generated {len(friends_recs)} friend-based recommendations")
    
    trending = SocialRecommender.get_trending_among_friends(test_user.id, top_n=5)
    print(f"   Found {len(trending)} trending products among friends")
else:
    print("   No users with friends found")

# Test 7: Test cache functions
print("\n7. Testing cache functions...")
from api.recommender import invalidate_user_recommendation_cache, warm_user_recommendation_cache

if AppUser.objects.exists():
    test_user = AppUser.objects.first()
    print(f"   Testing cache for user: {test_user.name} (ID: {test_user.id})")
    
    # Warm cache
    success = warm_user_recommendation_cache(test_user.id)
    if success:
        print("   ✓ Cache warmed successfully")
    else:
        print("   ✗ Cache warming failed")
    
    # Invalidate cache
    invalidate_user_recommendation_cache(test_user.id)
    print("   ✓ Cache invalidated successfully")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
