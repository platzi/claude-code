// Course types
export interface Course {
  id: number;
  name: string;
  description: string;
  thumbnail: string;
  slug: string;
  // Campos opcionales de rating
  average_rating?: number; // 0.0 - 5.0
  total_ratings?: number; // Cantidad de ratings
}

// Class types (shape returned by /classes/{class_id} endpoint)
export interface Class {
  id: number;
  title: string;
  description: string;
  video: string;
  duration: number;
  slug: string;
}

// Class summary shape returned inside /courses/{slug} response
export interface CourseClass {
  id: number;
  name: string;
  description: string;
  slug: string;
}

// Course Detail type (shape returned by /courses/{slug} endpoint)
export interface CourseDetail extends Course {
  description: string;
  classes: CourseClass[];
  teacher_id: number[];
  rating_distribution?: Record<string, number>;
}

// Progress types
export interface Progress {
  progress: number; // seconds
  user_id: number;
}

// Quiz types
export interface QuizOption {
  id: number;
  answer: string;
  correct: boolean;
}

export interface Quiz {
  id: number;
  question: string;
  options: QuizOption[];
}

// Favorite types
export interface FavoriteToggle {
  course_id: number;
}