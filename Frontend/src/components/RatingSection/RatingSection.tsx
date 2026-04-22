"use client";

import { useState, useEffect, useCallback } from "react";
import { ratingsApi } from "@/services/ratingsApi";
import { ApiError } from "@/types/rating";
import type { RatingStats, CourseRating } from "@/types/rating";
import { isValidRating } from "@/types/rating";
import styles from "./RatingSection.module.scss";

interface RatingSectionProps {
  courseId: number;
  initialStats: RatingStats;
}

const USER_ID = 1;

export const RatingSection = ({ courseId, initialStats }: RatingSectionProps) => {
  const [stats, setStats] = useState<RatingStats>(initialStats);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<"success" | "error" | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");

  useEffect(() => {
    ratingsApi
      .getUserRating(courseId, USER_ID)
      .then((existing: CourseRating | null) => {
        if (existing) setUserRating(existing.rating);
      })
      .catch(() => {});
  }, [courseId]);

  const refreshStats = useCallback(async () => {
    const updated = await ratingsApi.getRatingStats(courseId);
    setStats(updated);
  }, [courseId]);

  const handleStarClick = async (star: number) => {
    if (submitting || !isValidRating(star)) return;

    setSubmitting(true);
    setFeedback(null);
    setErrorMsg("");

    try {
      if (userRating === null) {
        await ratingsApi.createRating(courseId, { user_id: USER_ID, rating: star });
      } else {
        await ratingsApi.updateRating(courseId, USER_ID, { user_id: USER_ID, rating: star });
      }

      setUserRating(star);
      await refreshStats();
      setFeedback("success");
      setTimeout(() => setFeedback(null), 2000);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Error al guardar la calificación";
      setErrorMsg(message);
      setFeedback("error");
    } finally {
      setSubmitting(false);
    }
  };

  const displayRating = hovered ?? userRating ?? 0;

  return (
    <section className={styles.section} aria-label="Calificar este curso">
      <h2 className={styles.title}>Calificar curso</h2>

      <div className={styles.currentStats}>
        <span className={styles.average}>
          {stats.average_rating > 0 ? stats.average_rating.toFixed(1) : "—"}
        </span>
        <span className={styles.total}>
          {stats.total_ratings === 1
            ? "1 calificación"
            : `${stats.total_ratings} calificaciones`}
        </span>
      </div>

      <div
        className={styles.stars}
        role="group"
        aria-label="Selecciona una calificación del 1 al 5"
      >
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`${styles.star} ${displayRating >= star ? styles.active : ""}`}
            onClick={() => handleStarClick(star)}
            onMouseEnter={() => !submitting && setHovered(star)}
            onMouseLeave={() => setHovered(null)}
            disabled={submitting}
            aria-label={`Calificar con ${star} estrella${star > 1 ? "s" : ""}`}
            aria-pressed={userRating === star}
          >
            ★
          </button>
        ))}
      </div>

      {submitting && (
        <p className={styles.status} aria-live="polite">
          Guardando...
        </p>
      )}

      {!submitting && feedback === "success" && (
        <p className={`${styles.status} ${styles.statusSuccess}`} aria-live="polite">
          ¡Calificación guardada!
        </p>
      )}

      {!submitting && feedback === "error" && (
        <p className={`${styles.status} ${styles.statusError}`} aria-live="polite">
          {errorMsg}
        </p>
      )}
    </section>
  );
};
