import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import Sidebar from './Sidebar';
import Header from './Header';
import FloatingChatbot from '../FloatingChatbot';

const Layout = ({ children }) => {
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const scrollRef = useRef(null);

    // Reset scroll to top when path changes
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo(0, 0);
            scrollRef.current.scrollTop = 0;
        }
    }, [location.pathname]);

    const pageTitles = {
        '/': 'Dashboard',
        '/products': 'Products',
        '/upload': 'Upload & Process',
        '/low-confidence': 'Low Confidence Items',
        '/analytics': 'Analytics',
        '/chatbot': 'AI Assistant',
        '/audit-qa': 'AI Audit QA Pipeline',
        '/mastering-qa': 'Mastering QA Module',
    };

    const getTitle = () => {
        const path = location.pathname;
        if (path.startsWith('/products/')) return 'Product Details';
        return pageTitles[path] || 'Dashboard';
    };

    // Hide floating chatbot on chatbot page
    const isChatbotPage = location.pathname === '/chatbot';

    return (
        <div className="fixed inset-0 p-4 sm:p-5 lg:p-6 xl:px-20 2xl:px-32">
            {/* Centered Container Box - Fixed position, internal scroll only */}
            <div className="w-full h-full max-w-[1400px] mx-auto bg-[#B3C8DC] rounded-3xl shadow-2xl overflow-hidden flex">
                {/* Sidebar inside the box */}
                <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                    {/* Mobile Hamburger Button */}
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden fixed top-8 left-8 z-30 p-2 bg-white rounded-xl
                                   hover:bg-gray-50 transition-all shadow-md border border-gray-100"
                    >
                        <Menu size={24} className="text-gray-700" />
                    </button>

                    {/* Header - Fixed at top inside box */}
                    <div className="flex-shrink-0">
                        <Header title={getTitle()} />
                    </div>

                    {/* Main content - Scrollable area inside box */}
                    <main 
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto custom-scrollbar"
                    >
                        <div className="p-4 sm:p-6 lg:p-8">
                            {children}
                        </div>
                    </main>
                </div>
            </div>

            {/* Floating Chatbot Button - hide on chatbot page */}
            {!isChatbotPage && <FloatingChatbot />}
        </div>
    );
};

export default Layout;
