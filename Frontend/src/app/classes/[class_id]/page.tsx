import { Class } from "@/types";
import { VideoPlayer } from "@/components/VideoPlayer/VideoPlayer";
import Link from "next/link";
import styles from "./page.module.scss";

interface ClassPageProps {
  params: Promise<{ class_id: string }>;
}

async function getClassData(class_id: string): Promise<Class> {
  const res = await fetch(`http://localhost:8000/classes/${class_id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("No se pudo cargar la clase");
  return res.json();
}

export default async function ClassPage({ params }: ClassPageProps) {
  const { class_id } = await params;
  const classData = await getClassData(class_id);

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
