import React, { useEffect, useState, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { fetchProducts, addToCart, getReviews, addReview, checkProductAllergies, likeProduct, getLikedProducts } from '../api';
import ShareButton from '../components/ShareButton';
import AllergyAlertModal from '../components/AllergyAlertModal';
import ProductCard from '../components/ProductCard';

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
  const [allergyData, setAllergyData] = useState(null);
  const [showAllergyModal, setShowAllergyModal] = useState(false);
  const [checkingAllergies, setCheckingAllergies] = useState(false);
  const [expandedAccordion, setExpandedAccordion] = useState(null);
  const [relatedProducts, setRelatedProducts] = useState([]);
  const [likedProducts, setLikedProducts] = useState([]);

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
      
      // Load liked products if user is logged in
      if (user) {
        try {
          const token = localStorage.getItem('accessToken');
          const liked = await getLikedProducts(token);
          console.log('Loaded liked products:', liked);
          setLikedProducts(liked.map(item => item.product.id));
        } catch (err) {
          console.error('Error fetching liked products:', err);
        }
      }
      
      // Load related products (same category or same ingredients)
      if (p) {
        let related = data.filter(product => {
          if (product.id === p.id) return false;
          
          // Match by category
          if (product.category && p.category && product.category === p.category) {
            return true;
          }
          
          // Match by ingredients
          if (product.ingredients && p.ingredients && 
              Array.isArray(product.ingredients) && Array.isArray(p.ingredients) &&
              product.ingredients.length > 0 && p.ingredients.length > 0) {
            const hasCommonIngredient = product.ingredients.some(ing => 
              p.ingredients.some(pIng => 
                ing.toLowerCase().includes(pIng.toLowerCase()) ||
                pIng.toLowerCase().includes(ing.toLowerCase())
              )
            );
            if (hasCommonIngredient) return true;
          }
          
          return false;
        });
        
        console.log('Current product:', p.title);
        console.log('Related products found:', related.length);
        console.log('Related products:', related.map(r => r.title));
        
        // If no related products found, show random products
        if (related.length === 0) {
          related = data.filter(product => product.id !== p.id);
          // Shuffle and take first 4
          related = related.sort(() => Math.random() - 0.5);
        }
        
        // Limit to 4 products
        setRelatedProducts(related.slice(0, 4));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!user) return alert('Please login');
    
    // Check for allergies first
    setCheckingAllergies(true);
    try {
      const token = localStorage.getItem('accessToken');
      const allergyCheck = await checkProductAllergies(token, product.id);
      
      if (allergyCheck.has_allergens) {
        // Show allergy warning modal
        setAllergyData(allergyCheck);
        setShowAllergyModal(true);
        setCheckingAllergies(false);
      } else {
        // Safe to add - proceed with add to cart
        await addToCart(token, product.id, 1);
        alert('Added to cart');
        setCheckingAllergies(false);
      }
    } catch (err) {
      console.error('Error during add to cart:', err);
      // If allergy check fails, still allow adding (with warning)
      if (err.response?.status === 401) {
        alert('Please login again');
      } else {
        // Proceed with add to cart anyway if allergy check fails
        try {
          const token = localStorage.getItem('accessToken');
          await addToCart(token, product.id, 1);
          alert('Added to cart');
        } catch (addErr) {
          alert(addErr.response?.data?.error || 'Failed to add to cart');
        }
      }
      setCheckingAllergies(false);
    }
  };

  const handleAddAnywayFromModal = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      await addToCart(token, product.id, 1);
      alert('Added to cart (contains allergens - please be careful!)');
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

  const handleLike = async (productId) => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        alert('Please login to like products');
        return;
      }
      console.log('handleLike - Liking product:', productId);
      await likeProduct(token, productId);
      console.log('handleLike - Product liked, fetching updated list...');
      const liked = await getLikedProducts(token);
      console.log('handleLike - Updated liked products:', liked);
      setLikedProducts(liked.map(item => item.product.id));
    } catch (err) {
      console.error('Error liking product:', err);
      alert(err.response?.data?.error || 'Failed to like product');
    }
  };

  const handleAddToCartFromCard = async (product) => {
    if (!user) return alert('Please login');
    try {
      const token = localStorage.getItem('accessToken');
      const allergyCheck = await checkProductAllergies(token, product.id);
      
      if (allergyCheck.has_allergens) {
        alert(`Warning: This product contains ingredients you may be allergic to: ${allergyCheck.allergens.join(', ')}`);
        const confirm = window.confirm('Do you still want to add it to cart?');
        if (!confirm) return;
      }
      
      await addToCart(token, product.id, 1);
      alert('Added to cart');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to add to cart');
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

  // Helper to get full image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return 'https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&h=500&fit=crop';
    // If it already starts with http, return as is
    if (imagePath.startsWith('http')) return imagePath;
    // If it starts with /media/, prepend the backend URL
    if (imagePath.startsWith('/media/')) {
      return `http://localhost:8000${imagePath}`;
    }
    // Otherwise, construct the full URL
    return `http://localhost:8000/media/${imagePath}`;
  };

  const productImages = product.images && product.images.length > 0 
    ? product.images.map(img => getImageUrl(img))
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
                disabled={product.stock <= 0 || checkingAllergies}
              >
                {checkingAllergies ? (
                  <>
                    <i className="fas fa-spinner fa-spin"></i> Checking...
                  </>
                ) : (
                  <>
                    <i className="fas fa-shopping-bag"></i> Add to Bag
                  </>
                )}
              </button>
              <button 
                className="book-now-btn" 
                onClick={handleBookNow}
                disabled={product.stock <= 0}
              >
                <i className="far fa-calendar-check"></i> Book Now
              </button>
            </div>

            {/* Accordion Sections */}
            <div className="accordion-container">
              {/* Hero Ingredients */}
              <div className="accordion-item">
                <button 
                  className="accordion-header"
                  onClick={() => setExpandedAccordion(expandedAccordion === 'ingredients' ? null : 'ingredients')}
                >
                  <span className="accordion-title">Hero Ingredients</span>
                  <i className={`fas fa-chevron-down accordion-icon ${expandedAccordion === 'ingredients' ? 'accordion-icon-expanded' : ''}`}></i>
                </button>
                {expandedAccordion === 'ingredients' && (
                  <div className="accordion-content">
                    {product.ingredients && product.ingredients.length > 0 ? (
                      <ul className="ingredients-list">
                        {product.ingredients.map((ingredient, idx) => (
                          <li key={idx}>{ingredient}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>Hyaluronic Acid, Vitamin C, Niacinamide, Retinol, Peptides</p>
                    )}
                  </div>
                )}
              </div>

              {/* Product Benefits */}
              <div className="accordion-item">
                <button 
                  className="accordion-header"
                  onClick={() => setExpandedAccordion(expandedAccordion === 'benefits' ? null : 'benefits')}
                >
                  <span className="accordion-title">Product Benefits</span>
                  <i className={`fas fa-chevron-down accordion-icon ${expandedAccordion === 'benefits' ? 'accordion-icon-expanded' : ''}`}></i>
                </button>
                {expandedAccordion === 'benefits' && (
                  <div className="accordion-content">
                    {product.benefits && product.benefits.length > 0 ? (
                      <ul className="benefits-list">
                        {product.benefits.map((benefit, idx) => (
                          <li key={idx}><i className="fas fa-check-circle"></i> {benefit}</li>
                        ))}
                      </ul>
                    ) : (
                      <ul className="benefits-list">
                        <li><i className="fas fa-check-circle"></i> Deeply hydrates and nourishes skin</li>
                        <li><i className="fas fa-check-circle"></i> Reduces fine lines and wrinkles</li>
                        <li><i className="fas fa-check-circle"></i> Brightens and evens skin tone</li>
                        <li><i className="fas fa-check-circle"></i> Improves skin texture and elasticity</li>
                        <li><i className="fas fa-check-circle"></i> Non-comedogenic and suitable for all skin types</li>
                      </ul>
                    )}
                  </div>
                )}
              </div>

              {/* How To Use */}
              <div className="accordion-item">
                <button 
                  className="accordion-header"
                  onClick={() => setExpandedAccordion(expandedAccordion === 'howto' ? null : 'howto')}
                >
                  <span className="accordion-title">How To Use</span>
                  <i className={`fas fa-chevron-down accordion-icon ${expandedAccordion === 'howto' ? 'accordion-icon-expanded' : ''}`}></i>
                </button>
                {expandedAccordion === 'howto' && (
                  <div className="accordion-content">
                    {product.how_to_use && product.how_to_use.length > 0 ? (
                      <ol className="howto-list">
                        {product.how_to_use.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ol>
                    ) : (
                      <ol className="howto-list">
                        <li>Cleanse your face thoroughly and pat dry</li>
                        <li>Apply a small amount to your fingertips</li>
                        <li>Gently massage onto face and neck in upward circular motions</li>
                        <li>Use twice daily - morning and evening for best results</li>
                        <li>Follow with your favorite moisturizer and sunscreen (in AM)</li>
                      </ol>
                    )}
                  </div>
                )}
              </div>

              {/* FAQ */}
              <div className="accordion-item">
                <button 
                  className="accordion-header"
                  onClick={() => setExpandedAccordion(expandedAccordion === 'faq' ? null : 'faq')}
                >
                  <span className="accordion-title">FAQ</span>
                  <i className={`fas fa-chevron-down accordion-icon ${expandedAccordion === 'faq' ? 'accordion-icon-expanded' : ''}`}></i>
                </button>
                {expandedAccordion === 'faq' && (
                  <div className="accordion-content">
                    {product.faqs && product.faqs.length > 0 ? (
                      product.faqs.map((faq, idx) => (
                        <div className="faq-item" key={idx}>
                          <h5>{faq.question}</h5>
                          <p>{faq.answer}</p>
                        </div>
                      ))
                    ) : (
                      <>
                        <div className="faq-item">
                          <h5>Is this product suitable for sensitive skin?</h5>
                          <p>Yes, this product is formulated to be gentle and suitable for all skin types including sensitive skin.</p>
                        </div>
                        <div className="faq-item">
                          <h5>How long until I see results?</h5>
                          <p>Most users notice visible improvements within 2-4 weeks of consistent use.</p>
                        </div>
                        <div className="faq-item">
                          <h5>Can I use this with other products?</h5>
                          <p>Yes, this product works well with other skincare products. Apply after cleansing and before moisturizer.</p>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Delivery Options */}
            <div className="delivery-section">
              <h4 className="delivery-title">
                <i className="fas fa-truck"></i> Delivery Options
              </h4>
              <div className="delivery-options-list">
                <div className="delivery-option">
                  <i className="fas fa-check-circle delivery-check-icon"></i>
                  <span>Free delivery on orders above $50</span>
                </div>
                <div className="delivery-option">
                  <i className="fas fa-check-circle delivery-check-icon"></i>
                  <span>Cash on Delivery available</span>
                </div>
                <div className="delivery-option">
                  <i className="fas fa-check-circle delivery-check-icon"></i>
                  <span>Easy 30 days return & exchange</span>
                </div>
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

        {/* Related Products Section */}
        {relatedProducts.length > 0 && (
          <div className="related-products-section">
            <h2 className="related-products-title">Get Faster Results With</h2>
            <div className="products-grid">
              {relatedProducts.map(relatedProduct => (
                <ProductCard
                  key={relatedProduct.id}
                  product={relatedProduct}
                  onLike={handleLike}
                  onAddToCart={handleAddToCartFromCard}
                  isLiked={likedProducts.includes(relatedProduct.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Footer Info Section */}
        <div className="product-footer-section">
          <div className="product-footer-container">
            <div className="footer-column">
              <h3 className="footer-column-title">Know Us Better</h3>
              <ul className="footer-links-list">
                <li><a href="/about">About Us</a></li>
                <li><a href="/affiliate">Affiliate Program</a></li>
                <li><a href="/faq">FAQ</a></li>
                <li><a href="/blog">Blogs</a></li>
              </ul>
            </div>

            <div className="footer-column">
              <h3 className="footer-column-title">Help</h3>
              <ul className="footer-links-list">
                <li><a href="/contact">Contact Us</a></li>
                <li><a href="/grievance">Grievance Officer</a></li>
                <li><a href="/policies">Our Policies</a></li>
                <li><a href="/terms">Terms & Conditions</a></li>
              </ul>
            </div>

            <div className="footer-column">
              <h3 className="footer-column-title">Sign Up For Updates</h3>
              <div className="newsletter-form">
                <input 
                  type="email" 
                  placeholder="Enter Your Email" 
                  className="newsletter-input"
                />
                <button className="newsletter-button">SUBSCRIBE</button>
              </div>
              <h3 className="footer-column-title" style={{ marginTop: '1.5rem' }}>Follow Us</h3>
              <div className="footer-social-links">
                <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
                  <i className="fab fa-facebook-f"></i>
                </a>
                <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
                  <i className="fab fa-instagram"></i>
                </a>
                <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
                  <i className="fab fa-twitter"></i>
                </a>
                <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
                  <i className="fab fa-youtube"></i>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Allergy Alert Modal */}
      {showAllergyModal && allergyData && (
        <AllergyAlertModal
          allergyData={allergyData}
          onClose={() => setShowAllergyModal(false)}
          onAddAnyway={handleAddAnywayFromModal}
        />
      )}
    </div>
  );
};

export default ProductDetailPage;
