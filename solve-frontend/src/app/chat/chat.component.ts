import { Component } from '@angular/core';
import { TopbarComponent } from '../topbar/topbar.component';
import { Router } from '@angular/router';
import { ChatApiService } from '../services/chat-api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarComponent],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  company_name: string = '';
  industry: string = '';
  promptOptions: string[] = [
    'Operations and Management',
    'Market Risks',
    'Competitor Analysis',
    'Potential Concerns',
    'Industry Benchmarks',
    'Legal Standing'
  ];
  selectedPrompts: string[] = [];
  
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

  constructor(private router: Router, private chatApi: ChatApiService) {}

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

  sendUserData() {
    const userData = {
      company_name: this.company_name,
      industry: this.industry,
      prompts: this.selectedPrompts
    };

    this.chatApi.sendUserData(userData).subscribe({
      next: (response) => {
        console.log('Data successfully sent to backend:', response);
        this.router.navigate(['/processing']);
      },
      error: (error) => {
        console.error('Error sending data:', error);
      }
    });
  }
}