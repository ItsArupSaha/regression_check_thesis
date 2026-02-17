'use client';

import { useEffect, useState } from 'react';

interface Product {
    id: number;
    name: string;
    description: string;
    price: string;
}

export default function FeatureList() {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/products')
            .then((res) => res.json())
            .then((data) => {
                setProducts(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error('Failed to fetch products:', err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 text-center text-gray-500">
                Loading features...
            </div>
        );
    }

    return (
        <div className="bg-white py-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                    <h2 className="text-base text-indigo-600 font-semibold tracking-wide uppercase">Features</h2>
                    <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                        Our Products
                    </p>
                </div>

                <div className="mt-10">
                    <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
                        {products.map((product) => (
                            <div key={product.id} className="pt-6">
                                <div className="flow-root bg-gray-50 rounded-lg px-6 pb-8">
                                    <div className="-mt-6">
                                        <div className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                                            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                            </svg>
                                        </div>
                                        <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">{product.name}</h3>
                                        <p className="mt-5 text-base text-gray-500">
                                            {product.description}
                                        </p>
                                        <p className="mt-2 text-sm font-bold text-indigo-600">${product.price}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
