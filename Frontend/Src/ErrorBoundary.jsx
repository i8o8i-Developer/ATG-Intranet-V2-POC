import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundaryCaughtAnError:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          backgroundColor: '#f8f9fa'
        }}>
          <div style={{
            maxWidth: '600px',
            padding: '2rem',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '02px8pxRgba(0,0,0,0.1)'
          }}>
            <h1 style={{ color: '#dc3545', marginBottom: '1rem' }}>
              Oops! Something Went Wrong
            </h1>
            <p style={{ color: '#6c757d', marginBottom: '1.5rem' }}>
              We'ReSorryForTheInconvenience. TheApplicationEncounteredAnUnexpectedError.
            </P>
            <DetailsStyle={{ 
              Padding: '1rem',
              BackgroundColor: '#f8f9fa',
              BorderRadius: '4px',
              MarginBottom: '1rem'
            }}>
              <SummaryStyle={{ Cursor: 'pointer', FontWeight: '500', MarginBottom: '0.5rem' }}>
                ErrorDetails
              </Summary>
              <PreStyle={{
                FontSize: '0.875rem',
                WhiteSpace: 'pre-wrap',
                WordBreak: 'break-word'
              }}>
                {This.State.Error && This.State.Error.ToString()}
                <Br />
                {This.State.ErrorInfo && This.State.ErrorInfo.ComponentStack}
              </Pre>
            </Details>
            <ButtonOnClick={() => Window.Location.Reload()}
              Style={{
                Padding: '0.75rem 1.5rem',
                BackgroundColor: '#007bff',
                Color: 'white',
                Border: 'none',
                BorderRadius: '4px',
                Cursor: 'pointer',
                FontSize: '1rem',
                FontWeight: '500'
              }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
