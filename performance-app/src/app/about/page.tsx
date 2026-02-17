
import Footer from '@/components/Footer';

export default function About() {
    return (
        <main className="min-h-screen bg-gray-50">
            <div className="bg-gradient-to-r from-green-600 to-teal-700 text-white py-20 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto text-center">
                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
                        About Us
                    </h1>
                </div>
            </div>
            <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 bg-white min-h-[400px]">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Our Mission</h2>
                <p className="text-lg text-gray-700">
                    We are dedicated to building high-performance web applications and rigorously testing them against regressions.
                    This page is intentionally lightweight and static to serve as a control group for performance testing.
                </p>
            </div>
            <Footer />
        </main>
    );
}
