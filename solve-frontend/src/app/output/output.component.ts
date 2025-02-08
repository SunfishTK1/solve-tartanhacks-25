import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TopbarComponent } from '../topbar/topbar.component';
import { Router } from '@angular/router';

@Component({
  selector: 'app-output',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './output.component.html',
  styleUrls: ['./output.component.css']
})
export class OutputComponent implements OnInit {
  reportData: any; // remove the placeholder initialization
  expandedSections: Set<string> = new Set();

  constructor(private router: Router) {}

  ngOnInit() {
    const nav = this.router.getCurrentNavigation();
    if (nav && nav.extras.state && nav.extras.state['data']) {
      this.reportData = nav.extras.state['data']; // actual API results
    }
  }

  toggleSection(question: string) {
    if (this.expandedSections.has(question)) {
      this.expandedSections.delete(question);
    } else {
      this.expandedSections.add(question);
    }
  }
}
