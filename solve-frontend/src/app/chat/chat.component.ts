import { Component } from '@angular/core';
import { TopbarComponent } from '../topbar/topbar.component';
import { Router } from '@angular/router';
import { ChatApiService } from '../services/chat-api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
    selector: 'app-chat',
    imports: [CommonModule, FormsModule, TopbarComponent],
    templateUrl: './chat.component.html',
    styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  inputFields: { value: string, placeholder: string, locked: boolean }[] = [
    { value: '', placeholder: 'Enter company name(s)', locked: false }
  ];
  industryInputAdded = false;
  showCheckboxes = false;

  checkboxes = [
    { label: 'Operations and Management', checked: false },
    { label: 'Market Risks', checked: false },
    { label: 'Competitor Analysis', checked: false },
    { label: 'Potential Concerns', checked: false },
    { label: 'Industry Benchmarks', checked: false },
    { label: 'Legal Standing', checked: false }
  ];

  ellipses: string = ''; 
  ellipsesCount: number = 0;

  constructor(private router: Router, private chatApi: ChatApiService) {
    this.animateEllipses();
  }

  handleEnter(index: number) {
    if (!this.inputFields[index].locked) {
      this.inputFields[index].locked = true;

      if (index === 0 && !this.industryInputAdded) {
        this.inputFields.push({ value: '', placeholder: 'Enter the industry', locked: false });
        this.industryInputAdded = true;
      } else if (index === 1) {
        this.showCheckboxes = true;
      }
    }
  }

  enableEditing(index: number) {
    this.inputFields[index].locked = false;
  }

  toggleCheckbox(index: number) {
    this.checkboxes[index].checked = !this.checkboxes[index].checked;
  }

  submitForm() {
    this.router.navigate(['/processing']);
  }

  animateEllipses() {
    setInterval(() => {
      if (this.ellipsesCount < 3) {
        this.ellipsesCount++;
        this.ellipses = '.'.repeat(this.ellipsesCount);
      } else {
        this.ellipses = '...'; 
        setTimeout(() => {
          this.ellipsesCount = 0;
          this.ellipses = ''; 
        }, 400);
      }
    }, 600); // Adjust animation speed
  }
}
