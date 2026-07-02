import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import DialogHost from './components/DialogHost.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <DialogHost />
  </React.StrictMode>
)
