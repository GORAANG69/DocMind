import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          backgroundColor: 'var(--bg-primary)',
          color: 'var(--text-primary)',
          padding: '2rem',
          textAlign: 'center'
        }}>
          <AlertTriangle size={64} color="var(--danger)" style={{ marginBottom: '1.5rem' }} />
          <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Something went wrong</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', maxWidth: '600px' }}>
            An unexpected error occurred in the application. Our team has been notified.
            You can try reloading the page to see if the issue resolves.
          </p>
          
          <button 
            className="btn btn-primary" 
            onClick={this.handleReload}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem' }}
          >
            <RefreshCw size={18} />
            Reload Page
          </button>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <div style={{
              marginTop: '2rem',
              padding: '1.5rem',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '800px',
              width: '100%',
              textAlign: 'left',
              overflowX: 'auto'
            }}>
              <h3 style={{ color: 'var(--danger)', marginBottom: '1rem', fontFamily: 'monospace' }}>
                {this.state.error.toString()}
              </h3>
              <pre style={{ 
                color: 'var(--text-secondary)', 
                fontSize: '0.85rem',
                whiteSpace: 'pre-wrap'
              }}>
                {this.state.errorInfo?.componentStack}
              </pre>
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
