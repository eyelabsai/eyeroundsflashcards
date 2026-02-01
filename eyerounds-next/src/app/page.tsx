'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { FlashcardData, Flashcard } from '@/types/flashcard';
import FlashcardViewer from '@/components/FlashcardViewer';
import Sidebar from '@/components/Sidebar';

export default function Home() {
  const [data, setData] = useState<FlashcardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);

  // Load flashcard data
  useEffect(() => {
    fetch('/flashcards.json')
      .then((res) => res.json())
      .then((json: FlashcardData) => {
        setData(json);
        // Start with random card
        if (json.flashcards.length > 0) {
          setCurrentIndex(Math.floor(Math.random() * json.flashcards.length));
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load flashcards:', err);
        setLoading(false);
      });
  }, []);

  // Filter flashcards
  const filteredCards = useMemo(() => {
    if (!data) return [];

    let cards = data.flashcards;

    // Filter by category
    if (selectedCategory !== 'ALL') {
      cards = cards.filter((c) => c.category === selectedCategory);
    }

    // Filter by search
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      cards = cards.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q)
      );
    }

    return cards;
  }, [data, selectedCategory, searchTerm]);

  // Clamp index when filter changes
  useEffect(() => {
    if (filteredCards.length > 0 && currentIndex >= filteredCards.length) {
      setCurrentIndex(0);
    }
  }, [filteredCards, currentIndex]);

  // Navigation handlers
  const goToNext = useCallback(() => {
    if (filteredCards.length === 0) return;
    setCurrentIndex((prev) => (prev + 1) % filteredCards.length);
    setRevealed(false);
  }, [filteredCards.length]);

  const goToPrev = useCallback(() => {
    if (filteredCards.length === 0) return;
    setCurrentIndex((prev) => (prev - 1 + filteredCards.length) % filteredCards.length);
    setRevealed(false);
  }, [filteredCards.length]);

  const goToRandom = useCallback(() => {
    if (filteredCards.length === 0) return;
    setCurrentIndex(Math.floor(Math.random() * filteredCards.length));
    setRevealed(false);
  }, [filteredCards.length]);

  const handleCategoryChange = useCallback((cat: string) => {
    setSelectedCategory(cat);
    setCurrentIndex(0);
    setRevealed(false);
  }, []);

  const handleSearchChange = useCallback((term: string) => {
    setSearchTerm(term);
    setCurrentIndex(0);
    setRevealed(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading flashcards...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-600">Failed to load flashcards.</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar
        categories={data.categories}
        selectedCategory={selectedCategory}
        onCategoryChange={handleCategoryChange}
        searchTerm={searchTerm}
        onSearchChange={handleSearchChange}
        totalCards={data.total}
        filteredCount={filteredCards.length}
        currentIndex={currentIndex}
        onJumpToCard={(idx) => {
          setCurrentIndex(idx);
          setRevealed(false);
        }}
        onRandom={goToRandom}
        onPrev={goToPrev}
        onNext={goToNext}
      />

      <main className="flex-1 p-4 md:p-6 md:ml-0">
        {filteredCards.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No flashcards match your filters.</p>
          </div>
        ) : (
          <FlashcardViewer
            flashcards={filteredCards}
            initialIndex={currentIndex}
            key={`${selectedCategory}-${searchTerm}-${currentIndex}`}
          />
        )}
      </main>
    </div>
  );
}