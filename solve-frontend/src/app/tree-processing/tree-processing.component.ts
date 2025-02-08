import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TopbarComponent } from '../topbar/topbar.component';
import { HttpClient } from '@angular/common/http';
import { TreeNode } from './tree-node.interface';
import { SessionService } from '../services/session.service';
import { NgxGraphModule } from '@swimlane/ngx-graph';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';

@Component({
  selector: 'app-tree-processing',
  standalone: true,
  imports: [
    CommonModule, 
    TopbarComponent, 
    NgxGraphModule,
    MatTabsModule,
    MatExpansionModule
  ],
  templateUrl: './tree-processing.component.html',
  styleUrls: ['./tree-processing.component.css']
})

export class TreeProcessingComponent implements OnInit {
  sessionId: string = '';
  researchTree: TreeNode[] = [];
  processingComplete = false;
  graphData: any = { nodes: [], links: [] };
  summary: string = '';
  selectedNode: TreeNode | null = null;

  constructor(
    private router: Router, 
    private http: HttpClient,
    private sessionService: SessionService
  ) {}

  ngOnInit() {
    const existingSessionId = localStorage.getItem('research_session_id');
    if (existingSessionId) {
      this.sessionId = existingSessionId;
      this.startFetchingUpdates();
    } else {
      this.createSession();
    }
  }

  private createSession() {
    this.sessionService.createSession().subscribe({
      next: (response) => {
        this.sessionId = response.session_id;
        this.startFetchingUpdates();
      },
      error: (error) => {
        console.error('Error creating session:', error);
      }
    });
  }

  private startFetchingUpdates() {
    const interval = setInterval(() => {
      this.http.get<TreeNode[]>(`https://18.191.231.140/read_json?session_id=${this.sessionId}`)
        .subscribe({
          next: (response) => {
            this.updateGraphData(response);
            if (this.researchTree.some(node => node.complete)) {
              this.processingComplete = true;
              clearInterval(interval);
              setTimeout(() => {
                this.router.navigate(['/output']);
              }, 2000);
            }
          },
          error: (error) => {
            console.error('Error fetching research tree updates:', error);
          }
        });
    }, 1000); // Poll every second
  }

  private updateGraphData(response: TreeNode[]) {
    this.researchTree = response;
    this.graphData = this.convertToGraphFormat(response);
    this.summary = this.generateSummary(response);
  }

  private convertToGraphFormat(nodes: TreeNode[]) {
    // Convert TreeNode[] to format needed by ngx-graph
    const graphNodes = nodes.map(node => ({
      id: node.id,
      label: node.title || 'Node',
      data: node
    }));

    const graphLinks = nodes
      .filter(node => node.parent_id)
      .map(node => ({
        id: `${node.parent_id}-${node.id}`,
        source: node.parent_id,
        target: node.id
      }));

    return { nodes: graphNodes, links: graphLinks };
  }

  private generateSummary(nodes: TreeNode[]): string {
    const rootNode = nodes.find(node => !node.parent_id);
    return rootNode?.summary || 'Processing research data...';
  }
} 