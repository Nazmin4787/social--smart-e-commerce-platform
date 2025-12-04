import React, { createContext, useState, useEffect, useContext } from 'react';
import { AuthContext } from './AuthContext';
import { getCart, addToCart, updateCartItem, removeCartItem } from '../api';

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const { accessToken, user } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (accessToken) fetchCart();
    else setItems([]);
  }, [accessToken]);

  const fetchCart = async () => {
    setLoading(true);
    try {
      const data = await getCart(accessToken);
      setItems(data.map(i => ({ ...i.product, qty: i.qty })));
    } catch (err) {
      console.error('Failed to fetch cart', err);
    } finally {
      setLoading(false);
    }
  };

  const addItem = async (product, qty = 1) => {
    if (!accessToken) throw new Error('Not authenticated');
    await addToCart(accessToken, product.id, qty);
    await fetchCart();
  };

  const setQuantity = async (productId, qty) => {
    if (!accessToken) throw new Error('Not authenticated');
    await updateCartItem(accessToken, productId, qty);
    await fetchCart();
  };

  const removeItem = async (productId) => {
    if (!accessToken) throw new Error('Not authenticated');
    await removeCartItem(accessToken, productId);
    await fetchCart();
  };

  const subtotal = items.reduce((s, it) => s + (parseFloat(it.price) * it.qty), 0);
  const tax = +(subtotal * 0.08).toFixed(2);
  const total = +(subtotal + tax).toFixed(2);

  return (
    <CartContext.Provider value={{ items, loading, addItem, setQuantity, removeItem, subtotal, tax, total, fetchCart, refreshCart: fetchCart }}>
      {children}
    </CartContext.Provider>
  );
};
