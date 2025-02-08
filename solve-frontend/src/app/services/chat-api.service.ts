import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatApiService {
  private apiUrl = 'http://localhost:5000/api/chat'; // Update w backend

  constructor(private http: HttpClient) {}

  sendMessage(message: string): Observable<any> {
    return this.http.post<any>(this.apiUrl, { message });
  }
}
