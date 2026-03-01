import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Button,
  TextField,
  Chip,
  Grow,
  Fade,
  Divider,
} from "@mui/material";
import Favicon from "./Favicon";
import { initialWebsites } from "../data/mockData";

const WebsiteSetup = () => {
  const [available, setAvailable] = useState(initialWebsites);
  const [selected, setSelected] = useState(initialWebsites.slice(0, 3));
  const [newSite, setNewSite] = useState("");
  const [longPressedId, setLongPressedId] = useState(null);
  const pressTimer = useRef(null);
  const navigate = useNavigate();

  // Helper: extract hostname from a URL string for favicons
  const getDomain = (url) => {
    try { return new URL(url).hostname; } catch { return url; }
  };

  const handleStart = () => {
    navigate("/chat", { state: { selectedSites: selected } });
  };

  const toggleWebsite = (site) => {
    if (selected.find((s) => s.name === site.name)) {
      setSelected(selected.filter((s) => s.name !== site.name));
    } else {
      setSelected([...selected, site]);
    }
  };

  const handleAdd = () => {
    if (!newSite.trim()) return;
    // Accept both full URLs and bare domains; normalize to full URL
    let fullUrl = newSite.trim();
    if (!fullUrl.startsWith('http')) fullUrl = 'https://' + fullUrl;
    const site = { id: Date.now(), name: fullUrl, displayName: getDomain(fullUrl) };
    setSelected([...selected, site]);
    setAvailable([...available, site]);
    setNewSite("");
  };

  const handleMouseDown = (id) => {
    pressTimer.current = setTimeout(() => {
      setLongPressedId(id);
    }, 600);
  };

  const handleMouseUp = () => {
    clearTimeout(pressTimer.current);
  };

  const handleDeleteAvailable = (id) => {
    setAvailable((prev) => prev.filter((site) => site.id !== id));
    setSelected((prev) => prev.filter((site) => site.id !== id));
    if (longPressedId === id) setLongPressedId(null);
  };

  return (
    <Box
      sx={{
        display: "flex",
        height: "80vh",
        p: 4,
        gap: 4,
        background: "linear-gradient(145deg, #000, #1c1c1c)",
      }}
    >
      {/* LEFT SIDE */}
      <Paper
        elevation={6}
        sx={{
          flex: 1.2,
          p: 3,
          borderRadius: "16px",
          backgroundColor: "#111",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 500, color: "#f5f5f5" }}>
          Selected Websites
        </Typography>
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            gap: 1,
            mb: 3,
            minHeight: "58px",
            maxHeight: 250,
            overflowY: "auto",
            p: 1,
            border: "1px solid #444",
            borderRadius: 2,
          }}
        >
          {selected.map((site) => (
            <Grow in key={site.id}>
              <Chip
                icon={<Favicon domain={getDomain(site.name)} />}
                label={site.displayName || getDomain(site.name)}
                onDelete={() => toggleWebsite(site)}
                sx={{
                  background: "#333",
                  color: "#f5f5f5",
                  fontWeight: 500,
                  "&:hover": { background: "#444" },
                  transition: "all 0.2s ease",
                }}
              />
            </Grow>
          ))}
        </Box>

        <Divider sx={{ mb: 2, backgroundColor: "#555" }} />

        <Typography variant="h6" sx={{ mb: 1, fontWeight: 500, color: "#f5f5f5" }}>
          Available Websites
        </Typography>
        <Paper
          sx={{
            flexGrow: 1,
            overflowY: "auto",
            p: 1,
            borderRadius: "12px",
            backgroundColor: "#1c1c1c",
          }}
        >
          <List dense>
            {available.map((site) => {
              const isExpanded = longPressedId === site.id;
              return (
                <Fade in key={site.id}>
                  <ListItem disablePadding sx={{ mb: 1 }}>
                    <ListItemButton
                      onClick={() => toggleWebsite(site)}
                      onMouseDown={() => handleMouseDown(site.id)}
                      onMouseUp={handleMouseUp}
                      onMouseLeave={handleMouseUp}
                      sx={{
                        borderRadius: "8px",
                        minHeight: isExpanded ? 72 : 48,
                        backgroundColor: selected.find((s) => s.name === site.name)
                          ? "rgba(255,255,255,0.12)"
                          : "transparent",
                        "&:hover": { backgroundColor: "rgba(255,255,255,0.08)" },
                        transition: "all 0.2s ease",
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Favicon domain={getDomain(site.name)} />
                      </ListItemIcon>
                      <ListItemText
                        primary={site.displayName || getDomain(site.name)}
                        primaryTypographyProps={{
                          color: "#f5f5f5",
                          fontWeight: selected.find((s) => s.name === site.name)
                            ? 600
                            : 400,
                        }}
                      />
                      <Checkbox
                        edge="end"
                        checked={!!selected.find((s) => s.name === site.name)}
                        sx={{ color: "#f5f5f5" }}
                      />
                      {isExpanded && (
                        <Button
                          size="small"
                          color="error"
                          sx={{ ml: 2 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteAvailable(site.id);
                          }}
                        >
                          Delete
                        </Button>
                      )}
                    </ListItemButton>
                  </ListItem>
                </Fade>
              );
            })}
          </List>
        </Paper>

        <Button
          variant="contained"
          sx={{
            mt: 3,
            borderRadius: "12px",
            py: 1.2,
            fontWeight: 600,
            background: "#fff",
            color: "#000",
            "&:hover": { background: "#e0e0e0" },
          }}
          disabled={selected.length === 0}
          onClick={handleStart}
        >
          Start Conversation
        </Button>
      </Paper>

      <Paper
        elevation={6}
        sx={{
          flex: 0.8,
          p: 3,
          borderRadius: "16px",
          backgroundColor: "#111",
          height: "fit-content",
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 500, color: "#f5f5f5" }}>
          Add New Website
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Enter website domain (e.g. example.com)"
            value={newSite}
            onChange={(e) => setNewSite(e.target.value)}
            sx={{
              input: { color: "#f5f5f5" },
              backgroundColor: "#1c1c1c",
              borderRadius: "12px",
              "& fieldset": { border: "none" },
            }}
          />
          <Button
            variant="outlined"
            sx={{
              borderRadius: "12px",
              px: 3,
              color: "#f5f5f5",
              borderColor: "#555",
              "&:hover": {
                borderColor: "#aaa",
                backgroundColor: "rgba(255,255,255,0.08)",
              },
            }}
            onClick={handleAdd}
          >
            Add
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default WebsiteSetup;
