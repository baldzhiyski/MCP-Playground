import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { StytchProvider } from '@stytch/react';
import { createStytchUIClient } from '@stytch/react/ui';


const stytch = createStytchUIClient('public-token-test-ae71e9a8-114f-4d46-a4cf-9ac23b2622da');


createRoot(document.getElementById('root')).render(
  <StytchProvider stytch={stytch}>
    <App />
  </StytchProvider>
)
