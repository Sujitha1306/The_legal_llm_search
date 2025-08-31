import React, { useState } from "react";
import { ThemeProvider, createTheme, Box } from "@mui/material";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import SideMenu from "./components/SideMenu";
import WebsiteSetup from "./components/WebsiteSetup";
import Chat from "./components/Chat";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#131314",
      paper: "#1e1f20",
    },
    text: {
      primary: "#e8eaed",
      secondary: "#bdc1c6",
    },
  },
  typography: {
    fontFamily: "Google Sans, Arial, sans-serif",
  },
});

export default function App() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <ThemeProvider theme={darkTheme}>
      <Router>
        <Box
          sx={{
            bgcolor: "background.default",
            color: "text.primary",
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            fontFamily: "Google Sans, Arial, sans-serif",
          }}
        >
          <Header />
          <Box sx={{ display: "flex", flexGrow: 1 }}>
            <SideMenu isExpanded={isExpanded} setIsExpanded={setIsExpanded} />
            <Box
              sx={{
                flexGrow: 1,
                transition: "margin-left 0.25s ease-in-out",
                ml: { md: isExpanded ? "60px" : "68px" },
                p: 2,
              }}
            >
              <Routes>
                <Route path="/" element={<WebsiteSetup />} />
                <Route path="/chat" element={<Chat />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}
