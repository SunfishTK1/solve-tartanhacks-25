import { Routes } from '@angular/router';
import { ChatComponent } from './chat/chat.component';
import { ProcessingComponent } from './processing/processing.component';
import { OutputComponent } from './output/output.component';

export const routes: Routes = [
  { path: '', redirectTo: 'chat', pathMatch: 'full' },
  { path: 'chat', component: ChatComponent },
  { path: 'processing', component: ProcessingComponent },
  { path: 'output', component: OutputComponent },
];
