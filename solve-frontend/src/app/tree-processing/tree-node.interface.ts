export interface SubQuestion {
  question: string;
  result: string;
  depth: number;
  other_questions: string[];
}

export interface TreeNode {
  full_report: string;
  subquestions: SubQuestion[];
} 