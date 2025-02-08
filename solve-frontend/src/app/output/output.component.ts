import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
    selector: 'app-output',
    imports: [CommonModule, TopbarComponent],
    templateUrl: './output.component.html',
    styleUrls: ['./output.component.css']
})
export class OutputComponent {}
