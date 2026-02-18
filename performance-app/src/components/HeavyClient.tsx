'use client';

import { useEffect, useState } from 'react';

export default function HeavyClient() {
    const [isBlocking, setIsBlocking] = useState(false);

    useEffect(() => {
        // 🔴 INJECTED BUG: Freeze the browser main thread for 500ms
        const start = performance.now();
        while (performance.now() - start < 500) {
            // Busy wait - blocks UI
        }
        setIsBlocking(true);
    }, []);

    return (
        <div style={{ padding: '10px', background: '#ffebee', border: '1px solid red', fontSize: '12px' }}>
            {isBlocking ? "⚠️ Main Thread Lag Finished" : "Loading..."}
        </div>
    );
}
