import React, { useEffect, useState, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { fetchProducts, addToCart, getReviews, addReview } from '../api';

const ProductDetailPage = () => {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useContext(AuthContext);
  const [reviews, setReviews] = useState([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');

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
      await addToCart(user.token, product.id, 1);
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
      await addReview(user.token, product.id, rating, comment);
      setComment('');
      const rs = await getReviews(id);
      setReviews(rs);
      alert('Review submitted');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to submit review');
    }
  };

  if (loading) return <div className="container">Loading product...</div>;
  if (!product) return <div className="container">Product not found</div>;

  return (
    <div className="container py-8">
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          {product.images?.[0] ? (
            <img src={product.images[0]} alt={product.title} className="w-full h-96 object-cover" />
          ) : (
            <div className="w-full h-96 bg-gray-100 flex items-center justify-center">No Image</div>
          )}
        </div>
        <div>
          <h1 className="text-2xl font-bold">{product.title}</h1>
          <div className="text-xl text-green-600 mt-2">${product.price}</div>
          <p className="mt-4 text-gray-700">{product.description}</p>
          <div className="mt-4">Stock: {product.stock}</div>
          <div className="mt-4 flex gap-2">
            <button className="btn-primary" onClick={handleAddToCart} disabled={product.stock === 0}>Add to Cart</button>
            <button className="btn-secondary" onClick={handleBookNow}>Book Now</button>
          </div>

          <div className="mt-8">
            <h3 className="font-semibold">Reviews</h3>
            {reviews.length === 0 && <div className="text-sm text-gray-600">No reviews yet</div>}
            {reviews.map(r => (
              <div key={r.id} className="border-b py-3">
                <div className="flex justify-between">
                  <div className="font-semibold">{r.user.name}</div>
                  <div className="text-sm text-yellow-500">{r.rating} / 5</div>
                </div>
                <div className="text-sm text-gray-700">{r.comment}</div>
              </div>
            ))}

            <div className="mt-4">
              <h4 className="font-semibold">Leave a review</h4>
              <div className="mt-2">
                <label className="block text-sm">Rating</label>
                <select value={rating} onChange={e => setRating(e.target.value)} className="border p-2">
                  {[5,4,3,2,1].map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div className="mt-2">
                <label className="block text-sm">Comment</label>
                <textarea value={comment} onChange={e => setComment(e.target.value)} className="w-full border p-2" />
              </div>
              <div className="mt-2">
                <button className="btn-primary" onClick={submitReview}>Submit Review</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;
