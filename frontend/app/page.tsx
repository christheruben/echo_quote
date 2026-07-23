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
            console.error('Capture error:', error);
            setCaptureError(error.message ?? 'Audio capture failed');
            await fetch('http://localhost:8000/stop', { method: 'POST' });
            setIsRunning(false);
        }
    };

    const handleStop = async () => {
        stop();
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
        <div className="max-w-2xl mx-auto px-4">
            {/* Hero */}
            <section className="py-14">
                <div className="flex items-center gap-2 mb-5">
                    <span className="flex items-end gap-[3px] h-4" aria-hidden="true">
                        {[0, 1, 2, 3, 4].map((i) => (
                            <span
                                key={i}
                                className="waveform-bar w-[3px] h-full bg-green-500 rounded-full"
                                style={{ animationDelay: `${i * 0.15}s` }}
                            />
                        ))}
                    </span>
                    <span className="text-xs font-mono uppercase tracking-wider text-gray-500">
                        Live on the call
                    </span>
                </div>

                <h1 className="text-3xl sm:text-4xl font-semibold text-gray-900 leading-tight tracking-tight">
                    Turn the call into a quote<br />before you hang up.
                </h1>

                <p className="mt-4 text-gray-500 max-w-md leading-relaxed">
                    Echo listens to both sides of a solar sales call, pulls out what matters
                    — property type, roof, monthly bill — and turns it into a quote you can
                    send before the customer's off the line.
                </p>

                <div className="mt-7 flex flex-wrap gap-3">
                    
                    <a    href="#session"
                        className="bg-black hover:bg-gray-800 text-white text-sm font-medium py-2.5 px-5 rounded-lg transition-colors"
                    >
                        Start a call
                    </a>
                    
                    <a    href="/calculator"
                        className="border border-gray-200 hover:border-gray-400 text-gray-700 text-sm font-medium py-2.5 px-5 rounded-lg transition-colors"
                    >
                        Try the calculator instead
                    </a>
                </div>
            </section>

            {/* How it works */}
            <section className="pb-14 grid grid-cols-1 sm:grid-cols-3 gap-6">
                {[
                    { n: '01', title: 'Start the call', body: 'Hit start — Echo listens in on both sides of the conversation.' },
                    { n: '02', title: 'Talk through the basics', body: 'Name, property type, roof, monthly bill — said naturally, no script required.' },
                    { n: '03', title: 'Review and download', body: 'Check what was extracted, adjust anything, get your PDF quote.' },
                ].map((step) => (
                    <div key={step.n}>
                        <span className="text-xs font-mono text-gray-400">{step.n}</span>
                        <h3 className="text-sm font-semibold text-gray-900 mt-1">{step.title}</h3>
                        <p className="text-sm text-gray-500 mt-1 leading-relaxed">{step.body}</p>
                    </div>
                ))}
            </section>

            {/* Session controls + everything below, unchanged */}
            <div id="session" className="bg-white border border-gray-200 rounded-2xl overflow-hidden mb-14">
                <div className="p-6 border-b border-gray-100">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
                        Session
                    </p>
                    <div className="flex items-center gap-3">
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
                    {captureError && (
                        <p className="text-xs text-red-500 mt-2">{captureError}</p>
                    )}
                </div>

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