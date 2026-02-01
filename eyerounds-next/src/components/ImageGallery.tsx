'use client';

import { useState } from 'react';
import { FlashcardImage } from '@/types/flashcard';
import Image from 'next/image';

interface ImageGalleryProps {
  images: FlashcardImage[];
  showCaptions?: boolean;
}

export default function ImageGallery({ images, showCaptions = false }: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<FlashcardImage | null>(null);
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  // Filter out duplicates
  const uniqueImages = images.filter((img, index, self) => 
    index === self.findIndex((t) => t.url === img.url)
  );

  if (uniqueImages.length === 0) {
    return (
      <p className="text-gray-500 text-center py-4">No images available for this card.</p>
    );
  }

  const handleImageError = (url: string) => {
    setImageErrors((prev) => new Set(prev).add(url));
  };

  return (
    <>
      {/* Image Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {uniqueImages.map((img, index) => (
          !imageErrors.has(img.url) && (
            <div
              key={index}
              className="relative aspect-square bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
              onClick={() => setSelectedImage(img)}
            >
              <Image
                src={img.url}
                alt={img.alt || 'Clinical image'}
                fill
                className="object-contain p-2"
                sizes="(max-width: 768px) 50vw, 33vw"
                onError={() => handleImageError(img.url)}
                unoptimized
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                <span className="opacity-0 group-hover:opacity-100 text-white bg-black/50 px-2 py-1 rounded text-sm">
                  🔍 Expand
                </span>
              </div>
              {showCaptions && img.alt && (
                <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white text-xs p-2 line-clamp-2">
                  {img.alt}
                </div>
              )}
            </div>
          )
        ))}
      </div>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <button
            className="absolute top-4 right-4 text-white text-3xl hover:text-gray-300"
            onClick={() => setSelectedImage(null)}
          >
            ×
          </button>
          <div className="relative max-w-4xl max-h-[90vh] w-full h-full">
            <Image
              src={selectedImage.url}
              alt={selectedImage.alt || 'Clinical image'}
              fill
              className="object-contain"
              sizes="100vw"
              unoptimized
            />
          </div>
          {showCaptions && selectedImage.alt && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-lg max-w-lg text-center">
              {selectedImage.alt}
            </div>
          )}
        </div>
      )}
    </>
  );
}
