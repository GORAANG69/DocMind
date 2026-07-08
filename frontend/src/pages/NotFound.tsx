import { useNavigate } from 'react-router-dom';
import { FileQuestion, ArrowLeft } from 'lucide-react';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      textAlign: 'center',
      padding: '2rem'
    }}>
      <div style={{
        width: '120px',
        height: '120px',
        borderRadius: '50%',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '2rem'
      }}>
        <FileQuestion size={64} color="var(--accent-primary)" />
      </div>
      
      <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem' }}>404</h1>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Page Not Found
      </h2>
      
      <p style={{ color: 'var(--text-secondary)', marginBottom: '3rem', maxWidth: '400px' }}>
        The page you are looking for doesn't exist or has been moved.
      </p>
      
      <button 
        className="btn btn-primary" 
        onClick={() => navigate('/')}
        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem' }}
      >
        <ArrowLeft size={20} />
        Back to Dashboard
      </button>
    </div>
  );
};

export default NotFound;
