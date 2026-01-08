"""
Management command to pre-calculate and cache recommendations.
Run this command periodically (e.g., via cron job) to keep recommendations fresh.

Usage:
    python manage.py update_recommendations
    python manage.py update_recommendations --users 100  # Limit to top 100 active users
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count, Q
from datetime import datetime, timedelta

from api.models import AppUser, Product, UserLikedProduct, OrderItem
from api.recommender import (
    HybridRecommender,
    ContentBasedRecommender,
    DataExporter,
    ProductFeatureVector
)


class Command(BaseCommand):
    help = 'Pre-calculate and cache product recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=None,
            help='Number of most active users to process (default: all users)'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=None,
            help='Number of products to process for similarity (default: all products)'
        )
        parser.add_argument(
            '--rebuild-vectors',
            action='store_true',
            help='Rebuild product feature vectors before caching'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting recommendation cache update...'))
        
        start_time = datetime.now()
        
        # Step 1: Rebuild feature vectors if requested
        if options['rebuild_vectors']:
            self.stdout.write('Rebuilding product feature vectors...')
            ProductFeatureVector.build_feature_vectors()
            self.stdout.write(self.style.SUCCESS('✓ Feature vectors rebuilt'))
        
        # Step 2: Cache cold-start recommendations
        self.stdout.write('Caching cold-start recommendations...')
        self._cache_cold_start()
        self.stdout.write(self.style.SUCCESS('✓ Cold-start recommendations cached'))
        
        # Step 3: Get users to process
        users_to_process = self._get_active_users(options['users'])
        self.stdout.write(f'Processing {len(users_to_process)} users...')
        
        # Step 4: Cache personalized recommendations for active users
        cached_count = 0
        for user_id in users_to_process:
            try:
                self._cache_user_recommendations(user_id)
                cached_count += 1
                
                if cached_count % 10 == 0:
                    self.stdout.write(f'  Processed {cached_count}/{len(users_to_process)} users')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Failed to cache recommendations for user {user_id}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Cached recommendations for {cached_count} users'))
        
        # Step 5: Get products to process
        products_to_process = self._get_popular_products(options['products'])
        self.stdout.write(f'Processing {len(products_to_process)} products for similarity...')
        
        # Step 6: Cache similar products
        cached_products = 0
        for product_id in products_to_process:
            try:
                self._cache_similar_products(product_id)
                cached_products += 1
                
                if cached_products % 20 == 0:
                    self.stdout.write(f'  Processed {cached_products}/{len(products_to_process)} products')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Failed to cache similar products for {product_id}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Cached similar products for {cached_products} products'))
        
        # Step 7: Summary
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.stdout.write(self.style.SUCCESS(
            f'\nCache update completed in {elapsed_time:.2f} seconds'
        ))
        self.stdout.write(f'  Users processed: {cached_count}')
        self.stdout.write(f'  Products processed: {cached_products}')
    
    def _cache_cold_start(self):
        """Cache cold-start recommendations for new users."""
        for limit in [10, 20, 30]:
            cache_key = f'cold_start_recommendations_limit_{limit}'
            recommendations = HybridRecommender.get_cold_start_recommendations(top_n=limit)
            cache.set(cache_key, recommendations, 86400)  # 24 hours
    
    def _get_active_users(self, max_users=None):
        """
        Get list of active user IDs, prioritizing those with recent activity.
        """
        # Get users with activity in the last 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        
        active_users = AppUser.objects.annotate(
            recent_likes=Count(
                'liked_products',
                filter=Q(liked_products__created_at__gte=cutoff_date)
            ),
            recent_orders=Count(
                'orders',
                filter=Q(orders__created_at__gte=cutoff_date)
            ),
            recent_reviews=Count(
                'reviews',
                filter=Q(reviews__created_at__gte=cutoff_date)
            )
        ).annotate(
            activity_score=models.F('recent_likes') + 
                          models.F('recent_orders') * 3 + 
                          models.F('recent_reviews') * 2
        ).filter(
            activity_score__gt=0
        ).order_by('-activity_score')
        
        if max_users:
            active_users = active_users[:max_users]
        
        return list(active_users.values_list('id', flat=True))
    
    def _get_popular_products(self, max_products=None):
        """
        Get list of popular product IDs.
        """
        popular_products = Product.objects.annotate(
            like_count=Count('liked_by'),
            order_count=Count('orderitem'),
            review_count=Count('reviews')
        ).annotate(
            popularity_score=models.F('like_count') + 
                           models.F('order_count') * 3 + 
                           models.F('review_count') * 2
        ).filter(
            popularity_score__gt=0
        ).order_by('-popularity_score')
        
        if max_products:
            popular_products = popular_products[:max_products]
        else:
            # Default to top 100 most popular products
            popular_products = popular_products[:100]
        
        return list(popular_products.values_list('id', flat=True))
    
    def _cache_user_recommendations(self, user_id):
        """Cache personalized recommendations for a user."""
        for limit in [10, 20, 30]:
            cache_key = f'recommendations_user_{user_id}_limit_{limit}'
            
            # Check if user has history
            user_history = DataExporter.get_user_history(user_id)
            
            if not user_history['all']:
                # Use cold-start
                recommendations = HybridRecommender.get_cold_start_recommendations(top_n=limit)
            else:
                # Personalized
                recommendations = HybridRecommender.get_personalized_recommendations(user_id, top_n=limit)
            
            result = {
                "success": True,
                "count": len(recommendations),
                "recommendations": recommendations,
                "user_has_history": bool(user_history['all'])
            }
            
            # Cache for 1 hour
            cache.set(cache_key, result, 3600)
    
    def _cache_similar_products(self, product_id):
        """Cache similar products for a given product."""
        for limit in [5, 10, 15]:
            cache_key = f'similar_products_{product_id}_limit_{limit}'
            
            # Get similar products
            similar_items = ContentBasedRecommender.get_similar_products(product_id, top_n=limit)
            
            # Get full product details
            recommendations = []
            for item in similar_items:
                try:
                    similar_product = Product.objects.get(id=item['product_id'])
                    recommendations.append({
                        'product': similar_product.to_dict(),
                        'similarity_score': item['similarity_score']
                    })
                except Product.DoesNotExist:
                    continue
            
            product = Product.objects.get(id=product_id)
            result = {
                "success": True,
                "product_id": product_id,
                "product_title": product.title,
                "count": len(recommendations),
                "similar_products": recommendations
            }
            
            # Cache for 24 hours
            cache.set(cache_key, result, 86400)


# Import models for annotations
from django.db import models
