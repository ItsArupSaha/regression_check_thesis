
export default function Footer() {
    return (
        <footer className="bg-gray-800 text-white">
            <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center">
                    <div>
                        <p className="text-base text-gray-400">&copy; 2026 Performance Thesis. All rights reserved.</p>
                    </div>
                    <div className="flex space-x-6">
                        <a href="#" className="text-gray-400 hover:text-white">
                            Privacy
                        </a>
                        <a href="#" className="text-gray-400 hover:text-white">
                            Terms
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
