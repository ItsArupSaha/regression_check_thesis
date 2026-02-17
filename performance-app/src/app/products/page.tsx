
import FeatureList from '@/components/FeatureList';
import Footer from '@/components/Footer';

export default function Products() {
    return (
        <main className="min-h-screen bg-gray-50">
            <div className="bg-gradient-to-r from-purple-600 to-pink-700 text-white py-20 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto text-center">
                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
                        Products Page
                    </h1>
                </div>
            </div>
            <FeatureList />
            <Footer />
        </main>
    );
}
