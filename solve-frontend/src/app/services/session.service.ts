import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class SessionService {
  private currentSessionId: string = '';

  constructor(private http: HttpClient) {}

  generate_report(): Observable<{session_id: string}> {
    // Clear existing session
    localStorage.removeItem('research_session_id');
    this.currentSessionId = '';
    
    // Create new session
    return this.createSession();
  }

  getCurrentSessionId(): string {
    return this.currentSessionId;
  }

  createSession(): Observable<{session_id: string}> {
    return this.http.post<{session_id: string}>('https://18.191.231.140/create_session', {})
      .pipe(
        tap(response => {
          console.log('Received session ID:', response.session_id);
          this.currentSessionId = response.session_id;
          localStorage.setItem('research_session_id', response.session_id);
        })
      );
  }
} 