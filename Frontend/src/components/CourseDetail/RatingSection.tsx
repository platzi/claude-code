'use client';

/**
 * RatingSection Component
 * Sección interactiva de ratings para la página de detalle de curso.
 * Permite al usuario calificar el curso y muestra el rating general.
 */

import { useState, useEffect } from 'react';
import { StarRating } from '@/components/StarRating/StarRating';
import { ratingsApi, ApiError } from '@/services/ratingsApi';
import styles from './RatingSection.module.scss';

/**
 * Calcula el nuevo promedio localmente para optimistic updates
 */
function calculateOptimisticAverage(
  currentAverage: number,
  currentTotal: number,
  oldRating: number,
  newRating: number,
  isNewRating: boolean
): number {
  if (currentTotal === 0 || isNewRating) {
    const sum = currentAverage * currentTotal + newRating;
    return Math.round((sum / (currentTotal + 1)) * 10) / 10;
  }
  const sum = currentAverage * currentTotal - oldRating + newRating;
  return Math.round((sum / currentTotal) * 10) / 10;
}

interface RatingSectionProps {
  courseId: number;
  initialAverageRating?: number;
  initialTotalRatings?: number;
}

export const RatingSection = ({
  courseId,
  initialAverageRating = 0,
  initialTotalRatings = 0,
}: RatingSectionProps) => {
  const [userId, setUserId] = useState<number | null>(null);
  const [userRating, setUserRating] = useState(0);
  const [averageRating, setAverageRating] = useState(initialAverageRating);
  const [totalRatings, setTotalRatings] = useState(initialTotalRatings);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Generar o recuperar userId anónimo desde localStorage
  useEffect(() => {
    try {
      const KEY = 'platziflix_user_id';
      let uuid = localStorage.getItem(KEY);
      if (!uuid) {
        uuid = crypto.randomUUID();
        localStorage.setItem(KEY, uuid);
      }
      const id = parseInt(uuid.replace(/-/g, '').slice(0, 8), 16) % 2147483647 || 1;
      setUserId(id);
    } catch {
      // localStorage no disponible: generar en memoria sin persistir
      const uuid = crypto.randomUUID();
      setUserId(parseInt(uuid.replace(/-/g, '').slice(0, 8), 16) % 2147483647 || 1);
    }
  }, []);

  // Cargar rating existente del usuario al montar
  useEffect(() => {
    if (userId === null) return;

    const loadUserRating = async () => {
      try {
        const userRatingData = await ratingsApi.getUserRating(courseId, userId);
        if (userRatingData) {
          setUserRating(userRatingData.rating);
        }
      } catch {
        // No crítico: si falla, el usuario simplemente no ve su rating previo
      }
    };

    loadUserRating();
  }, [courseId, userId]);

  const handleRatingChange = async (newRating: number) => {
    if (userId === null) return;

    const previousRating = userRating;
    const previousAverage = averageRating;
    const previousTotal = totalRatings;
    const isNewRating = previousRating === 0;

    // Optimistic update
    setUserRating(newRating);
    setIsLoading(true);
    setError(null);

    const newAverage = calculateOptimisticAverage(
      previousAverage,
      previousTotal,
      previousRating,
      newRating,
      isNewRating
    );
    setAverageRating(newAverage);
    if (isNewRating) setTotalRatings(previousTotal + 1);

    try {
      await ratingsApi.createRating(courseId, { user_id: userId, rating: newRating });

      setSuccessMessage('Rating guardado exitosamente');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      // Rollback al estado previo
      setUserRating(previousRating);
      setAverageRating(previousAverage);
      setTotalRatings(previousTotal);

      const errorMessage =
        err instanceof ApiError
          ? err.message
          : 'Error al guardar rating. Por favor intenta de nuevo.';
      setError(errorMessage);
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className={styles.ratingSection}>
      <div className={styles.userRating}>
        <h3 className={styles.title}>Califica este curso</h3>
        <StarRating
          rating={userRating}
          onRatingChange={handleRatingChange}
          size="large"
          disabled={isLoading}
        />

        {isLoading && <p className={styles.loadingText}>Guardando...</p>}

        {error && (
          <p className={styles.errorText} role="alert">
            {error}
          </p>
        )}

        {successMessage && (
          <p className={styles.successText} role="status">
            {successMessage}
          </p>
        )}
      </div>

      <div className={styles.ratingsStats}>
        <h4 className={styles.statsTitle}>Rating general</h4>
        <StarRating
          rating={averageRating}
          readonly={true}
          size="medium"
          showCount={true}
          totalRatings={totalRatings}
        />
        <p className={styles.statsDescription}>
          Basado en {totalRatings} {totalRatings === 1 ? 'valoración' : 'valoraciones'}
        </p>
      </div>
    </section>
  );
};
