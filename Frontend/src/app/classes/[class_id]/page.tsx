import { notFound } from "next/navigation";
import { VideoPlayer } from "@/components/VideoPlayer/VideoPlayer";
import { coursesApi } from "@/services/coursesApi";
import Link from "next/link";
import styles from "./page.module.scss";

interface ClassPageProps {
  params: Promise<{ class_id: string }>;
}

export default async function ClassPage({ params }: ClassPageProps) {
  const { class_id } = await params;
  const classData = await coursesApi.getClassById(class_id);

  if (!classData) {
    notFound();
  }

  // Asumimos que classData tiene un campo 'slug' para el curso, si no, ajustar aquí
  // Si no hay relación directa, el botón puede regresar a /course
  return (
    <main className={styles.container}>
      <VideoPlayer src={classData.video} title={classData.title} />
      <h1 className={styles.title}>{classData.title}</h1>
      <p className={styles.description}>{classData.description}</p>
      <Link href="/course" className={styles.backButton}>
        ← Regresar al curso
      </Link>
    </main>
  );
}
