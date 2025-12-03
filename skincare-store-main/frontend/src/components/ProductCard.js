import React from 'react';
import { useNavigate } from 'react-router-dom';

const ProductCard = ({ product, onLike, onAddToCart, isLiked }) => {
  const navigate = useNavigate();
  
  // Helper to get full image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return null;
    // If it already starts with http, return as is
    if (imagePath.startsWith('http')) return imagePath;
    // If it starts with /media/, prepend the backend URL
    if (imagePath.startsWith('/media/')) {
      return `http://localhost:8000${imagePath}`;
    }
    // Otherwise, construct the full URL
    return `http://localhost:8000/media/${imagePath}`;
  };

  const productImage = product.images && product.images.length > 0 ? getImageUrl(product.images[0]) : null;

  return (
    <div className="product-card">
      <div className="product-image-container">
        {productImage ? (
          <img 
            src={productImage} 
            alt={product.title} 
            className="product-img"
            onClick={() => navigate(`/products/${product.id}`)}
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23f0f0f0" width="200" height="200"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="16" dy="100" dx="50"%3ENo Image%3C/text%3E%3C/svg%3E';
            }}
          />
        ) : (
          <div className="product-placeholder" onClick={() => navigate(`/products/${product.id}`)}>
            <i className="fas fa-image"></i>
            <span>No Image</span>
          </div>
        )}
        
        <button
          className={`like-btn ${isLiked ? 'liked' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onLike(product.id);
          }}
          aria-label="Like product"
        >
          <i className={`fas fa-heart ${isLiked ? 'filled' : ''}`}></i>
        </button>
        
        {product.stock === 0 && (
          <div className="out-of-stock-badge">Out of Stock</div>
        )}
        {product.stock > 0 && product.stock < 10 && (
          <div className="low-stock-badge">Only {product.stock} left</div>
        )}
      </div>
      
      <div className="product-info">
        <div className="product-category">{product.category || 'General'}</div>
        <h3 className="product-title" onClick={() => navigate(`/products/${product.id}`)}>
          {product.title}
        </h3>
        <p className="product-description">
          {product.description && product.description.substring(0, 60)}
          {product.description && product.description.length > 60 ? '...' : ''}
        </p>
        
        <div className="product-footer">
          <div className="product-pricing">
            <span className="product-price">${product.price}</span>
            {product.stock > 0 && (
              <span className="stock-indicator">
                <i className="fas fa-check-circle"></i> In Stock
              </span>
            )}
          </div>
          <button
            className="btn-add-cart"
            onClick={(e) => {
              e.stopPropagation();
              onAddToCart(product);
            }}
            disabled={product.stock === 0}
          >
            <i className="fas fa-shopping-bag"></i>
            Add to Bag
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
