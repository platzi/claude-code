"use client";

import { useEffect } from "react";
import styles from "./error.module.scss";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className={styles.container}>
      <div className={styles.errorCard}>
        <h1 className={styles.title}>¡Oops! Algo salió mal</h1>
        <p className={styles.message}>No pudimos cargar los detalles del curso. Por favor, inténtalo de nuevo.</p>
        <button className={styles.retryButton} onClick={() => reset()}>
          Intentar de nuevo
        </button>
      </div>
    </div>
  );
}
