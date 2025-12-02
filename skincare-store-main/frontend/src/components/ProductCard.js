import React from 'react';
import { useNavigate } from 'react-router-dom';

const ProductCard = ({ product, onLike, onAddToCart, isLiked }) => {
  const navigate = useNavigate();
  return (
    <div className="product-card">
      <div className="product-image">
        {product.images && product.images.length > 0 ? (
          <img src={product.images[0]} alt={product.title} onClick={() => navigate(`/products/${product.id}`)} style={{cursor: 'pointer'}} />
        ) : (
          <div className="product-placeholder" onClick={() => navigate(`/products/${product.id}`)} style={{cursor: 'pointer'}}>
            <i className="fas fa-image"></i>
          </div>
        )}
        <button
          className={`like-btn ${isLiked ? 'liked' : ''}`}
          onClick={() => onLike(product.id)}
        >
          <i className={`fas fa-heart ${isLiked ? 'filled' : ''}`}></i>
        </button>
        {product.stock === 0 && (
          <div className="out-of-stock-badge">Out of Stock</div>
        )}
      </div>
      
      <div className="product-info">
        <h3 className="product-title" onClick={() => navigate(`/products/${product.id}`)} style={{cursor: 'pointer'}}>{product.title}</h3>
        <p className="product-description">
          {product.description.substring(0, 80)}
          {product.description.length > 80 ? '...' : ''}
        </p>
        <div className="product-footer">
          <div className="product-price">${product.price}</div>
          <button
            className="btn-add-cart"
            onClick={() => onAddToCart(product)}
            disabled={product.stock === 0}
          >
            <i className="fas fa-shopping-cart"></i>
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
