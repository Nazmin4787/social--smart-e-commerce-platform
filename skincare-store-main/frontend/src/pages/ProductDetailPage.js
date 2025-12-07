import React, { useEffect, useState, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { fetchProducts, addToCart, getReviews, addReview } from '../api';
import ShareButton from '../components/ShareButton';

const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useContext(AuthContext);
  const [reviews, setReviews] = useState([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [selectedImage, setSelectedImage] = useState(0);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    loadProduct();
  }, [id]);

  const loadProduct = async () => {
    setLoading(true);
    try {
      const data = await fetchProducts();
      const p = data.find(pp => String(pp.id) === String(id));
      setProduct(p);
      const rs = await getReviews(id);
      setReviews(rs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!user) return alert('Please login');
    try {
      const token = localStorage.getItem('accessToken');
      await addToCart(token, product.id, 1);
      alert('Added to cart');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to add to cart');
    }
  };

  const handleBookNow = () => {
    window.location.href = `/book/${product.id}`;
  };

  const submitReview = async () => {
    if (!user) return alert('Please login to review');
    try {
      const token = localStorage.getItem('accessToken');
      await addReview(token, product.id, rating, comment);
      setComment('');
      const rs = await getReviews(id);
      setReviews(rs);
      alert('Review submitted');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to submit review');
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(<i key={`full-${i}`} className="fas fa-star" style={{ color: '#fbbf24' }}></i>);
    }
    if (hasHalfStar) {
      stars.push(<i key="half" className="fas fa-star-half-alt" style={{ color: '#fbbf24' }}></i>);
    }
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<i key={`empty-${i}`} className="far fa-star" style={{ color: '#d1d5db' }}></i>);
    }
    return stars;
  };

  if (loading) return <div className="container">Loading product...</div>;
  if (!product) return <div className="container">Product not found</div>;

  const productImages = product.images && product.images.length > 0 
    ? product.images.map(img => img || 'https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&h=500&fit=crop')
    : ['https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&h=500&fit=crop'];

  const avgRating = product.average_rating || (reviews.length > 0 ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1) : null);

  return (
    <div style={{ backgroundColor: '#f9fafb', minHeight: '100vh' }}>
      <div className="container mx-auto p-4">
        {/* Breadcrumb */}
        <nav className="breadcrumb-nav">
          <button onClick={() => navigate('/')} className="breadcrumb-link">Home</button>
          <span className="breadcrumb-separator">&gt;</span>
          <button onClick={() => navigate('/')} className="breadcrumb-link">Skin</button>
          <span className="breadcrumb-separator">&gt;</span>
          <span className="breadcrumb-current">{product.category || 'Products'}</span>
          <span className="breadcrumb-separator">&gt;</span>
          <span className="breadcrumb-current">{product.title}</span>
        </nav>

        <div className="product-detail-container">
          {/* Left Column - Image Gallery */}
          <div className="product-image-section">
            <div className="product-main-image">
              <img
                src={imageError ? 'https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&h=500&fit=crop' : productImages[selectedImage]}
                alt={product.title}
                className="main-image"
                onError={() => setImageError(true)}
              />
              {user && !user.is_staff && !user.is_superuser && (
                <div className="product-detail-action-icons">
                  <ShareButton product={product} iconOnly={true} />
                </div>
              )}
            </div>
            {productImages.length > 1 && (
              <div className="product-thumbnails">
                {productImages.map((img, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setSelectedImage(idx);
                      setImageError(false);
                    }}
                    className={`thumbnail ${selectedImage === idx ? 'thumbnail-active' : ''}`}
                  >
                    <img 
                      src={img} 
                      alt={`${product.title} ${idx + 1}`}
                      onError={(e) => e.target.src = 'https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=80&h=80&fit=crop'}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right Column - Product Info */}
          <div className="product-info-section">
            <h1 className="product-title">{product.title}</h1>
            
            {/* Rating Display */}
            {avgRating && (
              <div className="rating-display">
                <div className="rating-stars">
                  {renderStars(parseFloat(avgRating))}
                </div>
                <span className="rating-text">
                  {avgRating}/5
                </span>
                <span className="rating-count">
                  {reviews.length} {reviews.length === 1 ? 'rating' : 'ratings'} & {reviews.length} {reviews.length === 1 ? 'review' : 'reviews'}
                </span>
              </div>
            )}

            {/* Price */}
            <div className="product-price-section">
              <span className="product-price">${product.price}</span>
            </div>

            {/* Description */}
            <div className="product-description">
              <h3 className="section-title">Product Details</h3>
              <p>{product.description || 'Premium skincare product designed for your beauty needs.'}</p>
            </div>

            {/* Stock Info */}
            {product.stock > 0 ? (
              <div className="stock-info stock-available">
                <i className="fas fa-check-circle"></i> In Stock ({product.stock} available)
              </div>
            ) : (
              <div className="stock-info stock-unavailable">
                <i className="fas fa-times-circle"></i> Out of Stock
              </div>
            )}

            {/* Action Buttons */}
            <div className="product-actions">
              <button 
                className="add-to-bag-btn" 
                onClick={handleAddToCart}
                disabled={product.stock <= 0}
              >
                <i className="fas fa-shopping-bag"></i> Add to Bag
              </button>
              <button 
                className="book-now-btn" 
                onClick={handleBookNow}
                disabled={product.stock <= 0}
              >
                <i className="far fa-calendar-check"></i> Book Now
              </button>
            </div>

            {/* Delivery Options */}
            <div className="delivery-section">
              <h4 className="delivery-title">
                <i className="fas fa-truck"></i> Delivery Options
              </h4>
              <div className="delivery-content">
                <p className="delivery-text">
                  <i className="fas fa-check"></i> Free delivery on orders above $50
                </p>
                <p className="delivery-text">
                  <i className="fas fa-check"></i> Cash on Delivery available
                </p>
                <p className="delivery-text">
                  <i className="fas fa-check"></i> Easy 30 days return & exchange
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <div className="reviews-container">
          <h2 className="reviews-title">Customer Reviews</h2>
          
          <div className="reviews-grid">
            {/* Reviews List */}
            <div className="reviews-list">
              {reviews.length > 0 ? (
                reviews.map(r => (
                  <div key={r.id} className="review-card">
                    <div className="review-header">
                      <div className="review-user">
                        <div className="review-avatar">
                          {r.user?.name?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <span className="review-username">{r.user?.name || 'Anonymous'}</span>
                      </div>
                      <div className="review-rating">
                        {renderStars(r.rating)}
                      </div>
                    </div>
                    <p className="review-comment">{r.comment}</p>
                  </div>
                ))
              ) : (
                <p className="no-reviews">No reviews yet. Be the first to review this product!</p>
              )}
            </div>

            {/* Review Form */}
            <div className="review-form-container">
              <h3 className="review-form-title">Write a Review</h3>
              <div className="review-form">
                <div className="form-group">
                  <label className="form-label">Your Rating</label>
                  <div className="rating-select">
                    {[5,4,3,2,1].map(v => (
                      <button
                        key={v}
                        onClick={() => setRating(v)}
                        className={`rating-option ${rating === v ? 'rating-option-active' : ''}`}
                      >
                        {v} <i className="fas fa-star"></i>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Your Review</label>
                  <textarea 
                    value={comment} 
                    onChange={e => setComment(e.target.value)} 
                    className="form-textarea"
                    placeholder="Share your experience with this product..."
                    rows="5"
                  />
                </div>
                <button className="submit-review-btn" onClick={submitReview}>
                  <i className="fas fa-paper-plane"></i> Submit Review
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;
