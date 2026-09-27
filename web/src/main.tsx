import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

createRoot(document.getElementById('root')!, {
  // Caught render exceptions may contain private source data; never log them.
  onCaughtError: () => console.error('Workspace rendering failed. Details withheld for privacy.'),
}).render(<StrictMode><App /></StrictMode>);
