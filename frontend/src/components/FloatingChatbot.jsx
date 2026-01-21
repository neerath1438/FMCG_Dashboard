import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Loader, Sparkles, Minimize2, Maximize2, Copy, Download, Share2, Check } from 'lucide-react';
import Badge from './ui/Badge';
import { chatbotAPI } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as XLSX from 'xlsx';
import { toast } from 'react-hot-toast'; // Assuming toast is available or I'll just use alert

const FloatingChatbot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const exampleQuestions = [
        "Show me all products from Coca Cola",
        "What are the low confidence items?",
        "List all brands in the database",
    ];

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const handleSend = async (question = input) => {
        if (!question.trim()) return;

        const userMessage = { role: 'user', content: question };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await chatbotAPI.sendQuery(question, sessionId);

            if (response.status === 'success') {
                const assistantMessage = {
                    role: 'assistant',
                    content: response.result.answer,
                    data: response.result.data,
                    resultCount: response.result.result_count,
                };
                setMessages(prev => [...prev, assistantMessage]);
            } else {
                const errorMessage = {
                    role: 'assistant',
                    content: response.message || 'Sorry, I encountered an error processing your query.',
                    error: true,
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            console.error('Chatbot Error:', error);
            const errorMessage = {
                role: 'assistant',
                content: error.response?.data?.message || 'Sorry, I encountered an error. Please try again.',
                error: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        if (typeof toast !== 'undefined') toast.success('Copied to clipboard!');
        else alert('Copied to clipboard!');
    };

    const exportToExcel = (data, filename = 'chatbot_data.xlsx') => {
        if (!data || data.length === 0) return;
        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Results");
        XLSX.writeFile(workbook, filename);
    };

    const handleShare = (message) => {
        const shareText = `Check out this insight from FMCG Dashboard:\n\n${message.content}`;
        navigator.clipboard.writeText(shareText);
        alert('Share link/text copied to clipboard!');
    };

    const toggleOpen = () => {
        setIsOpen(!isOpen);
        if (!isOpen) {
            setIsExpanded(false);
        }
    };

    return (
        <>
            {/* Chat Window */}
            {isOpen && (
                <div
                    className={`fixed z-50 bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden transition-all duration-300 ${isExpanded
                        ? 'bottom-4 right-4 left-4 top-20 sm:left-auto sm:top-4 sm:w-[500px] sm:h-[calc(100vh-2rem)]'
                        : 'bottom-24 right-4 w-[360px] h-[500px] sm:w-[400px] sm:h-[550px]'
                        }`}
                >
                    {/* Header */}
                    <div className="bg-gradient-to-r from-pink-500 to-rose-500 px-4 py-3 flex items-center justify-between flex-shrink-0">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 bg-white/20 rounded-full flex items-center justify-center">
                                <Sparkles className="text-white" size={18} />
                            </div>
                            <div>
                                <h3 className="text-white font-semibold text-sm">AI Assistant</h3>
                                <p className="text-white/70 text-xs">Ask anything about your data</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                            >
                                {isExpanded ? (
                                    <Minimize2 className="text-white" size={18} />
                                ) : (
                                    <Maximize2 className="text-white" size={18} />
                                )}
                            </button>
                            <button
                                onClick={toggleOpen}
                                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                            >
                                <X className="text-white" size={18} />
                            </button>
                        </div>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
                        {/* Welcome message when empty */}
                        {messages.length === 0 && (
                            <div className="text-center py-6">
                                <div className="w-14 h-14 bg-gradient-to-br from-pink-500 to-rose-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                                    <MessageSquare className="text-white" size={24} />
                                </div>
                                <h4 className="font-semibold text-gray-900 mb-2">How can I help you?</h4>
                                <p className="text-gray-600 text-sm mb-4">Ask me anything about your FMCG product data</p>

                                {/* Quick Questions */}
                                <div className="space-y-2">
                                    {exampleQuestions.map((question, index) => (
                                        <button
                                            key={index}
                                            onClick={() => handleSend(question)}
                                            className="w-full text-left px-3 py-2.5 bg-white hover:bg-pink-50 border border-gray-200 hover:border-pink-200 rounded-xl transition-all text-sm text-gray-700 hover:text-pink-700"
                                        >
                                            {question}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Chat Messages */}
                        {messages.map((message, index) => (
                            <div
                                key={index}
                                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-[90%] rounded-2xl px-4 py-3 shadow-sm ${message.role === 'user'
                                        ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white'
                                        : message.error
                                            ? 'bg-red-50 text-red-900 border border-red-200'
                                            : 'bg-white text-gray-900 border border-gray-200'
                                        }`}
                                >
                                    <div className="text-sm prose prose-sm max-w-none prose-pink prose-p:leading-relaxed prose-table:my-2 prose-th:bg-gray-50 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-gray-100">
                                        {message.role === 'assistant' ? (
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {message.content}
                                            </ReactMarkdown>
                                        ) : (
                                            <p className="whitespace-pre-wrap">{message.content}</p>
                                        )}
                                    </div>

                                    {/* Action Buttons for Assistant */}
                                    {message.role === 'assistant' && !message.error && (
                                        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
                                            <button
                                                onClick={() => copyToClipboard(message.content)}
                                                className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-pink-600 transition-colors title='Copy'"
                                            >
                                                <Copy size={14} />
                                            </button>
                                            {message.data && message.data.length > 0 && (
                                                <button
                                                    onClick={() => exportToExcel(message.data)}
                                                    className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-pink-600 transition-colors title='Export to Excel'"
                                                >
                                                    <Download size={14} />
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleShare(message)}
                                                className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-pink-600 transition-colors title='Share'"
                                            >
                                                <Share2 size={14} />
                                            </button>
                                        </div>
                                    )}

                                    {/* Data Results */}
                                    {message.data && message.data.length > 0 && (
                                        <div className="mt-2 pt-2 border-t border-gray-100">
                                            <p className="text-[10px] uppercase tracking-wider text-gray-400 font-bold mb-2">
                                                QUERIED DATA ({message.resultCount})
                                            </p>
                                            <div className="space-y-1.5 max-h-40 overflow-y-auto custom-scrollbar">
                                                {message.data.slice(0, 3).map((item, idx) => (
                                                    <div key={idx} className="bg-gray-50 p-2 rounded-lg text-xs border border-gray-100">
                                                        <p className="font-bold text-gray-900">{item.BRAND || 'Unknown'}</p>
                                                        <p className="text-gray-600 truncate">{item.ITEM || item.normalized_item || 'N/A'}</p>
                                                    </div>
                                                ))}
                                                {message.data.length > 3 && (
                                                    <p className="text-[10px] text-gray-500 text-center py-1 bg-gray-100/50 rounded mt-1">
                                                        +{message.data.length - 3} more items available for export
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Loading indicator */}
                        {loading && (
                            <div className="flex justify-start">
                                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                                    <Loader className="animate-spin text-pink-500" size={18} />
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-3 border-t border-gray-200 bg-white flex-shrink-0">
                        <div className="flex gap-2">
                            <input
                                ref={inputRef}
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
                                placeholder="Type your message..."
                                disabled={loading}
                                className="flex-1 px-4 py-2.5 bg-gray-100 border-0 rounded-xl focus:ring-2 focus:ring-pink-500/30 focus:bg-white placeholder-gray-500 text-sm text-gray-900 disabled:bg-gray-100 transition-all"
                            />
                            <button
                                onClick={() => handleSend()}
                                disabled={loading || !input.trim()}
                                className="p-2.5 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl hover:from-pink-600 hover:to-rose-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                            >
                                {loading ? (
                                    <Loader className="animate-spin" size={18} />
                                ) : (
                                    <Send size={18} />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Floating Button */}
            <button
                onClick={toggleOpen}
                className={`fixed bottom-6 right-6 z-50
                           w-14 h-14 rounded-full
                           bg-gradient-to-r from-pink-500 to-rose-500
                           shadow-lg hover:shadow-xl
                           flex items-center justify-center
                           transform hover:scale-110 transition-all duration-300
                           ${isOpen ? 'rotate-0' : ''}`}
                aria-label="Toggle AI Assistant"
            >
                {isOpen ? (
                    <X className="text-white" size={24} />
                ) : (
                    <>
                        <MessageSquare className="text-white" size={24} />
                        {/* Pulse animation ring */}
                        <span className="absolute inset-0 rounded-full bg-pink-500 animate-ping opacity-20"></span>
                    </>
                )}
            </button>
        </>
    );
};

export default FloatingChatbot;
