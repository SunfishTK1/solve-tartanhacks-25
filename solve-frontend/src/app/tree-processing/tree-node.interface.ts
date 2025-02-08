export interface TreeNode {
  id: string;
  parent_id?: string;
  title: string;
  content: string;
  summary?: string;
  complete?: boolean;
  metrics?: {
    authority: number;
    relevance: number;
  };
} 