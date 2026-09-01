export interface Paper {
  index: number;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
  abstractSnippet: string | null;
  source: "openalex" | "arxiv";
  linkOk: boolean;
}

export interface SearchStatus {
  unavailable: string[];
}
