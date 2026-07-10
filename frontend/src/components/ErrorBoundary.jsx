import React from 'react'

// A render error inside a page used to blank the ENTIRE app (white/dark void)
// because nothing caught it — e.g. a malformed toast object throwing in the
// toast list. This boundary contains the blast radius to the current page and
// offers a way back, so a single bad screen never takes the whole game down.
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary] page crashed:', error, info)
  }

  // Reset when the caller signals a context change (e.g. tab switch) so
  // navigating away from the broken page clears the error.
  componentDidUpdate(prevProps) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null })
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: '4rem 2rem', textAlign: 'center', maxWidth: 620, margin: '0 auto' }}>
          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.6rem', color: 'var(--text-hi)', letterSpacing: '.06em' }}>
            THE PAGE FALTERED
          </div>
          <div style={{ fontStyle: 'italic', color: 'var(--muted)', margin: '12px 0 20px', lineHeight: 1.6 }}>
            Something went wrong rendering this screen. Your progress is safe — switch tabs and come back, or reload.
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: '#7a6f92', background: 'rgba(12,7,24,.5)', border: '1px solid rgba(150,110,230,.25)', padding: '10px 14px', wordBreak: 'break-word', textAlign: 'left' }}>
            {String(this.state.error && this.state.error.message || this.state.error)}
          </div>
          <button className="ilm-btn ilm-btn-violet" style={{ marginTop: 20 }} onClick={() => this.setState({ error: null })}>
            TRY AGAIN
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
