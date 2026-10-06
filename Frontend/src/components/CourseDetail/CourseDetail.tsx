import { FC } from "react";
import Link from "next/link";
import { CourseDetail } from "@/types";
import type { ActionResult } from "@/types/rating";
import { StarRating } from "@/components/StarRating/StarRating";
import { RatingDistribution } from "@/components/RatingDistribution/RatingDistribution";
import { RatingInput } from "@/components/RatingInput/RatingInput";
import styles from "./CourseDetail.module.scss";

interface CourseDetailComponentProps {
  course: CourseDetail;
  /** Rating actual del usuario (null si no ha calificado) */
  userRating?: number | null;
  /** Acciones de voto; si faltan (sin usuario) no se muestra el formulario */
  onRate?: (rating: number) => Promise<ActionResult>;
  onRemove?: () => Promise<ActionResult>;
}

export const CourseDetailComponent: FC<CourseDetailComponentProps> = ({
  course,
  userRating = null,
  onRate,
  onRemove,
}) => {
  const teacherNames = course.teachers?.map((teacher) => teacher.name).join(", ");
  const averageRating = course.average_rating ?? 0;
  const totalRatings = course.total_ratings ?? 0;

  return (
    <div className={styles.container}>
      <div className={styles.navigation}>
        <Link href="/" className={styles.backButton}>
          ← Volver a cursos
        </Link>
      </div>
      <div className={styles.header}>
        <div className={styles.thumbnailContainer}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={course.thumbnail} alt={course.name} className={styles.thumbnail} />
        </div>
        <div className={styles.courseInfo}>
          <h1 className={styles.title}>{course.name}</h1>
          {teacherNames && <p className={styles.teacher}>Por {teacherNames}</p>}
          <p className={styles.description}>{course.description}</p>
          <div className={styles.stats}>
            <span className={styles.classCount}>{course.classes.length} clases</span>
          </div>
        </div>
      </div>

      <section className={styles.ratingsSection} aria-labelledby="course-ratings-title">
        <h2 id="course-ratings-title" className={styles.sectionTitle}>
          Valoraciones
        </h2>
        <div className={styles.ratingsGrid}>
          <div className={styles.ratingSummary}>
            <div className={styles.averageRow}>
              <span className={styles.averageValue} aria-hidden="true">
                {averageRating.toFixed(1)}
              </span>
              <StarRating
                rating={averageRating}
                totalRatings={totalRatings}
                showCount={true}
                size="large"
              />
            </div>
            {course.rating_distribution && (
              <RatingDistribution
                distribution={course.rating_distribution}
                totalRatings={totalRatings}
              />
            )}
          </div>
          <div className={styles.ratingForm}>
            {onRate && onRemove ? (
              <RatingInput initialRating={userRating} onRate={onRate} onRemove={onRemove} />
            ) : (
              <p className={styles.ratingHint}>Inicia sesión para calificar este curso.</p>
            )}
          </div>
        </div>
      </section>

      <div className={styles.classesSection}>
        <h2 className={styles.sectionTitle}>Contenido del curso</h2>
        <div className={styles.classesList}>
          {course.classes.map((cls, index) => (
            <Link href={`/classes/${cls.id}`} key={cls.id} className={styles.classItem}>
              <div className={styles.classNumber}>{(index + 1).toString().padStart(2, "0")}</div>
              <div className={styles.classInfo}>
                <h3 className={styles.classTitle}>{cls.name}</h3>
                <p className={styles.classDescription}>{cls.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
