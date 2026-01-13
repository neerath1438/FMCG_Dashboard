import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const Table = ({
    columns,
    data,
    onRowClick,
    className = ''
}) => {
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const sortedData = React.useMemo(() => {
        if (!sortConfig.key) return data;

        return [...data].sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];

            if (aValue < bValue) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }, [data, sortConfig]);

    return (
        <div className={`overflow-x-auto custom-scrollbar rounded-xl ${className}`}>
            <table className="w-full min-w-full">
                <thead className="bg-gray-50/80 border-b border-gray-100">
                    <tr>
                        {columns.map((column) => (
                            <th
                                key={column.key}
                                className={`px-3 sm:px-6 py-3 sm:py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider
                                    ${column.sortable ? 'cursor-pointer hover:bg-gray-100/80 transition-colors' : ''}`}
                                onClick={() => column.sortable && handleSort(column.key)}
                            >
                                <div className="flex items-center gap-2">
                                    {column.label}
                                    {column.sortable && sortConfig.key === column.key && (
                                        sortConfig.direction === 'asc'
                                            ? <ChevronUp size={14} className="text-pink-500" />
                                            : <ChevronDown size={14} className="text-pink-500" />
                                    )}
                                </div>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                    {sortedData.map((row, index) => (
                        <tr
                            key={index}
                            className={`${onRowClick ? 'cursor-pointer hover:bg-gray-50' : 'hover:bg-gray-50/50'}
                                        transition-colors`}
                            onClick={() => onRowClick && onRowClick(row)}
                        >
                            {columns.map((column) => (
                                <td key={column.key} className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-gray-700">
                                    {column.render ? column.render(row[column.key], row) : row[column.key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            {sortedData.length === 0 && (
                <div className="text-center py-12 text-gray-500 text-sm bg-gray-50 rounded-b-xl">
                    No data available
                </div>
            )}
        </div>
    );
};

export default Table;
