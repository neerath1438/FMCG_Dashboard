import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader, Sparkles, HelpCircle, Copy, Download, Share2 } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { chatbotAPI } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as XLSX from 'xlsx';
import { toast } from 'react-hot-toast';

const Chatbot = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const messagesEndRef = useRef(null);

    const exampleQuestions = [
        "Show me all products from Coca Cola",
        "What are the low confidence items?",
        "Which products were merged the most?",
        "Show me products with more than 5 merged documents",
        "List all brands in the database",
    ];

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSend = async (question = input) => {
        if (!question.trim()) return;

        const userMessage = { role: 'user', content: question };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await chatbotAPI.sendQuery(question, sessionId);

            const assistantMessage = {
                role: 'assistant',
                content: response.result.answer,
                data: response.result.data,
                resultCount: response.result.result_count,
                explanation: response.result.explanation,
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your question. Please try again.',
                error: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleExampleClick = (question) => {
        handleSend(question);
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

    return (
        <div className="max-w-5xl mx-auto h-[calc(100vh-10rem)] sm:h-[calc(100vh-12rem)] flex flex-col">
            {/* Welcome Message - Pink gradient */}
            {messages.length === 0 && (
                <Card variant="gradient" className="mb-4 sm:mb-6">
                    <div className="text-center">
                        <Sparkles className="mx-auto text-white mb-2 sm:mb-3" size={28} />
                        <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">AI Product Assistant</h2>
                        <p className="text-sm sm:text-base text-white/80">
                            Ask me anything about your FMCG product data. I can help you find products, analyze merges, and more!
                        </p>
                    </div>
                </Card>
            )}

            {/* Example Questions - Glass styling */}
            {messages.length === 0 && (
                <Card title="Example Questions" className="mb-4 sm:mb-6">
                    <div className="space-y-2">
                        {exampleQuestions.map((question, index) => (
                            <button
                                key={index}
                                onClick={() => handleExampleClick(question)}
                                className="w-full text-left px-3 sm:px-4 py-2.5 sm:py-3
                                           bg-white/50 hover:bg-pink-50/70 backdrop-blur-sm
                                           border border-white/30 hover:border-pink-200/50
                                           rounded-xl transition-all duration-200
                                           text-xs sm:text-sm text-gray-700 hover:text-pink-700
                                           min-h-[44px] sm:min-h-0 flex items-center"
                            >
                                <HelpCircle size={14} className="inline mr-2 flex-shrink-0 text-pink-500" />
                                <span>{question}</span>
                            </button>
                        ))}
                    </div>
                </Card>
            )}

            {/* Messages - Glass container */}
            <Card className="flex-1 overflow-hidden flex flex-col mb-3 sm:mb-4">
                <div className="flex-1 overflow-y-auto custom-scrollbar p-3 sm:p-4 space-y-3 sm:space-y-4">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 py-3 ${message.role === 'user'
                                    ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white shadow-lg'
                                    : message.error
                                        ? 'bg-red-50/80 backdrop-blur-sm text-red-900 border border-red-200/50'
                                        : 'glass text-gray-900'
                                    }`}
                            >
                                <div className="text-sm prose prose-sm max-w-none prose-pink prose-p:leading-relaxed prose-table:my-2 prose-th:bg-gray-100 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-gray-100">
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
                                            className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-pink-600 transition-colors"
                                        >
                                            <Copy size={16} />
                                        </button>
                                        {message.data && message.data.length > 0 && (
                                            <button
                                                onClick={() => exportToExcel(message.data)}
                                                className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-pink-600 transition-colors"
                                            >
                                                <Download size={16} />
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleShare(message)}
                                            className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-pink-600 transition-colors"
                                        >
                                            <Share2 size={16} />
                                        </button>
                                    </div>
                                )}

                                {/* Data Results */}
                                {message.data && message.data.length > 0 && (
                                    <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-white/30">
                                        <p className="text-xs text-gray-600 mb-2">
                                            Found {message.resultCount} result{message.resultCount !== 1 ? 's' : ''}
                                        </p>
                                        <div className="space-y-2 max-h-48 sm:max-h-64 overflow-y-auto custom-scrollbar">
                                            {message.data.slice(0, 5).map((item, idx) => (
                                                <div key={idx} className="bg-white/60 backdrop-blur-sm p-2 sm:p-3 rounded-xl border border-white/30 text-xs">
                                                    <p className="font-semibold text-gray-900">{item.BRAND || 'Unknown'}</p>
                                                    <p className="text-gray-600 mt-1 text-xs">{item.ITEM || item.normalized_item || 'N/A'}</p>
                                                    {item.UPC && <p className="text-gray-500 mt-1 font-mono text-xs">UPC: {item.UPC}</p>}
                                                    {item.merged_from_docs > 1 && (
                                                        <Badge variant="glass-success" size="sm" className="mt-1 sm:mt-2">
                                                            Merged: {item.merged_from_docs} docs
                                                        </Badge>
                                                    )}
                                                </div>
                                            ))}
                                            {message.data.length > 5 && (
                                                <p className="text-xs text-gray-500 text-center py-2">
                                                    ... and {message.data.length - 5} more
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="flex justify-start">
                            <div className="glass rounded-2xl px-4 py-3">
                                <Loader className="animate-spin text-pink-600" size={18} />
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </Card>

            {/* Input - Glass styling */}
            <div className="flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
                    placeholder="Ask a question..."
                    disabled={loading}
                    className="flex-1 px-4 py-3
                               bg-white/50 backdrop-blur-sm
                               border border-white/40 rounded-xl
                               focus:ring-2 focus:ring-pink-500/30 focus:border-pink-500/50
                               focus:bg-white/70 placeholder-gray-400
                               disabled:bg-gray-100/50 text-sm sm:text-base
                               min-h-[44px] sm:min-h-0 transition-all duration-200"
                />
                <Button
                    variant="primary"
                    icon={Send}
                    onClick={() => handleSend()}
                    disabled={loading || !input.trim()}
                    loading={loading}
                    className="min-h-[44px] sm:min-h-0 px-4 sm:px-6"
                >
                    <span className="hidden sm:inline">Send</span>
                </Button>
            </div>
        </div>
    );
};

export default Chatbot;
