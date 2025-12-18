import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import ProductCard from './ProductCard';
import { AuthContext } from '../context/AuthContext';
import { fetchProducts as getProducts, getLikedProducts, likeProduct, getFriendsProductActivities, getFriendsPurchased } from '../api';
import { CartContext } from '../context/CartContext';

const ProductsSection = ({ title = 'Featured Products', limit = 8, isTrending = false, category = null, ingredient = null }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [likedProducts, setLikedProducts] = useState([]);
  const [friendsActivities, setFriendsActivities] = useState({});
  const [friendsPurchasedByProduct, setFriendsPurchasedByProduct] = useState({});
  const { user } = useContext(AuthContext);
  const { addItem } = useContext(CartContext);
  const navigate = useNavigate();

  useEffect(() => {
    console.log('ProductsSection - User:', user ? user.name : 'Not logged in');
    fetchProducts();
    if (user) {
      console.log('ProductsSection - Fetching liked products and friends activities');
      fetchLikedProducts();
      fetchFriendsActivities();
    } else {
      console.log('ProductsSection - User not logged in, skipping friends activities');
    }
  }, [user, category, ingredient]);

  useEffect(() => {
    // Fetch friends purchased for each product
    if (user && products.length > 0) {
      fetchAllFriendsPurchased();
    }
  }, [user, products]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await getProducts();
      
      // Debug logging
      console.log('All products:', data.length);
      console.log('Is trending section:', isTrending);
      if (isTrending && data.length > 0) {
        console.log('Sample product:', data[0]);
        console.log('Products with is_trending:', data.filter(p => p.is_trending).length);
      }
      
      let filteredProducts = data;
      
      // Filter by trending first if specified (trending section is independent of category)
      if (isTrending) {
        filteredProducts = filteredProducts.filter(product => product.is_trending);
        console.log('Filtered trending products:', filteredProducts.length);
      } else {
        // Apply category filter if specified
        if (category) {
          filteredProducts = filteredProducts.filter(product => 
            product.category && product.category.toUpperCase() === category.toUpperCase()
          );
        }
        
        // Apply ingredient filter if specified
        if (ingredient) {
          filteredProducts = filteredProducts.filter(product => 
            product.ingredients && Array.isArray(product.ingredients) && 
            product.ingredients.some(ing => ing.toUpperCase().includes(ingredient.toUpperCase()))
          );
        }
      }
      
      setProducts(filteredProducts.slice(0, limit));
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLikedProducts = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const data = await getLikedProducts(token);
      setLikedProducts(data.map(item => item.product.id));
    } catch (error) {
      console.error('Error fetching liked products:', error);
    }
  };

  const fetchFriendsActivities = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      console.log('Fetching friends activities with token:', token ? 'Token exists' : 'No token');
      const data = await getFriendsProductActivities(token);
      console.log('Friends activities response:', data);
      console.log('Activities by product:', data.activities_by_product);
      setFriendsActivities(data.activities_by_product || {});
    } catch (error) {
      console.error('Error fetching friends activities:', error);
      console.error('Error details:', error.response?.data);
    }
  };

  const fetchAllFriendsPurchased = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const purchasedData = {};
      
      // Fetch friends purchased for each product
      await Promise.all(
        products.map(async (product) => {
          try {
            const data = await getFriendsPurchased(product.id, token);
            if (data.friends && data.friends.length > 0) {
              purchasedData[product.id] = data.friends;
            }
          } catch (error) {
            console.error(`Error fetching friends purchased for product ${product.id}:`, error);
          }
        })
      );
      
      console.log('Friends purchased data:', purchasedData);
      setFriendsPurchasedByProduct(purchasedData);
    } catch (error) {
      console.error('Error fetching friends purchased:', error);
    }
  };

  const handleLike = async (productId) => {
    if (!user) {
      alert('Please login to like products');
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      await likeProduct(token, productId);
      if (likedProducts.includes(productId)) {
        setLikedProducts(likedProducts.filter(id => id !== productId));
      } else {
        setLikedProducts([...likedProducts, productId]);
      }
    } catch (error) {
      console.error('Error toggling like:', error);
      alert('Failed to update like status. Please try logging in again.');
    }
  };

  const handleAddToCart = async (product) => {
    if (!user) {
      alert('Please login to add items to cart');
      return;
    }

    try {
      await addItem(product, 1);
      navigate('/cart');
    } catch (error) {
      console.error('Error adding to cart via context:', error);
      alert(error.message === 'Not authenticated' ? 'Please login to add items to cart' : 'Failed to add to cart');
    }
  };

  if (loading) {
    return (
      <section className="products-section">
        <div className="container">
          <h2 className="section-title">{title}</h2>
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading products...</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="products" className={`products-section ${isTrending ? 'trending' : ''}`}>
      <div className="container">
        <h2 className="section-title">{title}</h2>
        <div className="products-grid">
          {products.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onLike={handleLike}
              onAddToCart={handleAddToCart}
              isLiked={likedProducts.includes(product.id)}
              friendsActivities={friendsActivities[product.id] || []}
              friendsPurchased={friendsPurchasedByProduct[product.id] || []}
            />
          ))}
        </div>
        {!isTrending && (
          <div className="text-center">
            <button
              className="btn-secondary"
              onClick={() => window.location.href = '/products'}
            >
              View All Products
            </button>
          </div>
        )}
      </div>
    </section>
  );
};

export default ProductsSection;
