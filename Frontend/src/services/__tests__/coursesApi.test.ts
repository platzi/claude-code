import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { coursesApi } from '../coursesApi';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('coursesApi', () => {
  it('getCourses fetches the catalog without caching', async () => {
    fetchMock.mockResolvedValue(jsonResponse([{ id: 1, name: 'React' }]));

    await expect(coursesApi.getCourses()).resolves.toEqual([{ id: 1, name: 'React' }]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/courses');
    expect(init.cache).toBe('no-store');
  });

  it('getCourses throws on server errors', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));

    await expect(coursesApi.getCourses()).rejects.toMatchObject({ name: 'ApiError', status: 500 });
  });

  it('getCourseBySlug encodes the slug and returns null on 404', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Course not found' }, 404));

    await expect(coursesApi.getCourseBySlug('curso de c++')).resolves.toBeNull();
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/courses/curso%20de%20c%2B%2B');
  });

  it('getClassById returns the class detail', async () => {
    const detail = { id: 19, title: 'Clase', description: 'd', slug: 's', video: 'v', duration: 0 };
    fetchMock.mockResolvedValue(jsonResponse(detail));

    await expect(coursesApi.getClassById('19')).resolves.toEqual(detail);
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/classes/19');
  });

  it('getClassById returns null on 404', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Class not found' }, 404));

    await expect(coursesApi.getClassById(999)).resolves.toBeNull();
  });
});
