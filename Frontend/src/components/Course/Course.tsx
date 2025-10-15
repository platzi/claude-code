import styles from "./Course.module.scss";
import { Course as CourseType } from "@/types";

type CourseProps = Omit<CourseType, "slug">;

export const Course = ({ id, name, description, thumbnail }: CourseProps) => {
  return (
    <article className={styles.courseCard}>
      <div className={styles.thumbnailContainer}>
        <img src={thumbnail} alt={name} className={styles.thumbnail} />
      </div>
      <div className={styles.courseInfo}>
        <h2 className={styles.courseTitle}>{name}</h2>
        <p className={styles.description}>{description}</p>
      </div>
    </article>
  );
};
