import { cache } from "react";
import { notFound } from "next/navigation";
import { CourseDetail } from "@/types";
import { CourseDetailComponent } from "@/components/CourseDetail/CourseDetail";
import { getCurrentUserId } from "@/lib/currentUser";
import { coursesApi } from "@/services/coursesApi";
import { ratingsApi } from "@/services/ratingsApi";
import { rateCourse, removeRating } from "./actions";

interface CoursePageProps {
  params: Promise<{ slug: string }>;
}

// cache(): la página y generateMetadata comparten un solo fetch por request
const getCourseData = cache(async (slug: string): Promise<CourseDetail> => {
  const course = await coursesApi.getCourseBySlug(slug);

  if (!course) {
    notFound();
  }

  return course;
});

// Si falla la consulta del rating del usuario, la página se muestra igual
// (sin selección); el voto sigue funcionando porque el PUT es un upsert.
async function getUserRating(courseId: number, userId: number): Promise<number | null> {
  try {
    const rating = await ratingsApi.getMyRating(courseId, userId);
    return rating?.rating ?? null;
  } catch (error) {
    console.error("Failed to fetch user rating", error);
    return null;
  }
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { slug } = await params;
  const [courseData, userId] = await Promise.all([getCourseData(slug), getCurrentUserId()]);

  if (userId === null) {
    return <CourseDetailComponent course={courseData} />;
  }

  const userRating = await getUserRating(courseData.id, userId);

  return (
    <CourseDetailComponent
      course={courseData}
      userRating={userRating}
      onRate={rateCourse.bind(null, courseData.id, slug)}
      onRemove={removeRating.bind(null, courseData.id, slug)}
    />
  );
}

export async function generateMetadata({ params }: CoursePageProps) {
  const { slug } = await params;
  const courseData = await getCourseData(slug);

  return {
    title: `${courseData.name} - Curso Online`,
    description: courseData.description,
  };
}
