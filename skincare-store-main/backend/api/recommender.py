"""
AI-Powered Product Recommendation System
Provides personalized product recommendations using:
- Content-Based Filtering (CBF)
- Collaborative Filtering (CF)
- Social Network Integration
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from django.db.models import Count, Q, Avg
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime, timedelta

from .models import (
    Product, AppUser, UserLikedProduct, Order, OrderItem, 
    Review, UserFollow
)


class DataExporter:
    """Export and prepare data for recommendation algorithms."""
    
    @staticmethod
    def get_user_product_interactions(user_id=None):
        """
        Create User-Product Interaction Matrix.
        Returns a dictionary with user_id as key and their interaction data.
        
        Interaction types:
        - Likes: 1 point
        - Purchase: 3 points
        - Review (5 stars): 2 points, (4 stars): 1.5 points, etc.
        """
        interactions = defaultdict(lambda: defaultdict(float))
        
        # Get all users or specific user
        users = [user_id] if user_id else AppUser.objects.values_list('id', flat=True)
        
        for uid in users:
            # 1. Liked Products (1 point each)
            liked_products = UserLikedProduct.objects.filter(user_id=uid).values_list('product_id', flat=True)
            for product_id in liked_products:
                interactions[uid][product_id] += 1.0
            
            # 2. Purchased Products (3 points each)
            purchased_products = OrderItem.objects.filter(
                order__user_id=uid,
                order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
            ).values_list('product_id', flat=True)
            for product_id in purchased_products:
                interactions[uid][product_id] += 3.0
            
            # 3. Reviewed Products (weighted by rating)
            reviews = Review.objects.filter(user_id=uid).values('product_id', 'rating')
            for review in reviews:
                # Rating weight: 5 stars = 2 points, 1 star = 0.4 points
                weight = (review['rating'] / 5.0) * 2.0
                interactions[uid][review['product_id']] += weight
        
        return dict(interactions)
    
    @staticmethod
    def get_interaction_matrix():
        """
        Create a full User-Product interaction matrix as DataFrame.
        Rows: Users, Columns: Products, Values: Interaction scores
        """
        interactions = DataExporter.get_user_product_interactions()
        
        if not interactions:
            return pd.DataFrame()
        
        # Get all unique products
        all_products = set()
        for user_items in interactions.values():
            all_products.update(user_items.keys())
        
        # Create matrix
        matrix_data = []
        for user_id, products in interactions.items():
            row = {'user_id': user_id}
            for product_id in all_products:
                row[f'product_{product_id}'] = products.get(product_id, 0.0)
            matrix_data.append(row)
        
        df = pd.DataFrame(matrix_data)
        df.set_index('user_id', inplace=True)
        return df
    
    @staticmethod
    def get_product_features():
        """
        Create Product-Feature Matrix for content-based filtering.
        Returns a dictionary with product_id as key and features.
        
        Features include:
        - Category
        - Ingredients (list)
        - Benefits (list)
        - Average rating
        - Price tier (budget/mid/premium)
        """
        products = Product.objects.all()
        product_features = {}
        
        for product in products:
            # Combine text features for vectorization
            text_features = []
            
            # Add category
            if product.category:
                text_features.append(product.category)
            
            # Add ingredients
            if product.ingredients:
                text_features.extend(product.ingredients)
            
            # Add benefits
            if product.benefits:
                text_features.extend(product.benefits)
            
            # Price tier
            price = float(product.price)
            if price < 20:
                price_tier = "budget"
            elif price < 50:
                price_tier = "mid-range"
            else:
                price_tier = "premium"
            text_features.append(price_tier)
            
            # Store features
            product_features[product.id] = {
                'id': product.id,
                'title': product.title,
                'category': product.category,
                'ingredients': product.ingredients,
                'benefits': product.benefits,
                'price': price,
                'price_tier': price_tier,
                'text_features': ' '.join(text_features),
                'average_rating': product.average_rating() or 0,
            }
        
        return product_features
    
    @staticmethod
    def get_product_feature_matrix():
        """
        Create a DataFrame with product features for similarity calculations.
        """
        features = DataExporter.get_product_features()
        
        if not features:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(features, orient='index')
        return df
    
    @staticmethod
    def get_user_friends(user_id):
        """
        Get list of user IDs that the given user is following.
        """
        friend_ids = UserFollow.objects.filter(
            follower_id=user_id
        ).values_list('following_id', flat=True)
        
        return list(friend_ids)
    
    @staticmethod
    def get_friends_interactions(user_id):
        """
        Get products that user's friends have interacted with.
        Returns a dictionary with product_id and aggregated scores.
        """
        friend_ids = DataExporter.get_user_friends(user_id)
        
        if not friend_ids:
            return {}
        
        friends_interactions = defaultdict(float)
        
        for friend_id in friend_ids:
            friend_interactions = DataExporter.get_user_product_interactions(friend_id)
            
            # Aggregate friend interactions with a social weight (0.5x)
            for product_id, score in friend_interactions.get(friend_id, {}).items():
                friends_interactions[product_id] += score * 0.5
        
        return dict(friends_interactions)
    
    @staticmethod
    def get_trending_products(days=7, limit=20):
        """
        Get trending products based on recent activity.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Count recent interactions
        trending_scores = defaultdict(int)
        
        # Recent likes
        recent_likes = UserLikedProduct.objects.filter(
            created_at__gte=cutoff_date
        ).values('product_id').annotate(count=Count('id'))
        
        for item in recent_likes:
            trending_scores[item['product_id']] += item['count'] * 1
        
        # Recent orders
        recent_orders = OrderItem.objects.filter(
            order__created_at__gte=cutoff_date,
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).values('product_id').annotate(count=Count('id'))
        
        for item in recent_orders:
            trending_scores[item['product_id']] += item['count'] * 3
        
        # Recent reviews
        recent_reviews = Review.objects.filter(
            created_at__gte=cutoff_date
        ).values('product_id').annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        )
        
        for item in recent_reviews:
            trending_scores[item['product_id']] += item['count'] * (item['avg_rating'] or 0)
        
        # Sort and return top products
        sorted_products = sorted(
            trending_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        return [product_id for product_id, score in sorted_products]
    
    @staticmethod
    def get_user_history(user_id):
        """
        Get a user's complete interaction history.
        Returns sets of product IDs for different interaction types.
        """
        liked = set(UserLikedProduct.objects.filter(
            user_id=user_id
        ).values_list('product_id', flat=True))
        
        purchased = set(OrderItem.objects.filter(
            order__user_id=user_id,
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).values_list('product_id', flat=True))
        
        reviewed = set(Review.objects.filter(
            user_id=user_id
        ).values_list('product_id', flat=True))
        
        return {
            'liked': liked,
            'purchased': purchased,
            'reviewed': reviewed,
            'all': liked | purchased | reviewed
        }


class ProductFeatureVector:
    """Generate and cache product feature vectors for content-based filtering."""
    
    _vectorizer = None
    _feature_matrix = None
    _product_ids = None
    
    @classmethod
    def build_feature_vectors(cls):
        """Build TF-IDF vectors from product text features."""
        product_features = DataExporter.get_product_features()
        
        if not product_features:
            return None, None, None
        
        # Extract text features
        texts = []
        product_ids = []
        
        for product_id, features in product_features.items():
            texts.append(features['text_features'])
            product_ids.append(product_id)
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        feature_matrix = vectorizer.fit_transform(texts)
        
        # Cache results
        cls._vectorizer = vectorizer
        cls._feature_matrix = feature_matrix
        cls._product_ids = product_ids
        
        return vectorizer, feature_matrix, product_ids
    
    @classmethod
    def get_feature_vectors(cls):
        """Get cached feature vectors or build if not available."""
        if cls._feature_matrix is None:
            cls.build_feature_vectors()
        
        return cls._vectorizer, cls._feature_matrix, cls._product_ids


# Statistics and debugging functions
def get_recommendation_stats():
    """Get statistics about the recommendation system data."""
    total_users = AppUser.objects.count()
    total_products = Product.objects.count()
    total_likes = UserLikedProduct.objects.count()
    total_purchases = OrderItem.objects.filter(
        order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
    ).count()
    total_reviews = Review.objects.count()
    total_follows = UserFollow.objects.count()
    
    return {
        'total_users': total_users,
        'total_products': total_products,
        'total_likes': total_likes,
        'total_purchases': total_purchases,
        'total_reviews': total_reviews,
        'total_follows': total_follows,
        'avg_interactions_per_user': (total_likes + total_purchases + total_reviews) / max(total_users, 1),
    }


# Cache management functions
def invalidate_user_recommendation_cache(user_id):
    """
    Invalidate cached recommendations for a specific user.
    Call this when user performs actions that affect recommendations:
    - Likes/unlikes a product
    - Makes a purchase
    - Adds a review
    - Follows/unfollows someone
    """
    from django.core.cache import cache
    
    # Invalidate personalized recommendations
    for limit in [10, 20, 30, 50]:
        cache_key = f'recommendations_user_{user_id}_limit_{limit}'
        cache.delete(cache_key)
    
    # Invalidate friends trending
    for limit in [15, 30]:
        cache_key = f'friends_trending_user_{user_id}_limit_{limit}'
        cache.delete(cache_key)


def invalidate_product_similarity_cache(product_id):
    """
    Invalidate cached similar products for a specific product.
    Call this when product details change significantly.
    """
    from django.core.cache import cache
    
    for limit in [5, 10, 15, 20]:
        cache_key = f'similar_products_{product_id}_limit_{limit}'
        cache.delete(cache_key)


def warm_user_recommendation_cache(user_id):
    """
    Pre-calculate and cache recommendations for a user.
    Useful after user performs significant actions.
    """
    from django.core.cache import cache
    
    try:
        user_history = DataExporter.get_user_history(user_id)
        
        for limit in [10, 20, 30]:
            cache_key = f'recommendations_user_{user_id}_limit_{limit}'
            
            if not user_history['all']:
                recommendations = HybridRecommender.get_cold_start_recommendations(top_n=limit)
            else:
                recommendations = HybridRecommender.get_personalized_recommendations(user_id, top_n=limit)
            
            result = {
                "success": True,
                "count": len(recommendations),
                "recommendations": recommendations,
                "user_has_history": bool(user_history['all'])
            }
            
            cache.set(cache_key, result, 3600)  # 1 hour
        
        return True
    except Exception:
        return False


class ContentBasedRecommender:
    """Content-Based Filtering: Recommend products similar to ones user liked."""
    
    @staticmethod
    def get_similar_products(product_id, top_n=10):
        """
        Find products similar to the given product based on features.
        Returns list of (product_id, similarity_score) tuples.
        """
        vectorizer, feature_matrix, product_ids = ProductFeatureVector.get_feature_vectors()
        
        if feature_matrix is None or product_id not in product_ids:
            return []
        
        # Get index of the target product
        try:
            product_idx = product_ids.index(product_id)
        except ValueError:
            return []
        
        # Calculate cosine similarity between this product and all others
        product_vector = feature_matrix[product_idx]
        similarities = cosine_similarity(product_vector, feature_matrix).flatten()
        
        # Get top N similar products (excluding the product itself)
        similar_indices = similarities.argsort()[::-1][1:top_n+1]
        
        recommendations = []
        for idx in similar_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                recommendations.append({
                    'product_id': product_ids[idx],
                    'similarity_score': float(similarities[idx])
                })
        
        return recommendations
    
    @staticmethod
    def get_recommendations_for_user(user_id, top_n=20):
        """
        Recommend products based on user's liked/purchased products.
        Aggregates similar products from all user interactions.
        """
        user_history = DataExporter.get_user_history(user_id)
        all_interacted = user_history['all']
        
        if not all_interacted:
            return []
        
        # Get user's interaction scores to weight recommendations
        user_interactions = DataExporter.get_user_product_interactions(user_id)
        user_scores = user_interactions.get(user_id, {})
        
        # Aggregate similarity scores from all interacted products
        aggregated_scores = defaultdict(float)
        
        for product_id in all_interacted:
            # Get weight based on interaction type
            interaction_weight = user_scores.get(product_id, 1.0)
            
            # Get similar products
            similar_products = ContentBasedRecommender.get_similar_products(product_id, top_n=15)
            
            for item in similar_products:
                similar_id = item['product_id']
                
                # Don't recommend products user already interacted with
                if similar_id not in all_interacted:
                    # Weighted score: similarity * interaction_strength
                    aggregated_scores[similar_id] += item['similarity_score'] * interaction_weight
        
        # Sort by aggregated score
        sorted_recommendations = sorted(
            aggregated_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {'product_id': pid, 'score': score, 'source': 'content_based'}
            for pid, score in sorted_recommendations
        ]


class CollaborativeFilteringRecommender:
    """Collaborative Filtering: Recommend based on similar users' preferences."""
    
    @staticmethod
    def find_similar_users(user_id, top_n=10):
        """
        Find users with similar taste using cosine similarity on interaction vectors.
        Returns list of (user_id, similarity_score) tuples.
        """
        # Get interaction matrix
        all_interactions = DataExporter.get_user_product_interactions()
        
        if user_id not in all_interactions:
            return []
        
        target_user_products = all_interactions[user_id]
        
        if not target_user_products:
            return []
        
        # Calculate similarity with all other users
        similarities = []
        
        for other_user_id, other_products in all_interactions.items():
            if other_user_id == user_id or not other_products:
                continue
            
            # Find common products
            common_products = set(target_user_products.keys()) & set(other_products.keys())
            
            if len(common_products) < 2:  # Need at least 2 common products
                continue
            
            # Calculate cosine similarity on common products
            target_vector = [target_user_products[p] for p in common_products]
            other_vector = [other_products[p] for p in common_products]
            
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(target_vector, other_vector))
            magnitude_target = sum(a ** 2 for a in target_vector) ** 0.5
            magnitude_other = sum(b ** 2 for b in other_vector) ** 0.5
            
            if magnitude_target > 0 and magnitude_other > 0:
                similarity = dot_product / (magnitude_target * magnitude_other)
                
                if similarity > 0.3:  # Minimum similarity threshold
                    similarities.append((other_user_id, similarity))
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    @staticmethod
    def get_user_based_recommendations(user_id, top_n=20):
        """
        User-Based Collaborative Filtering.
        Recommend products that similar users liked but target user hasn't interacted with.
        """
        # Find similar users
        similar_users = CollaborativeFilteringRecommender.find_similar_users(user_id, top_n=15)
        
        if not similar_users:
            return []
        
        # Get target user's history
        user_history = DataExporter.get_user_history(user_id)
        already_interacted = user_history['all']
        
        # Get all interactions
        all_interactions = DataExporter.get_user_product_interactions()
        
        # Aggregate product scores from similar users
        product_scores = defaultdict(float)
        
        for similar_user_id, similarity_score in similar_users:
            similar_user_products = all_interactions.get(similar_user_id, {})
            
            for product_id, interaction_score in similar_user_products.items():
                # Skip products user already interacted with
                if product_id not in already_interacted:
                    # Weight by similarity and interaction strength
                    product_scores[product_id] += similarity_score * interaction_score
        
        # Sort and return top recommendations
        sorted_recommendations = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {'product_id': pid, 'score': score, 'source': 'collaborative_filtering'}
            for pid, score in sorted_recommendations
        ]
    
    @staticmethod
    def get_item_based_recommendations(user_id, top_n=20):
        """
        Item-Based Collaborative Filtering.
        Find products frequently bought together with user's liked products.
        """
        user_history = DataExporter.get_user_history(user_id)
        user_products = user_history['all']
        
        if not user_products:
            return []
        
        # Find products that were bought together with user's products
        product_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        # Get all orders
        orders = Order.objects.filter(
            status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).prefetch_related('items')
        
        for order in orders:
            order_products = [item.product_id for item in order.items.all()]
            
            # Count co-occurrences
            for i, prod1 in enumerate(order_products):
                for prod2 in order_products[i+1:]:
                    product_cooccurrence[prod1][prod2] += 1
                    product_cooccurrence[prod2][prod1] += 1
        
        # Find products frequently bought with user's products
        recommendation_scores = defaultdict(float)
        
        for user_product in user_products:
            if user_product in product_cooccurrence:
                for related_product, count in product_cooccurrence[user_product].items():
                    # Don't recommend products user already has
                    if related_product not in user_products:
                        recommendation_scores[related_product] += count
        
        # Sort and return top recommendations
        sorted_recommendations = sorted(
            recommendation_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {'product_id': pid, 'score': float(score), 'source': 'item_based_cf'}
            for pid, score in sorted_recommendations
        ]


class SocialRecommender:
    """Social-based recommendations using friends' activity."""
    
    @staticmethod
    def get_friends_recommendations(user_id, top_n=20):
        """
        Recommend products that user's friends have purchased or liked.
        Weighted by recency and interaction type.
        """
        friend_ids = DataExporter.get_user_friends(user_id)
        
        if not friend_ids:
            return []
        
        # Get user's history to exclude
        user_history = DataExporter.get_user_history(user_id)
        already_interacted = user_history['all']
        
        # Get friends' interactions
        product_scores = defaultdict(float)
        
        for friend_id in friend_ids:
            friend_interactions = DataExporter.get_user_product_interactions(friend_id)
            
            for product_id, score in friend_interactions.get(friend_id, {}).items():
                if product_id not in already_interacted:
                    # Social weight: 0.7x (slightly lower than own preference)
                    product_scores[product_id] += score * 0.7
        
        # Boost by recency of friend activity
        recent_cutoff = datetime.now() - timedelta(days=30)
        
        # Recent friend likes
        recent_friend_likes = UserLikedProduct.objects.filter(
            user_id__in=friend_ids,
            created_at__gte=recent_cutoff
        ).values('product_id').annotate(count=Count('id'))
        
        for item in recent_friend_likes:
            if item['product_id'] not in already_interacted:
                product_scores[item['product_id']] += item['count'] * 0.3
        
        # Sort and return
        sorted_recommendations = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {'product_id': pid, 'score': score, 'source': 'social'}
            for pid, score in sorted_recommendations
        ]
    
    @staticmethod
    def get_trending_among_friends(user_id, top_n=15):
        """
        Get products that are trending among user's friends in the last 7 days.
        """
        friend_ids = DataExporter.get_user_friends(user_id)
        
        if not friend_ids:
            return []
        
        user_history = DataExporter.get_user_history(user_id)
        already_interacted = user_history['all']
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Count recent friend activities
        trending_scores = defaultdict(int)
        
        # Recent likes
        recent_likes = UserLikedProduct.objects.filter(
            user_id__in=friend_ids,
            created_at__gte=cutoff_date
        ).values('product_id').annotate(count=Count('id'))
        
        for item in recent_likes:
            if item['product_id'] not in already_interacted:
                trending_scores[item['product_id']] += item['count'] * 2
        
        # Recent purchases
        recent_purchases = OrderItem.objects.filter(
            order__user_id__in=friend_ids,
            order__created_at__gte=cutoff_date,
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).values('product_id').annotate(count=Count('id'))
        
        for item in recent_purchases:
            if item['product_id'] not in already_interacted:
                trending_scores[item['product_id']] += item['count'] * 5
        
        # Sort and return
        sorted_trending = sorted(
            trending_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {'product_id': pid, 'score': float(score), 'source': 'friends_trending'}
            for pid, score in sorted_trending
        ]


class HybridRecommender:
    """Combine multiple recommendation strategies for best results."""
    
    @staticmethod
    def get_personalized_recommendations(user_id, top_n=20):
        """
        Hybrid recommendation combining:
        - Content-Based Filtering (30%)
        - Collaborative Filtering (30%)
        - Social Recommendations (25%)
        - Trending Products (15%)
        """
        # Get recommendations from each strategy
        content_based = ContentBasedRecommender.get_recommendations_for_user(user_id, top_n=15)
        collaborative = CollaborativeFilteringRecommender.get_user_based_recommendations(user_id, top_n=15)
        item_based = CollaborativeFilteringRecommender.get_item_based_recommendations(user_id, top_n=10)
        social = SocialRecommender.get_friends_recommendations(user_id, top_n=15)
        trending = DataExporter.get_trending_products(days=7, limit=10)
        
        # Aggregate scores with weights
        final_scores = defaultdict(float)
        product_sources = defaultdict(list)
        
        # Content-Based (30% weight)
        for item in content_based:
            final_scores[item['product_id']] += item['score'] * 0.30
            product_sources[item['product_id']].append('content')
        
        # User-Based CF (20% weight)
        for item in collaborative:
            final_scores[item['product_id']] += item['score'] * 0.20
            product_sources[item['product_id']].append('collaborative')
        
        # Item-Based CF (10% weight)
        for item in item_based:
            final_scores[item['product_id']] += item['score'] * 0.10
            product_sources[item['product_id']].append('item_based')
        
        # Social (25% weight)
        for item in social:
            final_scores[item['product_id']] += item['score'] * 0.25
            product_sources[item['product_id']].append('social')
        
        # Trending (15% weight)
        for idx, product_id in enumerate(trending):
            # Decreasing score based on position
            trending_score = (len(trending) - idx) / len(trending) * 10
            final_scores[product_id] += trending_score * 0.15
            product_sources[product_id].append('trending')
        
        # Sort by final score
        sorted_recommendations = sorted(
            final_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        # Get product details and return
        recommendations = []
        for product_id, score in sorted_recommendations:
            try:
                product = Product.objects.get(id=product_id)
                recommendations.append({
                    'product': product.to_dict(),
                    'recommendation_score': round(score, 3),
                    'sources': product_sources[product_id]
                })
            except Product.DoesNotExist:
                continue
        
        return recommendations
    
    @staticmethod
    def get_cold_start_recommendations(top_n=20):
        """
        For new users with no history, recommend:
        - Trending products
        - Highly rated products
        - Popular products
        """
        recommendations = []
        
        # Get trending products
        trending_ids = DataExporter.get_trending_products(days=14, limit=top_n)
        
        # Get products with details
        for product_id in trending_ids:
            try:
                product = Product.objects.get(id=product_id)
                recommendations.append({
                    'product': product.to_dict(),
                    'recommendation_score': 1.0,
                    'sources': ['trending', 'cold_start']
                })
            except Product.DoesNotExist:
                continue
        
        # If not enough trending, add highest rated
        if len(recommendations) < top_n:
            top_rated = Product.objects.annotate(
                avg_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).filter(
                review_count__gte=3
            ).exclude(
                id__in=[r['product']['id'] for r in recommendations]
            ).order_by('-avg_rating', '-review_count')[:top_n - len(recommendations)]
            
            for product in top_rated:
                recommendations.append({
                    'product': product.to_dict(),
                    'recommendation_score': 0.9,
                    'sources': ['top_rated', 'cold_start']
                })
        
        return recommendations[:top_n]
