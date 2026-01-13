import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, LogIn, AlertCircle } from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login(email, password);

        if (!result.success) {
            setError(result.error || 'Invalid credentials');
        }

        setLoading(false);
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4"
            style={{
                background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 25%, #3d7ab5 50%, #5a9fd4 75%, #87ceeb 100%)'
            }}>
            {/* Login Card */}
            <div className="w-full max-w-md">
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl
                                    bg-white/20 backdrop-blur-sm mb-4 shadow-lg">
                        <div className="text-3xl font-bold text-white">FM</div>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        FMCG Product Mastering
                    </h1>
                    <p className="text-white/80 text-sm">
                        Sign in to access your dashboard
                    </p>
                </div>

                {/* Login Form Card - Matching dashboard container color */}
                <div className="bg-[#B3C8DC]/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
                                <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                                <div className="flex-1">
                                    <p className="text-sm text-red-800 font-medium">
                                        {error}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Email Input */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-800 mb-2">
                                Email Address
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Mail className="text-gray-500" size={20} />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full pl-12 pr-4 py-3.5 bg-white/70 border border-white/40
                                             rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500
                                             focus:border-transparent transition-all text-gray-900
                                             placeholder:text-gray-500"
                                    placeholder="rosini.alexander@metora.co"
                                />
                            </div>
                        </div>

                        {/* Password Input */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-800 mb-2">
                                Password
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Lock className="text-gray-500" size={20} />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full pl-12 pr-4 py-3.5 bg-white/70 border border-white/40
                                             rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500
                                             focus:border-transparent transition-all text-gray-900
                                             placeholder:text-gray-500"
                                    placeholder="Enter your password"
                                />
                            </div>
                        </div>

                        {/* Login Button - Pink gradient to match dashboard accent */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-pink-500 to-rose-500
                                     hover:from-pink-600 hover:to-rose-600
                                     text-white font-semibold py-3.5 rounded-xl
                                     transition-all duration-200 shadow-lg hover:shadow-xl
                                     disabled:opacity-50 disabled:cursor-not-allowed
                                     flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white
                                                  rounded-full animate-spin" />
                                    <span>Signing in...</span>
                                </>
                            ) : (
                                <>
                                    <LogIn size={20} />
                                    <span>Sign In</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Demo Info */}
                    {/* <div className="mt-6 pt-6 border-t border-white/30">
                        <p className="text-xs text-gray-700 text-center">
                            Demo credentials provided by client
                        </p>
                    </div> */}
                </div>

                {/* Footer */}
                {/* <div className="text-center mt-6">
                    <p className="text-white/60 text-sm">
                        © 2024 FMCG Product Mastering Platform
                    </p>
                </div> */}
            </div>
        </div>
    );
};

export default Login;
