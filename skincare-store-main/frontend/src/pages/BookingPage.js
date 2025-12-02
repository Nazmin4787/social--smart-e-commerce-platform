import React, { useState, useContext, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { createBooking, fetchProducts } from '../api';

const BookingPage = () => {
  const { id } = useParams();
  const { user } = useContext(AuthContext);
  const [product, setProduct] = useState(null);
  const [deliveryDate, setDeliveryDate] = useState('');
  const [qty, setQty] = useState(1);
  const [notes, setNotes] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadProduct();
  }, [id]);

  const loadProduct = async () => {
    try {
      const data = await fetchProducts();
      const p = data.find(pp => String(pp.id) === String(id));
      setProduct(p);
    } catch (err) {
      console.error(err);
    }
  };

  const submitBooking = async () => {
    if (!user) return alert('Please login to book');
    try {
      const res = await createBooking(user.token, product.id, { qty, delivery_date: deliveryDate, notes });
      alert('Booking created');
      navigate('/profile');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to create booking');
    }
  };

  if (!product) return <div className="container py-8">Loading...</div>;

  return (
    <div className="container py-8">
      <h2 className="text-2xl font-bold">Book: {product.title}</h2>
      <div className="mt-4">
        <label className="block text-sm">Quantity</label>
        <input type="number" value={qty} min={1} max={product.stock} onChange={e => setQty(Number(e.target.value))} className="border p-2" />
      </div>
      <div className="mt-4">
        <label className="block text-sm">Delivery / Pickup Date</label>
        <input type="date" value={deliveryDate} onChange={e => setDeliveryDate(e.target.value)} className="border p-2" />
      </div>
      <div className="mt-4">
        <label className="block text-sm">Notes</label>
        <textarea value={notes} onChange={e => setNotes(e.target.value)} className="w-full border p-2" />
      </div>
      <div className="mt-4">
        <button className="btn-primary" onClick={submitBooking}>Confirm Booking</button>
      </div>
    </div>
  );
};

export default BookingPage;
