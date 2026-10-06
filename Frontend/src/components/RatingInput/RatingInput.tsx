"use client";

/**
 * RatingInput Component
 * Permite al usuario calificar un curso (1-5), cambiar o quitar su calificación.
 *
 * Accesibilidad: es un radiogroup nativo (<fieldset> + <input type="radio">),
 * así que Tab, flechas y lectores de pantalla funcionan sin JS adicional.
 */

import { useId, useOptimistic, useState, useTransition } from "react";
import type { ActionResult } from "@/types/rating";
import styles from "./RatingInput.module.scss";

interface RatingInputProps {
  initialRating: number | null;
  onRate: (rating: number) => Promise<ActionResult>;
  onRemove: () => Promise<ActionResult>;
}

type Status = { type: "success" | "error"; message: string } | null;

const STARS = [1, 2, 3, 4, 5] as const;

const starLabel = (value: number) => `${value} ${value === 1 ? "estrella" : "estrellas"}`;

export const RatingInput = ({ initialRating, onRate, onRemove }: RatingInputProps) => {
  // Valor confirmado por el servidor. Se sincroniza si el prop cambia
  // (p. ej. tras revalidatePath) sin remontar el componente ni perder el foco.
  const [rating, setRating] = useState(initialRating);
  const [prevInitialRating, setPrevInitialRating] = useState(initialRating);
  if (initialRating !== prevInitialRating) {
    setPrevInitialRating(initialRating);
    setRating(initialRating);
  }

  // Mientras la acción está en curso se muestra el valor optimista; al terminar
  // la transición vuelve a `rating`, que solo cambia si el servidor confirmó.
  const [optimisticRating, setOptimisticRating] = useOptimistic(rating);
  const [isPending, startTransition] = useTransition();
  const [hovered, setHovered] = useState<number | null>(null);
  const [status, setStatus] = useState<Status>(null);
  const groupName = useId();

  const submit = (
    nextRating: number | null,
    action: () => Promise<ActionResult>,
    successMessage: string
  ) => {
    if (isPending) return;
    setStatus(null);
    startTransition(async () => {
      setOptimisticRating(nextRating);
      const result = await action();
      startTransition(() => {
        if (result.ok) {
          setRating(result.rating);
          setStatus({ type: "success", message: successMessage });
        } else {
          setStatus({ type: "error", message: result.error });
        }
      });
    });
  };

  const handleRate = (value: number) =>
    submit(value, () => onRate(value), `Guardado: ${starLabel(value)}.`);

  const handleRemove = () => submit(null, onRemove, "Calificación eliminada.");

  const displayed = hovered ?? optimisticRating ?? 0;

  return (
    <div className={styles.ratingInput}>
      <fieldset className={styles.fieldset} aria-busy={isPending}>
        <legend className={styles.legend}>Califica este curso</legend>
        <div className={styles.stars} onMouseLeave={() => setHovered(null)}>
          {STARS.map((value) => {
            const id = `${groupName}-${value}`;
            return (
              <span key={value} className={styles.option}>
                <input
                  type="radio"
                  id={id}
                  name={groupName}
                  value={value}
                  checked={optimisticRating === value}
                  onChange={() => handleRate(value)}
                  className={styles.radio}
                />
                <label
                  htmlFor={id}
                  className={`${styles.star} ${value <= displayed ? styles.filled : ""}`}
                  onMouseEnter={() => setHovered(value)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
                  </svg>
                  <span className={styles.visuallyHidden}>{starLabel(value)}</span>
                </label>
              </span>
            );
          })}
        </div>
      </fieldset>

      <p className={styles.current}>
        {optimisticRating
          ? `Tu calificación: ${optimisticRating} de 5`
          : "Aún no has calificado este curso"}
      </p>

      {optimisticRating !== null && (
        <button
          type="button"
          className={styles.removeButton}
          onClick={handleRemove}
          disabled={isPending}
        >
          Quitar calificación
        </button>
      )}

      <p
        role="status"
        className={`${styles.status} ${status?.type === "error" ? styles.error : styles.success}`}
      >
        {status?.message}
      </p>
    </div>
  );
};
