import { NextResponse } from 'next/server';

export async function GET() {
    // Simulate complex database query (REGRESSION)
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const products = Array.from({ length: 20 }).map((_, i) => ({
        id: i + 1,
        name: `Performance Product ${i + 1}`,
        description: `High-speed product description for item ${i + 1}.`,
        price: (Math.random() * 100).toFixed(2),
    }));

    return NextResponse.json(products);
}
