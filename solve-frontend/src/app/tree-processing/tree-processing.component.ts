import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TopbarComponent } from '../topbar/topbar.component';
import { HttpClient } from '@angular/common/http';
import { TreeNode } from './tree-node.interface';
import { SessionService } from '../services/session.service';

@Component({
  selector: 'app-tree-processing',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './tree-processing.component.html',
  styleUrls: ['./tree-processing.component.css']
})

export class TreeProcessingComponent implements OnInit {
  sessionId: string = '';
  researchTree: TreeNode[] = [];
  processingComplete = false;

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
            this.researchTree = response;
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
} 