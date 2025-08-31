import React, { useState } from 'react';
import { useLocation, Navigate } from 'react-router-dom';
import MainChatView from './MainChatView';
import LoadingAnimation from './LoadingAnimation';
import ChatResultsPage from './ChatResultsPage';
import { mockApiResponse } from '../data/mockData';

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

    const handleSearch = (query, existingMessages = []) => {
        setCurrentQuery(query);
        const newMessages = [...existingMessages, { type: 'user', text: query }];
        setMessages(newMessages);
        setStep("loading");

        // Simulate API call
        setTimeout(() => {
            const updatedMessages = [...newMessages];
            updatedMessages[updatedMessages.length - 1].response = mockApiResponse;
            setMessages(updatedMessages);
            setStep("results");
        }, 4000);
    }

    const renderStep = () => {
        switch(step) {
            case 'chat':
                return <MainChatView selectedSites={selectedSites} onSearch={handleSearch} />;
            case 'loading':
                return <LoadingAnimation query={currentQuery} />;
            case 'results':
                return <ChatResultsPage messages={messages} selectedSites={selectedSites} onSearch={handleSearch} />;
            default:
                return <MainChatView selectedSites={selectedSites} onSearch={handleSearch} />;
        }
    }

    return renderStep();
}

export default Chat;
