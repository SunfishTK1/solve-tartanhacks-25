import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatApiService {
  private apiUrl = 'http://0.0.0.0:8007/analyze'; // Updated API endpoint

  constructor(private http: HttpClient) {}

  sendUserData(userData: { company_name: string; industry: string; prompts: string[] }): Observable<any> {
    return this.http.post(this.apiUrl, userData);
  }
}
