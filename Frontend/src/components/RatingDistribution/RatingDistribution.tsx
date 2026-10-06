/**
 * RatingDistribution Component
 * Muestra cuántos votos tiene cada estrella (5 → 1) como barras proporcionales.
 */

import type { RatingDistribution as Distribution } from "@/types/rating";
import styles from "./RatingDistribution.module.scss";

interface RatingDistributionProps {
  distribution: Distribution;
  totalRatings: number;
}

const ROWS = ["5", "4", "3", "2", "1"] as const;

export const RatingDistribution = ({ distribution, totalRatings }: RatingDistributionProps) => {
  return (
    <div className={styles.distribution}>
      <ul className={styles.rows}>
        {ROWS.map((star) => {
          const count = distribution[star] ?? 0;
          const percent = totalRatings > 0 ? Math.round((count / totalRatings) * 100) : 0;
          const label = `${star} ${star === "1" ? "estrella" : "estrellas"}: ${count} ${
            count === 1 ? "voto" : "votos"
          } (${percent}%)`;

          return (
            <li key={star}>
              <div role="img" aria-label={label} className={styles.row}>
                <span className={styles.star}>{star} ★</span>
                <span className={styles.bar}>
                  <span className={styles.fill} style={{ width: `${percent}%` }} />
                </span>
                <span className={styles.count}>{count}</span>
              </div>
            </li>
          );
        })}
      </ul>
      <p className={styles.total}>
        {totalRatings} {totalRatings === 1 ? "valoración" : "valoraciones"}
      </p>
    </div>
  );
};
