// Cookie-scoped research library: saved articles + tracked topics, persisted
// in Upstash Redis (Vercel's current marketplace KV product — the old
// first-party @vercel/kv package is discontinued). Keyed by the opaque
// `cassandra_uid` cookie set in middleware.ts, so a returning visit on the
// same browser picks up prior saves without any account system.

import { Redis } from "@upstash/redis";
import { searchLiterature } from "./research/search";
import { summarizeResults, type ArticlePresentation } from "./research/summarize";

const redis = Redis.fromEnv();

const UIDS_SET_KEY = "library:uids";

export interface SavedArticle extends ArticlePresentation {
  savedAt: string;
}

export interface TrackedTopic {
  query: string;
  label: string;
  addedAt: string;
  /** Dedupe keys of every result already surfaced for this topic — the refresh cron only reports new ones. */
  seenKeys: string[];
}

export interface Library {
  trackedTopics: TrackedTopic[];
  savedArticles: SavedArticle[];
  /** Articles the refresh cron found for tracked topics, not yet saved or dismissed. */
  newFinds: SavedArticle[];
  lastRefresh: string | null;
}

const EMPTY_LIBRARY: Library = { trackedTopics: [], savedArticles: [], newFinds: [], lastRefresh: null };

function libraryKey(uid: string): string {
  return `library:${uid}`;
}

export function articleDedupeKey(a: Pick<ArticlePresentation, "doi" | "title">): string {
  return (a.doi || a.title).toLowerCase();
}

function topicDedupeKey(query: string): string {
  return query.trim().toLowerCase();
}

export async function getLibrary(uid: string): Promise<Library> {
  const data = await redis.get<Library>(libraryKey(uid));
  return data ?? EMPTY_LIBRARY;
}

async function putLibrary(uid: string, library: Library): Promise<void> {
  await redis.set(libraryKey(uid), library);
  await redis.sadd(UIDS_SET_KEY, uid);
}

export async function saveArticle(
  uid: string,
  article: ArticlePresentation,
): Promise<Library> {
  const library = await getLibrary(uid);
  const key = articleDedupeKey(article);
  if (!library.savedArticles.some((a) => articleDedupeKey(a) === key)) {
    library.savedArticles = [{ ...article, savedAt: new Date().toISOString() }, ...library.savedArticles];
  }
  library.newFinds = library.newFinds.filter((f) => articleDedupeKey(f) !== key);
  await putLibrary(uid, library);
  return library;
}

export async function trackTopic(uid: string, query: string, label?: string): Promise<Library> {
  const library = await getLibrary(uid);
  const key = topicDedupeKey(query);
  if (!library.trackedTopics.some((t) => topicDedupeKey(t.query) === key)) {
    library.trackedTopics = [
      { query: query.trim(), label: label?.trim() || query.trim(), addedAt: new Date().toISOString(), seenKeys: [] },
      ...library.trackedTopics,
    ];
    await putLibrary(uid, library);
  }
  return library;
}

export async function dismissNewFind(uid: string, key: string): Promise<Library> {
  const library = await getLibrary(uid);
  library.newFinds = library.newFinds.filter((f) => articleDedupeKey(f) !== key);
  await putLibrary(uid, library);
  return library;
}

export async function untrackTopic(uid: string, query: string): Promise<Library> {
  const library = await getLibrary(uid);
  const key = topicDedupeKey(query);
  library.trackedTopics = library.trackedTopics.filter((t) => topicDedupeKey(t.query) !== key);
  await putLibrary(uid, library);
  return library;
}

/** All uids with a library — used by the refresh cron to iterate tracked topics. */
export async function allLibraryUids(): Promise<string[]> {
  return (await redis.smembers(UIDS_SET_KEY)) as string[];
}

/**
 * Re-run every tracked topic's search for one library, appending genuinely new
 * results to `newFinds`. Called by the /api/cron/refresh route every ~2 days.
 */
export async function refreshLibrary(uid: string): Promise<{ uid: string; newCount: number }> {
  const library = await getLibrary(uid);
  let newCount = 0;

  for (const topic of library.trackedTopics) {
    const { results } = await searchLiterature(topic.query, { maxResults: 8 });
    if (results.length === 0) continue;

    const seen = new Set(topic.seenKeys);
    const unseen = results.filter((r) => !seen.has(articleDedupeKey(r)));
    if (unseen.length > 0) {
      const presented = await summarizeResults(unseen, topic.query);
      for (const p of presented) {
        const key = articleDedupeKey(p);
        const alreadyKnown =
          library.newFinds.some((f) => articleDedupeKey(f) === key) ||
          library.savedArticles.some((f) => articleDedupeKey(f) === key);
        if (!alreadyKnown) {
          library.newFinds = [{ ...p, savedAt: new Date().toISOString() }, ...library.newFinds];
          newCount++;
        }
      }
    }
    topic.seenKeys = Array.from(new Set([...topic.seenKeys, ...results.map(articleDedupeKey)]));
  }

  library.lastRefresh = new Date().toISOString();
  await putLibrary(uid, library);
  return { uid, newCount };
}
