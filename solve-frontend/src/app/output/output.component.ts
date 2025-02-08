import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
  selector: 'app-output',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './output.component.html',
  styleUrls: ['./output.component.css']
})
export class OutputComponent implements OnInit {
  reportData: any = {
    full_report: "Comprehensive Due Diligence and Market Analysis Report: Starbucks Corporation (SBUX)...",
    subquestions: [
      {
        question: "What has been Starbucks' revenue growth trend over the past 5 years, and how does it compare to industry benchmarks?",
        result: "Over the past five years, Starbucks has demonstrated a solid revenue growth trend...",
        depth: 1,
        other_questions: [
          {
            question: "How does Starbucks' revenue compare to competitors?",
            result: "Starbucks maintains a competitive revenue stream, surpassing many industry players...",
            depth: 2,
            other_questions: [
              {
                question: "What are the key revenue drivers for Starbucks?",
                result: "Starbucks' key revenue drivers include premium product pricing, global expansion, and digital sales growth...",
                depth: 3,
                other_questions: []
              }
            ]
          },
          {
            question: "How has Starbucks' revenue changed in international markets?",
            result: "Starbucks has experienced significant growth in international markets, particularly in Asia...",
            depth: 2,
            other_questions: []
          },
          {
            question: "What impact do seasonal trends have on Starbucks' revenue?",
            result: "Seasonal trends significantly affect Starbucks' revenue, with holiday promotions driving higher sales...",
            depth: 2,
            other_questions: []
          }
        ]
      },
      {
        question: "How have Starbucks' profit margins evolved, and what factors are driving changes in profitability?",
        result: "Starbucks has demonstrated remarkable financial resilience...",
        depth: 1,
        other_questions: [
          {
            question: "What cost-cutting measures has Starbucks implemented?",
            result: "Starbucks has introduced strategic cost-cutting initiatives to improve efficiency...",
            depth: 2,
            other_questions: []
          }
        ]
      }
    ]
  };
  expandedSections: Set<string> = new Set();

  constructor() {}

  ngOnInit() {}

  toggleSection(question: string) {
    if (this.expandedSections.has(question)) {
      this.expandedSections.delete(question);
    } else {
      this.expandedSections.add(question);
    }
  }
}