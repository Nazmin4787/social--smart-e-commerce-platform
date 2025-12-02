import React, { useContext } from 'react';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';

const CartPage = () => {
  const { items, loading, setQuantity, removeItem, subtotal, tax, total } = useContext(CartContext);
  const { user } = useContext(AuthContext);

  if (!user) {
    return <div className="container">Please login to view your cart.</div>;
  }

  if (loading) return <div className="container">Loading cart...</div>;

  return (
    <div className="container py-8">
      <h2 className="text-2xl font-bold mb-4">Your Cart</h2>
      {items.length === 0 ? (
        <div>Your cart is empty.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="col-span-2">
            {items.map(item => (
              <div key={item.id} className="flex items-center border-b py-4">
                <img src={item.images?.[0]} alt={item.title} className="w-20 h-20 object-cover mr-4" />
                <div className="flex-1">
                  <div className="font-semibold">{item.title}</div>
                  <div className="text-sm text-gray-600">${item.price} each</div>
                </div>
                <div className="flex items-center">
                  <button className="px-2" onClick={() => setQuantity(item.id, Math.max(0, item.qty - 1))}>-</button>
                  <div className="px-3">{item.qty}</div>
                  <button className="px-2" onClick={() => setQuantity(item.id, item.qty + 1)}>+</button>
                </div>
                <div className="w-28 text-right">${(item.price * item.qty).toFixed(2)}</div>
                <div className="pl-4">
                  <button className="text-red-600" onClick={() => removeItem(item.id)}>Remove</button>
                </div>
              </div>
            ))}
          </div>

          <div className="col-span-1 bg-white p-4 shadow rounded">
            <h3 className="font-semibold mb-2">Order Summary</h3>
            <div className="flex justify-between py-1"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
            <div className="flex justify-between py-1"><span>Tax (8%)</span><span>${tax.toFixed(2)}</span></div>
            <div className="flex justify-between py-2 font-bold"><span>Total</span><span>${total.toFixed(2)}</span></div>
            <button className="btn-primary w-full mt-3">Checkout</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;
