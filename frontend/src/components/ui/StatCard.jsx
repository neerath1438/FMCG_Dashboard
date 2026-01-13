import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import Card from './Card';

// Circular Progress Component
const CircularProgress = ({ percentage, size = 56, strokeWidth = 5, color = '#f43f5e' }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <div className="relative" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90" width={size} height={size}>
                {/* Background circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="rgba(0,0,0,0.08)"
                    strokeWidth={strokeWidth}
                />
                {/* Progress circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-gray-700">{percentage}%</span>
            </div>
        </div>
    );
};

const StatCard = ({
    icon: Icon,
    label,
    value,
    change,
    changeType = 'neutral',
    variant = 'default',
    percentage,
    subtitle,
    className = ''
}) => {
    const changeColors = {
        positive: 'text-emerald-600',
        negative: 'text-red-500',
        neutral: 'text-gray-600',
    };

    const iconBgColors = {
        default: 'bg-pink-100',
        gradient: 'bg-white/20',
    };

    return (
        <Card variant={variant} className={className}>
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className={`text-sm font-medium uppercase tracking-wide ${variant === 'gradient' ? 'text-white/80' : 'text-gray-500'}`}>
                        {label}
                    </p>
                    <p className={`text-3xl font-bold mt-2 ${variant === 'gradient' ? 'text-white' : 'text-gray-900'}`}>
                        {value}
                    </p>
                    {subtitle && (
                        <p className={`text-sm mt-1 ${variant === 'gradient' ? 'text-white/70' : 'text-gray-500'}`}>
                            {subtitle}
                        </p>
                    )}
                    {change !== undefined && (
                        <div className={`flex items-center gap-1 mt-2 text-sm font-medium ${changeColors[changeType]}`}>
                            {changeType === 'positive' && <TrendingUp size={16} />}
                            {changeType === 'negative' && <TrendingDown size={16} />}
                            <span>{change}</span>
                        </div>
                    )}
                </div>

                {/* Circular Progress OR Icon */}
                {percentage !== undefined ? (
                    <CircularProgress
                        percentage={percentage}
                        color={variant === 'gradient' ? '#fff' : '#f43f5e'}
                    />
                ) : Icon && (
                    <div className={`p-3 rounded-xl ${iconBgColors[variant] || iconBgColors.default}`}>
                        <Icon className={variant === 'gradient' ? 'text-white' : 'text-pink-600'} size={24} />
                    </div>
                )}
            </div>
        </Card>
    );
};

export default StatCard;
