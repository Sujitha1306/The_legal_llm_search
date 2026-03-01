import React, { useState, useRef, useEffect } from 'react';
import {
    Box, Typography, Paper, Button, List, ListItem, Card, CardContent, Link, Divider, Avatar
} from '@mui/material';
import { ThumbUpOutlined, ThumbDownOutlined, ShareOutlined, MoreVert, Language } from "@mui/icons-material";

const ChatResultsPage = ({ messages, selectedSites, onSearch }) => {
    const [query, setQuery] = useState('');
    const scrollRef = useRef(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query, [...messages, { type: 'user', text: query }]);
            setQuery('');
        }
    };

    const renderAnswer = (answer) => {
        return answer.map((part, index) => {
            if (part.type === 'heading') {
                return <Typography key={index} variant="h6" sx={{ mt: 2.5, mb: 1, fontWeight: 700, color: '#e8eaed' }}>{part.content}</Typography>;
            }
            if (part.type === 'list') {
                return (
                    <List key={index} sx={{ pl: 2, py: 0 }}>
                        {part.items.map((item, i) => (
                            <ListItem key={i} sx={{ display: 'list-item', listStyleType: 'disc', p: 0.4, color: '#e8eaed' }}>
                                <Typography variant="body1">{item}</Typography>
                            </ListItem>
                        ))}
                    </List>
                );
            }
            if (part.type === 'divider') {
                return <Divider key={index} sx={{ my: 2, borderColor: '#333' }} />;
            }
            return <Typography key={index} variant="body1" sx={{ mb: 1.5, color: '#e8eaed', lineHeight: 1.75 }}>{part.content}</Typography>;
        });
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)' }}>
            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 3 }}>
                <Box sx={{ maxWidth: '1000px', mx: 'auto' }}>
                    {messages.map((msg, index) => (
                        <Box key={index} sx={{ mb: 4 }}>
                            <Typography variant="h5" sx={{ mb: 3, color: '#e8eaed', fontWeight: 500 }}>
                                {msg.text}
                            </Typography>

                            <Box sx={{ display: 'flex', gap: 4 }}>
                                <Box sx={{ flex: 1.5, color: '#e8eaed' }}>
                                    {renderAnswer(msg.response.answer)}
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, color: '#bdc1c6' }}>
                                        <ThumbUpOutlined fontSize="small" />
                                        <ThumbDownOutlined fontSize="small" />
                                        <ShareOutlined fontSize="small" />
                                        <MoreVert fontSize="small" />
                                    </Box>
                                </Box>

                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="body2" sx={{ mb: 1, color: '#bdc1c6' }}>{msg.response.sources.length} sites</Typography>
                                    {msg.response.sources.map((source, i) => (
                                        <Card key={i} sx={{ mb: 1.5, bgcolor: '#1e1f20', display: 'flex', alignItems: 'center', borderRadius: 2 }}>
                                            <Box sx={{ p: 1.5, display: 'flex', alignItems: 'center' }}>
                                                <Avatar
                                                    src={source.imageUrl}
                                                    alt={source.title}
                                                    sx={{ width: 32, height: 32, bgcolor: '#333' }}
                                                >
                                                    <Language sx={{ fontSize: 18, color: '#9e9e9e' }} />
                                                </Avatar>
                                            </Box>
                                            <CardContent sx={{ flex: 1, py: '10px !important' }}>
                                                <Link href={source.link} target="_blank" rel="noopener" underline="hover" sx={{ color: '#e8eaed', fontWeight: 600, fontSize: '0.9rem' }}>{source.title}</Link>
                                                <Typography variant="body2" sx={{ color: '#bdc1c6', mt: 0.3 }}>{source.source} · {source.date}</Typography>
                                            </CardContent>
                                        </Card>
                                    ))}
                                    <Button size="small">Show all</Button>
                                </Box>
                            </Box>
                        </Box>
                    ))}
                    <div ref={scrollRef} />
                </Box>
            </Box>

            {/* Bottom Search Bar */}
            <Box sx={{ p: 2, bgcolor: '#131314' }}>
                <Paper
                    component="form"
                    onSubmit={handleSubmit}
                    sx={{
                        p: "10px 20px",
                        display: "flex",
                        alignItems: "center",
                        width: "100%",
                        maxWidth: '800px',
                        mx: 'auto',
                        borderRadius: "24px",
                        backgroundColor: "#1e1f20",
                    }}
                >
                    <input
                        placeholder="Ask a follow up..."
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
                    <Button type="submit" variant="contained" sx={{ background: '#fff', color: '#000', '&:hover': { background: '#e0e0e0' }, borderRadius: 20 }}>Send</Button>
                </Paper>
            </Box>
        </Box>
    );
};

export default ChatResultsPage;
