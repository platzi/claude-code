import { FC } from "react";
import Link from "next/link";
import { CourseDetail } from "@/types";
import { RatingSection } from "@/components/RatingSection/RatingSection";
import styles from "./CourseDetail.module.scss";

interface CourseDetailComponentProps {
  course: CourseDetail;
}

export const CourseDetailComponent: FC<CourseDetailComponentProps> = ({ course }) => {
  const formatDuration = (duration: number) => {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const totalDuration = course.classes.reduce((acc, cls) => acc + cls.duration, 0);

  return (
    <div className={styles.container}>
      <div className={styles.navigation}>
        <Link href="/" className={styles.backButton}>
          ← Volver a cursos
        </Link>
      </div>
      <div className={styles.header}>
        <div className={styles.thumbnailContainer}>
          <img src={course.thumbnail} alt={course.name} className={styles.thumbnail} />
        </div>
        <div className={styles.courseInfo}>
          <h1 className={styles.title}>{course.name}</h1>
          <p className={styles.description}>{course.description}</p>
          <div className={styles.stats}>
            <span className={styles.duration}>Duración total: {formatDuration(totalDuration)}</span>
            <span className={styles.classCount}>{course.classes.length} clases</span>
          </div>
        </div>
      </div>

      <RatingSection
        courseId={course.id}
        initialStats={{
          average_rating: course.average_rating ?? 0,
          total_ratings: course.total_ratings ?? 0,
        }}
      />

      <div className={styles.classesSection}>
        <h2 className={styles.sectionTitle}>Contenido del curso</h2>
        <div className={styles.classesList}>
          {course.classes.map((cls, index) => (
            <Link href={`/classes/${cls.id}`} key={cls.id} className={styles.classItem}>
              <div className={styles.classNumber}>{(index + 1).toString().padStart(2, "0")}</div>
              <div className={styles.classInfo}>
                <h3 className={styles.classTitle}>{cls.title}</h3>
                <p className={styles.classDescription}>{cls.description}</p>
                <span className={styles.classDuration}>{formatDuration(cls.duration)}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
