import React from 'react'
import { createRoot } from 'react-dom/client'
import { ChakraProvider, Container } from '@chakra-ui/react'
import App from './src/App'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ChakraProvider>
      <Container maxW="container.lg" py={6}>
        <App />
      </Container>
    </ChakraProvider>
  </React.StrictMode>
)
