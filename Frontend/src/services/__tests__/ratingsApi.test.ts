import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ratingsApi, ApiError } from '../ratingsApi';

const MOCK_RATING = {
  id: 1,
  course_id: 3,
  user_id: 7,
  rating: 4,
  created_at: '2026-09-28T10:00:00',
  updated_at: '2026-09-28T10:00:00',
};

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
  vi.useRealTimers();
});

describe('ratingsApi.getMyRating', () => {
  it('calls /ratings/me with the X-User-Id header', async () => {
    fetchMock.mockResolvedValue(jsonResponse(MOCK_RATING));

    const result = await ratingsApi.getMyRating(3, 7);

    expect(result).toEqual(MOCK_RATING);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/courses/3/ratings/me');
    expect(init.method).toBe('GET');
    expect(init.headers['X-User-Id']).toBe('7');
  });

  it('returns null when the user has not rated (RATING_NOT_FOUND)', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: 'User has not rated this course', code: 'RATING_NOT_FOUND' }, 404)
    );

    await expect(ratingsApi.getMyRating(3, 7)).resolves.toBeNull();
  });

  it('throws when the course does not exist (COURSE_NOT_FOUND)', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: 'Course with id 3 not found', code: 'COURSE_NOT_FOUND' }, 404)
    );

    await expect(ratingsApi.getMyRating(3, 7)).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      code: 'COURSE_NOT_FOUND',
    });
  });

  it('throws UNAUTHENTICATED on 401', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: 'Not authenticated', code: 'UNAUTHENTICATED' }, 401)
    );

    await expect(ratingsApi.getMyRating(3, 7)).rejects.toMatchObject({
      status: 401,
      code: 'UNAUTHENTICATED',
    });
  });
});

describe('ratingsApi.upsertMyRating', () => {
  it('sends PUT /ratings/me with the header and only the rating in the body', async () => {
    fetchMock.mockResolvedValue(jsonResponse(MOCK_RATING, 201));

    const result = await ratingsApi.upsertMyRating(3, 7, 4);

    expect(result).toEqual(MOCK_RATING);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/courses/3/ratings/me');
    expect(init.method).toBe('PUT');
    expect(init.headers['X-User-Id']).toBe('7');
    expect(JSON.parse(init.body)).toEqual({ rating: 4 });
  });

  it('throws with the backend detail on 422', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: 'Rating must be between 1 and 5, got 9', code: 'INVALID_RATING' }, 422)
    );

    await expect(ratingsApi.upsertMyRating(3, 7, 9)).rejects.toThrow(
      'Rating must be between 1 and 5, got 9'
    );
  });
});

describe('ratingsApi.deleteMyRating', () => {
  it('resolves on 204 without a body', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(ratingsApi.deleteMyRating(3, 7)).resolves.toBeUndefined();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/courses/3/ratings/me');
    expect(init.method).toBe('DELETE');
  });

  it('throws RATING_NOT_FOUND when there was nothing to delete', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: 'User has not rated this course', code: 'RATING_NOT_FOUND' }, 404)
    );

    await expect(ratingsApi.deleteMyRating(3, 7)).rejects.toMatchObject({
      code: 'RATING_NOT_FOUND',
    });
  });
});

describe('ratingsApi.getRatingStats', () => {
  it('does not hide a 404 for a missing course', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: 'Course with id 3 not found', code: 'COURSE_NOT_FOUND' }, 404)
    );

    await expect(ratingsApi.getRatingStats(3)).rejects.toBeInstanceOf(ApiError);
  });
});

describe('timeouts and network errors', () => {
  it('turns an aborted request into ApiError TIMEOUT', async () => {
    vi.useFakeTimers();
    fetchMock.mockImplementation(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError'))
          );
        })
    );

    const promise = ratingsApi.getRatingStats(3);
    const assertion = expect(promise).rejects.toMatchObject({ code: 'TIMEOUT', status: 408 });
    await vi.advanceTimersByTimeAsync(10000);

    await assertion;
  });

  it('turns a failed fetch into ApiError NETWORK_ERROR', async () => {
    fetchMock.mockRejectedValue(new TypeError('fetch failed'));

    await expect(ratingsApi.getRatingStats(3)).rejects.toMatchObject({ code: 'NETWORK_ERROR' });
  });
});

describe('non-network errors', () => {
  it('rethrows errors that fetch did not raise as network failures', async () => {
    const internal = new Error('Dynamic server usage');
    fetchMock.mockRejectedValue(internal);

    await expect(ratingsApi.getRatingStats(3)).rejects.toBe(internal);
  });
});
