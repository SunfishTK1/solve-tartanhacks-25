import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TreeProcessingComponent } from '../tree-processing/tree-processing.component';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
  selector: 'app-processing-wrapper',
  standalone: true,
  imports: [CommonModule, TreeProcessingComponent, TopbarComponent],
  template: `
    <app-topbar></app-topbar>
    <div class="wrapper-container">
      <app-tree-processing></app-tree-processing>
    </div>
  `,
  styles: [`
    .wrapper-container {
      width: 100%;
      max-width: 1400px;
      margin: 0 auto;
      padding: 1rem;
    }
  `]
})
export class ProcessingWrapperComponent {} 