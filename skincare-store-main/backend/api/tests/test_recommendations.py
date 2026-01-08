"""
Unit tests for AI Recommendation System
Run: python manage.py test api.tests.test_recommendations
"""

import json
from django.test import TestCase, Client
from django.core.cache import cache
from api.models import (
    Product, AppUser, UserLikedProduct, Order, OrderItem, 
    Review, UserFollow, Cart
)
from api.recommender import (
    DataExporter,
    ContentBasedRecommender,
    CollaborativeFilteringRecommender,
    SocialRecommender,
    HybridRecommender,
    ProductFeatureVector,
    invalidate_user_recommendation_cache,
    warm_user_recommendation_cache,
    get_recommendation_stats
)
from api.utils import create_jwt


class RecommenderDataExporterTest(TestCase):
    """Test DataExporter class functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = AppUser.objects.create(
            name="Test User 1",
            email="user1@test.com",
            password="password123"
        )
        self.user2 = AppUser.objects.create(
            name="Test User 2",
            email="user2@test.com",
            password="password123"
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            title="Moisturizer",
            description="Hydrating moisturizer",
            price=29.99,
            stock=100,
            category="moisturizer",
            ingredients=["hyaluronic acid", "glycerin"],
            benefits=["hydration", "anti-aging"]
        )
        self.product2 = Product.objects.create(
            title="Cleanser",
            description="Gentle cleanser",
            price=19.99,
            stock=50,
            category="cleanser",
            ingredients=["salicylic acid"],
            benefits=["cleansing", "acne control"]
        )
        self.product3 = Product.objects.create(
            title="Serum",
            description="Vitamin C serum",
            price=39.99,
            stock=75,
            category="serum",
            ingredients=["vitamin c", "hyaluronic acid"],
            benefits=["brightening", "anti-aging"]
        )
    
    def test_get_user_product_interactions(self):
        """Test user-product interaction matrix generation."""
        # Add likes
        UserLikedProduct.objects.create(user=self.user1, product=self.product1)
        
        # Add review
        Review.objects.create(user=self.user1, product=self.product2, rating=5, comment="Great!")
        
        # Get interactions
        interactions = DataExporter.get_user_product_interactions(self.user1.id)
        
        self.assertIn(self.user1.id, interactions)
        user_interactions = interactions[self.user1.id]
        
        # Like = 1 point
        self.assertEqual(user_interactions[self.product1.id], 1.0)
        
        # 5-star review = 2 points
        self.assertEqual(user_interactions[self.product2.id], 2.0)
    
    def test_get_product_features(self):
        """Test product feature extraction."""
        features = DataExporter.get_product_features()
        
        self.assertIn(self.product1.id, features)
        
        product_features = features[self.product1.id]
        self.assertEqual(product_features['title'], 'Moisturizer')
        self.assertEqual(product_features['category'], 'moisturizer')
        self.assertIn('hyaluronic acid', product_features['text_features'])
        # Price is 29.99, which falls in mid-range (20-50)
        self.assertIn('mid-range', product_features['price_tier'])
    
    def test_get_user_friends(self):
        """Test friends list retrieval."""
        # Create follow relationship
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        
        friends = DataExporter.get_user_friends(self.user1.id)
        
        self.assertEqual(len(friends), 1)
        self.assertIn(self.user2.id, friends)
    
    def test_get_user_history(self):
        """Test user history tracking."""
        # Add different interaction types
        UserLikedProduct.objects.create(user=self.user1, product=self.product1)
        Review.objects.create(user=self.user1, product=self.product2, rating=4)
        
        history = DataExporter.get_user_history(self.user1.id)
        
        self.assertEqual(len(history['liked']), 1)
        self.assertIn(self.product1.id, history['liked'])
        
        self.assertEqual(len(history['reviewed']), 1)
        self.assertIn(self.product2.id, history['reviewed'])
        
        self.assertEqual(len(history['all']), 2)


class ContentBasedRecommenderTest(TestCase):
    """Test content-based filtering recommendations."""
    
    def setUp(self):
        """Set up test data."""
        self.user = AppUser.objects.create(
            name="Test User",
            email="test@test.com",
            password="password123"
        )
        
        # Create products with similar features
        self.product1 = Product.objects.create(
            title="Anti-Aging Moisturizer",
            price=49.99,
            stock=100,
            category="moisturizer",
            ingredients=["retinol", "hyaluronic acid"],
            benefits=["anti-aging", "hydration"]
        )
        self.product2 = Product.objects.create(
            title="Hydrating Night Cream",
            price=39.99,
            stock=50,
            category="moisturizer",
            ingredients=["hyaluronic acid", "peptides"],
            benefits=["hydration", "anti-aging"]
        )
        self.product3 = Product.objects.create(
            title="Acne Cleanser",
            price=19.99,
            stock=75,
            category="cleanser",
            ingredients=["salicylic acid"],
            benefits=["acne control", "cleansing"]
        )
        
        # Build feature vectors
        ProductFeatureVector.build_feature_vectors()
    
    def test_get_similar_products(self):
        """Test finding similar products."""
        similar = ContentBasedRecommender.get_similar_products(self.product1.id, top_n=5)
        
        self.assertIsInstance(similar, list)
        
        if len(similar) > 0:
            # Most similar should be product2 (both moisturizers with similar ingredients)
            similar_ids = [item['product_id'] for item in similar]
            self.assertIn(self.product2.id, similar_ids)
            
            # Check similarity scores
            for item in similar:
                self.assertIn('product_id', item)
                self.assertIn('similarity_score', item)
                self.assertGreater(item['similarity_score'], 0)
    
    def test_get_recommendations_for_user(self):
        """Test user-based content recommendations."""
        # User likes product1
        UserLikedProduct.objects.create(user=self.user, product=self.product1)
        
        recommendations = ContentBasedRecommender.get_recommendations_for_user(
            self.user.id, top_n=5
        )
        
        self.assertIsInstance(recommendations, list)
        
        # Should not recommend already liked products
        recommended_ids = [rec['product_id'] for rec in recommendations]
        self.assertNotIn(self.product1.id, recommended_ids)


class CollaborativeFilteringTest(TestCase):
    """Test collaborative filtering recommendations."""
    
    def setUp(self):
        """Set up test data with multiple users and products."""
        # Create users
        self.user1 = AppUser.objects.create(name="User 1", email="user1@test.com")
        self.user2 = AppUser.objects.create(name="User 2", email="user2@test.com")
        self.user3 = AppUser.objects.create(name="User 3", email="user3@test.com")
        
        # Create products
        self.product1 = Product.objects.create(title="Product 1", price=20, stock=100)
        self.product2 = Product.objects.create(title="Product 2", price=30, stock=100)
        self.product3 = Product.objects.create(title="Product 3", price=40, stock=100)
        self.product4 = Product.objects.create(title="Product 4", price=50, stock=100)
        
        # Create similar interaction patterns for user1 and user2
        UserLikedProduct.objects.create(user=self.user1, product=self.product1)
        UserLikedProduct.objects.create(user=self.user1, product=self.product2)
        
        UserLikedProduct.objects.create(user=self.user2, product=self.product1)
        UserLikedProduct.objects.create(user=self.user2, product=self.product2)
        UserLikedProduct.objects.create(user=self.user2, product=self.product3)
        
        # User3 has different pattern
        UserLikedProduct.objects.create(user=self.user3, product=self.product4)
    
    def test_find_similar_users(self):
        """Test finding users with similar taste."""
        similar_users = CollaborativeFilteringRecommender.find_similar_users(
            self.user1.id, top_n=5
        )
        
        self.assertIsInstance(similar_users, list)
        
        if len(similar_users) > 0:
            # User2 should be most similar to User1
            most_similar_id = similar_users[0][0]
            self.assertEqual(most_similar_id, self.user2.id)
            
            # User3 should not be similar (different interaction pattern)
            similar_ids = [uid for uid, score in similar_users]
            self.assertNotIn(self.user3.id, similar_ids)
    
    def test_get_user_based_recommendations(self):
        """Test user-based collaborative filtering."""
        recommendations = CollaborativeFilteringRecommender.get_user_based_recommendations(
            self.user1.id, top_n=5
        )
        
        self.assertIsInstance(recommendations, list)
        
        if len(recommendations) > 0:
            # Should recommend product3 (liked by similar user2)
            recommended_ids = [rec['product_id'] for rec in recommendations]
            self.assertIn(self.product3.id, recommended_ids)
            
            # Should not recommend already interacted products
            self.assertNotIn(self.product1.id, recommended_ids)
            self.assertNotIn(self.product2.id, recommended_ids)


class SocialRecommenderTest(TestCase):
    """Test social-based recommendations."""
    
    def setUp(self):
        """Set up test data with social relationships."""
        # Create users
        self.user1 = AppUser.objects.create(name="User 1", email="user1@test.com")
        self.user2 = AppUser.objects.create(name="User 2", email="user2@test.com")
        self.user3 = AppUser.objects.create(name="User 3", email="user3@test.com")
        
        # Create products
        self.product1 = Product.objects.create(title="Product 1", price=20, stock=100)
        self.product2 = Product.objects.create(title="Product 2", price=30, stock=100)
        self.product3 = Product.objects.create(title="Product 3", price=40, stock=100)
        
        # Create follow relationships
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        UserFollow.objects.create(follower=self.user1, following=self.user3)
        
        # Friends' activities
        UserLikedProduct.objects.create(user=self.user2, product=self.product1)
        UserLikedProduct.objects.create(user=self.user3, product=self.product2)
    
    def test_get_friends_recommendations(self):
        """Test recommendations based on friends' activities."""
        recommendations = SocialRecommender.get_friends_recommendations(
            self.user1.id, top_n=10
        )
        
        self.assertIsInstance(recommendations, list)
        
        if len(recommendations) > 0:
            # Should recommend products liked by friends
            recommended_ids = [rec['product_id'] for rec in recommendations]
            self.assertTrue(
                self.product1.id in recommended_ids or 
                self.product2.id in recommended_ids
            )
    
    def test_get_trending_among_friends(self):
        """Test trending products among friends."""
        trending = SocialRecommender.get_trending_among_friends(
            self.user1.id, top_n=10
        )
        
        self.assertIsInstance(trending, list)


class HybridRecommenderTest(TestCase):
    """Test hybrid recommendation system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = AppUser.objects.create(
            name="Test User",
            email="test@test.com"
        )
        
        # Create products
        for i in range(5):
            Product.objects.create(
                title=f"Product {i}",
                price=20 + i * 10,
                stock=100,
                category="test"
            )
    
    def test_get_personalized_recommendations(self):
        """Test hybrid personalized recommendations."""
        # Add some user history
        product = Product.objects.first()
        UserLikedProduct.objects.create(user=self.user, product=product)
        
        recommendations = HybridRecommender.get_personalized_recommendations(
            self.user.id, top_n=10
        )
        
        self.assertIsInstance(recommendations, list)
        
        if len(recommendations) > 0:
            # Check structure
            rec = recommendations[0]
            self.assertIn('product', rec)
            self.assertIn('recommendation_score', rec)
            self.assertIn('sources', rec)
            self.assertIsInstance(rec['sources'], list)
    
    def test_get_cold_start_recommendations(self):
        """Test cold start recommendations for new users."""
        recommendations = HybridRecommender.get_cold_start_recommendations(top_n=10)
        
        self.assertIsInstance(recommendations, list)
        
        if len(recommendations) > 0:
            # Check structure
            rec = recommendations[0]
            self.assertIn('product', rec)
            self.assertIn('sources', rec)
            self.assertIn('cold_start', rec['sources'])


class RecommendationAPITest(TestCase):
    """Test recommendation API endpoints."""
    
    def setUp(self):
        """Set up test client and data."""
        self.client = Client()
        
        # Create test user
        self.user = AppUser.objects.create(
            name="Test User",
            email="test@test.com"
        )
        self.user.set_password("password123")
        self.user.save()
        
        # Create products
        for i in range(10):
            Product.objects.create(
                title=f"Product {i}",
                description=f"Description {i}",
                price=20 + i * 5,
                stock=100,
                category="skincare"
            )
        
        # Generate JWT token
        self.token = create_jwt({"user_id": self.user.id, "email": self.user.email})
        self.auth_header = f"Bearer {self.token}"
        
        # Clear cache
        cache.clear()
    
    def test_personalized_recommendations_authenticated(self):
        """Test personalized recommendations endpoint with authentication."""
        response = self.client.get(
            '/api/recommendations/personalized/',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('recommendations', data)
        self.assertIn('count', data)
        self.assertIsInstance(data['recommendations'], list)
    
    def test_personalized_recommendations_unauthorized(self):
        """Test personalized recommendations without authentication."""
        response = self.client.get('/api/recommendations/personalized/')
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)
    
    def test_similar_products_public(self):
        """Test similar products endpoint (public)."""
        product = Product.objects.first()
        
        # Build feature vectors first
        ProductFeatureVector.build_feature_vectors()
        
        response = self.client.get(f'/api/recommendations/similar/{product.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('similar_products', data)
        self.assertEqual(data['product_id'], product.id)
    
    def test_similar_products_invalid_id(self):
        """Test similar products with invalid product ID."""
        response = self.client.get('/api/recommendations/similar/99999/')
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
    
    def test_friends_trending_authenticated(self):
        """Test friends trending endpoint with authentication."""
        response = self.client.get(
            '/api/recommendations/friends-trending/',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('trending_products', data)
    
    def test_friends_trending_unauthorized(self):
        """Test friends trending without authentication."""
        response = self.client.get('/api/recommendations/friends-trending/')
        
        self.assertEqual(response.status_code, 401)
    
    def test_recommendation_stats_admin_only(self):
        """Test recommendation stats endpoint (admin only)."""
        # Non-admin user should get 403
        response = self.client.get(
            '/api/recommendations/stats/',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, 403)
        
        # Make user admin
        self.user.is_staff = True
        self.user.save()
        
        response = self.client.get(
            '/api/recommendations/stats/',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('stats', data)


class CacheFunctionsTest(TestCase):
    """Test cache management functions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = AppUser.objects.create(
            name="Test User",
            email="test@test.com"
        )
        
        self.product = Product.objects.create(
            title="Test Product",
            price=29.99,
            stock=100
        )
        
        cache.clear()
    
    def test_invalidate_user_cache(self):
        """Test user cache invalidation."""
        # Set some cache values
        cache.set(f'recommendations_user_{self.user.id}_limit_20', {'test': 'data'}, 3600)
        
        # Verify cache exists
        self.assertIsNotNone(cache.get(f'recommendations_user_{self.user.id}_limit_20'))
        
        # Invalidate
        invalidate_user_recommendation_cache(self.user.id)
        
        # Verify cache is cleared
        self.assertIsNone(cache.get(f'recommendations_user_{self.user.id}_limit_20'))
    
    def test_warm_user_cache(self):
        """Test warming user cache."""
        # Add some user history
        UserLikedProduct.objects.create(user=self.user, product=self.product)
        
        # Warm cache
        success = warm_user_recommendation_cache(self.user.id)
        
        self.assertTrue(success)
        
        # Verify cache is populated
        cached_data = cache.get(f'recommendations_user_{self.user.id}_limit_20')
        self.assertIsNotNone(cached_data)
        self.assertTrue(cached_data['success'])


class UtilityFunctionsTest(TestCase):
    """Test utility functions."""
    
    def test_get_recommendation_stats(self):
        """Test recommendation statistics function."""
        # Create test data
        user = AppUser.objects.create(name="User", email="user@test.com")
        product = Product.objects.create(title="Product", price=20, stock=100)
        UserLikedProduct.objects.create(user=user, product=product)
        
        stats = get_recommendation_stats()
        
        self.assertIn('total_users', stats)
        self.assertIn('total_products', stats)
        self.assertIn('total_likes', stats)
        self.assertIn('avg_interactions_per_user', stats)
        
        self.assertGreater(stats['total_users'], 0)
        self.assertGreater(stats['total_products'], 0)
        self.assertGreater(stats['total_likes'], 0)
