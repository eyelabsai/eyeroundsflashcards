'use client';

import { useState } from 'react';

interface SidebarProps {
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  totalCards: number;
  filteredCount: number;
  currentIndex: number;
  onJumpToCard: (index: number) => void;
  onRandom: () => void;
  onPrev: () => void;
  onNext: () => void;
}

export default function Sidebar({
  categories,
  selectedCategory,
  onCategoryChange,
  searchTerm,
  onSearchChange,
  totalCards,
  filteredCount,
  currentIndex,
  onJumpToCard,
  onRandom,
  onPrev,
  onNext,
}: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 bg-blue-600 text-white p-2 rounded-lg shadow-lg"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? '✕' : '☰'}
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:sticky top-0 left-0 h-screen w-72 bg-white shadow-xl z-40 transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } overflow-y-auto`}
      >
        <div className="p-4 space-y-4">
          {/* Logo */}
          <div className="text-center py-2 border-b">
            <h1 className="text-xl font-bold text-blue-600">👁️ EyeRounds</h1>
            <p className="text-xs text-gray-500">Ophthalmology Flashcards</p>
          </div>

          {/* Search */}
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">
              🔍 Search
            </label>
            <input
              type="text"
              placeholder="e.g. retinitis pigmentosa"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Category Filter */}
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">
              📂 Filter by Topic
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => onCategoryChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="ALL">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 py-2 border-y">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{filteredCount}</p>
              <p className="text-xs text-gray-500">Available</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-400">{totalCards}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
          </div>

          {/* Navigation */}
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-2">
              Navigation
            </label>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <button
                onClick={onPrev}
                className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
              >
                ⬅️ Prev
              </button>
              <button
                onClick={onNext}
                className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
              >
                Next ➡️
              </button>
            </div>
            <button
              onClick={onRandom}
              className="w-full px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg text-sm font-medium transition-colors"
            >
              🎲 Random Card
            </button>
          </div>

          {/* Jump to Card */}
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">
              Jump to Card
            </label>
            <input
              type="number"
              min={1}
              max={filteredCount}
              value={currentIndex + 1}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (val >= 1 && val <= filteredCount) {
                  onJumpToCard(val - 1);
                }
              }}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
        </div>
      </aside>
    </>
  );
}
