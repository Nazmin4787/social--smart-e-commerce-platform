import React, { useState, useEffect, useContext } from 'react';
import ProductCard from './ProductCard';
import { AuthContext } from '../context/AuthContext';
import { fetchProducts as getProducts, getLikedProducts, likeProduct, addToCart } from '../api';

const ProductsSection = ({ title = 'Featured Products', limit = 8, isTrending = false }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [likedProducts, setLikedProducts] = useState([]);
  const { user } = useContext(AuthContext);

  useEffect(() => {
    fetchProducts();
    if (user) {
      fetchLikedProducts();
    }
  }, [user]);

  const fetchProducts = async () => {
    try {
      const data = await getProducts();
      setProducts(data.slice(0, limit));
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLikedProducts = async () => {
    try {
      const data = await getLikedProducts(user.token);
      setLikedProducts(data.map(item => item.product.id));
    } catch (error) {
      console.error('Error fetching liked products:', error);
    }
  };

  const handleLike = async (productId) => {
    if (!user) {
      alert('Please login to like products');
      return;
    }

    try {
      await likeProduct(user.token, productId);
      if (likedProducts.includes(productId)) {
        setLikedProducts(likedProducts.filter(id => id !== productId));
      } else {
        setLikedProducts([...likedProducts, productId]);
      }
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  };

  const handleAddToCart = async (product) => {
    if (!user) {
      alert('Please login to add items to cart');
      return;
    }

    try {
      await addToCart(user.token, product.id, 1);
      alert('Product added to cart!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert(error.response?.data?.error || 'Failed to add to cart');
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
    <section className={`products-section ${isTrending ? 'trending' : ''}`}>
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
