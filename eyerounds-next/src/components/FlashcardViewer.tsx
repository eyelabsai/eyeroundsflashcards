'use client';

import { useState, useEffect, useCallback } from 'react';
import { Flashcard } from '@/types/flashcard';
import ImageGallery from './ImageGallery';
import TreatmentAccordion from './TreatmentAccordion';

interface FlashcardViewerProps {
  flashcards: Flashcard[];
  initialIndex?: number;
}

export default function FlashcardViewer({ flashcards, initialIndex = 0 }: FlashcardViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [revealed, setRevealed] = useState(false);
  const [treatment, setTreatment] = useState<string | null>(null);
  const [loadingTreatment, setLoadingTreatment] = useState(false);
  const [treatmentCache, setTreatmentCache] = useState<Record<string, string>>({});

  const card = flashcards[currentIndex];

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % flashcards.length);
    setRevealed(false);
    setTreatment(null);
  }, [flashcards.length]);

  const goToPrev = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length);
    setRevealed(false);
    setTreatment(null);
  }, [flashcards.length]);

  const goToRandom = useCallback(() => {
    const newIndex = Math.floor(Math.random() * flashcards.length);
    setCurrentIndex(newIndex);
    setRevealed(false);
    setTreatment(null);
  }, [flashcards.length]);

  const reveal = useCallback(() => {
    setRevealed(true);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        return;
      }

      switch (e.key) {
        case ' ':
        case 'Enter':
          e.preventDefault();
          if (!revealed) reveal();
          break;
        case 'ArrowRight':
          e.preventDefault();
          goToNext();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          goToPrev();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [revealed, reveal, goToNext, goToPrev]);

  // Fetch treatment when revealed
  useEffect(() => {
    if (revealed && card && !treatment && !loadingTreatment) {
      const cached = treatmentCache[card.id];
      if (cached) {
        setTreatment(cached);
        return;
      }

      setLoadingTreatment(true);
      fetch('/api/treatment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: card.title,
          description: card.description,
          contributor: card.contributor,
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.treatment) {
            setTreatment(data.treatment);
            setTreatmentCache((prev) => ({ ...prev, [card.id]: data.treatment }));
          }
        })
        .catch(console.error)
        .finally(() => setLoadingTreatment(false));
    }
  }, [revealed, card, treatment, loadingTreatment, treatmentCache]);

  if (!card) {
    return <div className="text-center py-8">No flashcards available</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-2">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl p-4 mb-4 text-center">
        <h1 className="text-xl font-bold flex items-center justify-center gap-2">
          👁️ EyeRounds Flashcards
        </h1>
        <p className="text-blue-100 text-sm mt-1">
          Card {currentIndex + 1} of {flashcards.length}
        </p>
      </div>

      {/* Category Badge */}
      <div className="mb-3">
        <span className="inline-block bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
          {card.category}
        </span>
      </div>

      {/* Question/Title */}
      <h2 className="text-xl font-semibold mb-4">
        {revealed ? card.title : 'What is the diagnosis?'}
      </h2>

      {!revealed ? (
        <>
          {/* Images */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <h3 className="text-sm font-medium text-gray-600 mb-3 flex items-center gap-2">
              🖼️ Clinical Images
            </h3>
            <ImageGallery images={card.images} showCaptions={false} />
          </div>
          <div className="text-center py-6">
            <button
              onClick={reveal}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl"
            >
              👁️ Reveal Answer
            </button>
            <p className="text-gray-500 text-sm mt-3">
              Press <kbd className="bg-gray-200 px-2 py-0.5 rounded">Space</kbd> or{' '}
              <kbd className="bg-gray-200 px-2 py-0.5 rounded">Enter</kbd> to reveal
            </p>
          </div>
        </>
      ) : (
        {/* Side-by-side: images + answer on left, Oral Boards Study Guide on right */}
        <div className="grid gap-6 grid-cols-1 md:grid-cols-[1fr_1.2fr]">
          {/* Left: Images, Answer, Contributor */}
          <div className="space-y-4 min-w-0">
            <div className="bg-gray-50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-gray-600 mb-3 flex items-center gap-2">
                🖼️ Clinical Images
              </h3>
              <ImageGallery images={card.images} showCaptions={revealed} />
            </div>
            <div className="bg-green-50 border-l-4 border-green-500 rounded-r-xl p-4">
              <h3 className="text-green-700 font-semibold mb-2">✅ Answer</h3>
              <p className="font-bold text-lg">{card.title}</p>
              {card.description && (
                <p className="text-gray-700 mt-2 text-base">{card.description}</p>
              )}
            </div>
            {(card.contributor || card.photographer || card.source_url) && (
              <div className="text-sm text-gray-600 space-y-1">
                {card.contributor && <p><strong>Contributor:</strong> {card.contributor}</p>}
                {card.photographer && <p><strong>Photographer:</strong> {card.photographer}</p>}
                {card.source_url && (
                  <p>
                    <strong>Source:</strong>{' '}
                    <a href={card.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {card.source_url}
                    </a>
                  </p>
                )}
              </div>
            )}
          </div>
          {/* Right: Oral Boards Study Guide - wider, bigger font, all expanded */}
          <div className="min-w-0 flex flex-col min-h-0">
            <TreatmentAccordion treatment={treatment} loading={loadingTreatment} />
          </div>
        </div>
      )}

      {/* Floating Next Button */}
      <button
        onClick={goToNext}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white px-6 py-3 rounded-full font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2 z-50"
      >
        Next Card ➡️
      </button>

      {/* Keyboard hint */}
      <div className="fixed bottom-6 left-6 text-xs text-gray-400 hidden md:block">
        ⌨️ Space/Enter = reveal · ←/→ = navigate
      </div>
    </div>
  );
}
