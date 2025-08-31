import React, { useState, useEffect } from 'react';
import { Box, Typography, keyframes } from '@mui/material';

const colorCycle = keyframes`
  0% { border-color: #4285F4; }
  25% { border-color: #EA4335; }
  50% { border-color: #FBBC05; }
  75% { border-color: #34A853; }
  100% { border-color: #4285F4; }
`;

const LoadingAnimation = ({ query }) => {
  const [message, setMessage] = useState("Thinking...");
  const messages = ["Kicking off searches...", "Looking at 15 sites..."];

  useEffect(() => {
    let messageIndex = 0;
    const interval = setInterval(() => {
      if (messageIndex < messages.length) {
        setMessage(messages[messageIndex]);
        messageIndex++;
      } else {
        clearInterval(interval);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'start',
        justifyContent: 'flex-start',
        height: 'calc(100vh - 200px)',
        pt: 4,
        width: '100%',
        maxWidth: '800px',
        mx: 'auto'
    }}>
        <Typography variant="h5" sx={{ mb: 4, color: '#e8eaed', fontWeight: 500 }}>
            {query}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
             <Box sx={{
                width: 28, height: 28, borderRadius: '50%',
                border: '3px solid',
                animation: `${colorCycle} 2s linear infinite`
             }} />
            <Typography variant="body1" sx={{ color: '#bdc1c6' }}>{message}</Typography>
        </Box>
    </Box>
  );
};

export default LoadingAnimation;
