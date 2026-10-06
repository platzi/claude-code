import "server-only";
import { cookies } from "next/headers";

/** Cookie con el id del usuario de prueba (modo demo, ver AUTH_MODE en el backend). */
export const USER_COOKIE = "pfx_uid";

function parseUserId(value: string | undefined): number | null {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
}

/**
 * Id del usuario actual, resuelto solo en el servidor: cookie `pfx_uid`
 * con fallback a la env `DEMO_USER_ID`. null si no hay usuario.
 */
export async function getCurrentUserId(): Promise<number | null> {
  const cookieStore = await cookies();
  return (
    parseUserId(cookieStore.get(USER_COOKIE)?.value) ?? parseUserId(process.env.DEMO_USER_ID)
  );
}
