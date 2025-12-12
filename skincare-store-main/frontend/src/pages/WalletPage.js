import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { getWalletBalance, addMoneyToWallet, getWalletTransactions } from '../api';
import { useNavigate } from 'react-router-dom';

const WalletPage = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addMoneyAmount, setAddMoneyAmount] = useState('');
  const [showAddMoney, setShowAddMoney] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchWalletData();
  }, [user, navigate]);

  const fetchWalletData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      const [walletData, transactionsData] = await Promise.all([
        getWalletBalance(token),
        getWalletTransactions(token)
      ]);
      setWallet(walletData.wallet);
      setTransactions(transactionsData.transactions || []);
    } catch (error) {
      console.error('Error fetching wallet data:', error);
      setMessage('Failed to load wallet data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMoney = async (e) => {
    e.preventDefault();
    const amount = parseFloat(addMoneyAmount);
    
    if (!amount || amount <= 0) {
      setMessage('Please enter a valid amount');
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      const response = await addMoneyToWallet(token, amount);
      setWallet(response.wallet);
      setMessage(response.message);
      setAddMoneyAmount('');
      setShowAddMoney(false);
      fetchWalletData(); // Refresh transactions
    } catch (error) {
      setMessage(error.response?.data?.error || 'Failed to add money');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return <div className="wallet-loading">Loading wallet...</div>;
  }

  return (
    <div className="wallet-page">
      <div className="wallet-container">
        {/* Wallet Balance Card */}
        <div className="wallet-balance-card">
          <div className="wallet-balance-header">
            <h2>
              <i className="fas fa-wallet"></i> My Wallet
            </h2>
          </div>
          <div className="wallet-balance-amount">
            <span className="currency-symbol">₹</span>
            <span className="amount">{wallet?.balance.toFixed(2) || '0.00'}</span>
          </div>
          <button 
            className="btn-add-money"
            onClick={() => setShowAddMoney(!showAddMoney)}
          >
            <i className="fas fa-plus-circle"></i> Add Money
          </button>
        </div>

        {/* Add Money Form */}
        {showAddMoney && (
          <div className="add-money-form">
            <h3>Add Money to Wallet</h3>
            <form onSubmit={handleAddMoney}>
              <div className="quick-amounts">
                {[100, 500, 1000, 2000].map(amt => (
                  <button
                    key={amt}
                    type="button"
                    className="quick-amount-btn"
                    onClick={() => setAddMoneyAmount(amt.toString())}
                  >
                    ₹{amt}
                  </button>
                ))}
              </div>
              <div className="form-group">
                <label>Enter Amount</label>
                <input
                  type="number"
                  value={addMoneyAmount}
                  onChange={(e) => setAddMoneyAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="1"
                  step="0.01"
                  required
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary">
                  Add Money
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setShowAddMoney(false);
                    setAddMoneyAmount('');
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Message */}
        {message && (
          <div className="wallet-message">
            {message}
          </div>
        )}

        {/* Transaction History */}
        <div className="wallet-transactions">
          <h3>
            <i className="fas fa-history"></i> Transaction History
          </h3>
          {transactions.length === 0 ? (
            <div className="no-transactions">
              <i className="fas fa-receipt"></i>
              <p>No transactions yet</p>
            </div>
          ) : (
            <div className="transactions-list">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className={`transaction-item ${transaction.transaction_type}`}
                >
                  <div className="transaction-icon">
                    {transaction.transaction_type === 'credit' ? (
                      <i className="fas fa-arrow-down"></i>
                    ) : (
                      <i className="fas fa-arrow-up"></i>
                    )}
                  </div>
                  <div className="transaction-details">
                    <div className="transaction-desc">{transaction.description}</div>
                    <div className="transaction-date">{formatDate(transaction.created_at)}</div>
                  </div>
                  <div className={`transaction-amount ${transaction.transaction_type}`}>
                    {transaction.transaction_type === 'credit' ? '+' : '-'}
                    ₹{transaction.amount.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WalletPage;
