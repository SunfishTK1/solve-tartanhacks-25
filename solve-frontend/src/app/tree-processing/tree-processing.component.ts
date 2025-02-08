import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TopbarComponent } from '../topbar/topbar.component';
import { HttpClient } from '@angular/common/http';
import { TreeNode } from './tree-node.interface';
import { SessionService } from '../services/session.service';
import { NgxGraphModule } from '@swimlane/ngx-graph';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { SummaryService } from '../services/summary.service';

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

export class TreeProcessingComponent implements OnInit, OnDestroy {
  sessionId: string = '';
  researchTree: TreeNode[] = [];
  processingComplete = false;
  graphData: any = { nodes: [], links: [] };
  currentSummary: string = 'Initializing research...';
  private summaryInterval: any;

  constructor(
    private router: Router, 
    private http: HttpClient,
    private sessionService: SessionService,
    private summaryService: SummaryService
  ) {}

  ngOnInit() {
    const existingSessionId = localStorage.getItem('research_session_id');
    if (existingSessionId) {
      this.sessionId = existingSessionId;
      this.startFetchingUpdates();
      this.startFetchingSummary();
    } else {
      this.createSession();
    }
  }

  ngOnDestroy() {
    if (this.summaryInterval) {
      clearInterval(this.summaryInterval);
    }
  }

  private startFetchingSummary() {
    // Initial fetch
    this.fetchSummary();
    
    // Set up periodic fetching
    this.summaryInterval = setInterval(() => {
      this.fetchSummary();
    }, 2000); // Poll every 2 seconds
  }

  private fetchSummary() {
    this.http.get<{content: string}>(`https://18.191.231.140/get_summary?session_id=${this.sessionId}`)
      .subscribe({
        next: (response) => {
          if (response && response.content) {
            this.currentSummary = response.content;
          }
        },
        error: (error) => {
          console.error('Error fetching summary:', error);
        }
      });
  }

  private createSession() {
    this.sessionService.createSession().subscribe({
      next: (response) => {
        this.sessionId = response.session_id;
        this.startFetchingUpdates();
        this.startFetchingSummary();
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
            this.updateGraphData(response[0]);
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

  private updateGraphData(response: TreeNode) {
    this.researchTree = [response]; // Wrap in array for compatibility
    this.summaryService.updateSummaries(this.researchTree);  // Update summaries
    this.graphData = this.convertToGraphFormat(response);
  }

  private convertToGraphFormat(data: TreeNode) {
    const graphNodes = [];
    const graphLinks = [];
    
    // Add root node for full report
    graphNodes.push({
      id: 'root',
      label: 'Full Report',
      data: { content: data.full_report }
    });

    // Add nodes for each subquestion
    data.subquestions.forEach((subq, index) => {
      const nodeId = `subq-${index}`;
      graphNodes.push({
        id: nodeId,
        label: subq.question,
        data: {
          content: subq.result,
          depth: subq.depth
        }
      });

      // Link to root node
      graphLinks.push({
        id: `link-${nodeId}`,
        source: 'root',
        target: nodeId
      });

      // Add nodes for other questions
      subq.other_questions.forEach((otherQ, otherIndex) => {
        const childId = `${nodeId}-child-${otherIndex}`;
        graphNodes.push({
          id: childId,
          label: otherQ,
          data: { depth: subq.depth + 1 }
        });

        graphLinks.push({
          id: `link-${childId}`,
          source: nodeId,
          target: childId
        });
      });
    });

    return { nodes: graphNodes, links: graphLinks };
  }
} 