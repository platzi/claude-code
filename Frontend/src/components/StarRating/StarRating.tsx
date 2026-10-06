/**
 * StarRating Component
 * Muestra un promedio de estrellas (solo lectura). Para votar, ver RatingInput.
 */

import { useId } from 'react';
import styles from './StarRating.module.scss';

interface StarRatingProps {
  rating: number; // 0-5, puede ser decimal
  totalRatings?: number; // Número total de ratings
  showCount?: boolean; // Mostrar contador de ratings
  size?: 'small' | 'medium' | 'large'; // Tamaño visual
  className?: string; // Clase CSS adicional
}

/**
 * Sub-componente: Icono de estrella con diferentes estados de relleno
 */
interface StarIconProps {
  fillState: 'empty' | 'half' | 'full';
  gradientId: string;
}

const StarIcon = ({ fillState, gradientId }: StarIconProps) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Gradient para media estrella: solo la estrella "half" lo define,
          y hay como mucho una por StarRating, así que el id es único en la página */}
      {fillState === 'half' && (
        <defs>
          <linearGradient id={gradientId}>
            <stop offset="50%" stopColor="currentColor" />
            <stop offset="50%" stopColor="transparent" />
          </linearGradient>
        </defs>
      )}
      <path
        d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
        fill={
          fillState === 'full'
            ? 'currentColor'
            : fillState === 'half'
            ? `url(#${gradientId})`
            : 'none'
        }
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

/**
 * Componente principal: StarRating
 */
export const StarRating = ({
  rating,
  totalRatings = 0,
  showCount = false,
  size = 'medium',
  className = '',
}: StarRatingProps) => {
  // Id único por instancia: con un id fijo, varias tarjetas en la misma página
  // compartirían el gradiente y el navegador usaría solo el primero.
  const gradientId = useId();

  /**
   * Determina el estado de relleno de cada estrella
   */
  const getStarFillState = (starIndex: number): 'empty' | 'half' | 'full' => {
    const currentRating = Math.max(0, Math.min(5, rating)); // Clamp 0-5

    if (currentRating >= starIndex) return 'full';
    if (currentRating >= starIndex - 0.5) return 'half';
    return 'empty';
  };

  // Formatear el rating para mostrar (1 decimal)
  const formattedRating = rating.toFixed(1);

  return (
    <div
      className={`${styles.starRating} ${styles[size]} ${className}`}
      role="img"
      aria-label={`Rating: ${formattedRating} out of 5 stars${
        showCount && totalRatings > 0 ? `, ${totalRatings} ratings` : ''
      }`}
    >
      <div className={styles.stars}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`${styles.star} ${styles[getStarFillState(star)]}`}
            aria-hidden="true"
          >
            <StarIcon fillState={getStarFillState(star)} gradientId={gradientId} />
          </span>
        ))}
      </div>

      {/* Contador de ratings (opcional) */}
      {showCount && totalRatings > 0 && (
        <span className={styles.count} aria-label={`${totalRatings} ratings`}>
          ({totalRatings})
        </span>
      )}
    </div>
  );
};
