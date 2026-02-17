
import Link from 'next/link';

export default function Hero() {
    return (
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto text-center">
                <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
                    Performance Thesis Testbed
                </h1>
                <p className="mt-6 max-w-2xl mx-auto text-xl text-indigo-100">
                    A modern web application built for measuring performance regression.
                </p>
                <div className="mt-10 flex justify-center gap-4">
                    <Link href="/products" className="bg-white text-indigo-600 px-8 py-3 rounded-lg font-medium hover:bg-indigo-50 transition-colors">
                        View Products
                    </Link>
                    <Link href="/about" className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-lg font-medium hover:bg-white/10 transition-colors">
                        About Us
                    </Link>
                </div>
            </div>
        </div>
    );
}
