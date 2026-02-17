import Hero from '@/components/Hero';
import FeatureList from '@/components/FeatureList';
import Footer from '@/components/Footer';
// import HeavyComponent from '@/components/HeavyComponent';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <Hero />
      <FeatureList />

      {/* 
        Uncomment the line below to simulate a performance regression (Total Blocking Time & LCP impact)
      */}
      {/* <HeavyComponent /> */}

      <Footer />
    </main>
  );
}
