import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TopbarComponent } from '../topbar/topbar.component';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-processing',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './processing.component.html',
  styleUrls: ['./processing.component.css']
})
export class ProcessingComponent implements OnInit {
  researchUpdates: string = '';
  researchSentences: string[] = [
    'Analyzing market trends...',
    'Gathering competitor data...',
    'Assessing financial statements...',
    'Identifying industry benchmarks...',
    'Processing customer sentiment analysis...',
    'Extracting key regulatory changes...',
    'Mapping operational risks...'
  ];
  processingComplete = false;
  processingStartTime!: number;

  constructor(private router: Router, private http: HttpClient) {
    this.startFetchingUpdates();
  }

  ngOnInit() {
    this.processingStartTime = Date.now();
    this.simulateResearchUpdates();
  }

  simulateResearchUpdates() {
    const interval = setInterval(() => {
      const elapsedTime = (Date.now() - this.processingStartTime) / 1000;
      if (elapsedTime >= 8) {
        this.processingComplete = true;
        clearInterval(interval);
        setTimeout(() => {
          this.router.navigate(['/output']);
        }, 2000);
        return;
      }
      const sentence = this.getRandomSentence();
      this.researchUpdates += sentence + '\n';
    }, 2000);
  }

  getRandomSentence(): string {
    return this.researchSentences[Math.floor(Math.random() * this.researchSentences.length)];
  }

  private startFetchingUpdates() {
    const interval = setInterval(() => {
      this.http.get('https://18.191.231.140/read', { responseType: 'text' })
        .subscribe({
          next: (response) => {
            this.researchUpdates = response;
            if (response.includes('COMPLETE')) {  // Or whatever completion indicator you prefer
              this.processingComplete = true;
              clearInterval(interval);
            }
          },
          error: (error) => {
            console.error('Error fetching research updates:', error);
          }
        });
    }, 1000); // Poll every second
  }
}