import { Routes } from '@angular/router';
import { ProcessingWrapperComponent } from './processing-wrapper/processing-wrapper.component';
import { ChatComponent } from './chat/chat.component';

export const routes: Routes = [
  { path: '', redirectTo: '/processing', pathMatch: 'full' },
  { path: 'processing', component: ProcessingWrapperComponent },
  { path: 'chat', component: ChatComponent },
  // Add any other routes your app needs
];
