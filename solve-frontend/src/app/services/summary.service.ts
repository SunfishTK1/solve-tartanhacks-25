import { Injectable } from '@angular/core';
import { TreeNode } from '../tree-processing/tree-node.interface';

interface SummaryNode {
  id: string;
  content: string;
  children: string[];  // Array of child UUIDs
  lastUpdated: Date;
}

@Injectable({
  providedIn: 'root'
})
export class SummaryService {
  private summaries: Map<string, SummaryNode> = new Map();

  updateSummaries(treeData: TreeNode[]): void {
    // Create a map of current tree structure
    const currentTree = new Map<string, TreeNode>();
    treeData.forEach(node => currentTree.set(node.id, node));

    // Update or add new summaries
    treeData.forEach(node => {
      const existingSummary = this.summaries.get(node.id);
      const children = treeData
        .filter(n => n.parent_id === node.id)
        .map(n => n.id);

      if (!existingSummary) {
        // Add new summary
        this.summaries.set(node.id, {
          id: node.id,
          content: node.content || '',
          children: children,
          lastUpdated: new Date()
        });
      } else if (this.hasStructureChanged(existingSummary, children) || 
                 existingSummary.content !== node.content) {
        // Update existing summary if structure or content changed
        this.summaries.set(node.id, {
          ...existingSummary,
          content: node.content || existingSummary.content,
          children: children,
          lastUpdated: new Date()
        });
      }
    });

    // Remove obsolete summaries
    const currentIds = new Set(treeData.map(node => node.id));
    for (const [id] of this.summaries) {
      if (!currentIds.has(id)) {
        this.summaries.delete(id);
      }
    }
  }

  getSummary(uuid: string): SummaryNode | null {
    return this.summaries.get(uuid) || null;
  }

  getAllSummaries(): SummaryNode[] {
    return Array.from(this.summaries.values());
  }

  private hasStructureChanged(summary: SummaryNode, newChildren: string[]): boolean {
    if (summary.children.length !== newChildren.length) return true;
    return !summary.children.every(child => newChildren.includes(child));
  }
} 