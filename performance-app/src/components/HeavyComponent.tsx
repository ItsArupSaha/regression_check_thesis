'use client';

import { useState, useEffect } from 'react';

export default function HeavyComponent() {
    const [items, setItems] = useState<string[]>([]);

    useEffect(() => {
        // Simulate heavy calculation
        const heavyItems = [];
        for (let i = 0; i < 5000; i++) {
            heavyItems.push(`Heavy Item ${i} - ${Math.random().toString(36).substring(7)}`);
        }
        setItems(heavyItems);
    }, []);

    return (
        <div className="bg-red-50 py-12 border-t-4 border-red-500">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-3xl font-bold text-red-900 mb-6">Heavy Component (Performance Regression)</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                    {items.map((item, index) => (
                        <div key={index} className="text-xs text-gray-600 bg-white p-2 rounded shadow-sm">
                            {item}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
