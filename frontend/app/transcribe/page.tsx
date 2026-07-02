'use client';

import { useState } from 'react';
import { useDualStreamCapture } from '@/features/useDualStreamCapture';

export default function TranscribePage() {
    const [isRunning, setIsRunning] = useState(false);
    const [extractResult, setExtractResult] = useState<string | null>(null);
    const { start, stop } = useDualStreamCapture();

    const handleStart = async () => {
        try {
            const response = await fetch('http://localhost:8000/start', { method: 'POST' });
            if (!response.ok) throw new Error('Failed to start transcription');
            await start(); // opens mic + tab-audio capture, opens both WS connections
            setIsRunning(true);
        } catch (error) {
            console.error(error);
            setIsRunning(false);
        }
    };

    const handleStop = async () => {
        stop(); // closes both WS connections, audio contexts, and media tracks
        setIsRunning(false);
        try {
            const response = await fetch('http://localhost:8000/stop', { method: 'POST' });
            if (!response.ok) throw new Error('Failed to stop transcription');
        } catch (error) {
            console.error(error);
        }
    };

    const handleExtract = async () => {
        try {
            const response = await fetch('http://localhost:8000/extract', { method: 'POST' });
            if (!response.ok) throw new Error('Failed to extract');
            const data = await response.json();
            setExtractResult(data.result);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div className="max-w-2xl mx-auto px-4 py-6 text-gray-900">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <div className="text-3xl">🎙</div>
                <div>
                    <h2 className="text-xl font-semibold">Live Transcription</h2>
                    <p className="text-sm text-gray-500">
                        Record a sales call and extract quote parameters
                    </p>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
                {/* Session controls */}
                <div className="p-6 border-b border-gray-100">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
                        Session
                    </p>
                    <div className="flex items-center gap-3">
                        {/* Status indicator */}
                        <span className="flex items-center gap-2 text-sm text-gray-500">
                            <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
                            {isRunning ? 'Listening...' : 'Idle'}
                        </span>

                        <div className="flex gap-2 ml-auto">
                            {!isRunning ? (
                                <button
                                    onClick={handleStart}
                                    className="bg-black hover:bg-green-600 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
                                >
                                    Start Recording
                                </button>
                            ) : (
                                <button
                                    onClick={handleStop}
                                    className="bg-red-500 hover:bg-red-600 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
                                >
                                    Stop
                                </button>
                            )}
                            <button
                                onClick={handleExtract}
                                disabled={!isRunning && !extractResult}
                                className="bg-white border border-gray-200 hover:border-gray-400 text-gray-700 text-sm font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                                Extract & Generate
                            </button>
                        </div>
                    </div>
                </div>

                {/* Result */}
                <div className="p-6">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
                        Extracted Parameters
                    </p>
                    {extractResult ? (
                        <pre className="text-sm text-gray-700 bg-gray-50 border border-gray-100 rounded-xl p-4 whitespace-pre-wrap break-words">
                            {extractResult}
                        </pre>
                    ) : (
                        <p className="text-sm text-gray-400">
                            No extraction yet — start a session and click Extract & Generate.
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}