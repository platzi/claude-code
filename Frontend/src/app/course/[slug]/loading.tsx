import styles from "./loading.module.scss";

export default function Loading() {
  return (
    <div className={styles.container}>
      <div className={styles.loadingCard}>
        <div className={styles.spinner}></div>
        <h2 className={styles.title}>Cargando curso...</h2>
        <p className={styles.message}>Estamos preparando el contenido para ti</p>
      </div>
    </div>
  );
}
