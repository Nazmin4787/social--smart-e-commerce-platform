import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  getDashboardStats, 
  getRecentOrders, 
  getLowStock, 
  getTopProducts,
  getAllOrders,
  updateOrderStatus,
  getAllProducts,
  updateProductStock,
  getBanners,
  createBanner,
  deleteBanner,
  createProduct,
  updateProduct,
  deleteProduct
} from '../api';

const AdminDashboard = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  
  // Dashboard stats
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  
  // Orders management
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  
  // Products management
  const [products, setProducts] = useState([]);
  const [productSearch, setProductSearch] = useState('');
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    title: '',
    description: '',
    price: '',
    stock: '',
    category: '',
    images: []
  });
  
  // Banners management
  const [banners, setBanners] = useState([]);
  const [bannerForm, setBannerForm] = useState({ 
    hero_title: '', 
    hero_description: '',
    hero_image: null,
    featured_title: '',
    featured_description: '',
    featured_image: null
  });

  useEffect(() => {
    if (!user || !user.is_staff) {
      navigate('/');
    }
  }, [user, navigate]);

  useEffect(() => {
    if (user && user.is_staff) {
      if (activeTab === 'dashboard') {
        fetchDashboardData();
      } else if (activeTab === 'orders') {
        fetchOrders();
      } else if (activeTab === 'products') {
        fetchProducts();
      } else if (activeTab === 'banners') {
        fetchBanners();
      }
    }
  }, [activeTab, user]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const [statsData, ordersData, stockData, topData] = await Promise.all([
        getDashboardStats(token),
        getRecentOrders(token),
        getLowStock(token),
        getTopProducts(token)
      ]);
      setStats(statsData || {});
      setRecentOrders(Array.isArray(ordersData) ? ordersData : []);
      setLowStock(Array.isArray(stockData) ? stockData : []);
      setTopProducts(Array.isArray(topData) ? topData : []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
    setLoading(false);
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const data = await getAllOrders(token);
      setOrders(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
    setLoading(false);
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      console.log('Fetching products with token:', token ? `Token exists (${token.substring(0, 20)}...)` : 'No token');
      const data = await getAllProducts(token);
      console.log('Products fetched:', data, 'Length:', data?.length);
      setProducts(Array.isArray(data) ? data : []);
      console.log('Products state set to:', Array.isArray(data) ? data.length : 0, 'items');
    } catch (error) {
      console.error('Error fetching products:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
    }
    setLoading(false);
  };

  const fetchBanners = async () => {
    setLoading(true);
    try {
      const data = await getBanners();
      setBanners(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching banners:', error);
    }
    setLoading(false);
  };

  const handleOrderStatusUpdate = async (orderId, newStatus) => {
    try {
      const token = localStorage.getItem('accessToken');
      await updateOrderStatus(token, orderId, newStatus);
      fetchOrders();
      alert('Order status updated successfully!');
    } catch (error) {
      alert('Error updating order status');
    }
  };

  const handleStockUpdate = async (productId, newStock) => {
    try {
      const token = localStorage.getItem('accessToken');
      await updateProductStock(token, productId, newStock);
      fetchProducts();
      alert('Stock updated successfully!');
    } catch (error) {
      alert('Error updating stock');
    }
  };

  const handleProductFormChange = (e) => {
    const { name, value } = e.target;
    setProductForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleProductImagesChange = (e) => {
    const files = Array.from(e.target.files);
    setProductForm(prev => ({
      ...prev,
      images: files
    }));
  };

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('accessToken');
      const formData = new FormData();
      formData.append('title', productForm.title);
      formData.append('description', productForm.description);
      formData.append('price', parseFloat(productForm.price));
      formData.append('stock', parseInt(productForm.stock));
      formData.append('category', productForm.category);
      
      // Append image files
      if (productForm.images && productForm.images.length > 0) {
        productForm.images.forEach((file, index) => {
          formData.append('images', file);
        });
      }

      if (editingProduct) {
        await updateProduct(token, editingProduct.id, formData);
        alert('Product updated successfully!');
      } else {
        await createProduct(token, formData);
        alert('Product created successfully!');
      }

      setShowProductForm(false);
      setEditingProduct(null);
      setProductForm({
        title: '',
        description: '',
        price: '',
        stock: '',
        category: '',
        images: []
      });
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      alert('Error saving product: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setProductForm({
      title: product.title,
      description: product.description || '',
      price: product.price.toString(),
      stock: product.stock.toString(),
      category: product.category || '',
      images: product.images || []
    });
    setShowProductForm(true);
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        const token = localStorage.getItem('accessToken');
        await deleteProduct(token, productId);
        alert('Product deleted successfully!');
        fetchProducts();
      } catch (error) {
        console.error('Error deleting product:', error);
        alert('Error deleting product');
      }
    }
  };

  const handleCancelProductForm = () => {
    setShowProductForm(false);
    setEditingProduct(null);
    setProductForm({
      title: '',
      description: '',
      price: '',
      stock: '',
      category: '',
      images: []
    });
  };

  const handleBannerSubmit = async (e, bannerType) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('accessToken');
      const formData = new FormData();
      
      // Determine which form fields to use based on banner type
      const title = bannerType === 'hero' ? bannerForm.hero_title : bannerForm.featured_title;
      const description = bannerType === 'hero' ? bannerForm.hero_description : bannerForm.featured_description;
      const image = bannerType === 'hero' ? bannerForm.hero_image : bannerForm.featured_image;
      
      if (!title || !image) {
        alert('Please fill in all required fields');
        return;
      }
      
      formData.append('title', title);
      formData.append('banner_type', bannerType);
      formData.append('description', description || '');
      formData.append('link_url', '/products');
      formData.append('order', bannerType === 'hero' ? 0 : 1);
      formData.append('image', image);
      
      await createBanner(token, formData);
      
      // Clear only the relevant form fields
      if (bannerType === 'hero') {
        setBannerForm({
          ...bannerForm,
          hero_title: '',
          hero_description: '',
          hero_image: null
        });
      } else {
        setBannerForm({
          ...bannerForm,
          featured_title: '',
          featured_description: '',
          featured_image: null
        });
      }
      
      fetchBanners();
      alert(`${bannerType === 'hero' ? 'Hero' : 'Featured'} banner uploaded successfully!`);
    } catch (error) {
      console.error('Error creating banner:', error);
      alert('Error creating banner: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleBannerDelete = async (bannerId) => {
    if (window.confirm('Are you sure you want to delete this banner?')) {
      try {
        const token = localStorage.getItem('accessToken');
        await deleteBanner(token, bannerId);
        fetchBanners();
        alert('Banner deleted successfully!');
      } catch (error) {
        alert('Error deleting banner');
      }
    }
  };

  const filteredProducts = products.filter(p => 
    p.title && p.title.toLowerCase().includes(productSearch.toLowerCase())
  );

  if (!user) {
    return <div style={{padding: '2rem', textAlign: 'center'}}>Loading...</div>;
  }

  if (!user.is_staff) {
    return (
      <div style={{padding: '2rem', textAlign: 'center'}}>
        <h2>Access Denied</h2>
        <p>You do not have permission to access this page.</p>
        <button onClick={() => navigate('/')}>Go to Home</button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-sidebar">
        <h2 className="admin-logo">Admin Panel</h2>
        <nav className="admin-nav">
          <button 
            className={`admin-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <i className="fas fa-tachometer-alt"></i> Dashboard
          </button>
          <button 
            className={`admin-nav-item ${activeTab === 'orders' ? 'active' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            <i className="fas fa-shopping-bag"></i> Orders
          </button>
          <button 
            className={`admin-nav-item ${activeTab === 'products' ? 'active' : ''}`}
            onClick={() => setActiveTab('products')}
          >
            <i className="fas fa-box"></i> Products
          </button>
          <button 
            className={`admin-nav-item ${activeTab === 'banners' ? 'active' : ''}`}
            onClick={() => setActiveTab('banners')}
          >
            <i className="fas fa-image"></i> Banners
          </button>
          <button 
            className="admin-nav-item"
            onClick={() => navigate('/')}
          >
            <i className="fas fa-home"></i> Back to Site
          </button>
        </nav>
      </div>

      <div className="admin-content">
        {loading && <div className="admin-loading">Loading...</div>}

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && stats && (
          <div className="dashboard-tab">
            <h1 className="admin-heading">Dashboard Overview</h1>
            
            <div className="stats-grid">
              <div className="stat-card">
                <i className="fas fa-box stat-icon"></i>
                <div>
                  <h3>{stats.total_products || 0}</h3>
                  <p>Total Products</p>
                </div>
              </div>
              <div className="stat-card">
                <i className="fas fa-shopping-cart stat-icon"></i>
                <div>
                  <h3>{stats.total_orders || 0}</h3>
                  <p>Total Orders</p>
                </div>
              </div>
              <div className="stat-card">
                <i className="fas fa-dollar-sign stat-icon"></i>
                <div>
                  <h3>${stats.total_revenue || 0}</h3>
                  <p>Total Revenue</p>
                </div>
              </div>
              <div className="stat-card">
                <i className="fas fa-exclamation-triangle stat-icon"></i>
                <div>
                  <h3>{stats.low_stock_count || 0}</h3>
                  <p>Low Stock Items</p>
                </div>
              </div>
            </div>

            <div className="dashboard-sections">
              <div className="dashboard-section">
                <h2>Recent Orders</h2>
                <div className="table-responsive">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>Customer</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Array.isArray(recentOrders) && recentOrders.length > 0 ? (
                        recentOrders.map(order => (
                          <tr key={order.id}>
                            <td>#{order.id}</td>
                            <td>{order.user?.name || 'N/A'}</td>
                            <td>${order.total}</td>
                            <td><span className={`status-badge ${order.status}`}>{order.status}</span></td>
                            <td>{new Date(order.created_at).toLocaleDateString()}</td>
                          </tr>
                        ))
                      ) : (
                        <tr><td colSpan="5">No recent orders</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="dashboard-section">
                <h2>Low Stock Products</h2>
                <div className="table-responsive">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Stock</th>
                        <th>Category</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Array.isArray(lowStock) && lowStock.length > 0 ? (
                        lowStock.map(product => (
                          <tr key={product.id}>
                            <td>{product.title}</td>
                            <td><span className="stock-warning">{product.stock}</span></td>
                            <td>{product.category}</td>
                          </tr>
                        ))
                      ) : (
                        <tr><td colSpan="3">No low stock items</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Orders Tab */}
        {activeTab === 'orders' && (
          <div className="orders-tab">
            <h1 className="admin-heading">Orders Management</h1>
            <div className="table-responsive">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>Email</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(orders) && orders.length > 0 ? (
                    orders.map(order => (
                      <tr key={order.id}>
                        <td>#{order.id}</td>
                        <td>{order.user?.name || 'N/A'}</td>
                        <td>{order.user?.email || 'N/A'}</td>
                        <td>${order.total}</td>
                        <td>
                          <select 
                            value={order.status} 
                            onChange={(e) => handleOrderStatusUpdate(order.id, e.target.value)}
                            className="status-select"
                          >
                            <option value="pending">Pending</option>
                            <option value="processing">Processing</option>
                            <option value="shipped">Shipped</option>
                            <option value="delivered">Delivered</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                        </td>
                        <td>{new Date(order.created_at).toLocaleDateString()}</td>
                        <td>
                          <button 
                            className="btn-view"
                            onClick={() => setSelectedOrder(order)}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="7">No orders found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Products Tab */}
        {activeTab === 'products' && (
          <div className="products-tab">
            <div className="admin-header-row">
              <h1 className="admin-heading">Products Management</h1>
              <button 
                className="btn-add-new"
                onClick={() => setShowProductForm(true)}
              >
                <i className="fas fa-plus"></i> Add New Product
              </button>
            </div>

            {showProductForm && (
              <div className="product-form-modal">
                <div className="product-form-content">
                  <div className="form-header">
                    <h2>{editingProduct ? 'Edit Product' : 'Add New Product'}</h2>
                    <button className="close-btn" onClick={handleCancelProductForm}>×</button>
                  </div>
                  
                  <form onSubmit={handleProductSubmit} className="product-form">
                    <div className="form-group">
                      <label>Product Title *</label>
                      <input
                        type="text"
                        name="title"
                        value={productForm.title}
                        onChange={handleProductFormChange}
                        required
                        placeholder="Enter product name"
                        className="form-control"
                      />
                    </div>

                    <div className="form-group">
                      <label>Description</label>
                      <textarea
                        name="description"
                        value={productForm.description}
                        onChange={handleProductFormChange}
                        placeholder="Enter product description"
                        rows="4"
                        className="form-control"
                      />
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Price ($) *</label>
                        <input
                          type="number"
                          name="price"
                          value={productForm.price}
                          onChange={handleProductFormChange}
                          required
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          className="form-control"
                        />
                      </div>

                      <div className="form-group">
                        <label>Stock *</label>
                        <input
                          type="number"
                          name="stock"
                          value={productForm.stock}
                          onChange={handleProductFormChange}
                          required
                          min="0"
                          placeholder="0"
                          className="form-control"
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label>Category</label>
                      <input
                        type="text"
                        name="category"
                        value={productForm.category}
                        onChange={handleProductFormChange}
                        placeholder="e.g., Skincare, Moisturizer, Serum"
                        className="form-control"
                      />
                    </div>

                    <div className="form-group">
                      <label>Product Images</label>
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handleProductImagesChange}
                        className="form-control"
                      />
                      <small>Select one or multiple images for the product</small>
                    </div>

                    <div className="form-actions">
                      <button type="button" className="btn-cancel" onClick={handleCancelProductForm}>
                        Cancel
                      </button>
                      <button type="submit" className="btn-save">
                        <i className="fas fa-save"></i> {editingProduct ? 'Update Product' : 'Create Product'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            <div className="products-controls">
              <input 
                type="text"
                placeholder="Search products..."
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="products-grid">
              {Array.isArray(filteredProducts) && filteredProducts.length > 0 ? (
                filteredProducts.map(product => {
                  // Helper to get full image URL
                  const getImageUrl = (imagePath) => {
                    if (!imagePath) return null;
                    if (imagePath.startsWith('http')) return imagePath;
                    if (imagePath.startsWith('/media/')) {
                      return `http://localhost:8000${imagePath}`;
                    }
                    return `http://localhost:8000/media/${imagePath}`;
                  };

                  const productImage = product.images && product.images.length > 0 ? getImageUrl(product.images[0]) : null;

                  return (
                    <div key={product.id} className="product-card-admin">
                      <div className="product-image-wrapper">
                        {productImage ? (
                          <img 
                            src={productImage} 
                            alt={product.title} 
                            className="admin-product-img"
                            onError={(e) => {
                              e.target.onerror = null;
                              e.target.style.display = 'none';
                              const placeholder = document.createElement('div');
                              placeholder.className = 'image-placeholder';
                              placeholder.innerHTML = '<i class="fas fa-image"></i><span>Image not available</span>';
                              e.target.parentElement.appendChild(placeholder);
                            }}
                          />
                        ) : (
                          <div className="image-placeholder">
                            <i className="fas fa-image"></i>
                            <span>No image</span>
                          </div>
                        )}
                      </div>
                      <div className="product-details">
                        <h3>{product.title}</h3>
                        <p className="product-description">{product.description}</p>
                        <div className="product-meta">
                          <span className="price">${product.price}</span>
                          <span className={`stock ${product.stock < 10 ? 'low' : ''}`}>
                            Stock: {product.stock}
                          </span>
                        </div>
                        <div className="category-badge">{product.category || 'Uncategorized'}</div>
                        <div className="product-actions">
                          <button 
                            className="btn-edit-product"
                            onClick={() => handleEditProduct(product)}
                            title="Edit Product"
                          >
                            <i className="fas fa-edit"></i> Edit
                          </button>
                          <button 
                            className="btn-delete-product"
                            onClick={() => handleDeleteProduct(product.id)}
                            title="Delete Product"
                          >
                            <i className="fas fa-trash"></i> Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="no-products">
                  <i className="fas fa-box-open"></i>
                  <p>No products found</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Banners Tab */}
        {activeTab === 'banners' && (
          <div className="banners-tab">
            <h1 className="admin-heading">Banners Management</h1>
            
            {/* Hero Banner Section */}
            <div className="banner-form-card">
              <h2><i className="fas fa-home"></i> Hero Banner (Homepage Top)</h2>
              <p className="banner-description">Upload a banner for the main hero section at the top of homepage</p>
              <form onSubmit={(e) => handleBannerSubmit(e, 'hero')} className="banner-form">
                <div className="form-group">
                  <label>Banner Title *</label>
                  <input 
                    type="text"
                    placeholder="e.g., Welcome to Our Skincare Store"
                    value={bannerForm.hero_title || ''}
                    onChange={(e) => setBannerForm({...bannerForm, hero_title: e.target.value})}
                    required
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Description (Optional)</label>
                  <textarea 
                    placeholder="Enter banner description..."
                    value={bannerForm.hero_description || ''}
                    onChange={(e) => setBannerForm({...bannerForm, hero_description: e.target.value})}
                    className="form-input"
                    rows="3"
                  />
                </div>
                <div className="form-group">
                  <label>Hero Banner Image *</label>
                  <input 
                    type="file"
                    accept="image/*"
                    onChange={(e) => setBannerForm({...bannerForm, hero_image: e.target.files[0]})}
                    className="file-input"
                    required={!banners.some(b => b.banner_type === 'hero')}
                  />
                  {bannerForm.hero_image && (
                    <span className="file-name">
                      <i className="fas fa-check-circle"></i> {bannerForm.hero_image.name}
                    </span>
                  )}
                </div>
                <button type="submit" className="btn-submit hero-btn">
                  <i className="fas fa-upload"></i> Upload Hero Banner
                </button>
              </form>
              
              {/* Show current hero banner */}
              {banners.filter(b => b.banner_type === 'hero').length > 0 && (
                <div className="current-banner-preview">
                  <h4>Current Hero Banner:</h4>
                  {banners.filter(b => b.banner_type === 'hero').map(banner => (
                    <div key={banner.id} className="banner-preview-item">
                      {banner.image && (
                        <img src={banner.image.startsWith('http') ? banner.image : `http://localhost:8000${banner.image}`} alt={banner.title} />
                      )}
                      <div className="banner-preview-info">
                        <h5>{banner.title}</h5>
                        <button 
                          className="btn-delete-small"
                          onClick={() => handleBannerDelete(banner.id)}
                        >
                          <i className="fas fa-trash"></i> Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Featured Products Banner Section */}
            <div className="banner-form-card featured-banner-section">
              <h2><i className="fas fa-star"></i> Featured Products Banner</h2>
              <p className="banner-description">Upload a banner for the featured products section (appears between product sections)</p>
              <form onSubmit={(e) => handleBannerSubmit(e, 'featured')} className="banner-form">
                <div className="form-group">
                  <label>Banner Title *</label>
                  <input 
                    type="text"
                    placeholder="e.g., Customer Favorites"
                    value={bannerForm.featured_title || ''}
                    onChange={(e) => setBannerForm({...bannerForm, featured_title: e.target.value})}
                    required
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Description (Optional)</label>
                  <textarea 
                    placeholder="e.g., Discover our best-selling products..."
                    value={bannerForm.featured_description || ''}
                    onChange={(e) => setBannerForm({...bannerForm, featured_description: e.target.value})}
                    className="form-input"
                    rows="3"
                  />
                </div>
                <div className="form-group">
                  <label>Featured Banner Image *</label>
                  <input 
                    type="file"
                    accept="image/*"
                    onChange={(e) => setBannerForm({...bannerForm, featured_image: e.target.files[0]})}
                    className="file-input"
                    required={!banners.some(b => b.banner_type === 'featured')}
                  />
                  {bannerForm.featured_image && (
                    <span className="file-name">
                      <i className="fas fa-check-circle"></i> {bannerForm.featured_image.name}
                    </span>
                  )}
                </div>
                <button type="submit" className="btn-submit featured-btn">
                  <i className="fas fa-upload"></i> Upload Featured Banner
                </button>
              </form>
              
              {/* Show current featured banner */}
              {banners.filter(b => b.banner_type === 'featured').length > 0 && (
                <div className="current-banner-preview">
                  <h4>Current Featured Banner:</h4>
                  {banners.filter(b => b.banner_type === 'featured').map(banner => (
                    <div key={banner.id} className="banner-preview-item">
                      {banner.image && (
                        <img src={banner.image.startsWith('http') ? banner.image : `http://localhost:8000${banner.image}`} alt={banner.title} />
                      )}
                      <div className="banner-preview-info">
                        <h5>{banner.title}</h5>
                        <button 
                          className="btn-delete-small"
                          onClick={() => handleBannerDelete(banner.id)}
                        >
                          <i className="fas fa-trash"></i> Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
