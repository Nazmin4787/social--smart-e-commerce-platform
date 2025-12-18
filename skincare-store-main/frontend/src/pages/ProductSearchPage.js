import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { fetchProducts } from '../api';
import ProductCard from '../components/ProductCard';
import Header from '../components/Header';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

const ProductSearchPage = () => {
  const query = useQuery();
  const keyword = query.get('q') || '';
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const search = async () => {
      setLoading(true);
      try {
        const allProducts = await fetchProducts();
        // Split keyword into words, match if any word in query matches any word in product title (case-insensitive)
        const queryWords = keyword.toLowerCase().split(/\s+/).filter(Boolean);
        const filtered = allProducts.filter(p => {
          if (!p.title) return false;
          const titleWords = p.title.toLowerCase().split(/\s+/);
          return queryWords.some(qw => titleWords.some(tw => tw.includes(qw)));
        });
        setProducts(filtered);
      } catch (err) {
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };
    if (keyword) search();
    else {
      setProducts([]);
      setLoading(false);
    }
  }, [keyword]);

  return (
    <div>
      <Header />
      <div className="container" style={{ padding: '2rem 0' }}>
        <h2>Search Results for "{keyword}"</h2>
        {loading ? (
          <p>Loading...</p>
        ) : products.length === 0 ? (
          <p>No products found.</p>
        ) : (
          <div className="products-grid">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductSearchPage;
