import React, { useState } from 'react';
import { Box, Typography, Paper, Button, Chip } from '@mui/material';
import Favicon from './Favicon';

const MainChatView = ({ selectedSites, onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        flexGrow: 1,
        width: "100%",
        maxWidth: "750px",
        mx: "auto",
        px: 2,
        mt: 10,
        color: "#f5f5f5",
      }}
    >
      <Typography variant="h3" sx={{ mb: 2, fontWeight: 600, mt: 10 }}>
        Meet AI Mode
      </Typography>
      <Typography variant="body1" sx={{ mb: 4, color: "#bbb" }}>
        Ask detailed questions for better responses
      </Typography>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: "16px 24px",
          display: "flex",
          alignItems: "center",
          width: "100%",
          borderRadius: "24px",
          backgroundColor: "#111",
          border: "1px solid #333",
        }}
      >
        <input
          placeholder="Ask anything..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            width: "100%",
            border: "none",
            outline: "none",
            background: "transparent",
            color: "#f5f5f5",
            fontSize: "16px",
          }}
        />
        <Button
          type="submit"
          sx={{
            ml: 2,
            borderRadius: "12px",
            px: 3,
            background: "#fff",
            color: "#000",
            "&:hover": { background: "#e0e0e0" },
          }}
          variant="contained"
        >
          Send
        </Button>
      </Paper>
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: 'center',
          gap: 1,
          mt: 4,
          maxWidth: '100%',
          p: 1,
        }}
      >
        {selectedSites.map((site) => {
          const domain = site.name.startsWith('http') ? (() => { try { return new URL(site.name).hostname; } catch { return site.name; } })() : site.name;
          return (
            <Chip
              key={site.id}
              icon={<Favicon domain={domain} />}
              label={site.displayName || domain}
              sx={{
                background: "#333",
                color: "#f5f5f5",
                fontWeight: 500,
                "&:hover": { background: "#444" },
                transition: "all 0.2s ease",
              }}
            />
          );
        })}
      </Box>
    </Box>
  );
};

export default MainChatView;
