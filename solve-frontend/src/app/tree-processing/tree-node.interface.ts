export interface TreeNode {
  topic: string;
  subtopics: TreeNode[];
  complete?: boolean;
} 