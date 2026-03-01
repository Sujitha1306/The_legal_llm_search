import React, { useState } from 'react';
import { useLocation, Navigate } from 'react-router-dom';
import MainChatView from './MainChatView';
import LoadingAnimation from './LoadingAnimation';
import ChatResultsPage from './ChatResultsPage';
import axios from 'axios';

const Chat = () => {
    const location = useLocation();
    const [step, setStep] = useState("chat"); // 'chat', 'loading', 'results'
    const [messages, setMessages] = useState([]);
    const [currentQuery, setCurrentQuery] = useState('');

    // If the user navigates to /chat directly without selecting sites, redirect them.
    if (!location.state?.selectedSites) {
        return <Navigate to="/" />;
    }

    const { selectedSites } = location.state;

    const handleSearch = async (query, existingMessages = []) => {
        setCurrentQuery(query);
        const newMessages = [...existingMessages, { type: 'user', text: query }];
        setMessages(newMessages);
        setStep("loading");

        try {
            // site.name is now a full URL (e.g. "https://www.thehindu.com/news/national/")
            const siteUrls = selectedSites.map(site => site.name);
            const response = await axios.post('http://localhost:8000/api/chat', {
                query: query,
                sites: siteUrls
            });

            const updatedMessages = [...newMessages];
            // Backend returns: { answers: { "url": "markdown text" }, sources: ["url1", ...] }
            const rawData = response.data;

            // Parse each per-source answer as markdown into structured blocks
            const allAnswerBlocks = [];
            Object.entries(rawData.answers).forEach(([url, text], idx) => {
                if (idx > 0) {
                    allAnswerBlocks.push({ type: 'divider' });
                }
                // Convert markdown text into structured answer blocks
                const blocks = parseMarkdownToBlocks(text);
                allAnswerBlocks.push(...blocks);
            });

            const formattedSources = (rawData.sources || []).map(url => {
                try {
                    const urlObj = new URL(url);
                    const domain = urlObj.hostname;
                    // Try to match with a selected site to get a nice display name
                    const matchedSite = selectedSites.find(s => s.name === url || s.name.includes(domain));
                    return {
                        title: matchedSite?.displayName || domain,
                        source: domain,
                        date: new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }),
                        link: url,
                        imageUrl: `https://www.google.com/s2/favicons?domain=${domain}&sz=64`
                    };
                } catch (e) {
                    return { title: url, source: url, date: 'Today', link: url, imageUrl: '' };
                }
            });

            updatedMessages[updatedMessages.length - 1].response = {
                answer: allAnswerBlocks.length > 0 ? allAnswerBlocks : [{ type: 'paragraph', content: 'No content found.' }],
                sources: formattedSources
            };
            setMessages(updatedMessages);
            setStep("results");
        } catch (error) {
            console.error("Error communicating with backend:", error);
            const updatedMessages = [...newMessages];
            updatedMessages[updatedMessages.length - 1].response = {
                answer: [{ type: 'paragraph', content: `Error: Could not reach the backend. Make sure the backend server is running on port 8000.\n\nDetails: ${error.message}` }],
                sources: []
            };
            setMessages(updatedMessages);
            setStep("results");
        }
    };

    const renderStep = () => {
        switch (step) {
            case 'chat':
                return <MainChatView selectedSites={selectedSites} onSearch={handleSearch} />;
            case 'loading':
                return <LoadingAnimation query={currentQuery} />;
            case 'results':
                return <ChatResultsPage messages={messages} selectedSites={selectedSites} onSearch={handleSearch} />;
            default:
                return <MainChatView selectedSites={selectedSites} onSearch={handleSearch} />;
        }
    };

    return renderStep();
};

/**
 * Converts a markdown string from the LLM into structured blocks
 * for the ChatResultsPage to render.
 */
function parseMarkdownToBlocks(text) {
    if (!text) return [];
    const lines = text.split('\n');
    const blocks = [];
    let listItems = [];

    const flushList = () => {
        if (listItems.length > 0) {
            blocks.push({ type: 'list', items: listItems });
            listItems = [];
        }
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) {
            flushList();
            continue;
        }
        // Heading: ## or ###
        if (/^#{1,4}\s+/.test(line)) {
            flushList();
            blocks.push({ type: 'heading', content: line.replace(/^#{1,4}\s+/, '') });
            // Numbered list: 1. item
        } else if (/^\d+\.\s+/.test(line)) {
            listItems.push(line.replace(/^\d+\.\s+/, '').replace(/\*\*(.*?)\*\*/g, '$1'));
            // Bullet list: - item or * item
        } else if (/^[-*]\s+/.test(line)) {
            listItems.push(line.replace(/^[-*]\s+/, '').replace(/\*\*(.*?)\*\*/g, '$1'));
            // Normal paragraph
        } else {
            flushList();
            // Strip inline markdown bold for plain text rendering
            blocks.push({ type: 'paragraph', content: line.replace(/\*\*(.*?)\*\*/g, '$1') });
        }
    }
    flushList();
    return blocks;
}

export default Chat;
