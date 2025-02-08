import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
  selector: 'app-processing',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './processing.component.html',
  styleUrls: ['./processing.component.css']
})
export class ProcessingComponent implements OnInit {
  researchTree: any[] = [];
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

  constructor(private router: Router) {}

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
      this.addToTree(sentence);
    }, 2000);
  }

  getRandomSentence(): string {
    return this.researchSentences[Math.floor(Math.random() * this.researchSentences.length)];
  }

  addToTree(sentence: string) {
    if (this.researchTree.length === 0) {
      this.researchTree.push({ topic: sentence, subtopics: [] });
    } else {
      const parentIndex = Math.floor(Math.random() * this.researchTree.length);
      this.researchTree[parentIndex].subtopics.push({ topic: sentence, subtopics: [] });
    }
  }
}