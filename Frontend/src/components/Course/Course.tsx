import styles from "./Course.module.scss";
import { Course as CourseType } from "@/types";
import { StarRating } from "@/components/StarRating/StarRating";
import { CourseThumbnail } from "./CourseThumbnail";

type CourseProps = Omit<CourseType, "slug">;

export const Course = ({
  name,
  description,
  thumbnail,
  average_rating,
  total_ratings
}: CourseProps) => {
  return (
    <article className={styles.courseCard}>
      <div className={styles.thumbnailContainer}>
        <CourseThumbnail src={thumbnail} alt={name} name={name} />
      </div>
      <div className={styles.courseInfo}>
        <h2 className={styles.courseTitle}>{name}</h2>
        <p className={styles.description}>{description}</p>

        {typeof average_rating === 'number' && average_rating > 0 && (
          <div className={styles.ratingContainer}>
            <StarRating
              rating={average_rating}
              totalRatings={total_ratings}
              showCount={true}
              size="small"
              readonly={true}
            />
            <span className={styles.ratingValue}>{average_rating.toFixed(1)}</span>
          </div>
        )}
      </div>
    </article>
  );
};
