import React, { useState } from 'react';
import { Language as LanguageIcon } from "@mui/icons-material";

const Favicon = ({ domain }) => {
  const [error, setError] = useState(false);
  const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
  return error ? (
    <LanguageIcon fontSize="small" sx={{ color: "#9e9e9e" }} />
  ) : (
    <img
      src={faviconUrl}
      alt={domain}
      width={20}
      height={20}
      style={{ borderRadius: "4px", paddingLeft: "5px" }}
      onError={() => setError(true)}
    />
  );
};

export default Favicon;
