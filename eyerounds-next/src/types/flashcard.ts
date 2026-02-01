export interface FlashcardImage {
  url: string;
  alt: string;
  figure_label?: string;
}

export interface Flashcard {
  id: string;
  category: string;
  title: string;
  description: string;
  contributor: string;
  photographer: string;
  source_url: string;
  images: FlashcardImage[];
}

export interface FlashcardData {
  total: number;
  categories: string[];
  flashcards: Flashcard[];
}
