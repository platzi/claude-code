import type { RatingDistribution } from "./rating";

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

// Resumen de clase dentro de GET /courses/{slug}
export interface ClassSummary {
  id: number;
  name: string;
  description: string;
  slug: string;
}

// Respuesta de GET /classes/{class_id}
export interface ClassDetail {
  id: number;
  title: string;
  description: string;
  slug: string;
  video: string;
  duration: number;
}

export interface TeacherSummary {
  id: number;
  name: string;
}

// Course Detail type
export interface CourseDetail extends Course {
  classes: ClassSummary[];
  teacher_id: number[];
  teachers?: TeacherSummary[];
  rating_distribution?: RatingDistribution;
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
