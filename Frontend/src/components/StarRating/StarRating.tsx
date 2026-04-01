/**
 * StarRating Component
 * Componente de calificación con estrellas.
 * Soporta modo readonly (display) e interactivo (submit de rating).
 */

'use client';

import React, { useState, useRef } from 'react';
import styles from './StarRating.module.scss';

interface StarRatingProps {
  rating: number; // 0-5, puede ser decimal
  onRatingChange?: (rating: number) => void; // Callback para modo interactivo
  totalRatings?: number; // Número total de ratings
  showCount?: boolean; // Mostrar contador de ratings
  size?: 'small' | 'medium' | 'large'; // Tamaño visual
  readonly?: boolean; // Modo solo lectura
  disabled?: boolean; // Deshabilitar interacción (ej: durante API call)
  className?: string; // Clase CSS adicional
}

/**
 * Sub-componente: Icono de estrella con diferentes estados de relleno
 */
interface StarIconProps {
  fillState: 'empty' | 'half' | 'full';
}

const StarIcon = ({ fillState }: StarIconProps) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        {/* Gradient para media estrella */}
        <linearGradient id="halfStarGradient">
          <stop offset="50%" stopColor="currentColor" />
          <stop offset="50%" stopColor="transparent" />
        </linearGradient>
      </defs>
      <path
        d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
        fill={
          fillState === 'full'
            ? 'currentColor'
            : fillState === 'half'
            ? 'url(#halfStarGradient)'
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
  onRatingChange,
  totalRatings = 0,
  showCount = false,
  size = 'medium',
  readonly = false,
  disabled = false,
  className = '',
}: StarRatingProps) => {
  const [hoverRating, setHoverRating] = useState(0);
  const starRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Modo interactivo: solo cuando hay callback y no es readonly
  const isInteractive = !readonly && !!onRatingChange;

  /**
   * Determina el estado de relleno de cada estrella.
   * En modo interactivo, prioriza hoverRating para feedback visual.
   */
  const getStarFillState = (starIndex: number): 'empty' | 'half' | 'full' => {
    const displayRating =
      isInteractive && hoverRating > 0
        ? hoverRating
        : Math.max(0, Math.min(5, rating));

    if (displayRating >= starIndex) return 'full';
    if (displayRating >= starIndex - 0.5) return 'half';
    return 'empty';
  };

  const handleMouseEnter = (star: number) => {
    if (disabled) return;
    setHoverRating(star);
  };

  const handleMouseLeave = () => {
    setHoverRating(0);
  };

  const handleClick = (star: number) => {
    if (disabled) return;
    onRatingChange?.(star);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, star: number) => {
    if (disabled) return;

    if (e.key === 'ArrowRight' && star < 5) {
      e.preventDefault();
      starRefs.current[star]?.focus(); // star es 1-based; refs[star] = siguiente estrella
    } else if (e.key === 'ArrowLeft' && star > 1) {
      e.preventDefault();
      starRefs.current[star - 2]?.focus(); // refs[star-2] = estrella anterior
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onRatingChange?.(star);
    } else if (e.key === 'Escape') {
      setHoverRating(0);
    }
  };

  const formattedRating = rating.toFixed(1);

  // ── Modo interactivo ──────────────────────────────────────────────────────
  if (isInteractive) {
    return (
      <div
        className={`${styles.starRating} ${styles[size]} ${className}`}
        role="group"
        aria-label={`Rating: ${formattedRating} out of 5 stars`}
        onMouseLeave={handleMouseLeave}
      >
        <div className={styles.stars}>
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              ref={(el) => { starRefs.current[star - 1] = el; }}
              className={`${styles.star} ${styles[getStarFillState(star)]}`}
              onClick={() => handleClick(star)}
              onMouseEnter={() => handleMouseEnter(star)}
              onKeyDown={(e) => handleKeyDown(e, star)}
              disabled={disabled}
              aria-label={`Rate ${star} stars`}
              aria-pressed={rating === star}
            >
              <StarIcon fillState={getStarFillState(star)} />
            </button>
          ))}
        </div>

        {showCount && totalRatings > 0 && (
          <span className={styles.count} aria-label={`${totalRatings} ratings`}>
            ({totalRatings})
          </span>
        )}
      </div>
    );
  }

  // ── Modo readonly / display ───────────────────────────────────────────────
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
            <StarIcon fillState={getStarFillState(star)} />
          </span>
        ))}
      </div>

      {showCount && totalRatings > 0 && (
        <span className={styles.count} aria-label={`${totalRatings} ratings`}>
          ({totalRatings})
        </span>
      )}
    </div>
  );
};
