'use client';

import { useEffect, useRef, useState } from 'react';
import { useDualStreamCapture } from '@/features/useDualStreamCapture';

export default function TranscribePage() {
    const [isRunning, setIsRunning] = useState(false);
    const [extractResult, setExtractResult] = useState<string | null>(null);
    const [transcriptLines, setTranscriptLines] = useState<string[]>([]);
    const [quoteFields, setQuoteFields] = useState<Record<string, string>>({});
    const [captureError, setCaptureError] = useState<string | null>(null);
    const { start, stop } = useDualStreamCapture();
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const pollTranscript = async () => { try{ const response = await fetch('http://localhost:8000/transcript'); if (!response.ok) throw new Error('Failed to transcribe'); const data = await response.json(); setTranscriptLines(data.lines) }catch(error){ console.error(error)}
    }

    useEffect(() => {
        if (isRunning) {
            setTranscriptLines([]);
            pollRef.current = setInterval(pollTranscript, 2000);
        } else {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        }

        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        };
    }, [isRunning]);

    const handleStart = async () => {
        try {
            const response = await fetch('http://localhost:8000/start', { method: 'POST' });
            if (!response.ok) throw new Error('Failed to start transcription');
            setIsRunning(true);
        } catch (error) {
            console.error(error);
            return;    
        }
        try{
            setCaptureError(null);
            await start();
        } catch (error: any) {
            console.error('Capture error:', error); // ← add this
            setCaptureError(error.message ?? 'Audio capture failed');
            await fetch('http://localhost:8000/stop', { method: 'POST' });
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
            setQuoteFields(data.pdf_data);
        } catch (error) {
            console.error(error);
        }
    };

    const handleFieldChange = (field: string, value: string) => {
        setQuoteFields((prev) => ({ ...prev, [field]: value }));
    };

    const handleGenerateQuote = async () => {
            try {
                if (!quoteFields) throw new Error('No quote fields available');
                const response = await fetch('http://localhost:8000/quote', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(quoteFields),
                });
                if (!response.ok) throw new Error('Failed to generate quote');

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'quote.pdf';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error(error);
                setCaptureError('Failed to generate quote. Please try again.');
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
                        {captureError && (
                            <p className="text-xs text-red-500 mt-2">{captureError}</p>
                        )}
                    </div>
                </div>

                {/* Live transcript */}
                <div className="p-6 border-b border-gray-100">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
                        Live Transcript
                    </p>
                    {transcriptLines.length > 0 ? (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {transcriptLines.map((line, i) => (
                                <p key={i} className="text-sm text-gray-700 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
                                    {line}
                                </p>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-gray-400">
                            {isRunning ? 'Waiting for speech...' : 'No transcript yet — start a session.'}
                        </p>
                    )}
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
                {/* Quote Form */}
                {Object.keys(quoteFields).length > 0 && (
                    <div className="p-6 border-t border-gray-100">
                        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
                            Quote Parameters
                        </p>
                        <div className="space-y-2">
                            {Object.entries(quoteFields).map(([key, value]) => (
                                <div key={key} className="flex items-center gap-2">
                                    <label className="text-sm text-gray-500 w-32">
                                        {key.replace('_', ' ')}:
                                    </label>
                                    <input
                                        type="text"
                                        value={value}
                                        onChange={(e) => handleFieldChange(key, e.target.value)}
                                        className="text-sm text-gray-700 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            ))}
                            <button
                                onClick={handleGenerateQuote}
                                className="bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
                            >
                                Generate Quote
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}