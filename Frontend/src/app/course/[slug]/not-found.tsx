import Link from "next/link";
import styles from "./not-found.module.scss";

export default function NotFound() {
  return (
    <div className={styles.container}>
      <div className={styles.notFoundCard}>
        <h1 className={styles.title}>Curso no encontrado</h1>
        <p className={styles.message}>Lo sentimos, el curso que buscas no existe o ha sido removido.</p>
        <Link href="/" className={styles.homeButton}>
          Volver a cursos
        </Link>
      </div>
    </div>
  );
}
