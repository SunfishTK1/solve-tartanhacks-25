import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProcessingComponent } from '../processing/processing.component';
import { TreeProcessingComponent } from '../tree-processing/tree-processing.component';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
  selector: 'app-processing-wrapper',
  standalone: true,
  imports: [CommonModule, ProcessingComponent, TreeProcessingComponent, TopbarComponent],
  template: `
    <app-topbar></app-topbar>
    <div class="wrapper-container">
      <app-processing></app-processing>
      <app-tree-processing></app-tree-processing>
    </div>
  `,
  styles: [`
    .wrapper-container {
      display: flex;
      width: 100%;
      max-width: 1400px;
      margin: 0 auto;
      padding: 1rem;
      gap: 2rem;
    }
    
    @media (max-width: 768px) {
      .wrapper-container {
        flex-direction: column;
      }
    }
  `]
})
export class ProcessingWrapperComponent {} 